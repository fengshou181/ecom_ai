-- Instacart 数据集建表 SQL
CREATE DATABASE IF NOT EXISTS instacart;

USE instacart;

-- 1. 商品分类（过道）表
CREATE TABLE IF NOT EXISTS aisles (
    aisle_id INT,
    aisle VARCHAR(100)
)
DUPLICATE KEY(aisle_id)
DISTRIBUTED BY HASH(aisle_id) BUCKETS 1
PROPERTIES ('replication_num' = '1');

-- 2. 部门表
CREATE TABLE IF NOT EXISTS departments (
    department_id INT,
    department VARCHAR(50)
)
DUPLICATE KEY(department_id)
DISTRIBUTED BY HASH(department_id) BUCKETS 1
PROPERTIES ('replication_num' = '1');

-- 3. 商品表
CREATE TABLE IF NOT EXISTS products (
    product_id INT,
    product_name VARCHAR(300),
    aisle_id INT,
    department_id INT
)
DUPLICATE KEY(product_id)
DISTRIBUTED BY HASH(product_id) BUCKETS 3
PROPERTIES ('replication_num' = '1');

-- 4. 订单表
CREATE TABLE IF NOT EXISTS orders (
    order_id INT,
    user_id INT,
    eval_set VARCHAR(10),
    order_number INT,
    order_dow INT,
    order_hour_of_day INT,
    days_since_prior_order DOUBLE
)
DUPLICATE KEY(order_id)
DISTRIBUTED BY HASH(order_id) BUCKETS 6
PROPERTIES ('replication_num' = '1');

-- 5. 订单商品表（prior 数据集，3200万行）
CREATE TABLE IF NOT EXISTS order_products_prior (
    order_id INT,
    product_id INT,
    add_to_cart_order INT,
    reordered TINYINT
)
DUPLICATE KEY(order_id, product_id)
DISTRIBUTED BY HASH(order_id) BUCKETS 12
PROPERTIES ('replication_num' = '1');

-- 6. 订单商品表（train 数据集，138万行）
CREATE TABLE IF NOT EXISTS order_products_train (
    order_id INT,
    product_id INT,
    add_to_cart_order INT,
    reordered TINYINT
)
DUPLICATE KEY(order_id, product_id)
DISTRIBUTED BY HASH(order_id) BUCKETS 6
PROPERTIES ('replication_num' = '1');
