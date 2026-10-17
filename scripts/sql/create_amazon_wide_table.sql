-- ============================================================
-- Amazon 商品评论宽表 (3表整合)
-- 粒度: 评论记录
-- 整合表: reviews + products + categories
-- ============================================================

-- 1. 删除已存在的宽表
DROP TABLE IF EXISTS amazon.amazon_review_wide;

-- 2. 创建宽表
CREATE TABLE amazon.amazon_review_wide (
    -- ===== 评论信息 =====
    review_id INT COMMENT '评论ID',
    product_id VARCHAR(20) COMMENT '商品ASIN',
    user_id VARCHAR(50) COMMENT '用户ID',
    profile_name VARCHAR(200) COMMENT '用户昵称',
    helpfulness_numerator INT COMMENT '有用投票数(分子)',
    helpfulness_denominator INT COMMENT '总投票数(分母)',
    score INT COMMENT '评分(1-5)',
    review_time BIGINT COMMENT '评论时间戳',
    review_date DATETIME COMMENT '评论日期',
    summary VARCHAR(500) COMMENT '评论摘要',
    text TEXT COMMENT '评论内容',
    
    -- ===== 商品信息 =====
    title VARCHAR(500) COMMENT '商品标题',
    imgUrl VARCHAR(500) COMMENT '商品图片URL',
    productURL VARCHAR(500) COMMENT '商品链接',
    stars DOUBLE COMMENT '商品平均星级',
    review_count INT COMMENT '商品评论总数',
    price DOUBLE COMMENT '商品价格',
    listPrice DOUBLE COMMENT '商品标价',
    isBestSeller VARCHAR(10) COMMENT '是否畅销',
    boughtInLastMonth INT COMMENT '近月购买量',
    
    -- ===== 分类信息 =====
    category_id INT COMMENT '分类ID',
    category_name VARCHAR(200) COMMENT '分类名称',
    
    -- ===== 计算字段 =====
    helpfulness_ratio DOUBLE COMMENT '有用率 = 有用数/总投票数',
    price_discount_rate DOUBLE COMMENT '折扣率 = (标价-售价)/标价'
) 
ENGINE=OLAP
DUPLICATE KEY(review_id, product_id)
COMMENT 'Amazon商品评论宽表(3表整合)'
DISTRIBUTED BY HASH(product_id) BUCKETS 10
PROPERTIES (
    "replication_num" = "1",
    "compression" = "LZ4"
);
