"""
services/atm_service.py ─ ATM 목록/상세 조회, 상태 변경, 현금 보충 비즈니스 로직
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : 업무 규칙 검증, dao 호출, 트랜잭션(commit/rollback)
  ❌ 이 파일에서 하면 안 됨 : SQL 직접 작성, Flask request/session/flash 접근

[이 파일이 구현하는 데이터셋 이슈]
  Issue 2 ─ ATM 상태 ↔ 장애로그 동기화 : change_status()에서 처리
  Issue 3 ─ 타 은행 관리자 현금보충 차단 : process_refill()에서 처리
"""

from db import get_connection
from dao import atm_dao, auth_dao


def get_atm_list(is_super, branch_id, status=None):
    """
    ATM 목록을 반환한다.

    [파라미터]
      is_super  : True면 슈퍼관리자 → 전체 지점 조회
                  False면 일반관리자 → branch_id 지점만 조회
      branch_id : 세션에서 가져온 관리자의 소속 지점ID
      status    : URL 쿼리파라미터로 받은 상태 필터 (없으면 None)

    [반환값]
      list of dict (dao.find_all 결과 그대로 전달)
    """
    conn = get_connection()
    try:
        # 슈퍼관리자는 branch_id 필터 없이 전체 조회
        bid = None if is_super else branch_id
        return atm_dao.find_all(conn, branch_id=bid, status=status)
    finally:
        conn.close()  # 예외 발생 여부와 상관없이 연결 반드시 종료


def get_atm_detail(atm_id):
    """
    ATM 상세 정보와 관련 로그들을 묶어서 반환한다. (ATM 상세 페이지 전용)

    [반환값]
      dict {
        "atm"         : ATM 기본 정보 dict
        "error_logs"  : 장애로그 list (최근 10건)
        "transactions": 거래내역 list (최근 10건)
        "refill_logs" : 현금보충 이력 list (최근 5건)
      }
      ATM이 존재하지 않으면 None 반환 → route에서 404 처리.

    [데이터셋 Issue 8 참고]
      현재 ATM 상태가 "장애"여도 transactions에 과거 성공 거래가 포함될 수 있음.
      ATM 상태는 현재 시점, 거래내역은 2024~2025년 전체 기간 데이터이기 때문임.
    """
    from dao import transaction_dao

    conn = get_connection()
    try:
        atm = atm_dao.find_by_id(conn, atm_id)

        if atm is None:
            # ATM_ID가 존재하지 않으면 None 반환 → route에서 flash + redirect 처리
            return None

        return {
            "atm":          atm,
            "error_logs":   atm_dao.find_error_logs(conn, atm_id),
            "transactions": transaction_dao.find_recent_by_atm(conn, atm_id),
            "refill_logs":  atm_dao.find_refill_logs(conn, atm_id),
        }
    finally:
        conn.close()


def change_status(atm_id, new_status):
    """
    ATM 상태를 변경한다. (BR-06: 장애→정상 복구 시 장애로그도 함께 처리완료 처리)

    [데이터셋 Issue 2 해결]
      ATM 상태와 장애로그 처리상태를 항상 동기화함:
        - "정상"으로 변경 시 → 미처리 장애로그 전부 처리완료 처리 (resolve_error_logs)
        - "점검중" / "장애"로 변경 시 → 장애로그는 그대로 유지

    [트랜잭션 처리]
      update_status + resolve_error_logs가 하나의 트랜잭션으로 묶임.
      중간에 에러 발생 시 rollback하여 부분 업데이트 방지.

    [파라미터]
      new_status : "정상" / "점검중" / "장애" 중 하나
                   그 외 값이면 ValueError 발생 → route에서 flash로 표시.
    """
    # 허용된 상태값 목록 (이 외의 값은 잘못된 요청)
    allowed = {"정상", "점검중", "장애"}
    if new_status not in allowed:
        raise ValueError(f"올바르지 않은 상태값입니다: {new_status}")

    conn = get_connection()
    try:
        # 1단계: ATM 테이블의 상태 컬럼 업데이트
        atm_dao.update_status(conn, atm_id, new_status)

        # 2단계: "정상"으로 복구할 때만 장애로그도 처리완료로 변경
        # (Issue 2) 미처리 장애로그가 있는데 ATM이 정상 상태인 모순을 방지
        if new_status == "정상":
            atm_dao.resolve_error_logs(conn, atm_id)

        conn.commit()  # 두 쿼리 모두 성공했을 때만 커밋
    except Exception:
        conn.rollback()  # 하나라도 실패하면 전체 취소
        raise            # 예외를 route까지 전달하여 flash 처리
    finally:
        conn.close()


def process_refill(atm_id, admin_id, amount, is_super=False):
    """
    현금 보충을 처리한다. (BR-05)

    [처리 순서]
      1. 금액 유효성 검증 (0원 이하, 1억 초과 불가)
      2. [Issue 3] 타 은행 관리자 접근 차단 (슈퍼관리자는 예외)
      3. 현금보충 이력 INSERT (atm_dao.insert_refill)
      4. ATM 현금잔량 UPDATE   (atm_dao.update_cash_amount)
      5. commit

    [데이터셋 Issue 3 해결]
      관리자 소속 은행ID와 ATM 소속 은행ID를 DB에서 각각 조회 후 비교.
      불일치 시 ValueError 발생 → 보충 이력이 INSERT되지 않음.
      예) A은행 관리자가 B은행 ATM에 보충 시도 → 차단.

    [파라미터]
      is_super : 슈퍼관리자이면 True. 슈퍼관리자는 은행 제한 없이 모든 ATM 보충 가능.
                 route에서 session["admin_role"] 으로 판별하여 전달.
    """
    # ── 1단계: 금액 유효성 검증 ─────────────────────────────────────
    if amount <= 0:
        raise ValueError("보충 금액은 0보다 커야 합니다.")
    if amount > 100_000_000:  # 1억 초과는 현실적으로 불가능한 1회 보충량
        raise ValueError("1회 최대 보충 금액은 1억원입니다.")

    conn = get_connection()
    try:
        # ── 2단계: 타 은행 관리자 접근 차단 (Issue 3) ────────────────
        # 슈퍼관리자는 모든 ATM에 접근 가능하므로 은행 체크 skip
        if not is_super:
            # ATM이 속한 은행ID 조회 (지점 → 은행 경로)
            atm_bank_id = atm_dao.find_bank_id_by_atm(conn, atm_id)
            # 관리자가 속한 은행ID 조회 (관리자 → 지점 → 은행 경로)
            admin_bank_id = auth_dao.find_bank_id_by_admin(conn, admin_id)

            # 두 은행ID가 다르면 타 은행 ATM 접근 시도 → 거부
            if atm_bank_id is not None and admin_bank_id is not None:
                if atm_bank_id != admin_bank_id:
                    raise ValueError("타 은행 ATM에는 현금을 보충할 수 없습니다.")

        # ── 3단계: 현금보충 이력 INSERT ──────────────────────────────
        atm_dao.insert_refill(conn, atm_id, admin_id, amount)

        # ── 4단계: ATM 현금잔량 누적 UPDATE ─────────────────────────
        atm_dao.update_cash_amount(conn, atm_id, amount)

        conn.commit()  # 이력 INSERT + 잔량 UPDATE가 모두 성공해야 커밋
    except Exception:
        conn.rollback()  # 어느 단계에서든 실패하면 전체 취소
        raise
    finally:
        conn.close()


def get_cash_alerts(is_super, branch_id):
    """
    현금 경고 ATM 목록을 반환한다. (현금잔량 <= 경고임계값인 ATM)

    [데이터셋 Issue 7 관련]
      이 함수의 결과가 비어있지 않으면 대시보드에 경고 카드가 표시됨.
      데이터셋에는 의도적으로 경고 케이스(ATM-1, ATM-6 등)가 포함되어 있음.
    """
    conn = get_connection()
    try:
        bid = None if is_super else branch_id
        return atm_dao.find_cash_alerts(conn, branch_id=bid)
    finally:
        conn.close()


def get_status_summary(is_super, branch_id):
    """
    상태별 ATM 대수 요약을 반환한다. (대시보드 상단 요약 카드)

    [반환값]
      dict  예) {"정상": 21, "점검중": 6, "장애": 3}
    """
    conn = get_connection()
    try:
        bid = None if is_super else branch_id
        return atm_dao.count_by_status(conn, branch_id=bid)
    finally:
        conn.close()
