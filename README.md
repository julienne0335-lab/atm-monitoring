# ATM 운영 현황 모니터링 시스템

## 프로젝트 소개
MariaDB + Python Flask 기반 ATM 운영 현황 모니터링 시스템 

## 기술 스택
- DB : MariaDB (HeidiSQL)
- 백엔드 : Python 3.x + Flask + pymysql
- 프론트 : HTML + Bootstrap 5
- 문서 : Notion 

## 프로젝트 구조
atm_monitoring_system/
app.py                  # Flask 앱 시작점
db_example.py           # DB 연결 템플릿 (db.py로 복사해서 사용)
dao/                    # SQL 쿼리 함수
services/               # 비즈니스 로직
routes/                 # URL 라우팅
templates/              # HTML
static/                 # CSS, JS

## 시작 방법
1. 패키지 설치
   pip install -r requirements.txt

2. DB 설정
   db_example.py → db.py 복사 후 비밀번호 수정

3. DB 테이블 생성
   HeidiSQL에서 노션의 ddl.sql 실행

4. 서버 실행
   python app.py
   → http://127.0.0.1:5000 접속

## 주의사항
- db.py는 .gitignore에 등록되어 있음 (비밀번호 보안)
- SQL 파일은 노션에서 관리
