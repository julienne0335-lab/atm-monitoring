"""
db.example.py ─ DB 접속 설정 템플릿
──────────────────────────────────────────────────────────────────────
[사용 방법]
  1. 이 파일을 복사하여 db.py 로 이름 변경
  2. DB_CONFIG의 "password", "db" 등을 본인 환경에 맞게 수정
  3. 실제 db.py 파일은 .gitignore에 등록되어 있어 GitHub에 올라가지 않음
     → 비밀번호 등 민감 정보 유출 방지

[pymysql 설치]
  pip install pymysql

[MariaDB 기본 설정 (로컬 개발)]
  host     : localhost (같은 PC에서 실행 중인 MariaDB)
  port     : 3306      (MariaDB 기본 포트)
  user     : root      (개발용 계정)
  db       : atm_system (데이터베이스 이름, CREATE DATABASE atm_system; 먼저 실행)
  charset  : utf8mb4   (한글 깨짐 방지 - utf8보다 확장된 버전)
"""

import pymysql

# ── 접속 정보 수정 영역 ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",            # MariaDB 서버 주소
    "port":     3306,                   # MariaDB 포트 (기본값 3306)
    "user":     "root",                 # DB 접속 계정
    "password": "your_password_here",   # ← 본인 비밀번호로 변경
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
