# -*- coding: utf-8 -*-
"""
Olist 巴西电商数据集探索分析
包含 9 个数据表的综合探索
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
            print(f"  {name}: {len(datasets[name]):,} 行, {datasets[name].shape[1]} 列")
        else:
            print(f"  {name}: 文件不存在 ({filename})")

    print(f"[{datetime.now()}] 数据加载完成\n")
    return datasets


def basic_overview(datasets):
    """数据集基础概览"""
    print("=" * 70)
    print("一、数据集基础概览")
    print("=" * 70)

    for name, df in datasets.items():
        print(f"\n--- {name} ---")
        print(f"  形状: {df.shape[0]:,} 行 × {df.shape[1]} 列")
        print(f"  列名: {list(df.columns)}")
        print(f"  数据类型:")
        for col in df.columns:
            print(f"    {col}: {df[col].dtype}")

        # 缺失值统计
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print(f"  缺失值:")
            for col in df.columns:
                if null_counts[col] > 0:
                    pct = null_counts[col] / len(df) * 100
                    print(f"    {col}: {null_counts[col]:,} ({pct:.2f}%)")
        else:
            print(f"  缺失值: 无")


def orders_analysis(orders, order_items, order_payments):
    """订单数据分析"""
    print("\n" + "=" * 70)
    print("二、订单数据分析")
    print("=" * 70)

    # 订单状态分布
    print("\n--- 订单状态分布 ---")
    status_counts = orders['order_status'].value_counts()
    total_orders = len(orders)
    print(f"{'状态':<20} {'数量':>10} {'占比':>10}")
    print("-" * 45)
    for status, count in status_counts.items():
        print(f"{status:<20} {count:>10,} {count/total_orders*100:>9.2f}%")

    # 订单时间范围
    orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
    print(f"\n订单时间范围:")
    print(f"  最早订单: {orders['order_purchase_timestamp'].min()}")
    print(f"  最晚订单: {orders['order_purchase_timestamp'].max()}")

    # 月度订单趋势
    orders['order_month'] = orders['order_purchase_timestamp'].dt.to_period('M')
    monthly_orders = orders.groupby('order_month').size()
    print(f"\n--- 月度订单趋势 ---")
    print(f"{'月份':<10} {'订单数':>10}")
    print("-" * 25)
    for month, count in monthly_orders.items():
        print(f"{month:<10} {count:>10,}")

    # 订单金额分析（已交付订单）
    delivered_orders = orders[orders['order_status'] == 'delivered']
    payments_by_order = order_payments.groupby('order_id')['payment_value'].sum().reset_index()
    delivered_payments = delivered_orders.merge(payments_by_order, on='order_id', how='left')

    print(f"\n--- 订单金额分析（已交付订单） ---")
    print(f"已交付订单数: {len(delivered_orders):,}")
    print(f"总销售额: R$ {delivered_payments['payment_value'].sum():,.2f}")
    print(f"平均订单金额: R$ {delivered_payments['payment_value'].mean():.2f}")
    print(f"订单金额中位数: R$ {delivered_payments['payment_value'].median():.2f}")
    print(f"最小订单金额: R$ {delivered_payments['payment_value'].min():.2f}")
    print(f"最大订单金额: R$ {delivered_payments['payment_value'].max():.2f}")

    # 每订单商品数
    items_per_order = order_items.groupby('order_id').size()
    print(f"\n--- 每订单商品数 ---")
    print(f"平均每订单商品数: {items_per_order.mean():.2f}")
    print(f"每订单商品数中位数: {items_per_order.median():.0f}")
    print(f"最多商品数: {items_per_order.max()}")

    # 支付方式分析
    print(f"\n--- 支付方式分析 ---")
    payment_type_counts = order_payments.groupby('payment_type')['order_id'].nunique().sort_values(ascending=False)
    total_paid_orders = order_payments['order_id'].nunique()
    print(f"{'支付方式':<20} {'订单数':>10} {'占比':>10}")
    print("-" * 45)
    for ptype, count in payment_type_counts.items():
        print(f"{ptype:<20} {count:>10,} {count/total_paid_orders*100:>9.2f}%")

    # 分期付款分析
    installment_orders = order_payments[order_payments['payment_type'] == 'credit_card']
    print(f"\n--- 信用卡分期付款分析 ---")
    print(f"使用分期的订单数: {len(installment_orders):,}")
    print(f"平均分期数: {installment_orders['payment_installments'].mean():.1f}")
    install_counts = installment_orders['payment_installments'].value_counts().sort_index()
    print(f"分期数分布:")
    for inst, count in install_counts.head(12).items():
        print(f"  {inst:>2}期: {count:>6,} ({count/len(installment_orders)*100:.1f}%)")


def customer_analysis(customers, orders, order_payments):
    """客户分析"""
    print("\n" + "=" * 70)
    print("三、客户分析")
    print("=" * 70)

    total_customers = customers['customer_unique_id'].nunique()
    print(f"\n总客户数(去重): {total_customers:,}")
    print(f"总订单数: {len(orders):,}")

    # 客户地理分布
    print(f"\n--- 客户州分布 Top 15 ---")
    state_counts = customers['customer_state'].value_counts()
    print(f"{'州':<6} {'客户数':>10} {'占比':>10}")
    print("-" * 32)
    for state, count in state_counts.head(15).items():
        print(f"{state:<6} {count:>10,} {count/len(customers)*100:>9.2f}%")

    # 客户城市分布 Top 10
    print(f"\n--- 客户城市分布 Top 10 ---")
    city_counts = customers['customer_city'].value_counts()
    print(f"{'城市':<25} {'客户数':>10} {'占比':>10}")
    print("-" * 50)
    for city, count in city_counts.head(10).items():
        print(f"{city:<25} {count:>10,} {count/len(customers)*100:>9.2f}%")

    # 客户复购分析
    orders_with_customer = orders.merge(customers[['order_id', 'customer_unique_id']], on='order_id', how='left')
    orders_per_customer = orders_with_customer.groupby('customer_unique_id').size()

    print(f"\n--- 客户购买频次分析 ---")
    print(f"只购买1次的客户: {sum(orders_per_customer == 1):,} ({sum(orders_per_customer == 1)/total_customers*100:.2f}%)")
    print(f"购买2次及以上的客户: {sum(orders_per_customer >= 2):,} ({sum(orders_per_customer >= 2)/total_customers*100:.2f}%)")
    print(f"平均购买次数: {orders_per_customer.mean():.2f}")
    print(f"最多购买次数: {orders_per_customer.max()}")

    # 客户价值分析（RFM初步）
    delivered = orders[orders['order_status'] == 'delivered']
    delivered_with_customer = delivered.merge(customers[['order_id', 'customer_unique_id']], on='order_id', how='left')
    payments_by_order = order_payments.groupby('order_id')['payment_value'].sum().reset_index()
    customer_value = delivered_with_customer.merge(payments_by_order, on='order_id', how='left')
    customer_value = customer_value.groupby('customer_unique_id')['payment_value'].sum()

    print(f"\n--- 客户累计消费金额分布 ---")
    print(f"平均消费金额: R$ {customer_value.mean():.2f}")
    print(f"消费金额中位数: R$ {customer_value.median():.2f}")
    print(f"最高消费金额: R$ {customer_value.max():.2f}")

    # 消费分档
    bins = [0, 50, 100, 200, 500, 1000, float('inf')]
    labels = ['<50', '50-100', '100-200', '200-500', '500-1000', '1000+']
    value_bins = pd.cut(customer_value, bins=bins, labels=labels)
    print(f"\n消费金额分档:")
    for label in labels:
        count = sum(value_bins == label)
        print(f"  R$ {label:<10}: {count:>8,} 客户 ({count/len(customer_value)*100:.1f}%)")


def product_analysis(products, order_items, category_translation):
    """商品分析"""
    print("\n" + "=" * 70)
    print("四、商品分析")
    print("=" * 70)

    total_products = len(products)
    print(f"\n总商品数: {total_products:,}")
    print(f"商品品类数: {products['product_category_name'].nunique()}")

    # 品类分布
    print(f"\n--- 商品品类分布 Top 15 ---")
    category_counts = products['product_category_name'].value_counts()
    print(f"{'品类':<40} {'商品数':>10} {'占比':>10}")
    print("-" * 65)
    for cat, count in category_counts.head(15).items():
        # 尝试翻译
        translation = category_translation[category_translation['product_category_name'] == cat]
        cat_name = cat
        if len(translation) > 0:
            cat_name = translation.iloc[0]['product_category_name_english']
        print(f"{cat_name:<40} {count:>10,} {count/total_products*100:>9.2f}%")

    # 销量最高的品类
    print(f"\n--- 销量最高的品类 Top 15 ---")
    items_with_category = order_items.merge(products[['product_id', 'product_category_name']], on='product_id', how='left')
    category_sales = items_with_category.groupby('product_category_name').agg(
        order_count=('order_id', 'nunique'),
        item_count=('order_item_id', 'count'),
        total_sales=('price', 'sum')
    ).sort_values('item_count', ascending=False)

    print(f"{'品类':<30} {'销量':>10} {'订单数':>10} {'销售额(R$)':>15}")
    print("-" * 70)
    for cat, row in category_sales.head(15).iterrows():
        translation = category_translation[category_translation['product_category_name'] == cat]
        cat_name = cat
        if len(translation) > 0:
            cat_name = translation.iloc[0]['product_category_name_english']
        print(f"{cat_name:<30} {int(row['item_count']):>10,} {int(row['order_count']):>10,} {row['total_sales']:>14,.2f}")

    # 商品价格分析
    print(f"\n--- 商品价格分析 ---")
    print(f"平均价格: R$ {order_items['price'].mean():.2f}")
    print(f"价格中位数: R$ {order_items['price'].median():.2f}")
    print(f"最低价格: R$ {order_items['price'].min():.2f}")
    print(f"最高价格: R$ {order_items['price'].max():.2f}")

    # 运费分析
    print(f"\n--- 运费分析 ---")
    print(f"平均运费: R$ {order_items['freight_value'].mean():.2f}")
    print(f"运费中位数: R$ {order_items['freight_value'].median():.2f}")
    print(f"运费占价格比例: {order_items['freight_value'].sum() / order_items['price'].sum() * 100:.2f}%")


def seller_analysis(sellers, order_items):
    """卖家分析"""
    print("\n" + "=" * 70)
    print("五、卖家分析")
    print("=" * 70)

    total_sellers = len(sellers)
    print(f"\n总卖家数: {total_sellers:,}")

    # 卖家地理分布
    print(f"\n--- 卖家州分布 ---")
    state_counts = sellers['seller_state'].value_counts()
    print(f"{'州':<6} {'卖家数':>10} {'占比':>10}")
    print("-" * 32)
    for state, count in state_counts.items():
        print(f"{state:<6} {count:>10,} {count/total_sellers*100:>9.2f}%")

    # 卖家销量分析
    seller_sales = order_items.groupby('seller_id').agg(
        order_count=('order_id', 'nunique'),
        item_count=('order_item_id', 'count'),
        total_sales=('price', 'sum'),
        total_freight=('freight_value', 'sum')
    ).sort_values('total_sales', ascending=False)

    print(f"\n--- 卖家销售分布 ---")
    print(f"有销售记录的卖家数: {len(seller_sales):,}")
    print(f"无销售记录的卖家数: {total_sellers - len(seller_sales):,}")
    print(f"平均销售额: R$ {seller_sales['total_sales'].mean():.2f}")
    print(f"销售额中位数: R$ {seller_sales['total_sales'].median():.2f}")
    print(f"最高销售额: R$ {seller_sales['total_sales'].max():.2f}")

    # Top 10 卖家
    print(f"\n--- 销售额 Top 10 卖家 ---")
    print(f"{'排名':<6} {'订单数':>10} {'销量':>10} {'销售额(R$)':>15}")
    print("-" * 45)
    for i, (seller_id, row) in enumerate(seller_sales.head(10).iterrows(), 1):
        print(f"{i:<6} {int(row['order_count']):>10,} {int(row['item_count']):>10,} {row['total_sales']:>14,.2f}")

    # 卖家集中度（帕累托分析）
    seller_sales_sorted = seller_sales['total_sales'].sort_values(ascending=False)
    cumulative = seller_sales_sorted.cumsum() / seller_sales_sorted.sum()
    top_20_pct = int(len(seller_sales_sorted) * 0.2)
    top_20_contribution = cumulative.iloc[top_20_pct - 1] * 100
    print(f"\n--- 卖家集中度 ---")
    print(f"前 20% 卖家贡献了 {top_20_contribution:.1f}% 的销售额")


def review_analysis(order_reviews, orders):
    """评价分析"""
    print("\n" + "=" * 70)
    print("六、评价分析")
    print("=" * 70)

    total_reviews = len(order_reviews)
    print(f"\n总评价数: {total_reviews:,}")
    print(f"有评价的订单数: {order_reviews['order_id'].nunique():,}")

    # 评分分布
    print(f"\n--- 评分分布 ---")
    score_counts = order_reviews['review_score'].value_counts().sort_index()
    print(f"{'评分':<8} {'数量':>10} {'占比':>10}")
    print("-" * 32)
    for score, count in score_counts.items():
        print(f"{score}星{'':<4} {count:>10,} {count/total_reviews*100:>9.2f}%")

    print(f"\n平均评分: {order_reviews['review_score'].mean():.2f}")

    # 是否有评论消息
    has_comment = order_reviews['review_comment_message'].notna().sum()
    print(f"\n有文字评论的评价: {has_comment:,} ({has_comment/total_reviews*100:.2f}%)")

    # 评论标题
    has_title = order_reviews['review_comment_title'].notna().sum()
    print(f"有评论标题的评价: {has_title:,} ({has_title/total_reviews*100:.2f}%)")


def logistics_analysis(orders, order_items, customers, sellers):
    """物流分析"""
    print("\n" + "=" * 70)
    print("七、物流分析")
    print("=" * 70)

    # 转换时间列
    time_cols = [
        'order_purchase_timestamp', 'order_delivered_carrier_date',
        'order_delivered_customer_date', 'order_estimated_delivery_date'
    ]
    for col in time_cols:
        orders[col] = pd.to_datetime(orders[col])

    # 已交付订单
    delivered = orders[orders['order_status'] == 'delivered'].copy()

    # 配送时长
    delivered['delivery_days'] = (
        delivered['order_delivered_customer_date'] - delivered['order_purchase_timestamp']
    ).dt.total_seconds() / 86400

    print(f"\n--- 配送时长分析 ---")
    print(f"平均配送时长: {delivered['delivery_days'].mean():.1f} 天")
    print(f"配送时长中位数: {delivered['delivery_days'].median():.1f} 天")
    print(f"最短配送时长: {delivered['delivery_days'].min():.1f} 天")
    print(f"最长配送时长: {delivered['delivery_days'].max():.1f} 天")

    # 预计送达 vs 实际送达
    delivered['estimated_days'] = (
        delivered['order_estimated_delivery_date'] - delivered['order_purchase_timestamp']
    ).dt.total_seconds() / 86400
    delivered['delay_days'] = delivered['delivery_days'] - delivered['estimated_days']

    on_time = (delivered['delay_days'] <= 0).sum()
    print(f"\n--- 准时送达率 ---")
    print(f"准时送达: {on_time:,} ({on_time/len(delivered)*100:.2f}%)")
    print(f"延迟送达: {len(delivered) - on_time:,} ({(len(delivered)-on_time)/len(delivered)*100:.2f}%)")
    print(f"平均延迟天数: {delivered['delay_days'].mean():.1f} 天")

    # 各配送时长区间
    bins = [0, 3, 7, 14, 21, 30, float('inf')]
    labels = ['<3天', '3-7天', '7-14天', '14-21天', '21-30天', '30天+']
    delivery_bins = pd.cut(delivered['delivery_days'], bins=bins, labels=labels)
    print(f"\n配送时长区间分布:")
    for label in labels:
        count = sum(delivery_bins == label)
        print(f"  {label:<10}: {count:>6,} ({count/len(delivered)*100:.1f}%)")


def save_summary(datasets, output_path):
    """保存分析摘要"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Olist 巴西电商数据集探索分析报告\n")
        f.write("=" * 60 + "\n\n")

        f.write("数据集概览:\n")
        for name, df in datasets.items():
            f.write(f"  {name}: {len(df):,} 行 × {df.shape[1]} 列\n")

        if 'orders' in datasets:
            orders = datasets['orders']
            f.write(f"\n订单总数: {len(orders):,}\n")
            f.write(f"订单状态: {orders['order_status'].nunique()} 种\n")

        if 'customers' in datasets:
            customers = datasets['customers']
            f.write(f"客户总数: {customers['customer_unique_id'].nunique():,}\n")

        if 'products' in datasets:
            products = datasets['products']
            f.write(f"商品总数: {len(products):,}\n")
            f.write(f"商品品类数: {products['product_category_name'].nunique()}\n")

        if 'sellers' in datasets:
            sellers = datasets['sellers']
            f.write(f"卖家总数: {len(sellers):,}\n")


def main():
    data_dir = r"E:\ecom_ai\data\raw\olist"
    output_dir = r"E:\ecom_ai\data\processed\olist"
    os.makedirs(output_dir, exist_ok=True)

    start_time = pd.Timestamp.now()
    print(f"[{datetime.now()}] Olist 数据集探索分析开始")
    print(f"数据目录: {data_dir}\n")

    # 1. 加载数据
    datasets = load_datasets(data_dir)

    # 2. 基础概览
    basic_overview(datasets)

    # 3. 订单分析
    if all(k in datasets for k in ['orders', 'order_items', 'order_payments']):
        orders_analysis(datasets['orders'], datasets['order_items'], datasets['order_payments'])

    # 4. 客户分析
    if all(k in datasets for k in ['customers', 'orders', 'order_payments']):
        customer_analysis(datasets['customers'], datasets['orders'], datasets['order_payments'])

    # 5. 商品分析
    if all(k in datasets for k in ['products', 'order_items', 'category_translation']):
        product_analysis(datasets['products'], datasets['order_items'], datasets['category_translation'])

    # 6. 卖家分析
    if all(k in datasets for k in ['sellers', 'order_items']):
        seller_analysis(datasets['sellers'], datasets['order_items'])

    # 7. 评价分析
    if all(k in datasets for k in ['order_reviews', 'orders']):
        review_analysis(datasets['order_reviews'], datasets['orders'])

    # 8. 物流分析
    if all(k in datasets for k in ['orders', 'order_items', 'customers', 'sellers']):
        logistics_analysis(datasets['orders'], datasets['order_items'], datasets['customers'], datasets['sellers'])

    # 保存摘要
    summary_path = os.path.join(output_dir, "eda_summary.txt")
    save_summary(datasets, summary_path)
    print(f"\n分析摘要已保存至: {summary_path}")

    elapsed = (pd.Timestamp.now() - start_time).total_seconds()
    print(f"\n[{datetime.now()}] 分析完成，耗时: {elapsed:.2f}秒")


if __name__ == "__main__":
    main()
