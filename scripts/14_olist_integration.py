# -*- coding: utf-8 -*-
"""
Olist 9 表整合脚本
将 9 个数据表整合成 2 张宽表：
1. olist_order_items_wide - 订单商品级宽表（最细粒度，每行一个订单项）
2. olist_orders_wide - 订单级宽表（每行一个订单，聚合后的汇总信息）
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime


def load_datasets(data_dir):
    """加载所有 Olist 数据集"""
    datasets = {}

    files = {
        'customers': 'olist_customers_dataset.csv',
        'geolocation': 'olist_geolocation_dataset.csv',
        'order_items': 'olist_order_items_dataset.csv',
        'order_payments': 'olist_order_payments_dataset.csv',
        'order_reviews': 'olist_order_reviews_dataset.csv',
        'orders': 'olist_orders_dataset.csv',
        'products': 'olist_products_dataset.csv',
        'sellers': 'olist_sellers_dataset.csv',
        'category_translation': 'product_category_name_translation.csv'
    }

    print(f"[{datetime.now()}] 正在加载 Olist 数据集...")
    for name, filename in files.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            datasets[name] = pd.read_csv(filepath)
            print(f"  {name}: {len(datasets[name]):,} 行 × {datasets[name].shape[1]} 列")
        else:
            print(f"  {name}: 文件不存在 ({filename})")

    print()
    return datasets


def preprocess_geolocation(geolocation):
    """预处理地理信息表：按邮政编码去重，取平均坐标"""
    print("预处理 geolocation 表...")
    geo_agg = geolocation.groupby('geolocation_zip_code_prefix').agg({
        'geolocation_lat': 'mean',
        'geolocation_lng': 'mean',
        'geolocation_city': 'first',
        'geolocation_state': 'first'
    }).reset_index()

    geo_agg.columns = [
        'zip_code_prefix', 'geo_lat', 'geo_lng', 'geo_city', 'geo_state'
    ]
    print(f"  原始: {len(geolocation):,} 行 → 去重后: {len(geo_agg):,} 行")
    return geo_agg


def preprocess_order_payments(order_payments):
    """预处理支付表：按订单聚合（一个订单可能有多种支付方式）"""
    print("预处理 order_payments 表...")

    # 支付方式透视
    payment_pivot = order_payments.pivot_table(
        index='order_id',
        columns='payment_type',
        values='payment_value',
        aggfunc='sum',
        fill_value=0
    ).add_prefix('payment_value_')

    # 分期付款聚合（只针对信用卡）
    credit_installments = order_payments[order_payments['payment_type'] == 'credit_card'].groupby('order_id').agg({
        'payment_installments': 'max'
    }).rename(columns={'payment_installments': 'payment_installments_credit_card'})

    # 总支付金额
    total_payment = order_payments.groupby('order_id').agg({
        'payment_value': 'sum',
        'payment_sequential': 'max'  # 支付方式数量
    }).rename(columns={
        'payment_value': 'payment_total_value',
        'payment_sequential': 'payment_methods_count'
    })

    # 合并所有支付信息
    payments_agg = total_payment.join(payment_pivot, how='left')
    payments_agg = payments_agg.join(credit_installments, how='left')

    # 填充缺失值
    payments_agg['payment_installments_credit_card'] = payments_agg['payment_installments_credit_card'].fillna(0).astype(int)

    print(f"  原始: {len(order_payments):,} 行 → 聚合后: {len(payments_agg):,} 行")
    return payments_agg.reset_index()


def preprocess_order_reviews(order_reviews):
    """预处理评价表：按订单聚合（一个订单可能有多条评价，取最新的）"""
    print("预处理 order_reviews 表...")

    # 转换时间列
    order_reviews['review_creation_date'] = pd.to_datetime(order_reviews['review_creation_date'])

    # 按订单取最新评价
    reviews_latest = order_reviews.sort_values('review_creation_date', ascending=False) \
        .drop_duplicates('order_id', keep='first')

    # 重命名列，加上前缀
    reviews_latest = reviews_latest.add_prefix('review_')
    reviews_latest = reviews_latest.rename(columns={'review_order_id': 'order_id'})

    # 评价数
    review_counts = order_reviews.groupby('order_id').size().reset_index(name='review_count')

    # 合并
    reviews_agg = reviews_latest.merge(review_counts, on='order_id', how='left')

    print(f"  原始: {len(order_reviews):,} 行 → 聚合后: {len(reviews_agg):,} 行")
    return reviews_agg


def preprocess_order_items_summary(order_items, products):
    """预处理订单项：按订单聚合商品信息汇总"""
    print("预处理 order_items 汇总信息...")

    # 关联商品品类
    items_with_cat = order_items.merge(
        products[['product_id', 'product_category_name']],
        on='product_id',
        how='left'
    )

    # 按订单聚合
    order_items_summary = items_with_cat.groupby('order_id').agg(
        order_item_count=('order_item_id', 'count'),
        order_product_count=('product_id', 'nunique'),
        order_total_price=('price', 'sum'),
        order_total_freight=('freight_value', 'sum'),
        order_avg_price=('price', 'mean'),
        order_min_price=('price', 'min'),
        order_max_price=('price', 'max'),
        order_category_count=('product_category_name', 'nunique'),
        order_seller_count=('seller_id', 'nunique')
    ).reset_index()

    # 总金额 = 商品价 + 运费
    order_items_summary['order_total_amount'] = (
        order_items_summary['order_total_price'] + order_items_summary['order_total_freight']
    )

    # 运费占比
    order_items_summary['order_freight_ratio'] = (
        order_items_summary['order_total_freight'] / order_items_summary['order_total_price']
    )

    print(f"  聚合后: {len(order_items_summary):,} 个订单")
    return order_items_summary


def build_order_items_wide(datasets, geo_agg):
    """构建订单商品级宽表（最细粒度）"""
    print("\n" + "=" * 70)
    print("构建订单商品级宽表 (order_items_wide)")
    print("=" * 70)

    order_items = datasets['order_items'].copy()
    print(f"起点: order_items ({len(order_items):,} 行)")

    # 1. 关联订单信息
    df = order_items.merge(datasets['orders'], on='order_id', how='left')
    print(f"+ orders → {len(df):,} 行, {df.shape[1]} 列")

    # 2. 关联客户信息
    df = df.merge(datasets['customers'], on='customer_id', how='left')
    print(f"+ customers → {len(df):,} 行, {df.shape[1]} 列")

    # 3. 关联商品信息
    df = df.merge(datasets['products'], on='product_id', how='left')
    print(f"+ products → {len(df):,} 行, {df.shape[1]} 列")

    # 4. 关联品类翻译
    df = df.merge(datasets['category_translation'], on='product_category_name', how='left')
    print(f"+ category_translation → {len(df):,} 行, {df.shape[1]} 列")

    # 5. 关联卖家信息
    df = df.merge(datasets['sellers'], on='seller_id', how='left')
    print(f"+ sellers → {len(df):,} 行, {df.shape[1]} 列")

    # 6. 关联客户地理信息
    geo_customer = geo_agg.add_prefix('customer_')
    df = df.merge(
        geo_customer,
        left_on='customer_zip_code_prefix',
        right_on='customer_zip_code_prefix',
        how='left'
    )
    print(f"+ customer_geolocation → {len(df):,} 行, {df.shape[1]} 列")

    # 7. 关联卖家地理信息
    geo_seller = geo_agg.add_prefix('seller_')
    df = df.merge(
        geo_seller,
        left_on='seller_zip_code_prefix',
        right_on='seller_zip_code_prefix',
        how='left'
    )
    print(f"+ seller_geolocation → {len(df):,} 行, {df.shape[1]} 列")

    # 8. 关联支付信息（聚合后的）
    payments_agg = preprocess_order_payments(datasets['order_payments'])
    df = df.merge(payments_agg, on='order_id', how='left')
    print(f"+ order_payments (aggregated) → {len(df):,} 行, {df.shape[1]} 列")

    # 9. 关联评价信息（最新的一条）
    reviews_agg = preprocess_order_reviews(datasets['order_reviews'])
    df = df.merge(reviews_agg, on='order_id', how='left')
    print(f"+ order_reviews (latest) → {len(df):,} 行, {df.shape[1]} 列")

    # 10. 添加派生字段
    df = add_derived_features(df)
    print(f"+ 派生字段 → {len(df):,} 行, {df.shape[1]} 列")

    return df


def build_orders_wide(datasets, geo_agg):
    """构建订单级宽表（每行一个订单）"""
    print("\n" + "=" * 70)
    print("构建订单级宽表 (orders_wide)")
    print("=" * 70)

    orders = datasets['orders'].copy()
    print(f"起点: orders ({len(orders):,} 行)")

    # 1. 关联客户信息
    df = orders.merge(datasets['customers'], on='customer_id', how='left')
    print(f"+ customers → {len(df):,} 行, {df.shape[1]} 列")

    # 2. 关联客户地理信息
    geo_customer = geo_agg.add_prefix('customer_')
    df = df.merge(
        geo_customer,
        left_on='customer_zip_code_prefix',
        right_on='customer_zip_code_prefix',
        how='left'
    )
    print(f"+ customer_geolocation → {len(df):,} 行, {df.shape[1]} 列")

    # 3. 关联订单项汇总
    items_summary = preprocess_order_items_summary(datasets['order_items'], datasets['products'])
    df = df.merge(items_summary, on='order_id', how='left')
    print(f"+ order_items (aggregated) → {len(df):,} 行, {df.shape[1]} 列")

    # 4. 关联支付信息
    payments_agg = preprocess_order_payments(datasets['order_payments'])
    df = df.merge(payments_agg, on='order_id', how='left')
    print(f"+ order_payments (aggregated) → {len(df):,} 行, {df.shape[1]} 列")

    # 5. 关联评价信息
    reviews_agg = preprocess_order_reviews(datasets['order_reviews'])
    df = df.merge(reviews_agg, on='order_id', how='left')
    print(f"+ order_reviews (latest) → {len(df):,} 行, {df.shape[1]} 列")

    # 6. 添加派生字段
    df = add_derived_features(df, is_order_level=True)
    print(f"+ 派生字段 → {len(df):,} 行, {df.shape[1]} 列")

    return df


def add_derived_features(df, is_order_level=False):
    """添加派生特征"""

    # 转换时间列
    time_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    for col in time_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # 配送相关
    if all(col in df.columns for col in ['order_purchase_timestamp', 'order_delivered_customer_date']):
        delivered_mask = df['order_delivered_customer_date'].notna()
        df.loc[delivered_mask, 'delivery_days'] = (
            df.loc[delivered_mask, 'order_delivered_customer_date'] -
            df.loc[delivered_mask, 'order_purchase_timestamp']
        ).dt.total_seconds() / 86400

    if all(col in df.columns for col in ['order_estimated_delivery_date', 'order_purchase_timestamp']):
        df['estimated_delivery_days'] = (
            df['order_estimated_delivery_date'] -
            df['order_purchase_timestamp']
        ).dt.total_seconds() / 86400

    if all(col in df.columns for col in ['order_delivered_customer_date', 'order_estimated_delivery_date']):
        delivered_mask = df['order_delivered_customer_date'].notna()
        df.loc[delivered_mask, 'delay_days'] = (
            df.loc[delivered_mask, 'order_delivered_customer_date'] -
            df.loc[delivered_mask, 'order_estimated_delivery_date']
        ).dt.total_seconds() / 86400
        df.loc[df['delay_days'] < 0, 'delay_days'] = 0
        df.loc[delivered_mask, 'is_delayed'] = (
            df.loc[delivered_mask, 'order_delivered_customer_date'] >
            df.loc[delivered_mask, 'order_estimated_delivery_date']
        ).astype(int)

    # 购买时间特征
    if 'order_purchase_timestamp' in df.columns:
        df['purchase_date'] = df['order_purchase_timestamp'].dt.date
        df['purchase_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
        df['purchase_hour'] = df['order_purchase_timestamp'].dt.hour
        df['purchase_dayofweek'] = df['order_purchase_timestamp'].dt.dayofweek  # 0=周一
        df['purchase_is_weekend'] = (df['purchase_dayofweek'] >= 5).astype(int)

        # 时间段
        df['purchase_time_period'] = pd.cut(
            df['purchase_hour'],
            bins=[-1, 6, 12, 14, 18, 22, 24],
            labels=['凌晨', '上午', '中午', '下午', '晚上', '深夜']
        )

    # 商品相关（订单项级别）
    if all(col in df.columns for col in ['price', 'freight_value']):
        df['item_total_value'] = df['price'] + df['freight_value']
        df['freight_ratio'] = df['freight_value'] / df['price']

    # 商品体积（订单项级别）
    if all(col in df.columns for col in ['product_length_cm', 'product_height_cm', 'product_width_cm']):
        df['product_volume_cm3'] = (
            df['product_length_cm'] *
            df['product_height_cm'] *
            df['product_width_cm']
        )

    if all(col in df.columns for col in ['product_weight_g', 'product_volume_cm3']):
        df['product_density_g_per_cm3'] = df['product_weight_g'] / df['product_volume_cm3']

    # 评价情感
    if 'review_score' in df.columns:
        df['review_is_positive'] = (df['review_score'] >= 4).astype(int)
        df['review_is_negative'] = (df['review_score'] <= 2).astype(int)
        df['review_is_neutral'] = (df['review_score'] == 3).astype(int)

    # 评论长度
    if 'review_comment_message' in df.columns:
        df['review_comment_length'] = df['review_comment_message'].str.len().fillna(0)

    # 买卖双方距离（粗略估算，使用经纬度）
    if all(col in df.columns for col in [
        'customer_geo_lat', 'customer_geo_lng',
        'seller_geo_lat', 'seller_geo_lng'
    ]):
        # 简化的欧氏距离（不是真实地理距离，但可用于相对比较）
        df['buyer_seller_geo_distance_approx'] = np.sqrt(
            (df['customer_geo_lat'] - df['seller_geo_lat']) ** 2 +
            (df['customer_geo_lng'] - df['seller_geo_lng']) ** 2
        )

    return df


def save_wide_tables(order_items_wide, orders_wide, output_dir):
    """保存宽表"""
    print("\n" + "=" * 70)
    print("保存宽表")
    print("=" * 70)

    os.makedirs(output_dir, exist_ok=True)

    # 订单商品级宽表
    items_path = os.path.join(output_dir, 'olist_order_items_wide.csv')
    order_items_wide.to_csv(items_path, index=False)
    items_size_mb = os.path.getsize(items_path) / 1024 / 1024
    print(f"\n订单商品级宽表:")
    print(f"  行数: {len(order_items_wide):,}")
    print(f"  列数: {order_items_wide.shape[1]}")
    print(f"  文件大小: {items_size_mb:.1f} MB")
    print(f"  保存路径: {items_path}")

    # 订单级宽表
    orders_path = os.path.join(output_dir, 'olist_orders_wide.csv')
    orders_wide.to_csv(orders_path, index=False)
    orders_size_mb = os.path.getsize(orders_path) / 1024 / 1024
    print(f"\n订单级宽表:")
    print(f"  行数: {len(orders_wide):,}")
    print(f"  列数: {orders_wide.shape[1]}")
    print(f"  文件大小: {orders_size_mb:.1f} MB")
    print(f"  保存路径: {orders_path}")

    # 同时保存 Parquet 格式（更快读取，更小体积）
    items_parquet = os.path.join(output_dir, 'olist_order_items_wide.parquet')
    order_items_wide.to_parquet(items_parquet, index=False)
    items_parquet_mb = os.path.getsize(items_parquet) / 1024 / 1024
    print(f"\n订单商品级宽表 (Parquet):")
    print(f"  文件大小: {items_parquet_mb:.1f} MB")
    print(f"  压缩比: {items_size_mb / items_parquet_mb:.1f}x")

    orders_parquet = os.path.join(output_dir, 'olist_orders_wide.parquet')
    orders_wide.to_parquet(orders_parquet, index=False)
    orders_parquet_mb = os.path.getsize(orders_parquet) / 1024 / 1024
    print(f"\n订单级宽表 (Parquet):")
    print(f"  文件大小: {orders_parquet_mb:.1f} MB")
    print(f"  压缩比: {orders_size_mb / orders_parquet_mb:.1f}x")


def save_integration_report(order_items_wide, orders_wide, output_path):
    """保存整合报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("Olist 9 表整合报告\n")
        f.write("=" * 70 + "\n\n")

        f.write("一、整合结果概览\n")
        f.write("-" * 50 + "\n")
        f.write(f"订单商品级宽表 (order_items_wide):\n")
        f.write(f"  行数: {len(order_items_wide):,}\n")
        f.write(f"  列数: {order_items_wide.shape[1]}\n\n")

        f.write(f"订单级宽表 (orders_wide):\n")
        f.write(f"  行数: {len(orders_wide):,}\n")
        f.write(f"  列数: {orders_wide.shape[1]}\n\n")

        f.write("二、整合的数据源\n")
        f.write("-" * 50 + "\n")
        f.write("  1. orders - 订单主表\n")
        f.write("  2. customers - 客户信息\n")
        f.write("  3. order_items - 订单商品\n")
        f.write("  4. products - 商品信息\n")
        f.write("  5. category_translation - 品类翻译\n")
        f.write("  6. sellers - 卖家信息\n")
        f.write("  7. geolocation - 地理坐标（客户+卖家）\n")
        f.write("  8. order_payments - 支付信息（聚合）\n")
        f.write("  9. order_reviews - 评价信息（最新）\n\n")

        f.write("三、添加的派生字段\n")
        f.write("-" * 50 + "\n")
        f.write("  - delivery_days: 实际配送天数\n")
        f.write("  - estimated_delivery_days: 预计配送天数\n")
        f.write("  - delay_days: 延迟天数\n")
        f.write("  - is_delayed: 是否延迟\n")
        f.write("  - purchase_month/hour/dayofweek: 购买时间特征\n")
        f.write("  - purchase_is_weekend: 是否周末\n")
        f.write("  - purchase_time_period: 时间段\n")
        f.write("  - product_volume_cm3: 商品体积\n")
        f.write("  - product_density_g_per_cm3: 商品密度\n")
        f.write("  - freight_ratio: 运费占比\n")
        f.write("  - review_is_positive/negative/neutral: 评价情感\n")
        f.write("  - buyer_seller_geo_distance_approx: 买卖双方距离（近似）\n\n")

        f.write("四、宽表使用说明\n")
        f.write("-" * 50 + "\n")
        f.write("  - order_items_wide: 适合商品维度分析（销量、价格、品类等）\n")
        f.write("  - orders_wide: 适合订单/客户维度分析（转化率、复购、客单价等）\n")
        f.write("  - Parquet 格式推荐用于大数据量读取，速度更快、体积更小\n")

        f.write("\n五、订单商品级宽表字段列表\n")
        f.write("-" * 50 + "\n")
        for i, col in enumerate(order_items_wide.columns, 1):
            f.write(f"  {i:3d}. {col}\n")


def main():
    data_dir = r"E:\ecom_ai\data\raw\olist"
    output_dir = r"E:\ecom_ai\data\processed\olist"

    start_time = pd.Timestamp.now()
    print(f"[{datetime.now()}] Olist 9 表整合开始")
    print(f"输入目录: {data_dir}")
    print(f"输出目录: {output_dir}\n")

    # 1. 加载所有数据
    datasets = load_datasets(data_dir)

    # 2. 预处理地理信息
    geo_agg = preprocess_geolocation(datasets['geolocation'])

    # 3. 构建订单商品级宽表
    order_items_wide = build_order_items_wide(datasets, geo_agg)

    # 4. 构建订单级宽表
    orders_wide = build_orders_wide(datasets, geo_agg)

    # 5. 保存宽表
    save_wide_tables(order_items_wide, orders_wide, output_dir)

    # 6. 保存整合报告
    report_path = os.path.join(output_dir, "integration_report.txt")
    save_integration_report(order_items_wide, orders_wide, report_path)
    print(f"\n整合报告已保存至: {report_path}")

    elapsed = (pd.Timestamp.now() - start_time).total_seconds()
    print(f"\n[{datetime.now()}] 整合完成，耗时: {elapsed:.2f}秒")

    # 打印宽表前几列的概览
    print("\n" + "=" * 70)
    print("订单商品级宽表前 5 行概览（部分列）")
    print("=" * 70)
    preview_cols = [
        'order_id', 'order_item_id', 'product_id', 'price', 'freight_value',
        'order_status', 'customer_state', 'product_category_name_english',
        'seller_state', 'payment_total_value', 'review_score', 'delivery_days'
    ]
    available_cols = [c for c in preview_cols if c in order_items_wide.columns]
    print(order_items_wide[available_cols].head().to_string())


if __name__ == "__main__":
    main()
