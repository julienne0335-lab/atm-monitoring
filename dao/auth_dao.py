"""
dao/auth_dao.py ─ 관리자 인증 관련 SQL 쿼리 모음
──────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : SQL 실행, cursor.execute(), fetchone()
  ❌ 이 파일에서 하면 안 됨 : 비밀번호 해시 비교, Flask session 처리
                              (그 역할은 services/auth_service.py가 담당)

[참조 테이블]
  관리자, 지점, 장애로그, ATM
"""


def find_by_login_id(conn, login_id):
    """
    로그인 아이디로 관리자 1명을 조회한다. (로그인 처리 전용)

    [반환값]
      dict  예) {
        "관리자ID": 1,
        "이름":       "김관리",
        "로그인아이디": "admin01",
        "비밀번호해시": "sha256해시값...",
        "권한등급":   "슈퍼",   -- "슈퍼" 또는 "일반"
        "지점_id":    None      -- 슈퍼관리자는 지점 없음(NULL)
      }
      로그인아이디가 존재하지 않으면 None 반환.
      → service에서 None이면 "아이디 또는 비밀번호 불일치" 에러 발생.

    [SQL 예시]
      SELECT 관리자ID, 이름, 로그인아이디, 비밀번호해시, 권한등급,
             지점ID AS 지점_id
      FROM 관리자
      WHERE 로그인아이디 = %(login_id)s
    """
    pass


def find_unresolved_error_count(conn, branch_id=None):
    """
    미처리 장애 건수를 집계한다. (대시보드 경고 카운터 전용)

    [데이터셋 Issue 2 관련]
      이 쿼리가 0보다 크면 대시보드에 빨간 경고 배지가 표시됨.
      슈퍼관리자(branch_id=None)는 전 은행 합산 건수,
      일반관리자는 자신의 지점 소속 ATM 장애 건수만 조회.

    [파라미터]
      branch_id : None이면 전체(슈퍼관리자), 값이 있으면 해당 지점만

    [반환값]
      int  예) 5

    [SQL 예시]
      SELECT COUNT(*) AS cnt
      FROM 장애로그 e
      JOIN ATM a ON e.ATM_ID = a.ATM_ID
      WHERE e.처리상태 = '미처리'
        AND (%(branch_id)s IS NULL OR a.지점ID = %(branch_id)s)
    """
    pass


def find_bank_id_by_admin(conn, admin_id):
    """
    관리자가 속한 은행ID를 조회한다.

    [데이터셋 Issue 3 해결을 위한 함수]
      현금보충·유지보수 처리 시 타 은행 접근을 차단하기 위해
      service 계층의 process_refill()에서 호출됨.
      atm_dao.find_bank_id_by_atm()으로 ATM 소속 은행과 비교하여
      서로 다르면 ValueError("타 은행 ATM에는 접근할 수 없습니다.")를 발생시킴.

    [특이사항]
      슈퍼관리자는 지점ID가 NULL이므로 지점 JOIN이 실패할 수 있음.
      슈퍼관리자는 권한등급 검사를 먼저 통과하므로 이 함수 호출 전에
      service에서 슈퍼관리자 여부를 확인하고 필요 시 skip 처리 권장.

    [반환값]
      int  예) 1  (A은행=1, B은행=2)
      소속 지점이 없는 슈퍼관리자이거나 존재하지 않는 관리자이면 None 반환.

    [SQL 예시]
      SELECT b.은행ID
      FROM 관리자 ad
      JOIN 지점 b ON ad.지점ID = b.지점ID
      WHERE ad.관리자ID = %(admin_id)s
    """
    pass
