-- Doris 测试 SQL

SHOW DATABASES;

CREATE DATABASE IF NOT EXISTS test;

USE test;

CREATE TABLE IF NOT EXISTS test_table (
    id INT,
    name VARCHAR(50),
    value DOUBLE
)
DUPLICATE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 1
PROPERTIES ('replication_num' = '1');

INSERT INTO test_table VALUES (1, 'hello', 3.14), (2, 'world', 2.718), (3, 'doris', 9.99);

SELECT * FROM test_table;

SELECT COUNT(*) as cnt, SUM(value) as total FROM test_table;
