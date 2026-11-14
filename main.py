
import json
import re
import time
import math
from pathlib import Path

# 설정
EPSILON = 1e-9
REPEAT_COUNT = 10
DATA_FILE = Path(__file__).with_name("data.json")


# --------------------------------------------------
# 1. 행렬 입력 및 검증
# --------------------------------------------------

def parse_matrix(text, size):
    """공백으로 구분된 숫자를 행렬 한 행으로 변환한다."""

    tokens = text.strip().split()

    if len(tokens) != size:
        raise ValueError(
            f"각 줄에는 {size}개의 숫자를 입력해야 합니다."
        )

    try:
        row = [float(value) for value in tokens]
    except ValueError:
        raise ValueError("숫자만 입력할 수 있습니다.")

    if not all(math.isfinite(value) for value in row):
        raise ValueError(
            "nan이나 inf가 아닌 유효한 숫자를 입력하세요."
        )

    return row


def validate_matrix(matrix, name="행렬"):
    """정사각형 행렬인지, 숫자 데이터인지 검사한다."""

    if not isinstance(matrix, list) or len(matrix) == 0:
        raise ValueError(
            f"{name}: 올바른 2차원 배열이 아닙니다."
        )

    size = len(matrix)

    for row in matrix:
        if not isinstance(row, list):
            raise ValueError(
                f"{name}: 각 행은 리스트여야 합니다."
            )

        if len(row) != size:
            raise ValueError(
                f"{name}: 행과 열의 크기가 일치하지 않습니다."
            )

        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(
                    f"{name}: 유효하지 않은 숫자가 포함되어 있습니다."
                )

    return size


def input_matrix(size, name):
    """사용자에게 행렬을 입력받고 오류가 있으면 재입력한다."""

    print(f"\n{name} ({size}줄 입력, 공백 구분)")

    matrix = []

    for row_number in range(size):
        while True:
            text = input(
                f"{row_number + 1}번째 줄: "
            )

            try:
                row = parse_matrix(text, size)
                matrix.append(row)
                break

            except ValueError as error:
                print(f"입력 형식 오류: {error}")

    return matrix


# --------------------------------------------------
# 2. MAC 연산
# --------------------------------------------------

def mac(filter_matrix, input_matrix):
    """두 행렬의 같은 위치 값을 곱하고 모두 더한다."""

    size = validate_matrix(filter_matrix, "필터")
    input_size = validate_matrix(input_matrix, "입력 패턴")

    if size != input_size:
        raise ValueError(
            "필터와 입력 패턴의 크기가 다릅니다."
        )

    score = 0.0

    for row in range(size):
        for col in range(size):
            score += (
                filter_matrix[row][col]
                * input_matrix[row][col]
            )

    return score


# --------------------------------------------------
# 3. 점수 판정 및 라벨 정규화
# --------------------------------------------------

def decide(score_a, score_b, label_a, label_b):
    """epsilon 기준으로 두 점수를 비교한다."""

    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"

    if score_a > score_b:
        return label_a

    return label_b


def normalize_label(label):
    """입력 라벨을 Cross 또는 X로 통일한다."""

    if not isinstance(label, str):
        return None

    value = label.strip().lower()

    if value in ("+", "cross"):
        return "Cross"

    if value == "x":
        return "X"

    return None


def normalize_filter_keys(filter_info):
    """필터 딕셔너리의 키를 cross 또는 x로 통일한다."""

    if not isinstance(filter_info, dict):
        raise ValueError(
            "필터 데이터는 객체 형식이어야 합니다."
        )

    normalized = {}

    for key, value in filter_info.items():

        if not isinstance(key, str):
            raise ValueError(
                "필터 키는 문자열이어야 합니다."
            )

        key_normalized = key.strip().lower()

        if key_normalized in ("cross", "+"):
            standard_key = "cross"

        elif key_normalized == "x":
            standard_key = "x"

        else:
            raise ValueError(
                f"지원하지 않는 필터 키입니다: {key}"
            )

        if standard_key in normalized:
            raise ValueError(
                f"중복된 필터 키가 있습니다: {standard_key}"
            )

        normalized[standard_key] = value

    return normalized


# --------------------------------------------------
# 4. 성능 측정
# --------------------------------------------------

def average_mac_time(filter_matrix, input_data):
    """MAC 연산을 10회 반복하여 평균 시간을 측정한다."""

    start = time.perf_counter()

    for _ in range(REPEAT_COUNT):
        mac(filter_matrix, input_data)

    end = time.perf_counter()

    elapsed_ms = (end - start) * 1000

    return elapsed_ms / REPEAT_COUNT


def make_sample_matrix(size):
    """성능 측정용 입력 행렬을 생성한다."""

    return [
        [1.0 for _ in range(size)]
        for _ in range(size)
    ]


def print_performance(size, filter_matrix):
    """특정 크기의 MAC 평균 시간을 출력한다."""

    sample = make_sample_matrix(size)

    average_time = average_mac_time(
        filter_matrix,
        sample
    )

    operation_count = size * size

    print(
        f"{size} x {size} | "
        f"연산 횟수 {operation_count}회 | "
        f"평균 {average_time:.6f} ms"
    )


def print_user_performance(filter_matrix):
    print("\n=== 3 x 3 성능 분석 ===")

    print_performance(3, filter_matrix)


def print_json_performance(filters):
    """필터 키를 정규화한 뒤 크기별 성능을 측정한다."""

    print("\n=== 크기별 성능 분석 ===")

    for size in (3, 5, 13, 25):

        if size == 3:
            sample_filter = make_sample_matrix(3)

        else:
            size_data = filters.get(f"size_{size}")

            if not isinstance(size_data, dict):
                print(
                    f"{size} x {size} | "
                    "필터 데이터가 없어 측정할 수 없습니다."
                )
                continue

            try:
                normalized_filters = normalize_filter_keys(
                    size_data
                )

                sample_filter = normalized_filters.get("cross")

                if sample_filter is None:
                    raise ValueError(
                        "Cross 필터 데이터가 없습니다."
                    )

                validate_matrix(
                    sample_filter,
                    f"{size}x{size} 성능 측정 필터"
                )

                if len(sample_filter) != size:
                    raise ValueError(
                        "필터 크기가 일치하지 않습니다."
                    )

            except (TypeError, ValueError) as error:
                print(
                    f"{size} x {size} | "
                    f"측정 불가: {error}"
                )
                continue

        print_performance(size, sample_filter)


# --------------------------------------------------
# 5. 사용자 입력 모드
# --------------------------------------------------

def user_mode():
    print("\n=== 사용자 입력 모드 ===")

    filter_a = input_matrix(3, "필터 A")
    filter_b = input_matrix(3, "필터 B")

    print("\n필터 입력이 완료되었습니다.")

    input_data = input_matrix(3, "패턴")

    try:
        score_a = mac(filter_a, input_data)
        score_b = mac(filter_b, input_data)

        result = decide(
            score_a,
            score_b,
            "A",
            "B"
        )

        print("\n=== MAC 결과 ===")
        print(f"A 점수: {score_a:.6f}")
        print(f"B 점수: {score_b:.6f}")

        if result == "UNDECIDED":
            print(
                f"판정: 판정 불가 "
                f"(|A-B| < {EPSILON})"
            )
        else:
            print(f"판정: {result}")

        print_user_performance(filter_a)

    except (TypeError, ValueError) as error:
        print(f"연산 오류: {error}")


# --------------------------------------------------
# 6. JSON 파일 읽기
# --------------------------------------------------

def load_data():
    """현재 main.py와 같은 폴더의 data.json을 읽는다."""

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8-sig"
    ) as file:
        return json.load(file)


# --------------------------------------------------
# 7. JSON 분석 모드
# --------------------------------------------------

def json_mode():
    print("\n=== JSON 분석 모드 ===")

    try:
        data = load_data()

    except (OSError, json.JSONDecodeError) as error:
        print(
            f"데이터 파일을 읽지 못했습니다: {error}"
        )
        return

    if not isinstance(data, dict):
        print(
            "데이터 형식 오류: JSON 최상위 항목은 객체여야 합니다."
        )
        return

    filters = data.get("filters")
    patterns = data.get("patterns")

    if not isinstance(filters, dict):
        print(
            "데이터 형식 오류: filters는 객체여야 합니다."
        )
        return

    if not isinstance(patterns, dict):
        print(
            "데이터 형식 오류: patterns는 객체여야 합니다."
        )
        return

    total = 0
    passed = 0
    failed = 0
    failures = []

    print("\n=== 패턴 분석 ===")

    for pattern_id, pattern_info in patterns.items():
        total += 1

        try:
            if not isinstance(pattern_info, dict):
                raise ValueError(
                    "패턴 데이터가 객체 형식이 아닙니다."
                )

            # 패턴 ID에서 크기 추출
            match = re.fullmatch(
                r"size_(\d+)_(\d+)",
                pattern_id
            )

            if not match:
                raise ValueError(
                    "패턴 ID 형식이 올바르지 않습니다."
                )

            size = int(match.group(1))

            if size not in (5, 13, 25):
                raise ValueError(
                    f"지원하지 않는 행렬 크기입니다: {size}"
                )

            # 해당 크기의 필터 가져오기
            filter_info = filters.get(
                f"size_{size}"
            )

            if not isinstance(filter_info, dict):
                raise ValueError(
                    f"size_{size} 필터 데이터가 없습니다."
                )

            # 필터 키 정규화
            normalized_filters = normalize_filter_keys(
                filter_info
            )

            if "cross" not in normalized_filters:
                raise ValueError(
                    "Cross 필터 데이터가 없습니다."
                )

            if "x" not in normalized_filters:
                raise ValueError(
                    "X 필터 데이터가 없습니다."
                )

            # 입력 패턴 가져오기
            input_data = pattern_info.get("input")

            input_size = validate_matrix(
                input_data,
                "입력 패턴"
            )

            if input_size != size:
                raise ValueError(
                    "입력 패턴 크기가 패턴 ID와 다릅니다."
                )

            # 정규화된 키로 필터 가져오기
            cross_filter = normalized_filters["cross"]
            x_filter = normalized_filters["x"]

            cross_size = validate_matrix(
                cross_filter,
                "Cross 필터"
            )

            x_size = validate_matrix(
                x_filter,
                "X 필터"
            )

            # 필터 크기 검증
            if cross_size != size:
                raise ValueError(
                    "Cross 필터 크기가 패턴 ID와 다릅니다."
                )

            if x_size != size:
                raise ValueError(
                    "X 필터 크기가 패턴 ID와 다릅니다."
                )

            # MAC 연산
            cross_score = mac(
                cross_filter,
                input_data
            )

            x_score = mac(
                x_filter,
                input_data
            )

            # 판정
            result = decide(
                cross_score,
                x_score,
                "Cross",
                "X"
            )

            # expected 정규화
            expected = normalize_label(
                pattern_info.get("expected")
            )

            if expected is None:
                raise ValueError(
                    "expected 라벨이 올바르지 않습니다."
                )

            # PASS / FAIL 비교
            is_pass = result == expected

            if is_pass:
                passed += 1
                status = "PASS"

            else:
                failed += 1
                status = "FAIL"

                if result == "UNDECIDED":
                    reason = (
                        "두 점수가 epsilon 기준으로 동점"
                    )
                else:
                    reason = (
                        f"예상 {expected}, 실제 {result}"
                    )

                failures.append(
                    (pattern_id, reason)
                )

            # 결과 출력
            print(f"\n[{pattern_id}] {status}")
            print(
                f"Cross 점수: {cross_score:.6f} | "
                f"X 점수: {x_score:.6f}"
            )
            print(
                f"판정: {result} | 정답: {expected}"
            )

        except (KeyError, TypeError, ValueError) as error:
            failed += 1

            failures.append(
                (pattern_id, str(error))
            )

            print(
                f"\n[{pattern_id}] FAIL - {error}"
            )

    # 전체 결과
    print("\n=== 테스트 요약 ===")
    print(f"전체 테스트: {total}")
    print(f"통과: {passed}")
    print(f"실패: {failed}")

    if failures:
        print("\n실패 케이스:")

        for case_id, reason in failures:
            print(f"- {case_id}: {reason}")

    # 성능 분석
    print_json_performance(filters)


# --------------------------------------------------
# 8. 프로그램 시작
# --------------------------------------------------

def main():
    while True:
        print("\n=== Mini NPU Simulator ===")
        print("\n1. 사용자 입력 모드")
        print("2. JSON 분석 모드")
        print("0. 종료")

        choice = input(
            "\n실행 모드를 선택하세요: "
        ).strip()

        if choice == "1":
            user_mode()

        elif choice == "2":
            json_mode()

        elif choice == "0":
            print("프로그램을 종료합니다.")
            break

        else:
            print(
                "잘못된 선택입니다. 다시 입력하세요."
            )


if __name__ == "__main__":
    main()
