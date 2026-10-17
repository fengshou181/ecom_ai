-- 商品样本数据建表 SQL
CREATE DATABASE IF NOT EXISTS product_samples;

USE product_samples;

-- 通用商品样本表
CREATE TABLE IF NOT EXISTS products_sample (
    upc VARCHAR(50),
    availability VARCHAR(50),
    category VARCHAR(200),
    description TEXT,
    detail_url VARCHAR(500),
    in_stock VARCHAR(20),
    price DOUBLE,
    price_excl_tax DOUBLE,
    price_incl_tax DOUBLE,
    product_type VARCHAR(50),
    rating DOUBLE,
    review_count INT,
    tax DOUBLE,
    title VARCHAR(500)
)
DUPLICATE KEY(upc)
DISTRIBUTED BY HASH(upc) BUCKETS 1
PROPERTIES ('replication_num' = '1');

-- 京东商品数据
CREATE TABLE IF NOT EXISTS jd_products (
    url VARCHAR(500),
    name VARCHAR(300),
    price DOUBLE,
    shop VARCHAR(200),
    comments INT
)
DUPLICATE KEY(url)
DISTRIBUTED BY HASH(url) BUCKETS 1
PROPERTIES ('replication_num' = '1');
