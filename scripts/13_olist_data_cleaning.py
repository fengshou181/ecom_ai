# -*- coding: utf-8 -*-
"""
Olist 巴西电商数据集清洗脚本
对 9 个数据表进行清洗和预处理
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
            print(f"  {name}: {len(datasets[name]):,} 行")
        else:
            print(f"  {name}: 文件不存在")

    print(f"[{datetime.now()}] 数据加载完成\n")
    return datasets


def clean_orders(orders):
    """清洗订单表"""
    print("-" * 50)
    print("清洗 orders 表")
    print("-" * 50)

    original_count = len(orders)
    print(f"原始记录数: {original_count:,}")

    # 转换时间列
    time_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    for col in time_cols:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors='coerce')

    # 缺失值统计
    null_counts = orders.isnull().sum()
    if null_counts.sum() > 0:
        print("\n缺失值:")
        for col in orders.columns:
            if null_counts[col] > 0:
                print(f"  {col}: {null_counts[col]:,} ({null_counts[col]/len(orders)*100:.2f}%)")

    # 订单状态分布
    print(f"\n订单状态分布:")
    status_counts = orders['order_status'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count:,} ({count/len(orders)*100:.2f}%)")

    # 添加派生字段
    # 配送时长（仅已交付订单）
    delivered = orders['order_status'] == 'delivered'
    orders.loc[delivered, 'delivery_days'] = (
        orders.loc[delivered, 'order_delivered_customer_date'] -
        orders.loc[delivered, 'order_purchase_timestamp']
    ).dt.total_seconds() / 86400

    # 预计配送时长
    orders['estimated_delivery_days'] = (
        orders['order_estimated_delivery_date'] -
        orders['order_purchase_timestamp']
    ).dt.total_seconds() / 86400

    # 是否延迟送达
    orders.loc[delivered, 'is_delayed'] = (
        orders.loc[delivered, 'order_delivered_customer_date'] >
        orders.loc[delivered, 'order_estimated_delivery_date']
    ).astype(int)

    # 延迟天数
    orders.loc[delivered, 'delay_days'] = (
        orders.loc[delivered, 'order_delivered_customer_date'] -
        orders.loc[delivered, 'order_estimated_delivery_date']
    ).dt.total_seconds() / 86400
    # 提前送达的延迟天数为 0
    orders.loc[orders['delay_days'] < 0, 'delay_days'] = 0

    # 添加日期相关字段
    orders['purchase_date'] = orders['order_purchase_timestamp'].dt.date
    orders['purchase_month'] = orders['order_purchase_timestamp'].dt.to_period('M')
    orders['purchase_hour'] = orders['order_purchase_timestamp'].dt.hour
    orders['purchase_dayofweek'] = orders['order_purchase_timestamp'].dt.dayofweek

    print(f"\n添加字段:")
    print(f"  - delivery_days: 实际配送天数")
    print(f"  - estimated_delivery_days: 预计配送天数")
    print(f"  - is_delayed: 是否延迟送达 (1=是, 0=否)")
    print(f"  - delay_days: 延迟天数")
    print(f"  - purchase_date: 购买日期")
    print(f"  - purchase_month: 购买月份")
    print(f"  - purchase_hour: 购买小时")
    print(f"  - purchase_dayofweek: 购买星期几 (0=周一)")

    print(f"\n清洗后记录数: {len(orders):,}")
    return orders


def clean_order_items(order_items):
    """清洗订单商品表"""
    print("-" * 50)
    print("清洗 order_items 表")
    print("-" * 50)

    original_count = len(order_items)
    print(f"原始记录数: {original_count:,}")

    # 缺失值检查
    null_counts = order_items.isnull().sum()
    if null_counts.sum() > 0:
        print(f"\n缺失值: {null_counts.sum():,}")
    else:
        print(f"\n缺失值: 无")

    # 价格分布检查
    print(f"\n价格统计:")
    print(f"  均值: R$ {order_items['price'].mean():.2f}")
    print(f"  中位数: R$ {order_items['price'].median():.2f}")
    print(f"  最小值: R$ {order_items['price'].min():.2f}")
    print(f"  最大值: R$ {order_items['price'].max():.2f}")

    # 运费统计
    print(f"\n运费统计:")
    print(f"  均值: R$ {order_items['freight_value'].mean():.2f}")
    print(f"  中位数: R$ {order_items['freight_value'].median():.2f}")
    print(f"  占价格比例: {order_items['freight_value'].sum() / order_items['price'].sum() * 100:.2f}%")

    # 添加运费占比字段
    order_items['freight_ratio'] = order_items['freight_value'] / order_items['price']

    # 限制异常值（运费占比 > 100% 的可能是数据异常）
    abnormal_freight = order_items[order_items['freight_ratio'] > 2]
    if len(abnormal_freight) > 0:
        print(f"\n运费占比 > 200% 的异常记录: {len(abnormal_freight):,} ({len(abnormal_freight)/len(order_items)*100:.2f}%)")

    print(f"\n清洗后记录数: {len(order_items):,}")
    return order_items


def clean_products(products, category_translation):
    """清洗商品表"""
    print("-" * 50)
    print("清洗 products 表")
    print("-" * 50)

    original_count = len(products)
    print(f"原始记录数: {original_count:,}")

    # 缺失值统计
    null_counts = products.isnull().sum()
    if null_counts.sum() > 0:
        print("\n缺失值:")
        for col in products.columns:
            if null_counts[col] > 0:
                print(f"  {col}: {null_counts[col]:,} ({null_counts[col]/len(products)*100:.2f}%)")

    # 品类名称翻译
    if category_translation is not None:
        products = products.merge(
            category_translation,
            on='product_category_name',
            how='left'
        )
        print(f"\n已添加英文品类名称 (product_category_name_english)")

    # 商品体积（长 x 宽 x 高）
    if all(col in products.columns for col in ['product_length_cm', 'product_height_cm', 'product_width_cm']):
        products['product_volume_cm3'] = (
            products['product_length_cm'] *
            products['product_height_cm'] *
            products['product_width_cm']
        )
        print(f"已添加商品体积字段 (product_volume_cm3)")

    # 重量/体积比（密度相关）
    if 'product_weight_g' in products.columns and 'product_volume_cm3' in products.columns:
        products['product_density'] = products['product_weight_g'] / products['product_volume_cm3']
        print(f"已添加商品密度字段 (product_density)")

    print(f"\n清洗后记录数: {len(products):,}")
    return products


def clean_customers(customers):
    """清洗客户表"""
    print("-" * 50)
    print("清洗 customers 表")
    print("-" * 50)

    original_count = len(customers)
    print(f"原始记录数: {original_count:,}")
    print(f"唯一客户数 (customer_unique_id): {customers['customer_unique_id'].nunique():,}")

    # 缺失值检查
    null_counts = customers.isnull().sum()
    if null_counts.sum() > 0:
        print(f"\n缺失值: {null_counts.sum():,}")
    else:
        print(f"\n缺失值: 无")

    # 州名标准化（确保都是大写）
    customers['customer_state'] = customers['customer_state'].str.upper()

    # 城市名标准化
    customers['customer_city'] = customers['customer_city'].str.lower().str.strip()

    print(f"\n清洗后记录数: {len(customers):,}")
    return customers


def clean_sellers(sellers):
    """清洗卖家表"""
    print("-" * 50)
    print("清洗 sellers 表")
    print("-" * 50)

    original_count = len(sellers)
    print(f"原始记录数: {original_count:,}")

    # 缺失值检查
    null_counts = sellers.isnull().sum()
    if null_counts.sum() > 0:
        print(f"\n缺失值: {null_counts.sum():,}")
    else:
        print(f"\n缺失值: 无")

    # 州名标准化
    sellers['seller_state'] = sellers['seller_state'].str.upper()

    # 城市名标准化
    sellers['seller_city'] = sellers['seller_city'].str.lower().str.strip()

    print(f"\n清洗后记录数: {len(sellers):,}")
    return sellers


def clean_order_payments(order_payments):
    """清洗支付表"""
    print("-" * 50)
    print("清洗 order_payments 表")
    print("-" * 50)

    original_count = len(order_payments)
    print(f"原始记录数: {original_count:,}")

    # 缺失值检查
    null_counts = order_payments.isnull().sum()
    if null_counts.sum() > 0:
        print(f"\n缺失值: {null_counts.sum():,}")
    else:
        print(f"\n缺失值: 无")

    # 支付方式分布
    print(f"\n支付方式分布:")
    payment_type_counts = order_payments['payment_type'].value_counts()
    for ptype, count in payment_type_counts.items():
        print(f"  {ptype}: {count:,} ({count/len(order_payments)*100:.2f}%)")

    # 分期付款数为 0 的记录（可能是一次性付款）
    zero_installments = order_payments[order_payments['payment_installments'] == 0]
    if len(zero_installments) > 0:
        print(f"\n分期付款数为 0 的记录: {len(zero_installments):,} ({len(zero_installments)/len(order_payments)*100:.2f}%)")
        # 将分期付款数为 0 的设为 1（一次性付款）
        order_payments.loc[order_payments['payment_installments'] == 0, 'payment_installments'] = 1
        print("已将分期付款数为 0 的记录修正为 1")

    print(f"\n清洗后记录数: {len(order_payments):,}")
    return order_payments


def clean_order_reviews(order_reviews):
    """清洗评价表"""
    print("-" * 50)
    print("清洗 order_reviews 表")
    print("-" * 50)

    original_count = len(order_reviews)
    print(f"原始记录数: {original_count:,}")

    # 转换时间列
    time_cols = ['review_creation_date', 'review_answer_timestamp']
    for col in time_cols:
        if col in order_reviews.columns:
            order_reviews[col] = pd.to_datetime(order_reviews[col], errors='coerce')

    # 缺失值统计
    null_counts = order_reviews.isnull().sum()
    if null_counts.sum() > 0:
        print("\n缺失值:")
        for col in order_reviews.columns:
            if null_counts[col] > 0:
                print(f"  {col}: {null_counts[col]:,} ({null_counts[col]/len(order_reviews)*100:.2f}%)")

    # 评分分布
    print(f"\n评分分布:")
    score_counts = order_reviews['review_score'].value_counts().sort_index()
    for score, count in score_counts.items():
        print(f"  {score}星: {count:,} ({count/len(order_reviews)*100:.2f}%)")

    # 评论长度
    if 'review_comment_message' in order_reviews.columns:
        order_reviews['comment_length'] = order_reviews['review_comment_message'].str.len().fillna(0)
        print(f"\n评论长度统计:")
        print(f"  有评论的评价数: {(order_reviews['comment_length'] > 0).sum():,}")
        print(f"  平均评论长度: {order_reviews[order_reviews['comment_length'] > 0]['comment_length'].mean():.1f} 字符")

    # 添加是否正面/负面评价
    order_reviews['is_positive'] = (order_reviews['review_score'] >= 4).astype(int)
    order_reviews['is_negative'] = (order_reviews['review_score'] <= 2).astype(int)
    print(f"\n已添加评价情感字段:")
    print(f"  - is_positive: 正面评价 (4-5星)")
    print(f"  - is_negative: 负面评价 (1-2星)")

    print(f"\n清洗后记录数: {len(order_reviews):,}")
    return order_reviews


def clean_geolocation(geolocation):
    """清洗地理信息表"""
    print("-" * 50)
    print("清洗 geolocation 表")
    print("-" * 50)

    original_count = len(geolocation)
    print(f"原始记录数: {original_count:,}")

    # 缺失值检查
    null_counts = geolocation.isnull().sum()
    if null_counts.sum() > 0:
        print(f"\n缺失值: {null_counts.sum():,}")
    else:
        print(f"\n缺失值: 无")

    # 按 zip code 去重，取平均值
    geo_by_zip = geolocation.groupby('geolocation_zip_code_prefix').agg({
        'geolocation_lat': 'mean',
        'geolocation_lng': 'mean',
        'geolocation_city': 'first',
        'geolocation_state': 'first'
    }).reset_index()

    print(f"按邮政编码去重后: {len(geo_by_zip):,} 条记录")
    print(f"邮政编码数量: {geolocation['geolocation_zip_code_prefix'].nunique():,}")

    return geo_by_zip


def save_cleaned_data(datasets, output_dir):
    """保存清洗后的数据"""
    print("\n" + "=" * 60)
    print("保存清洗后的数据")
    print("=" * 60)

    os.makedirs(output_dir, exist_ok=True)

    for name, df in datasets.items():
        output_path = os.path.join(output_dir, f"{name}_cleaned.csv")
        df.to_csv(output_path, index=False)
        print(f"  {name}: {len(df):,} 行 -> {os.path.basename(output_path)}")

    print(f"\n数据已保存至: {output_dir}")


def save_cleaning_report(datasets, output_path):
    """保存清洗报告"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Olist 巴西电商数据清洗报告\n")
        f.write("=" * 60 + "\n\n")

        f.write("一、数据集概览\n")
        f.write("-" * 40 + "\n")
        for name, df in datasets.items():
            f.write(f"  {name}: {len(df):,} 行 × {df.shape[1]} 列\n")

        f.write("\n二、主要清洗操作\n")
        f.write("-" * 40 + "\n")
        f.write("  1. 时间字段格式转换\n")
        f.write("  2. 缺失值处理\n")
        f.write("  3. 添加派生字段（配送时长、延迟天数等）\n")
        f.write("  4. 地理信息按邮政编码去重\n")
        f.write("  5. 品类名称翻译\n")
        f.write("  6. 评价情感标注\n")
        f.write("  7. 文本字段标准化\n")


def main():
    data_dir = r"E:\ecom_ai\data\raw\olist"
    output_dir = r"E:\ecom_ai\data\processed\olist"
    os.makedirs(output_dir, exist_ok=True)

    start_time = pd.Timestamp.now()
    print(f"[{datetime.now()}] Olist 数据清洗开始")
    print(f"输入目录: {data_dir}")
    print(f"输出目录: {output_dir}\n")

    # 1. 加载数据
    datasets = load_datasets(data_dir)

    # 2. 清洗各表
    print("\n" + "=" * 60)
    print("开始清洗各数据表")
    print("=" * 60)

    if 'orders' in datasets:
        datasets['orders'] = clean_orders(datasets['orders'])

    if 'order_items' in datasets:
        datasets['order_items'] = clean_order_items(datasets['order_items'])

    if 'products' in datasets:
        cat_trans = datasets.get('category_translation', None)
        datasets['products'] = clean_products(datasets['products'], cat_trans)

    if 'customers' in datasets:
        datasets['customers'] = clean_customers(datasets['customers'])

    if 'sellers' in datasets:
        datasets['sellers'] = clean_sellers(datasets['sellers'])

    if 'order_payments' in datasets:
        datasets['order_payments'] = clean_order_payments(datasets['order_payments'])

    if 'order_reviews' in datasets:
        datasets['order_reviews'] = clean_order_reviews(datasets['order_reviews'])

    if 'geolocation' in datasets:
        datasets['geolocation'] = clean_geolocation(datasets['geolocation'])

    # 3. 保存清洗后的数据
    save_cleaned_data(datasets, output_dir)

    # 4. 保存清洗报告
    report_path = os.path.join(output_dir, "cleaning_report.txt")
    save_cleaning_report(datasets, report_path)
    print(f"\n清洗报告已保存至: {report_path}")

    elapsed = (pd.Timestamp.now() - start_time).total_seconds()
    print(f"\n[{datetime.now()}] 数据清洗完成，耗时: {elapsed:.2f}秒")


if __name__ == "__main__":
    main()
