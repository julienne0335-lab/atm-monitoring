# ATM 운영 현황 모니터링 시스템

## 프로젝트 소개
MariaDB + Python Flask 기반 ATM 운영 현황 모니터링 시스템입니다.  
관리자가 ATM 상태·현금잔량·거래내역·장애이력을 웹에서 실시간으로 조회하고 관리할 수 있습니다.

## 기술 스택
| 영역 | 사용 기술 |
|------|-----------|
| DB | MariaDB (HeidiSQL) |
| 백엔드 | Python 3.x + Flask + pymysql |
| 프론트 | HTML + Bootstrap 5 |
| 문서 | Notion |

## 주요 기능
- ATM 목록 조회 및 상태 필터링 (정상 / 점검중 / 장애)
- ATM 상세 페이지 (현금잔량, 장애이력, 거래내역, 현금보충 이력)
- ATM 상태 변경 및 현금보충
- 거래내역 목록 조회 (필터 + 페이지네이션)
- 거래 통계 (거래유형별, 지점별 자행/타행 비율)
- 지점장애 / 은행장애 등록 및 처리완료 관리
- 관리자 권한 구분 (슈퍼관리자 / 일반관리자)
- 대시보드 (미처리 장애 건수, 현금부족 ATM, 오늘 거래 현황)

## 프로젝트 구조
```
atm_monitoring_system/
├── app.py              # Flask 앱 시작점, Blueprint 등록
├── db.example.py       # DB 연결 템플릿 (db.py로 복사해서 사용)
├── requirements.txt    # 패키지 목록
│
├── dao/                # SQL 쿼리 함수 모음 (DB 직접 접근)
│   ├── atm_dao.py          # ATM, 현금보충 관련 쿼리
│   ├── auth_dao.py         # 관리자 인증 관련 쿼리
│   ├── transaction_dao.py  # 거래내역·통계 쿼리
│   └── error_dao.py        # ATM·지점·은행 장애로그 쿼리
│
├── services/           # 비즈니스 로직 (권한 검증, commit/rollback)
│   ├── atm_service.py
│   ├── auth_service.py
│   ├── transaction_service.py
│   └── error_service.py
│
├── routes/             # URL 라우팅 (request/response 처리)
│   ├── atm.py
│   ├── auth.py
│   ├── transaction.py
│   ├── dashboard.py
│   └── error.py
│
├── templates/          # Jinja2 HTML 템플릿
│   ├── base.html
│   ├── dashboard.html
│   ├── atm_detail.html
│   ├── transaction_list.html
│   ├── transaction_stats.html
│   └── error_list.html
│
├── static/             # CSS, JS
│   └── css/style.css
│
└── sql/                # DDL, 샘플 데이터, DAO 쿼리 문서
```

## 시작 방법

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. DB 설정
`db.example.py`를 `db.py`로 복사한 후 비밀번호를 수정하세요.
```bash
cp db.example.py db.py
```
> ⚠️ `db.py`는 `.gitignore`에 등록되어 있어 GitHub에 올라가지 않습니다.

### 3. DB 테이블 생성 및 데이터 삽입
HeidiSQL에서 `sql/` 폴더의 DDL 파일을 실행한 뒤, INSERT 파일로 샘플 데이터를 삽입하세요.

### 4. 서버 실행
```bash
python app.py
```
→ http://127.0.0.1:5000 접속
