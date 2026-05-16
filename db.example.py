"""
db_example.py ─ DB 접속 설정 템플릿
                MariaDB 연결 정보를 담고, 연결 객체를 반환하는 함수 하나만 가짐. 
──────────────────────────────────────────────────────
이 파일을 복사해서 db.py 로 이름을 바꾼 뒤,
본인 환경에 맞게 수정해서 사용! (비밀번호 등 노출 방지)

⚠️ 실제 db.py 파일은 .gitignore 에 등록되어 있어서
    GitHub 에 올라가지 않는다. 
"""

import pymysql

# ── 접속 정보 수정 영역 ─────────────────────────────
DB_CONFIG = {
    "host":     "localhost",   # MariaDB 서버 주소 
    "port":     3306,          # MariaDB 포트 
    "user":     "root",        # DB 계정
    "password": "your_password_here",  # 본인 비밀번호로 변경 
    "db":       "atm_system",  # 사용할 데이터베이스 이름
    "charset":  "utf8mb4",     # 한글 깨짐 방지
    "cursorclass": pymysql.cursors.DictCursor,  # 결과를 딕셔너리로 받기
}
# ───────────────────────────────────────────────────


def get_connection():
    """
    DB 연결 객체를 반환하는 함수.

    사용 예시:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ATM")
        rows = cursor.fetchall()
        conn.close()
    """
    return pymysql.connect(**DB_CONFIG)