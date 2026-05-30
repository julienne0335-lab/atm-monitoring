"""
db.py ─ DB 접속 설정 템플릿 
"""

import pymysql

# ── 접속 정보 수정 영역 ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",            # MariaDB 서버 주소
    "port":     3306,                   # MariaDB 포트 (기본값 3306)
    "user":     "root",                 # DB 접속 계정
    "password": "030609",               # ← 본인 비밀번호로 변경
    "db":       "atm_system",           # ← 사용할 데이터베이스 이름
    "charset":  "utf8mb4",              # 한글 + 이모지 등 4바이트 문자 지원
    # DictCursor: SELECT 결과를 튜플 대신 딕셔너리로 반환
    # 예) row[0] 대신 row["ATM_ID"] 로 접근 가능
    "cursorclass": pymysql.cursors.DictCursor,
}
# ────────────────────────────────────────────────────────────────────


def get_connection():
    """
    DB 연결 객체(Connection)를 반환한다.

    [중요]
      이 함수를 호출하면 매번 새로운 연결을 열어서 반환함.
      사용 후 반드시 conn.close()로 닫아야 함.
      service 계층에서는 항상 try/finally 블록으로 닫기를 보장함.

    [사용 예시]
      conn = get_connection()
      try:
          cursor = conn.cursor()
          cursor.execute("SELECT * FROM ATM")
          rows = cursor.fetchall()   # list of dict 반환 (DictCursor 덕분)
          conn.commit()              # INSERT/UPDATE/DELETE 후 반드시 commit
      except Exception:
          conn.rollback()            # 오류 시 롤백
          raise
      finally:
          conn.close()               # 연결 반드시 종료

    [반환값]
      pymysql.connections.Connection 객체
    """
    return pymysql.connect(**DB_CONFIG)
