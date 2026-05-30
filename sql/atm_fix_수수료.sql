-- 타행 거래 수수료 누락 수정
-- 타행 ATM 거래 109건에 대해 각 은행의 타행수수료를 적용
UPDATE 거래내역 g
JOIN ATM a ON g.ATM_ID = a.ATM_ID
JOIN 지점 j ON a.지점ID = j.지점ID
JOIN 계좌 c ON g.계좌ID = c.계좌ID
JOIN 은행 b ON j.은행ID = b.은행ID
SET g.수수료 = b.타행수수료
WHERE g.수수료 = 0 AND j.은행ID != c.은행ID;
