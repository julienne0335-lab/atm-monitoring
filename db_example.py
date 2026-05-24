"""
db_example.py ─ DB 접속 설정 템플릿
이 파일을 db.py로 복사한 후 비밀번호를 수정하세요.
db.py는 .gitignore에 등록되어 있어 GitHub에 올라가지 않습니다.
"""

import pymysql

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "여기에_본인_비밀번호_입력",  # ← 수정 필수
    "db":       "atm_system",
    "charset":  "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)
