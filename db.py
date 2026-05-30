"""
db.py ─ DB 접속 설정 (환경변수 버전)
"""

import pymysql
import os


def get_connection():
    return pymysql.connect(
        host=os.environ.get("MYSQLHOST"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        db=os.environ.get("MYSQLDATABASE"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
