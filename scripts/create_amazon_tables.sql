-- Amazon 数据集建表 SQL
CREATE DATABASE IF NOT EXISTS amazon;

USE amazon;

-- 1. 商品分类表
CREATE TABLE IF NOT EXISTS categories (
    id INT,
    category_name VARCHAR(200)
)
DUPLICATE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 1
PROPERTIES ('replication_num' = '1');

-- 2. 商品表
CREATE TABLE IF NOT EXISTS products (
    asin VARCHAR(20),
    title VARCHAR(500),
    imgUrl VARCHAR(500),
    productURL VARCHAR(500),
    stars DOUBLE,
    reviews INT,
    price DOUBLE,
    listPrice DOUBLE,
    category_id INT,
    isBestSeller VARCHAR(10),
    boughtInLastMonth INT
)
DUPLICATE KEY(asin)
DISTRIBUTED BY HASH(asin) BUCKETS 6
PROPERTIES ('replication_num' = '1');

-- 3. 评论表（大数据量）
CREATE TABLE IF NOT EXISTS reviews (
    id INT,
    product_id VARCHAR(20),
    user_id VARCHAR(50),
    profile_name VARCHAR(200),
    helpfulness_numerator INT,
    helpfulness_denominator INT,
    score INT,
    time BIGINT,
    summary VARCHAR(500),
    text TEXT
)
DUPLICATE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 6
PROPERTIES ('replication_num' = '1');
