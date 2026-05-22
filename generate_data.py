import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 0. 초기 설정 및 시드 고정
# ---------------------------------------------------------
np.random.seed(42)
random.seed(42)

surnames = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서']
first_names = ['정희', '하은', '유진', '준우', '민준', '서연', '은정', '미숙', '지훈', '현우', '도윤', '영희', '철수', '수민', '재성', '다은']

def generate_korean_name():
    return random.choice(surnames) + random.choice(first_names)

def generate_phone_number():
    return f"010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

# ---------------------------------------------------------
# 1. 은행 및 지점 데이터 생성
# ---------------------------------------------------------

# 실제 칼럼 바인딩을 위해 한글 표준 스펙 변환 적용
df_bank = pd.DataFrame([
    {"은행ID": 1, "은행명": "A은행", "타행수수료": 1000},
    {"은행ID": 2, "은행명": "B은행", "타행수수료": 1000}
])

branches = [
    {"지점ID": 1, "은행ID": 1, "지점명": "강남지점", "주소": "서울시 강남구 테헤란로 12"},
    {"지점ID": 2, "은행ID": 1, "지점명": "홍대지점", "주소": "서울시 마포구 양화로 45"},
    {"지점ID": 3, "은행ID": 1, "지점명": "종로지점", "주소": "서울시 종로구 세종대로 78"},
    {"지점ID": 4, "은행ID": 1, "지점명": "여의도지점", "주소": "서울시 영등포구 의사당대로 99"},
    {"지점ID": 5, "은행ID": 1, "지점명": "신촌지점", "주소": "서울시 서대문구 신촌로 21"},
    {"지점ID": 6, "은행ID": 2, "지점명": "강서지점", "주소": "서울시 강서구 화곡로 102"},
    {"지점ID": 7, "은행ID": 2, "지점명": "마포지점", "주소": "서울시 마포구 마포대로 55"},
    {"지점ID": 8, "은행ID": 2, "지점명": "성수지점", "주소": "서울시 성동구 아차산로 88"},
    {"지점ID": 9, "은행ID": 2, "지점명": "잠실지점", "주소": "서울시 송파구 올림픽로 14"},
    {"지점ID": 10, "은행ID": 2, "지점명": "이태원지점", "주소": "서울시 용산구 이태원로 30"}
]
df_branch = pd.DataFrame(branches)

# ---------------------------------------------------------
# 2. 관리자 데이터 생성
# ---------------------------------------------------------
admin_list = []
admin_list.append({
    "관리자ID": 1, "지점ID": 1, "이름": "김민준",
    "로그인아이디": "super_a", "비밀번호해시": "$2b$12$eXAmPlEhAsHeDpAsSwOrD11111111111111",
    "권한등급": "슈퍼", "생성일시": datetime(2023, 1, 1, 9, 0, 0)
})
admin_list.append({
    "관리자ID": 2, "지점ID": 6, "이름": "박서연",
    "로그인아이디": "super_b", "비밀번호해시": "$2b$12$eXAmPlEhAsHeDpAsSwOrD22222222222222",
    "권한등급": "슈퍼", "생성일시": datetime(2023, 1, 1, 9, 0, 0)
})

for i, br in enumerate(branches):
    admin_list.append({
        "관리자ID": i + 3, "지점ID": br["지점ID"], "이름": generate_korean_name(),
        "로그인아이디": f"admin_{br['지점ID']}", "비밀번호해시": f"$2b$12$examplehashedpassword{i+3:02d}uniquevals",
        "권한등급": "일반", "생성일시": datetime(2023, 1, 2, 9, 0, 0)
    })
df_admin = pd.DataFrame(admin_list)

# 🔥 [해결 1] '일반' 관리자만 필터링하여 현장 업무 풀링용 맵 빌딩 (슈퍼관리자 배정 원천 차단)
field_admins = df_admin[df_admin["권한등급"] == "일반"]

branch_to_admins = (
    field_admins
    .groupby("지점ID")["관리자ID"]
    .apply(list)
    .to_dict()
)

# ---------------------------------------------------------
# 3. ATM 기본 빌딩 및 상태 비율 보장 기법
# ---------------------------------------------------------

atm_status_pool = ['장애'] * 3 + ['점검중'] * 6 + ['정상'] * 21
random.shuffle(atm_status_pool)

atm_raw_list = []
atm_id_counter = 1
threshold_options = [500000, 1000000, 1500000, 2000000]
atm_time_tracker = {}

for br in branches:
    for _ in range(3):
        atm_id = atm_id_counter
        status = atm_status_pool[atm_id_counter - 1]
        threshold = random.choice(threshold_options)

        if atm_id_counter == 19:
            cash = 19610
            threshold = 1000000
        elif atm_id_counter == 20:
            cash = 99914
            threshold = 1000000
        else:
            cash = random.randint(500000, 10000000)

        cash_status = "현금부족경고" if cash < threshold else "정상"
        atm_time_tracker[atm_id] = [datetime(2024, 1, 1, 0, 0, 0)]

        atm_raw_list.append({
            "ATM_ID": atm_id,
            "지점ID": br["지점ID"],
            "상태": status,
            "현금잔량": cash,
            "경고임계값": threshold,
            "ATM현금상태": cash_status
        })

        atm_id_counter += 1

atm_lookup = {a["ATM_ID"]: a for a in atm_raw_list}
branch_lookup = {b["지점ID"]: b for b in branches}

final_faulty_atm_ids = [
    a["ATM_ID"]
    for a in atm_raw_list
    if a["상태"] == "장애"
]

# ---------------------------------------------------------
# 4. 고객 및 계좌 데이터 생성 (Unique 제약 조건 고도화)
# ---------------------------------------------------------
customers = []
for i in range(1, 101):
    customers.append({"고객ID": i, "이름": generate_korean_name(), "전화번호": generate_phone_number()})
df_customer = pd.DataFrame(customers)

accounts = []
acc_id_counter = 1
used_account_numbers = set() # 🔥 [해결 2] 중복 계좌 검증용 고속 집합 구조 선언

for cust in customers:
    num_accounts = random.choices([1, 2], weights=[0.58, 0.42])[0]
    for _ in range(num_accounts):
        b_id = random.choice([1, 2])
        prefix = "110" if b_id == 1 else "220"

        # 🔥 [해결 2] 유일성이 보장될 때까지 무한 루프 검증 (중복 발생 가능성 0% 확보)
        while True:
            acc_num = f"{prefix}-{random.randint(100,999)}-{random.randint(100000,999999)}"
            if acc_num not in used_account_numbers:
                used_account_numbers.add(acc_num)
                break

        open_date = datetime(2023, 12, 31) - timedelta(days=random.randint(0, 1000))

        accounts.append({
            "계좌ID": acc_id_counter,
            "고객ID": cust["고객ID"],
            "계좌번호": acc_num,
            "잔액": random.randint(5000000, 50000000),
            "개설일": open_date.date(),
            "은행ID": b_id
        })
        acc_id_counter += 1

df_account = pd.DataFrame(accounts)


# ---------------------------------------------------------
# 5. 거래내역 풀링 및 시간순 시뮬레이션
# ---------------------------------------------------------

temp_tx_pool = []
start_tx_date = datetime(2024, 1, 1)

# ✅ 장애 ATM 제외 (수정)
usable_atm_ids = [
    atm["ATM_ID"]
    for atm in atm_raw_list
    if atm["상태"] != "장애"
]

for _ in range(250):
    temp_tx_pool.append({
        "ATM_ID": random.choice(usable_atm_ids),
        "계좌ID": random.choice(df_account["계좌ID"].tolist()),
        "연관거래ID": None,
        "거래유형": "출금",
        "거래금액": random.randint(1, 50) * 10000,
        "거래일시": start_tx_date + timedelta(
            days=random.randint(0, 720),
            seconds=random.randint(0, 86400)
        ),
        "상대계좌ID": None
    })

for _ in range(150):
    temp_tx_pool.append({
        "ATM_ID": random.choice(usable_atm_ids),
        "계좌ID": random.choice(df_account["계좌ID"].tolist()),
        "연관거래ID": None,
        "거래유형": "입금",
        "거래금액": random.randint(1, 100) * 10000,
        "거래일시": start_tx_date + timedelta(
            days=random.randint(0, 720),
            seconds=random.randint(0, 86400)
        ),
        "상대계좌ID": None
    })

for _ in range(50):
    from_id = random.choice(df_account["계좌ID"].tolist())

    temp_tx_pool.append({
        "ATM_ID": random.choice(usable_atm_ids),
        "계좌ID": from_id,
        "연관거래ID": "LINKED",
        "거래유형": "이체(출금)",
        "거래금액": random.randint(1, 30) * 10000,
        "거래일시": start_tx_date + timedelta(
            days=random.randint(0, 720),
            seconds=random.randint(0, 86400)
        ),
        "상대계좌ID": random.choice([
            i for i in df_account["계좌ID"].tolist()
            if i != from_id
        ])
    })

temp_tx_pool.sort(key=lambda x: x["거래일시"])

final_tx_list = []
tx_id_counter = 1

account_balance_dict = df_account.set_index("계좌ID")["잔액"].to_dict()
account_bank_dict = df_account.set_index("계좌ID")["은행ID"].to_dict()

atm_cash_dict = {
    atm["ATM_ID"]: atm["현금잔량"]
    for atm in atm_raw_list
}

for tx in temp_tx_pool:

    atm_id = tx["ATM_ID"]
    acc_id = tx["계좌ID"]
    tx_time = tx["거래일시"]
    amount = tx["거래금액"]
    g_type = tx["거래유형"]

    atm_bank_id = branch_lookup[atm_lookup[atm_id]["지점ID"]]["은행ID"]
    acc_bank_id = account_bank_dict[acc_id]

    base_status = random.choices(
        ["성공", "실패"],
        weights=[0.95, 0.05]
    )[0]

    # -------------------------------------------------
    # 출금
    # -------------------------------------------------
    if g_type == "출금":

        fee = 1000 if (
            atm_bank_id != acc_bank_id
            and base_status == "성공"
        ) else 0

        # ✅ ATM 현금 부족 검증 복구
        if (
            base_status == "성공"
            and account_balance_dict[acc_id] >= (amount + fee)
            and atm_cash_dict[atm_id] >= amount
        ):

            account_balance_dict[acc_id] -= (amount + fee)
            atm_cash_dict[atm_id] -= amount
            status = "성공"

        else:
            status = "실패"
            fee = 0

        atm_time_tracker[atm_id].append(tx_time)

        final_tx_list.append({
            "거래ID": tx_id_counter,
            "ATM_ID": atm_id,
            "계좌ID": acc_id,
            "연관거래ID": None,
            "거래유형": "출금",
            "거래금액": amount,
            "수수료": fee,
            "처리상태": status,
            "거래일시": tx_time
        })

        tx_id_counter += 1

    # -------------------------------------------------
    # 입금
    # -------------------------------------------------
    elif g_type == "입금":

        if base_status == "성공":
            account_balance_dict[acc_id] += amount
            atm_cash_dict[atm_id] += amount
            status = "성공"
        else:
            status = "실패"

        atm_time_tracker[atm_id].append(tx_time)

        final_tx_list.append({
            "거래ID": tx_id_counter,
            "ATM_ID": atm_id,
            "계좌ID": acc_id,
            "연관거래ID": None,
            "거래유형": "입금",
            "거래금액": amount,
            "수수료": 0,
            "처리상태": status,
            "거래일시": tx_time
        })

        tx_id_counter += 1

    # -------------------------------------------------
    # 이체
    # -------------------------------------------------
    elif g_type == "이체(출금)":

        to_id = tx["상대계좌ID"]

        fee = 1000 if (
            atm_bank_id != acc_bank_id
            and base_status == "성공"
        ) else 0

        if (
            base_status == "성공"
            and account_balance_dict[acc_id] >= (amount + fee)
        ):

            # ✅ 계좌 간 전산 이체만 수행
            account_balance_dict[acc_id] -= (amount + fee)
            account_balance_dict[to_id] += amount

            status = "성공"

        else:
            status = "실패"
            fee = 0

        atm_time_tracker[atm_id].append(tx_time)

        final_tx_list.append({
            "거래ID": tx_id_counter,
            "ATM_ID": atm_id,
            "계좌ID": acc_id,
            "연관거래ID": tx_id_counter + 1,
            "거래유형": "이체(출금)",
            "거래금액": amount,
            "수수료": fee,
            "처리상태": status,
            "거래일시": tx_time
            })

        final_tx_list.append({
            "거래ID": tx_id_counter + 1,
            "ATM_ID": atm_id,
            "계좌ID": to_id,
            "연관거래ID": tx_id_counter,
            "거래유형": "이체(입금)",
            "거래금액": amount,
            "수수료": 0,
            "처리상태": status,
            "거래일시": tx_time
        })

        tx_id_counter += 2

df_transaction = pd.DataFrame(final_tx_list)


# ---------------------------------------------------------
# 6. ATM장애로그 생성
# ---------------------------------------------------------

fail_list = []
fail_id_counter = 1
fail_specs = {
    "현금부족": "내부 현금 보관 잔액 부족",
    "기계오류": "지폐 방출기 세그먼트 걸림",
    "네트워크": "통신 모듈 패킷 유실",
    "전산오류": "IC 버퍼 오버플로우",
    "카드리더오류": "셔터 개폐 비정상"
}
fail_types = list(fail_specs.keys())
resolved_fault_registry = {}

for i in range(1, 41):
    # 정각(10:00:00) 기점에서 며칠 뒤, 그리고 무작위 시/분/초를 '더해' 나갑니다.
    fail_time = datetime(2024, 2, 1, 10, 0, 0) + timedelta(
        days=i * 12,
        hours=random.randint(1, 11),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )

    if i <= 12:
        status = "미처리"
        atm_id = final_faulty_atm_ids[(i - 1) % len(final_faulty_atm_ids)]
    else:
        status = "처리완료"
        normal_candidate_atms = [atm["ATM_ID"] for atm in atm_raw_list if atm["ATM_ID"] not in final_faulty_atm_ids]
        atm_id = random.choice(normal_candidate_atms)

    atm_branch_id = atm_lookup[atm_id]["지점ID"]
    assigned_admin = random.choice(branch_to_admins[atm_branch_id])
    resolved_at = None

    if status == "처리완료":
        # 발생 시점(fail_time)에 정확히 무작위 시/분/초를 '누적'하여 더하므로 시간 역전이 불가능합니다.
        resolved_at = fail_time + timedelta(
            hours=random.randint(1, 4),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        resolved_fault_registry[fail_id_counter] = {"atm_id": atm_id, "resolved_at": resolved_at}

    atm_time_tracker[atm_id].append(fail_time)
    if resolved_at:
        atm_time_tracker[atm_id].append(resolved_at)

    f_type = random.choice(fail_types)
    fail_list.append({
        "장애ID": fail_id_counter, "ATM_ID": atm_id, "관리자ID": assigned_admin,
        "장애유형": f_type, "상세내용": fail_specs[f_type],
        "처리상태": status, "발생일시": fail_time, "처리완료일시": resolved_at
    })
    fail_id_counter += 1
df_failure_log = pd.DataFrame(fail_list)

# ---------------------------------------------------------
# 6-1. 지점장애로그 생성
# ---------------------------------------------------------

branch_fail_list = []
branch_fail_specs = {
    "서버오류": "지점 내부 서버 응답 없음",
    "네트워크": "지점 통신 회선 단절",
    "전산오류": "지점 전산 시스템 오류",
    "전력이상": "지점 전력 공급 불안정"
}
branch_fail_types = list(branch_fail_specs.keys())
branch_fail_id = 1

for branch in branches:
    branch_id = branch["지점ID"]
    available_admins = branch_to_admins.get(branch_id, [])

    # 정각 기점에 지점ID별 가중치 + 무작위 분/초 부여
    fail_time = datetime(2024, 3, 1, 9, 0, 0) + timedelta(
        days=branch_id * 20,
        hours=branch_id * 2,
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )

    if branch_id <= 3:
        status = "미처리"; resolved_at = None; assigned_admin = None
    else:
        status = "처리완료"
        # 발생시간 이후로 무작위 분/초가 자연스럽게 흘러가도록 설정
        resolved_at = fail_time + timedelta(
            hours=branch_id * 1,
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        assigned_admin = available_admins[0] if available_admins else None

    f_type = branch_fail_types[branch_id % len(branch_fail_types)]
    branch_fail_list.append({
        "지점장애ID": branch_fail_id, "지점ID": branch_id, "관리자ID": assigned_admin,
        "장애유형": f_type, "상세내용": branch_fail_specs[f_type],
        "처리상태": status, "발생일시": fail_time, "처리완료일시": resolved_at
    })
    branch_fail_id += 1
df_branch_failure = pd.DataFrame(branch_fail_list)

# ---------------------------------------------------------
# 6-2. 은행장애로그 생성
# ---------------------------------------------------------

bank_fail_list = []
bank_fail_specs = {
    "전산망장애": "은행 전체 전산망 일시 중단",
    "보안시스템오류": "보안 인증 시스템 응답 없음",
    "데이터베이스오류": "중앙 DB 연결 불가",
    "네트워크": "은행 내부 네트워크 패킷 유실"
}
bank_fail_types = list(bank_fail_specs.keys())
bank_fail_id = 1

for bank in [{"은행ID": 1, "은행명": "A은행"}, {"은행ID": 2, "은행명": "B은행"}]:
    bank_id = bank["은행ID"]
    for j in range(1, 4):
        fail_time = datetime(2024, 4, 1, 10, 0, 0) + timedelta(
            days=bank_id * 30 + j * 10,
            hours=j * 3,
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        if j == 1:
            status = "미처리"; resolved_at = None; assigned_admin = None
        else:
            status = "처리완료"
            resolved_at = fail_time + timedelta(
                hours=j * 2,
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            super_admin = df_admin[
                (df_admin["권한등급"] == "슈퍼") &
                (df_admin["지점ID"].isin(
                    df_branch[df_branch["은행ID"] == bank_id]["지점ID"].tolist()
                    ))
            ]["관리자ID"].values
            assigned_admin = int(super_admin[0]) if len(super_admin) > 0 else None

        f_type = bank_fail_types[(bank_id + j) % len(bank_fail_types)]
        bank_fail_list.append({
            "은행장애ID": bank_fail_id, "은행ID": bank_id, "관리자ID": assigned_admin,
            "장애유형": f_type, "상세내용": bank_fail_specs[f_type],
            "처리상태": status, "발생일시": fail_time, "처리완료일시": resolved_at
        })
        bank_fail_id += 1
df_bank_failure = pd.DataFrame(bank_fail_list)


# ---------------------------------------------------------
# 7. 현금보충 생성 (일반 관리자 전용 배정)
# ---------------------------------------------------------

replenish_list = []

for i in range(1, 41):
    atm_id = random.choice(range(1, 31))
    atm_branch_id = atm_lookup[atm_id]["지점ID"]
    assigned_admin = random.choice(branch_to_admins[atm_branch_id])

    # 보충 일시 정각 기점에 랜덤 분/초 믹스
    rep_time = datetime(2024, 3, 15, 9, 0, 0) + timedelta(
        days=i * 14,
        hours=random.randint(1, 5),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )

    replenish_amount = random.randint(1, 10) * 1000000
    atm_cash_dict[atm_id] += replenish_amount
    atm_time_tracker[atm_id].append(rep_time)

    replenish_list.append({
        "보충ID": i, "ATM_ID": atm_id, "관리자ID": assigned_admin,
        "보충금액": replenish_amount, "보충일시": rep_time
    })

df_replenishment = pd.DataFrame(replenish_list)

# ---------------------------------------------------------
# 8. 유지보수이력 생성
# ---------------------------------------------------------
maint_list = []
maint_id = 1

# 처리완료 장애 전부 유지보수이력 생성
for fault_id, fault_info in resolved_fault_registry.items():
    atm_id = fault_info["atm_id"]
    base_resolved_time = fault_info["resolved_at"]
    maint_time = base_resolved_time + timedelta(
        minutes=random.randint(10, 119),
        seconds=random.randint(0, 59)
    )
    atm_branch_id = atm_lookup[atm_id]["지점ID"]
    assigned_admin = random.choice(branch_to_admins[atm_branch_id])
    atm_time_tracker[atm_id].append(maint_time)
    maint_list.append({
        "이력ID": maint_id,
        "ATM_ID": atm_id,
        "관리자ID": assigned_admin,
        "장애ID": fault_id,
        "점검내용": "장애 복구 점검",
        "점검일시": maint_time
    })
    maint_id += 1

# 정기 점검 추가 (총 40건)
while maint_id <= 40:
    atm_id = random.choice(range(1, 31))
    maint_time = datetime(2024, 1, 10, 10, 0, 0) + timedelta(
        days=maint_id * 15,
        hours=random.randint(1, 5),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    atm_branch_id = atm_lookup[atm_id]["지점ID"]
    assigned_admin = random.choice(branch_to_admins[atm_branch_id])
    atm_time_tracker[atm_id].append(maint_time)
    maint_list.append({
        "이력ID": maint_id,
        "ATM_ID": atm_id,
        "관리자ID": assigned_admin,
        "장애ID": None,
        "점검내용": "정기 점검",
        "점검일시": maint_time
    })
    maint_id += 1

df_maintenance = pd.DataFrame(maint_list)

# ---------------------------------------------------------
# 현금부족 ATM 강제 생성
# ---------------------------------------------------------
atm_cash_dict[19] = 20000
atm_cash_dict[20] = 50000
atm_cash_dict[27] = 100000

# ---------------------------------------------------------
# 9. 최종 조립 및 엑셀 드라이브 업로드 준비 (3중 연동 보완 버전)
# ---------------------------------------------------------
final_atm_list = []

for raw_atm in atm_raw_list:
    atm_id = raw_atm["ATM_ID"]
    branch_id = raw_atm["지점ID"]
    bank_id = branch_lookup[branch_id]["은행ID"]

    # 최신 현금 및 현금상태 반영
    raw_atm["현금잔량"] = atm_cash_dict[atm_id]
    raw_atm["ATM현금상태"] = "현금부족경고" if raw_atm["현금잔량"] < raw_atm["경고임계값"] else "정상"

    # [검사 1] ATM 자체에 미처리 장애가 있는지
    unresolved_atm = df_failure_log[(df_failure_log["ATM_ID"] == atm_id) & (df_failure_log["처리상태"] == "미처리")]

    # 미처리 장애 발생 시간 수집 그릇
    fault_times = []
    if not unresolved_atm.empty:
        fault_times.append(pd.to_datetime(unresolved_atm["발생일시"].max()))

    # 3가지 중 하나라도 미처리가 있으면 ATM 상태는 무조건 '장애'
    if len(fault_times) > 0:
        raw_atm["상태"] = "장애"
        # 인프라 마비로 다운된 시점을 마스터 데이터 최종 갱신일로 동결 (현실 고증)
        raw_atm["최종갱신일시"] = max(fault_times)
    elif raw_atm["상태"] == "점검중":
        raw_atm["상태"] = "점검중"
        raw_atm["최종갱신일시"] = max(atm_time_tracker[atm_id])
    else:
        raw_atm["상태"] = "정상"
        raw_atm["최종갱신일시"] = max(atm_time_tracker[atm_id])

    final_atm_list.append(raw_atm)

df_atm = pd.DataFrame(final_atm_list)

file_name = "V12_data.xlsx"

with pd.ExcelWriter(file_name, engine='openpyxl') as writer:

    df_bank.to_excel(writer, sheet_name="은행", index=False)
    df_branch.to_excel(writer, sheet_name="지점", index=False)
    df_customer.to_excel(writer, sheet_name="고객", index=False)
    df_account.to_excel(writer, sheet_name="계좌", index=False)
    df_atm.to_excel(writer, sheet_name="ATM", index=False)
    df_admin.to_excel(writer, sheet_name="관리자", index=False)
    df_transaction.to_excel(writer, sheet_name="거래내역", index=False)
    df_failure_log.to_excel(writer, sheet_name="ATM장애로그", index=False)
    df_replenishment.to_excel(writer, sheet_name="현금보충", index=False)
    df_maintenance.to_excel(writer, sheet_name="유지보수이력", index=False)
    df_branch_failure.to_excel(writer, sheet_name="지점장애로그", index=False)
    df_bank_failure.to_excel(writer, sheet_name="은행장애로그", index=False)

    # ---------------------------------------------------------
    # 모든 시트 자동 필터 적용
    # ---------------------------------------------------------
    for sheet_name in writer.sheets:

        ws = writer.sheets[sheet_name]

        max_row = ws.max_row
        max_col = ws.max_column

        ws.auto_filter.ref = ws.dimensions
