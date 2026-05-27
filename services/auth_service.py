"""
services/auth_service.py ─ 로그인 검증, 미처리 장애 건수 처리 비즈니스 로직
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : 비밀번호 해시 비교, 업무 규칙 검증, dao 호출
  ❌ 이 파일에서 하면 안 됨 : Flask session.update(), flash() 직접 호출
                              (그 역할은 routes/auth.py가 담당)

[비밀번호 해시 방식]
  현재 sha256을 사용 중이지만, 실제 서비스에서는 bcrypt 사용 권장.
  sha256은 레인보우 테이블 공격에 취약하므로 프로덕션에서는 반드시 교체.
"""

import hashlib
from db import get_connection
from dao import auth_dao, error_dao


def login(login_id, password):
    """
    로그인 자격증명을 검증하고 세션 저장용 관리자 정보를 반환한다.

    [처리 순서]
      1. 입력값 빈 값 체크
      2. DB에서 로그인아이디로 관리자 조회
      3. 존재하지 않으면 에러 (아이디 불일치)
      4. 비밀번호 해시 비교 (sha256)
      5. 불일치 시 에러 (비밀번호 불일치)
      6. 성공 시 세션에 저장할 dict 반환

    [보안 주의]
      아이디 불일치와 비밀번호 불일치 모두 "아이디 또는 비밀번호가 올바르지 않습니다."
      라는 동일한 메시지를 사용함. 어느 쪽이 틀렸는지 공격자에게 알리지 않기 위함.

    [반환값]
      dict {
        "admin_id"   : int,   관리자 PK
        "admin_name" : str,   관리자 이름 (환영 메시지에 사용)
        "admin_role" : str,   "슈퍼" 또는 "일반" (권한 분기에 사용)
        "branch_id"  : int|None  슈퍼관리자는 None
      }
      실패 시 ValueError 발생 → route에서 flash로 표시.
    """
    # 입력값 빈 값 체크
    if not login_id or not password:
        raise ValueError("아이디와 비밀번호를 모두 입력해주세요.")

    conn = get_connection()
    try:
        # DB에서 로그인아이디로 관리자 1명 조회
        admin = auth_dao.find_by_login_id(conn, login_id)

        # 아이디가 존재하지 않는 경우
        if admin is None:
            raise ValueError("아이디 또는 비밀번호가 올바르지 않습니다.")

        # 비밀번호 해시 비교 (입력값을 sha256으로 해시 후 DB값과 비교)
        # 실제 서비스에서는 bcrypt.checkpw() 사용 권장
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if admin["비밀번호해시"] != pw_hash:
            raise ValueError("아이디 또는 비밀번호가 올바르지 않습니다.")

        # 로그인 성공 → 세션에 저장할 정보만 골라서 반환
        # (비밀번호해시 같은 민감 정보는 세션에 절대 포함하지 않음)
        return {
            "admin_id":   admin["관리자ID"],
            "admin_name": admin["이름"],
            "admin_role": admin["권한등급"],   # "슈퍼" or "일반"
            "branch_id":  admin["지점_id"],    # 슈퍼관리자도 지점_id 보유 (은행ID 조회용)
            "bank_id":    admin["은행ID"],     # 슈퍼관리자의 소속 은행 필터링에 사용
        }
    finally:
        conn.close()


def get_unresolved_error_count(is_super, branch_id, bank_id=None):
    """
    미처리 장애 건수를 반환한다. (대시보드 경고 배지 숫자)

    [데이터셋 Issue 2 관련]
      이 값이 0보다 크면 대시보드에 빨간 경고 배지 표시.
      슈퍼관리자는 자기 은행 ATM 건수, 일반관리자는 자기 지점 ATM 건수만.

    [반환값]
      int  예) 5
    """
    conn = get_connection()
    try:
        bid      = None if is_super else branch_id
        bank_fid = bank_id if is_super else None
        return error_dao.find_unresolved_atm_error_count(conn, branch_id=bid, bank_id=bank_fid)
    finally:
        conn.close()
