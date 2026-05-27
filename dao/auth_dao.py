"""
dao/auth_dao.py ─ 관리자 인증 관련 SQL 쿼리 모음
──────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : SQL 실행, cursor.execute(), fetchone()
  ❌ 이 파일에서 하면 안 됨 : 비밀번호 해시 비교, Flask session 처리
                              (그 역할은 services/auth_service.py가 담당)

[참조 테이블]
  관리자, 지점

[장애 건수 집계]
  미처리 장애 건수 조회는 dao/error_dao.py 로 이동됨.
  (find_unresolved_atm_error_count)
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
        "지점_id":    None     -- 슈퍼관리자는 지점 없음(NULL)
      }
      로그인아이디가 존재하지 않으면 None 반환.
      → service에서 None이면 "아이디 또는 비밀번호 불일치" 에러 발생.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ad.관리자ID, ad.이름, ad.로그인아이디, ad.비밀번호해시, ad.권한등급,
               ad.지점ID AS 지점_id, b.은행ID
        FROM 관리자 ad
        LEFT JOIN 지점 b ON ad.지점ID = b.지점ID
        WHERE ad.로그인아이디 = %s
    """, (login_id,))
    return cursor.fetchone()


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
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.은행ID
        FROM 관리자 ad
        JOIN 지점 b ON ad.지점ID = b.지점ID
        WHERE ad.관리자ID = %s
    """, (admin_id,))
    row = cursor.fetchone()
    return row["은행ID"] if row else None
