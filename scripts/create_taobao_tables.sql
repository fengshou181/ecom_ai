-- 淘宝用户行为数据集建表 SQL
CREATE DATABASE IF NOT EXISTS taobao;

USE taobao;

-- 用户行为表（1亿行，大表）
CREATE TABLE IF NOT EXISTS user_behavior (
    user_id BIGINT,
    item_id BIGINT,
    category_id BIGINT,
    behavior_type VARCHAR(10),
    timestamp BIGINT
)
DUPLICATE KEY(user_id, item_id, category_id)
DISTRIBUTED BY HASH(user_id) BUCKETS 32
PROPERTIES (
    'replication_num' = '1',
    'compression' = 'LZ4'
);
