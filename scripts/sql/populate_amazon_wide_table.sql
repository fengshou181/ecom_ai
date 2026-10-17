-- ============================================================
-- 填充 Amazon 评论宽表
-- ============================================================

INSERT INTO amazon.amazon_review_wide
SELECT
    -- 评论信息
    r.id AS review_id,
    r.product_id,
    r.user_id,
    r.profile_name,
    r.helpfulness_numerator,
    r.helpfulness_denominator,
    r.score,
    r.time AS review_time,
    FROM_UNIXTIME(r.time) AS review_date,
    r.summary,
    r.text,
    
    -- 商品信息
    p.title,
    p.imgUrl,
    p.productURL,
    p.stars,
    p.reviews AS review_count,
    p.price,
    p.listPrice,
    p.isBestSeller,
    p.boughtInLastMonth,
    
    -- 分类信息
    p.category_id,
    c.category_name,
    
    -- 计算字段
    CASE 
        WHEN r.helpfulness_denominator > 0 THEN r.helpfulness_numerator / r.helpfulness_denominator
        ELSE NULL
    END AS helpfulness_ratio,
    CASE 
        WHEN p.listPrice > 0 AND p.price > 0 THEN (p.listPrice - p.price) / p.listPrice
        ELSE NULL
    END AS price_discount_rate
    
FROM amazon.reviews r
LEFT JOIN amazon.products p ON r.product_id = p.asin
LEFT JOIN amazon.categories c ON p.category_id = c.id;
