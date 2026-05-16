"""
services/auth_service.py ─ 로그인 검증, 미처리 장애 건수 처리 비즈니스 로직 
"""

import hashlib
from db import get_connection
from dao import auth_dao


def login(login_id, password):
    """
    로그인 검증
    성공 : 세션에 저장할 관리자 정보 dict 반환
    실패 : ValueError 발생 (메시지를 flash로 쓸 수 있음)
    """
    if not login_id or not password:
        raise ValueError("아이디와 비밀번호를 모두 입력해주세요.")

    conn = get_connection()
    try:
        admin = auth_dao.find_by_login_id(conn, login_id)

        if admin is None:
            raise ValueError("아이디 또는 비밀번호가 올바르지 않습니다.")

        # 비밀번호 검증 (sha256 예시 — 실제는 bcrypt 권장)
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if admin["비밀번호해시"] != pw_hash:
            raise ValueError("아이디 또는 비밀번호가 올바르지 않습니다.")

        # 성공 시 세션에 저장할 정보만 골라서 반환
        return {
            "admin_id":   admin["관리자ID"],
            "admin_name": admin["이름"],
            "admin_role": admin["권한등급"],
            "branch_id":  admin["지점_id"],
        }
    finally:
        conn.close()


def get_unresolved_error_count(is_super, branch_id):
    """미처리 장애 건수"""
    conn = get_connection()
    try:
        bid = None if is_super else branch_id
        return auth_dao.find_unresolved_error_count(conn, branch_id=bid)
    finally:
        conn.close()