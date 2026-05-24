"""
services/error_service.py ─ 지점장애 / 은행장애 비즈니스 로직
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : 권한 검증, dao 호출, commit/rollback
  ❌ 이 파일에서 하면 안 됨 : SQL 직접 작성, Flask session/request 접근

[담당 테이블]
  지점장애로그, 은행장애로그
"""

from db import get_connection
from dao import error_dao


# ── 공통 헬퍼 ──────────────────────────────────────────────────────

def get_all_branches(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT 지점ID, 지점명 FROM 지점 ORDER BY 지점ID")
    return cursor.fetchall()


def get_all_banks(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT 은행ID, 은행명 FROM 은행 ORDER BY 은행ID")
    return cursor.fetchall()


# ── 지점장애 ───────────────────────────────────────────────────────

BRANCH_ERROR_TYPES = ['네트워크', '전산오류', '전력이상', '서버오류']

# 지점장애 유형 → ATM장애 유형 매핑 (ATM장애로그 CHECK 제약 조건 대응)
BRANCH_TO_ATM_TYPE = {
    '네트워크': '네트워크',
    '전산오류': '전산오류',
    '전력이상': '기계오류',
    '서버오류': '전산오류',
}


def get_branch_errors(unresolved_only=False):
    """
    지점장애 목록을 반환한다.

    [파라미터]
      unresolved_only : True면 미처리만, False면 전체
    """
    conn = get_connection()
    try:
        if unresolved_only:
            return error_dao.find_unresolved_branch_errors(conn)
        return error_dao.find_all_branch_errors(conn)
    finally:
        conn.close()


def report_branch_error(branch_id, error_type, detail, is_super, admin_branch_id):
    """
    지점장애를 등록한다. (BR-11: 소속 ATM 전체 장애로그 일괄 생성)

    [권한]
      슈퍼관리자 : 모든 지점 장애 등록 가능
      일반관리자 : 자신의 소속 지점만 등록 가능 (BR-14)
    """
    if error_type not in BRANCH_ERROR_TYPES:
        raise ValueError(f"올바르지 않은 장애유형입니다: {error_type}")

    if not is_super and int(branch_id) != int(admin_branch_id):
        raise ValueError("자신의 소속 지점 장애만 등록할 수 있습니다.")

    conn = get_connection()
    try:
        # 지점장애로그 INSERT + 소속 ATM 전체 장애로그 일괄 INSERT (BR-11)
        error_dao.insert_branch_error(conn, branch_id, error_type, detail)
        atm_ids = error_dao.find_atm_ids_by_branch(conn, branch_id)
        if atm_ids:
            atm_type = BRANCH_TO_ATM_TYPE.get(error_type, '전산오류')
            error_dao.bulk_insert_atm_errors(conn, atm_ids, atm_type, detail)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def resolve_branch_error(branch_error_id, admin_id, is_super, admin_branch_id):
    """
    지점장애를 처리완료 처리한다.

    [권한]
      슈퍼관리자 : 모든 지점 장애 처리 가능
      일반관리자 : 자신의 소속 지점 장애만 처리 가능 (BR-14)
    """
    conn = get_connection()
    try:
        if not is_super:
            error_branch_id = error_dao.find_branch_id_by_branch_error(conn, branch_error_id)
            if error_branch_id is not None and int(admin_branch_id) != error_branch_id:
                raise ValueError("자신의 소속 지점 장애만 처리할 수 있습니다.")

        error_dao.resolve_branch_error(conn, branch_error_id, admin_id)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_branch_form_data():
    """지점장애 등록 폼에 필요한 지점 목록을 반환한다."""
    conn = get_connection()
    try:
        return get_all_branches(conn)
    finally:
        conn.close()


# ── 은행장애 ───────────────────────────────────────────────────────

BANK_ERROR_TYPES = ['데이터베이스오류', '네트워크', '전산망장애', '보안시스템오류']

# 은행장애 유형 → ATM장애 유형 매핑 (ATM장애로그 CHECK 제약 조건 대응)
BANK_TO_ATM_TYPE = {
    '데이터베이스오류': '전산오류',
    '네트워크':       '네트워크',
    '전산망장애':     '전산오류',
    '보안시스템오류': '전산오류',
}


def get_bank_errors(unresolved_only=False):
    """
    은행장애 목록을 반환한다.

    [파라미터]
      unresolved_only : True면 미처리만, False면 전체
    """
    conn = get_connection()
    try:
        if unresolved_only:
            return error_dao.find_unresolved_bank_errors(conn)
        return error_dao.find_all_bank_errors(conn)
    finally:
        conn.close()


def report_bank_error(bank_id, error_type, detail, is_super, admin_id):
    """
    은행장애를 등록한다. (BR-12: 소속 전 ATM 장애로그 일괄 생성)

    [권한]
      슈퍼관리자만 등록 가능, 자기 은행만 (BR-08, BR-13)
    """
    from dao import auth_dao

    if not is_super:
        raise ValueError("은행 장애 등록은 슈퍼관리자만 가능합니다.")

    if error_type not in BANK_ERROR_TYPES:
        raise ValueError(f"올바르지 않은 장애유형입니다: {error_type}")

    conn = get_connection()
    try:
        # BR-13: 자기 은행 장애만 등록 가능
        admin_bank_id = auth_dao.find_bank_id_by_admin(conn, admin_id)
        if admin_bank_id is not None and int(bank_id) != admin_bank_id:
            raise ValueError("자신의 소속 은행 장애만 등록할 수 있습니다.")

        # 은행장애로그 INSERT + 소속 전 ATM 장애로그 일괄 INSERT (BR-12)
        error_dao.insert_bank_error(conn, bank_id, error_type, detail)
        atm_ids = error_dao.find_atm_ids_by_bank(conn, bank_id)
        if atm_ids:
            atm_type = BANK_TO_ATM_TYPE.get(error_type, '전산오류')
            error_dao.bulk_insert_atm_errors(conn, atm_ids, atm_type, detail)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def resolve_bank_error(bank_error_id, admin_id, is_super):
    """
    은행장애를 처리완료 처리한다.

    [권한]
      슈퍼관리자만 처리 가능, 자기 은행만 (BR-08, BR-13)
    """
    from dao import auth_dao

    if not is_super:
        raise ValueError("은행 장애 처리는 슈퍼관리자만 가능합니다.")

    conn = get_connection()
    try:
        # BR-13: 자기 은행 장애만 처리 가능
        admin_bank_id  = auth_dao.find_bank_id_by_admin(conn, admin_id)
        error_bank_id  = error_dao.find_bank_id_by_bank_error(conn, bank_error_id)
        if admin_bank_id is not None and error_bank_id is not None:
            if admin_bank_id != error_bank_id:
                raise ValueError("자신의 소속 은행 장애만 처리할 수 있습니다.")

        error_dao.resolve_bank_error(conn, bank_error_id, admin_id)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_bank_form_data():
    """은행장애 등록 폼에 필요한 은행 목록을 반환한다."""
    conn = get_connection()
    try:
        return get_all_banks(conn)
    finally:
        conn.close()
