-- Olist 数据集建表 SQL
CREATE DATABASE IF NOT EXISTS olist;

USE olist;

-- 1. 客户表
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50),
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix INT,
    customer_city VARCHAR(100),
    customer_state VARCHAR(10)
)
DUPLICATE KEY(customer_id)
DISTRIBUTED BY HASH(customer_id) BUCKETS 3
PROPERTIES ('replication_num' = '1');

-- 2. 地理位置表
CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix INT,
    geolocation_lat DOUBLE,
    geolocation_lng DOUBLE,
    geolocation_city VARCHAR(100),
    geolocation_state VARCHAR(10)
)
DUPLICATE KEY(geolocation_zip_code_prefix)
DISTRIBUTED BY HASH(geolocation_zip_code_prefix) BUCKETS 3
PROPERTIES ('replication_num' = '1');

-- 3. 订单商品表
CREATE TABLE IF NOT EXISTS order_items (
    order_id VARCHAR(50),
    order_item_id INT,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    shipping_limit_date DATETIME,
    price DOUBLE,
    freight_value DOUBLE
)
DUPLICATE KEY(order_id, order_item_id)
DISTRIBUTED BY HASH(order_id) BUCKETS 6
PROPERTIES ('replication_num' = '1');

-- 4. 订单支付表
CREATE TABLE IF NOT EXISTS order_payments (
    order_id VARCHAR(50),
    payment_sequential INT,
    payment_type VARCHAR(30),
    payment_installments INT,
    payment_value DOUBLE
)
DUPLICATE KEY(order_id, payment_sequential)
DISTRIBUTED BY HASH(order_id) BUCKETS 3
PROPERTIES ('replication_num' = '1');

-- 5. 订单评论表
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id VARCHAR(50),
    order_id VARCHAR(50),
    review_score INT,
    review_comment_title VARCHAR(200),
    review_comment_message TEXT,
    review_creation_date DATETIME,
    review_answer_timestamp DATETIME
)
DUPLICATE KEY(review_id)
DISTRIBUTED BY HASH(review_id) BUCKETS 3
PROPERTIES ('replication_num' = '1');

-- 6. 订单表
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50),
    customer_id VARCHAR(50),
    order_status VARCHAR(20),
    order_purchase_timestamp DATETIME,
    order_approved_at DATETIME,
    order_delivered_carrier_date DATETIME,
    order_delivered_customer_date DATETIME,
    order_estimated_delivery_date DATETIME
)
DUPLICATE KEY(order_id)
DISTRIBUTED BY HASH(order_id) BUCKETS 6
PROPERTIES ('replication_num' = '1');

-- 7. 商品表
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50),
    product_category_name VARCHAR(100),
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g INT,
    product_length_cm INT,
    product_height_cm INT,
    product_width_cm INT
)
DUPLICATE KEY(product_id)
DISTRIBUTED BY HASH(product_id) BUCKETS 3
PROPERTIES ('replication_num' = '1');

-- 8. 卖家表
CREATE TABLE IF NOT EXISTS sellers (
    seller_id VARCHAR(50),
    seller_zip_code_prefix INT,
    seller_city VARCHAR(100),
    seller_state VARCHAR(10)
)
DUPLICATE KEY(seller_id)
DISTRIBUTED BY HASH(seller_id) BUCKETS 3
PROPERTIES ('replication_num' = '1');

-- 9. 商品类别翻译表
CREATE TABLE IF NOT EXISTS product_category_name_translation (
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100)
)
DUPLICATE KEY(product_category_name)
DISTRIBUTED BY HASH(product_category_name) BUCKETS 1
PROPERTIES ('replication_num' = '1');
