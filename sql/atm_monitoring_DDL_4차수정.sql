-- ============================================
-- ATM 관리 시스템 DDL (최종본)
-- DBMS: MariaDB
-- 명명규칙: PK/FK 모두 테이블명ID 형식 통일
-- ============================================

DROP DATABASE IF EXISTS atm_system;
CREATE DATABASE atm_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE atm_system;

-- 1. 은행
CREATE TABLE 은행 (
    은행ID     INT          AUTO_INCREMENT PRIMARY KEY,
    은행명     VARCHAR(50)  NOT NULL,
    타행수수료 DECIMAL(10,0) NOT NULL DEFAULT 0
);

-- 2. 고객
CREATE TABLE 고객 (
    고객ID   INT         AUTO_INCREMENT PRIMARY KEY,
    이름     VARCHAR(50) NOT NULL,
    전화번호 VARCHAR(20)
);

-- 3. 지점
CREATE TABLE 지점 (
    지점ID  INT          AUTO_INCREMENT PRIMARY KEY,
    은행ID  INT          NOT NULL,
    지점명  VARCHAR(100) NOT NULL,
    주소    VARCHAR(255),
    FOREIGN KEY (은행ID) REFERENCES 은행(은행ID)
);

-- 4. 계좌
CREATE TABLE 계좌 (
    계좌ID   INT           AUTO_INCREMENT PRIMARY KEY,
    고객ID   INT           NOT NULL,
    은행ID   INT           NOT NULL,
    계좌번호 VARCHAR(30)   NOT NULL,
    잔액     DECIMAL(15,0) NOT NULL DEFAULT 0 CHECK (잔액 >= 0),
    개설일   DATE          NOT NULL,
    UNIQUE (은행ID, 계좌번호),
    FOREIGN KEY (고객ID) REFERENCES 고객(고객ID),
    FOREIGN KEY (은행ID) REFERENCES 은행(은행ID)
);

-- 5. ATM
CREATE TABLE ATM (
    ATM_ID       INT           AUTO_INCREMENT PRIMARY KEY,
    지점ID       INT           NOT NULL,
    상태         VARCHAR(20)   NOT NULL DEFAULT '정상'
                 CHECK (상태 IN ('정상', '점검중', '장애')),
    현금잔량     DECIMAL(15,0) NOT NULL DEFAULT 0 CHECK (현금잔량 >= 0),
    경고임계값   DECIMAL(15,0) NOT NULL DEFAULT 1000000,
    ATM현금상태  VARCHAR(20)   NOT NULL DEFAULT '정상'
                 CHECK (ATM현금상태 IN ('정상', '현금부족경고')),
    최종갱신일시 DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (지점ID) REFERENCES 지점(지점ID)
);

-- 6. 관리자
CREATE TABLE 관리자 (
    관리자ID     INT          AUTO_INCREMENT PRIMARY KEY,
    지점ID       INT          NOT NULL,
    이름         VARCHAR(50)  NOT NULL,
    로그인아이디 VARCHAR(50)  NOT NULL UNIQUE,
    비밀번호해시 VARCHAR(255) NOT NULL,
    권한등급     VARCHAR(20)  NOT NULL DEFAULT '일반'
                 CHECK (권한등급 IN ('슈퍼', '일반')),
    생성일시     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (지점ID) REFERENCES 지점(지점ID)
);

-- 7. 거래내역
-- 처리상태: 성공/실패만 (지점장애/은행장애는 ATM장애로그.장애유형으로 관리)
CREATE TABLE 거래내역 (
    거래ID      INT           AUTO_INCREMENT PRIMARY KEY,
    ATM_ID      INT           NOT NULL,
    계좌ID      INT           NOT NULL,
    연관거래ID  INT           NULL,
    거래유형    VARCHAR(20)   NOT NULL
                CHECK (거래유형 IN ('출금', '입금', '이체(출금)', '이체(입금)')),
    거래금액    DECIMAL(15,0) NOT NULL,
    수수료      DECIMAL(10,0) NOT NULL DEFAULT 0,
    처리상태    VARCHAR(20)   NOT NULL DEFAULT '성공'
                CHECK (처리상태 IN ('성공', '실패')),
    거래일시    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ATM_ID)     REFERENCES ATM(ATM_ID),
    FOREIGN KEY (계좌ID)     REFERENCES 계좌(계좌ID),
    FOREIGN KEY (연관거래ID) REFERENCES 거래내역(거래ID)
);

-- 8. ATM장애로그
-- 장애유형: 기존 5종 + 지점장애/은행장애 추가 (BR-11, BR-12)
CREATE TABLE ATM장애로그 (
    장애ID       INT         AUTO_INCREMENT PRIMARY KEY,
    ATM_ID       INT         NOT NULL,
    관리자ID     INT,
    장애유형     VARCHAR(50) NOT NULL
                 CHECK (장애유형 IN ('현금부족', '기계오류', '네트워크', '전산오류', '카드리더오류', '지점장애', '은행장애')),
    상세내용     TEXT,
    처리상태     VARCHAR(20) NOT NULL DEFAULT '미처리'
                 CHECK (처리상태 IN ('미처리', '처리완료')),
    발생일시     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    처리완료일시 DATETIME,
    FOREIGN KEY (ATM_ID)   REFERENCES ATM(ATM_ID),
    FOREIGN KEY (관리자ID) REFERENCES 관리자(관리자ID)
);

-- 9. 현금보충
CREATE TABLE 현금보충 (
    보충ID   INT           AUTO_INCREMENT PRIMARY KEY,
    ATM_ID   INT           NOT NULL,
    관리자ID INT           NOT NULL,
    보충금액 DECIMAL(15,0) NOT NULL,
    보충일시 DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ATM_ID)   REFERENCES ATM(ATM_ID),
    FOREIGN KEY (관리자ID) REFERENCES 관리자(관리자ID)
);

-- 10. 유지보수이력
CREATE TABLE 유지보수이력 (
    이력ID   INT      AUTO_INCREMENT PRIMARY KEY,
    ATM_ID   INT      NOT NULL,
    관리자ID INT      NOT NULL,
    장애ID   INT,
    점검내용 TEXT,
    점검일시 DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ATM_ID)   REFERENCES ATM(ATM_ID),
    FOREIGN KEY (관리자ID) REFERENCES 관리자(관리자ID),
    FOREIGN KEY (장애ID)   REFERENCES ATM장애로그(장애ID)
);

-- 11. 지점장애로그
CREATE TABLE 지점장애로그 (
    지점장애ID   INT         AUTO_INCREMENT PRIMARY KEY,
    지점ID       INT         NOT NULL,
    관리자ID     INT,
    장애유형     VARCHAR(50) NOT NULL
                 CHECK (장애유형 IN ('네트워크', '전산오류', '전력이상', '서버오류')),
    상세내용     TEXT,
    처리상태     VARCHAR(20) NOT NULL DEFAULT '미처리'
                 CHECK (처리상태 IN ('미처리', '처리완료')),
    발생일시     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    처리완료일시 DATETIME,
    FOREIGN KEY (지점ID)   REFERENCES 지점(지점ID),
    FOREIGN KEY (관리자ID) REFERENCES 관리자(관리자ID)
);

-- 12. 은행장애로그
CREATE TABLE 은행장애로그 (
    은행장애ID   INT         AUTO_INCREMENT PRIMARY KEY,
    은행ID       INT         NOT NULL,
    관리자ID     INT,
    장애유형     VARCHAR(50) NOT NULL
                 CHECK (장애유형 IN ('데이터베이스오류', '네트워크', '전산망장애', '보안시스템오류')),
    상세내용     TEXT,
    처리상태     VARCHAR(20) NOT NULL DEFAULT '미처리'
                 CHECK (처리상태 IN ('미처리', '처리완료')),
    발생일시     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    처리완료일시 DATETIME,
    FOREIGN KEY (은행ID)   REFERENCES 은행(은행ID),
    FOREIGN KEY (관리자ID) REFERENCES 관리자(관리자ID)
);


-- ============================================
-- 인덱스
-- ============================================

CREATE INDEX idx_거래내역_거래일시   ON 거래내역(거래일시);
CREATE INDEX idx_거래내역_ATM_일시   ON 거래내역(ATM_ID, 거래일시);
CREATE INDEX idx_ATM장애로그_처리상태 ON ATM장애로그(ATM_ID, 처리상태);
CREATE INDEX idx_유지보수_ATM_일시   ON 유지보수이력(ATM_ID, 점검일시);
CREATE INDEX idx_지점장애_처리상태   ON 지점장애로그(지점ID, 처리상태);
CREATE INDEX idx_은행장애_처리상태   ON 은행장애로그(은행ID, 처리상태);
CREATE INDEX idx_ATM장애_처리상태단독 ON ATM장애로그(처리상태);

-- ============================================
-- 프로시저
-- ============================================

DELIMITER //

-- proc_지점장애_생성
-- 지점장애로그 INSERT 시 해당 지점 소속 ATM 전체에 ATM장애로그 일괄 생성 (BR-11)
-- 트랜잭션 내 일부 실패 시 전체 롤백
CREATE PROCEDURE proc_지점장애_생성(
    IN p_지점ID    INT,
    IN p_장애유형  VARCHAR(50),
    IN p_상세내용  TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 지점장애로그 INSERT
    INSERT INTO 지점장애로그 (지점ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
    VALUES (p_지점ID, NULL, p_장애유형, p_상세내용, '미처리', NOW());

    -- 해당 지점 ATM 상태 전환
    UPDATE ATM
    SET 상태 = '장애', 최종갱신일시 = NOW()
    WHERE 지점ID = p_지점ID;

    -- 해당 지점 소속 ATM 전체에 ATM장애로그 일괄 생성
    INSERT INTO ATM장애로그 (ATM_ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
    SELECT ATM_ID, NULL, '지점장애', p_상세내용, '미처리', NOW()
    FROM ATM
    WHERE 지점ID = p_지점ID;

    COMMIT;
END //


-- proc_은행장애_생성
-- 은행장애로그 INSERT 시 해당 은행 소속 전 지점 ATM 전체에 ATM장애로그 일괄 생성 (BR-12)
-- 트랜잭션 내 일부 실패 시 전체 롤백
CREATE PROCEDURE proc_은행장애_생성(
    IN p_은행ID    INT,
    IN p_장애유형  VARCHAR(50),
    IN p_상세내용  TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 은행장애로그 INSERT
    INSERT INTO 은행장애로그 (은행ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
    VALUES (p_은행ID, NULL, p_장애유형, p_상세내용, '미처리', NOW());

    -- 해당 은행 전체 ATM 상태 전환
    UPDATE ATM
    SET 상태 = '장애', 최종갱신일시 = NOW()
    WHERE 지점ID IN (SELECT 지점ID FROM 지점 WHERE 은행ID = p_은행ID);

    -- 해당 은행 소속 전 ATM에 ATM장애로그 일괄 생성
    INSERT INTO ATM장애로그 (ATM_ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
    SELECT ATM_ID, NULL, '은행장애', p_상세내용, '미처리', NOW()
    FROM ATM
    WHERE 지점ID IN (SELECT 지점ID FROM 지점 WHERE 은행ID = p_은행ID);

    COMMIT;
END //

DELIMITER ;
