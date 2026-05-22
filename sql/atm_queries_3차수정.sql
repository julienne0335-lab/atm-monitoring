-- ============================================
-- ATM 관리 시스템 시나리오 기반 쿼리 (2차 수정본)
-- DBMS: MariaDB
-- ============================================
USE atm_system;


-- ============================================
-- S1. 고객 거래 (출금·입금·이체)
-- 흐름: 계좌 잔액 변동 → 거래내역 기록 → ATM 현금잔량 변동
-- ============================================

-- [S1-1] 출금 (수수료: 자행 0원 / 타행 은행.타행수수료)

START TRANSACTION;

SET @수수료 = (
    SELECT CASE WHEN k.은행ID = j.은행ID THEN 0
                ELSE b.타행수수료
           END
    FROM 계좌 k
    JOIN 은행 b ON k.은행ID = b.은행ID
    JOIN ATM a  ON a.ATM_ID = 1
    JOIN 지점 j ON a.지점ID = j.지점ID
    WHERE k.계좌ID = 1
);

UPDATE 계좌
SET 잔액 = 잔액 - 100000 - @수수료
WHERE 계좌ID = 1;

INSERT INTO 거래내역 (ATM_ID, 계좌ID, 연관거래ID, 거래유형, 거래금액, 수수료, 처리상태, 거래일시)
VALUES (1, 1, NULL, '출금', 100000, @수수료, '성공', NOW());

UPDATE ATM
SET 현금잔량 = 현금잔량 - 100000,
    최종갱신일시 = NOW()
WHERE ATM_ID = 1;

COMMIT;


-- [S1-2] 입금 (수수료 항상 0원)

START TRANSACTION;

UPDATE 계좌
SET 잔액 = 잔액 + 100000
WHERE 계좌ID = 1;

INSERT INTO 거래내역 (ATM_ID, 계좌ID, 연관거래ID, 거래유형, 거래금액, 수수료, 처리상태, 거래일시)
VALUES (1, 1, NULL, '입금', 100000, 0, '성공', NOW());

UPDATE ATM
SET 현금잔량 = 현금잔량 + 100000,
    최종갱신일시 = NOW()
WHERE ATM_ID = 1;

COMMIT;


-- [S1-3] 이체 (ATM 현금잔량 변동 없음)

START TRANSACTION;

SET @수수료 = (
    SELECT CASE WHEN k.은행ID = j.은행ID THEN 0
                ELSE b.타행수수료
           END
    FROM 계좌 k
    JOIN 은행 b ON k.은행ID = b.은행ID
    JOIN ATM a  ON a.ATM_ID = 1
    JOIN 지점 j ON a.지점ID = j.지점ID
    WHERE k.계좌ID = 1
);

UPDATE 계좌 SET 잔액 = 잔액 - 50000 - @수수료 WHERE 계좌ID = 1;
UPDATE 계좌 SET 잔액 = 잔액 + 50000 WHERE 계좌ID = 2;

INSERT INTO 거래내역 (ATM_ID, 계좌ID, 연관거래ID, 거래유형, 거래금액, 수수료, 처리상태, 거래일시)
VALUES (1, 1, NULL, '이체(출금)', 50000, @수수료, '성공', NOW());

SET @출금거래ID = LAST_INSERT_ID();

INSERT INTO 거래내역 (ATM_ID, 계좌ID, 연관거래ID, 거래유형, 거래금액, 수수료, 처리상태, 거래일시)
VALUES (1, 2, @출금거래ID, '이체(입금)', 50000, 0, '성공', NOW());

UPDATE 거래내역
SET 연관거래ID = LAST_INSERT_ID()
WHERE 거래ID = @출금거래ID;

COMMIT;


-- [S1-4] 타행이체 (수수료 발생)

START TRANSACTION;

SET @수수료 = (
    SELECT CASE WHEN k.은행ID = j.은행ID THEN 0
                ELSE b.타행수수료
           END
    FROM 계좌 k
    JOIN 은행 b ON k.은행ID = b.은행ID
    JOIN ATM a  ON a.ATM_ID = 1
    JOIN 지점 j ON a.지점ID = j.지점ID
    WHERE k.계좌ID = 1
);

UPDATE 계좌 SET 잔액 = 잔액 - 50000 - @수수료 WHERE 계좌ID = 1;
UPDATE 계좌 SET 잔액 = 잔액 + 50000 WHERE 계좌ID = 3;

INSERT INTO 거래내역 (ATM_ID, 계좌ID, 연관거래ID, 거래유형, 거래금액, 수수료, 처리상태, 거래일시)
VALUES (1, 1, NULL, '이체(출금)', 50000, @수수료, '성공', NOW());

SET @출금거래ID = LAST_INSERT_ID();

INSERT INTO 거래내역 (ATM_ID, 계좌ID, 연관거래ID, 거래유형, 거래금액, 수수료, 처리상태, 거래일시)
VALUES (1, 3, @출금거래ID, '이체(입금)', 50000, 0, '성공', NOW());

UPDATE 거래내역
SET 연관거래ID = LAST_INSERT_ID()
WHERE 거래ID = @출금거래ID;

COMMIT;


-- ============================================
-- S2. 기록 조회
-- ============================================

-- [S2-1] 특정 고객의 거래내역 조회
SELECT
    g.거래ID,
    g.거래유형,
    g.거래금액,
    g.수수료,
    g.처리상태,
    g.거래일시,
    k.계좌번호,
    a.ATM_ID,
    j.지점명
FROM 거래내역 g
JOIN 계좌 k ON g.계좌ID = k.계좌ID
JOIN ATM a  ON g.ATM_ID = a.ATM_ID
JOIN 지점 j ON a.지점ID = j.지점ID
JOIN 고객 c ON k.고객ID = c.고객ID
WHERE c.고객ID = 1
ORDER BY g.거래일시 DESC;

-- [S2-2] 특정 ATM의 거래내역 조회
SELECT
    g.거래ID,
    g.거래유형,
    g.거래금액,
    g.수수료,
    g.처리상태,
    g.거래일시
FROM 거래내역 g
WHERE g.ATM_ID = 1
ORDER BY g.거래일시 DESC;

-- [S2-3] 관리자 담당 지점 ATM 현황 조회
SELECT
    a.ATM_ID,
    a.상태,
    a.현금잔량,
    a.경고임계값,
    a.최종갱신일시
FROM ATM a
WHERE a.지점ID = (SELECT 지점ID FROM 관리자 WHERE 관리자ID = 1);


-- ============================================
-- S3. 현금잔량 경고 및 보충
-- ============================================

-- [S3-1] 경고 ATM 조회 (현금잔량 < 경고임계값)
SELECT
    a.ATM_ID,
    a.현금잔량,
    a.경고임계값,
    j.지점명
FROM ATM a
JOIN 지점 j ON a.지점ID = j.지점ID
WHERE a.현금잔량 < a.경고임계값;

-- [S3-2] 현금보충 처리
START TRANSACTION;

INSERT INTO 현금보충 (ATM_ID, 관리자ID, 보충금액, 보충일시)
VALUES (1, 1, 5000000, NOW());

UPDATE ATM
SET 현금잔량 = 현금잔량 + 5000000,
    최종갱신일시 = NOW()
WHERE ATM_ID = 1;

COMMIT;


-- ============================================
-- S4. ATM 장애 발생 및 처리
-- ============================================

-- [S4-1] ATM 장애 발생: ATM 상태 전환 + ATM장애로그 생성 (관리자 미배정)
START TRANSACTION;

UPDATE ATM
SET 상태 = '장애',
    최종갱신일시 = NOW()
WHERE ATM_ID = 1;

INSERT INTO ATM장애로그 (ATM_ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
VALUES (1, NULL, '기계오류', '카드리더기 인식 불가', '미처리', NOW());

COMMIT;

-- [S4-2] ATM 장애 처리 완료: 관리자 배정 + 처리상태 변경 + ATM 정상 복구
START TRANSACTION;

UPDATE ATM장애로그
SET 관리자ID = 1,
    처리상태 = '처리완료',
    처리완료일시 = NOW()
WHERE 장애ID = 1;

UPDATE ATM
SET 상태 = '정상',
    최종갱신일시 = NOW()
WHERE ATM_ID = 1;

COMMIT;


-- ============================================
-- S5. 유지보수 이력 관리
-- ============================================

-- [S5-1] 장애 후 점검 등록 (장애ID 연결)
INSERT INTO 유지보수이력 (ATM_ID, 관리자ID, 장애ID, 점검내용, 점검일시)
VALUES (1, 1, 1, '카드리더기 교체 완료', NOW());

-- [S5-2] 정기점검 등록 (장애ID = NULL)
INSERT INTO 유지보수이력 (ATM_ID, 관리자ID, 장애ID, 점검내용, 점검일시)
VALUES (1, 1, NULL, '정기 소모품 점검', NOW());

-- [S5-3] 미점검 ATM 탐지 (최근 30일 내 유지보수이력 없음)
SELECT
    a.ATM_ID,
    a.상태,
    CASE WHEN a.상태 = '장애' THEN 'Y' ELSE 'N' END AS 장애여부,
    j.지점명,
    MAX(u.점검일시) AS 마지막점검일시
FROM ATM a
JOIN 지점 j ON a.지점ID = j.지점ID
LEFT JOIN 유지보수이력 u ON a.ATM_ID = u.ATM_ID
GROUP BY a.ATM_ID, a.상태, j.지점명
HAVING 마지막점검일시 IS NULL
    OR 마지막점검일시 < DATE_SUB(NOW(), INTERVAL 30 DAY);


-- ============================================
-- S6. 관리자 로그인 및 권한
-- ============================================

-- [S6-1] 로그인 인증
SELECT
    관리자ID,
    이름,
    비밀번호해시,
    권한등급,
    지점ID
FROM 관리자
WHERE 로그인아이디 = 'super_a';

-- [S6-2] 슈퍼관리자: 같은 은행 전체 ATM 조회
SELECT
    a.ATM_ID,
    a.상태,
    a.현금잔량,
    j.지점명
FROM ATM a
JOIN 지점 j ON a.지점ID = j.지점ID
WHERE j.은행ID = (
    SELECT j2.은행ID
    FROM 관리자 m
    JOIN 지점 j2 ON m.지점ID = j2.지점ID
    WHERE m.관리자ID = 1
);

-- [S6-3] 일반관리자: 자기 지점 ATM만 조회
SELECT
    a.ATM_ID,
    a.상태,
    a.현금잔량
FROM ATM a
WHERE a.지점ID = (SELECT 지점ID FROM 관리자 WHERE 관리자ID = 1);


-- ============================================
-- S7. 거래 통계 및 대시보드
-- ============================================

-- [S7-1] ATM별 거래 건수 · 금액 · 수수료
SELECT
    a.ATM_ID,
    j.지점명,
    COUNT(g.거래ID)  AS 거래건수,
    SUM(g.거래금액)  AS 거래금액합계,
    SUM(g.수수료)    AS 수수료합계
FROM 거래내역 g
JOIN ATM a  ON g.ATM_ID = a.ATM_ID
JOIN 지점 j ON a.지점ID = j.지점ID
GROUP BY a.ATM_ID, j.지점명;

-- [S7-2] 지점별 자행/타행 비율
SELECT
    j.지점명,
    COUNT(g.거래ID) AS 전체거래,
    SUM(CASE WHEN k.은행ID = j.은행ID THEN 1 ELSE 0 END) AS 자행거래,
    SUM(CASE WHEN k.은행ID != j.은행ID THEN 1 ELSE 0 END) AS 타행거래,
    ROUND(
        SUM(CASE WHEN k.은행ID != j.은행ID THEN 1 ELSE 0 END)
        / COUNT(g.거래ID) * 100, 1
    ) AS 타행비율
FROM 거래내역 g
JOIN ATM a  ON g.ATM_ID = a.ATM_ID
JOIN 지점 j ON a.지점ID = j.지점ID
JOIN 계좌 k ON g.계좌ID = k.계좌ID
GROUP BY j.지점명;

-- [S7-3] 월별 거래유형별 집계
SELECT
    DATE_FORMAT(g.거래일시, '%Y-%m') AS 월,
    g.거래유형,
    COUNT(g.거래ID)  AS 거래건수,
    SUM(g.거래금액)  AS 거래금액합계,
    SUM(g.수수료)    AS 수수료수익
FROM 거래내역 g
GROUP BY DATE_FORMAT(g.거래일시, '%Y-%m'), g.거래유형
ORDER BY 월, g.거래유형;

-- [S7-4] 전월 대비 거래 증감율
SELECT
    월,
    거래건수,
    LAG(거래건수) OVER (ORDER BY 월) AS 전월건수,
    ROUND(
        (거래건수 - LAG(거래건수) OVER (ORDER BY 월))
        / NULLIF(LAG(거래건수) OVER (ORDER BY 월), 0) * 100, 1
    ) AS 증감율
FROM (
    SELECT DATE_FORMAT(거래일시, '%Y-%m') AS 월, COUNT(*) AS 거래건수
    FROM 거래내역
    GROUP BY 월
) sub;


-- ============================================
-- S8. 지점 장애 발생 및 처리
-- ============================================

-- [S8-1] 지점 장애 발생: 지점장애로그 생성 + 해당 지점 ATM 전체 상태 전환
START TRANSACTION;

INSERT INTO 지점장애로그 (지점ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
VALUES (1, NULL, '네트워크', '지점 통신 회선 단절', '미처리', NOW());

UPDATE ATM
SET 상태 = '장애',
    최종갱신일시 = NOW()
WHERE 지점ID = 1;

COMMIT;

-- [S8-2] 지점 장애 처리 완료: 관리자 배정 + 처리완료 + 해당 지점 ATM 전체 정상 복구
START TRANSACTION;

UPDATE 지점장애로그
SET 관리자ID = 1,
    처리상태 = '처리완료',
    처리완료일시 = NOW()
WHERE 지점장애ID = 1;

UPDATE ATM
SET 상태 = '정상',
    최종갱신일시 = NOW()
WHERE 지점ID = 1;

COMMIT;


-- ============================================
-- S9. 은행 장애 발생 및 처리
-- ============================================

-- [S9-1] 은행 장애 발생: 은행장애로그 생성 + 해당 은행 전체 ATM 상태 전환
START TRANSACTION;

INSERT INTO 은행장애로그 (은행ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
VALUES (1, NULL, '데이터베이스오류', '중앙 DB 연결 불가', '미처리', NOW());

UPDATE ATM
SET 상태 = '장애',
    최종갱신일시 = NOW()
WHERE 지점ID IN (SELECT 지점ID FROM 지점 WHERE 은행ID = 1);

COMMIT;

-- [S9-2] 은행 장애 처리 완료: 관리자 배정 + 처리완료 + 해당 은행 전체 ATM 정상 복구
START TRANSACTION;

UPDATE 은행장애로그
SET 관리자ID = 1,
    처리상태 = '처리완료',
    처리완료일시 = NOW()
WHERE 은행장애ID = 1;

UPDATE ATM
SET 상태 = '정상',
    최종갱신일시 = NOW()
WHERE 지점ID IN (SELECT 지점ID FROM 지점 WHERE 은행ID = 1);

COMMIT;
