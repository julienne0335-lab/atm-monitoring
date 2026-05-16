"""
services/atm_service.py ─ ATM 목록/상세 조회, 상태 변경, 현금 보충 비즈니스 로직 
──────────────────────────────────────────────────────
✅ 업무 규칙 검증, dao 호출, 트랜잭션(commit/rollback)
❌ SQL 직접 작성, Flask request/session/flash

dao 함수를 조합해서 하나의 "업무 행위"를 완성하는 계층.
"""

from db import get_connection
from dao import atm_dao


def get_atm_list(is_super, branch_id, status=None):
    """
    ATM 목록 반환
    is_super  : 슈퍼관리자면 전체 조회, 아니면 branch_id 기준 필터
    """
    conn = get_connection()
    try:
        # 슈퍼관리자는 branch_id 필터 없이 전체 조회
        bid = None if is_super else branch_id
        return atm_dao.find_all(conn, branch_id=bid, status=status)
    finally:
        conn.close()


def get_atm_detail(atm_id):
    """
    ATM 상세 정보 + 관련 로그 묶음 반환
    반환값 : dict { atm, error_logs, transactions, refill_logs }
    """
    from dao import transaction_dao

    conn = get_connection()
    try:
        atm = atm_dao.find_by_id(conn, atm_id)

        if atm is None:
            # None을 반환하면 route에서 404 처리
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
    ATM 상태 변경 (BR-06)
    장애→정상 복구 시 미처리 장애로그도 함께 처리완료 처리
    """
    allowed = {"정상", "점검중", "장애"}
    if new_status not in allowed:
        # 잘못된 상태값이면 예외 발생 → route에서 flash 처리
        raise ValueError(f"올바르지 않은 상태값입니다: {new_status}")

    conn = get_connection()
    try:
        atm_dao.update_status(conn, atm_id, new_status)

        # 정상으로 복구할 때만 장애로그도 처리완료로 변경
        if new_status == "정상":
            atm_dao.resolve_error_logs(conn, atm_id)

        conn.commit()
    except Exception:
        conn.rollback()
        raise  # 예외를 route까지 전달
    finally:
        conn.close()


def process_refill(atm_id, admin_id, amount):
    """
    현금 보충 처리 (BR-05)
    1. 금액 유효성 검증
    2. 현금보충 이력 INSERT
    3. ATM 현금잔량 UPDATE
    """
    if amount <= 0:
        raise ValueError("보충 금액은 0보다 커야 합니다.")
    if amount > 100_000_000:
        raise ValueError("1회 최대 보충 금액은 1억원입니다.")

    conn = get_connection()
    try:
        atm_dao.insert_refill(conn, atm_id, admin_id, amount)    # 이력 기록
        atm_dao.update_cash_amount(conn, atm_id, amount)         # 잔량 증가
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_cash_alerts(is_super, branch_id):
    """현금 경고 ATM 목록 반환"""
    conn = get_connection()
    try:
        bid = None if is_super else branch_id
        return atm_dao.find_cash_alerts(conn, branch_id=bid)
    finally:
        conn.close()


def get_status_summary(is_super, branch_id):
    """상태별 ATM 대수 요약 반환"""
    conn = get_connection()
    try:
        bid = None if is_super else branch_id
        return atm_dao.count_by_status(conn, branch_id=bid)
    finally:
        conn.close()