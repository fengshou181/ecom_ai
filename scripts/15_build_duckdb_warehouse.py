# -*- coding: utf-8 -*-
"""
电商统一数据仓库构建脚本
将所有数据集导入 DuckDB，建立统一的分析入口
"""
import os
import duckdb
from datetime import datetime


class EcomDataWarehouse:
    """电商数据仓库构建器"""

    def __init__(self, db_path, data_base_dir):
        self.db_path = db_path
        self.data_base_dir = data_base_dir
        self.con = duckdb.connect(db_path)
        print(f"[{datetime.now()}] 连接数据库: {db_path}")
        print(f"DuckDB 版本: {duckdb.__version__}\n")

    def close(self):
        self.con.close()
        print(f"\n[{datetime.now()}] 数据库连接已关闭")

    def import_csv(self, table_name, csv_path, schema=None, delimiter=','):
        """导入 CSV 文件到指定表"""
        if not os.path.exists(csv_path):
            print(f"  ⚠️  文件不存在，跳过: {csv_path}")
            return False

        file_size_mb = os.path.getsize(csv_path) / 1024 / 1024
        print(f"  导入: {table_name} ({file_size_mb:.1f} MB) ...", end=' ', flush=True)

        # 如果表已存在，先删除
        self.con.execute(f"DROP TABLE IF EXISTS {table_name}")

        # 使用 DuckDB 的 read_csv_auto 自动推断类型
        self.con.execute(f"""
            CREATE TABLE {table_name} AS
            SELECT * FROM read_csv_auto('{csv_path}', header=true, delim='{delimiter}')
        """)

        row_count = self.con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"✅ {row_count:,} 行")
        return True

    def import_parquet(self, table_name, parquet_path):
        """导入 Parquet 文件到指定表"""
        if not os.path.exists(parquet_path):
            print(f"  ⚠️  文件不存在，跳过: {parquet_path}")
            return False

        file_size_mb = os.path.getsize(parquet_path) / 1024 / 1024
        print(f"  导入: {table_name} ({file_size_mb:.1f} MB) ...", end=' ', flush=True)

        self.con.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.con.execute(f"""
            CREATE TABLE {table_name} AS
            SELECT * FROM read_parquet('{parquet_path}')
        """)

        row_count = self.con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"✅ {row_count:,} 行")
        return True

    def create_schema(self, schema_name):
        """创建 Schema（命名空间）"""
        self.con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        print(f"  Schema: {schema_name}")

    # ===== Olist 数据层 =====
    def build_olist_layer(self):
        """构建 Olist 数据层"""
        print("\n" + "=" * 70)
        print("构建 Olist 数据层")
        print("=" * 70)

        olist_dir = os.path.join(self.data_base_dir, 'raw', 'olist')
        processed_dir = os.path.join(self.data_base_dir, 'processed', 'olist')

        self.create_schema('olist')

        # 原始 9 张表
        raw_tables = {
            'olist.customers': 'olist_customers_dataset.csv',
            'olist.geolocation': 'olist_geolocation_dataset.csv',
            'olist.order_items': 'olist_order_items_dataset.csv',
            'olist.order_payments': 'olist_order_payments_dataset.csv',
            'olist.order_reviews': 'olist_order_reviews_dataset.csv',
            'olist.orders': 'olist_orders_dataset.csv',
            'olist.products': 'olist_products_dataset.csv',
            'olist.sellers': 'olist_sellers_dataset.csv',
            'olist.category_translation': 'product_category_name_translation.csv',
        }

        for table_name, filename in raw_tables.items():
            csv_path = os.path.join(olist_dir, filename)
            self.import_csv(table_name, csv_path)

        # 宽表（从 Parquet 导入，更快）
        print("\n  宽表（Parquet）:")
        wide_tables = {
            'olist.order_items_wide': 'olist_order_items_wide.parquet',
            'olist.orders_wide': 'olist_orders_wide.parquet',
        }

        for table_name, filename in wide_tables.items():
            parquet_path = os.path.join(processed_dir, filename)
            self.import_parquet(table_name, parquet_path)

    # ===== 淘宝用户行为数据层 =====
    def build_taobao_layer(self):
        """构建淘宝用户行为数据层"""
        print("\n" + "=" * 70)
        print("构建淘宝用户行为数据层")
        print("=" * 70)

        taobao_dir = os.path.join(self.data_base_dir, 'raw', 'taobao_behavior')

        self.create_schema('taobao')

        # 原始数据（注意：1 亿条数据，用 CSV 直接建表，不复制数据，用 VIEW）
        csv_path = os.path.join(taobao_dir, 'UserBehavior.csv')
        if os.path.exists(csv_path):
            file_size_mb = os.path.getsize(csv_path) / 1024 / 1024
            print(f"  数据文件: UserBehavior.csv ({file_size_mb:.1f} MB)")
            print(f"  由于数据量大，创建视图而非导入表（直接查询 CSV 文件）")

            # 创建视图（直接查询 CSV，不占用额外空间）
            self.con.execute("DROP VIEW IF EXISTS taobao.user_behavior")
            self.con.execute(f"""
                CREATE VIEW taobao.user_behavior AS
                SELECT
                    column00 AS user_id,
                    column01 AS item_id,
                    column02 AS category_id,
                    column03 AS behavior_type,
                    column04 AS timestamp,
                    epoch_ms(column04 * 1000) AS datetime,
                    date_trunc('day', epoch_ms(column04 * 1000)) AS date,
                    extract(hour FROM epoch_ms(column04 * 1000)) AS hour
                FROM read_csv('{csv_path}', header=false, columns={{
                    'column00': 'BIGINT',
                    'column01': 'BIGINT',
                    'column02': 'BIGINT',
                    'column03': 'VARCHAR',
                    'column04': 'BIGINT'
                }}, delim=',')
            """)

            # 快速计数验证
            row_count = self.con.execute("SELECT COUNT(*) FROM taobao.user_behavior").fetchone()[0]
            print(f"  ✅ 视图创建成功，共 {row_count:,} 条记录")

            # 如果有清洗后的 Parquet，也导入
            processed_dir = os.path.join(self.data_base_dir, 'processed', 'taobao_behavior')
            cleaned_parquet = os.path.join(processed_dir, 'cleaned.parquet')
            if os.path.exists(cleaned_parquet):
                print("\n  清洗后数据:")
                self.import_parquet('taobao.user_behavior_cleaned', cleaned_parquet)
        else:
            print("  ⚠️  淘宝用户行为数据不存在")

    # ===== Amazon Reviews 数据层 =====
    def build_amazon_layer(self):
        """构建 Amazon 评论数据层"""
        print("\n" + "=" * 70)
        print("构建 Amazon Reviews 数据层")
        print("=" * 70)

        amazon_dir = os.path.join(self.data_base_dir, 'raw', 'amazon_reviews')

        self.create_schema('amazon')

        tables = {
            'amazon.reviews': 'Reviews.csv',
            'amazon.products': 'amazon_products.csv',
            'amazon.categories': 'amazon_categories.csv',
        }

        for table_name, filename in tables.items():
            csv_path = os.path.join(amazon_dir, filename)
            self.import_csv(table_name, csv_path)

    # ===== Instacart 数据层 =====
    def build_instacart_layer(self):
        """构建 Instacart 杂货配送数据层"""
        print("\n" + "=" * 70)
        print("构建 Instacart 数据层")
        print("=" * 70)

        instacart_dir = os.path.join(self.data_base_dir, 'raw', 'instacart')

        self.create_schema('instacart')

        tables = {
            'instacart.orders': 'orders.csv',
            'instacart.products': 'products.csv',
            'instacart.aisles': 'aisles.csv',
            'instacart.departments': 'departments.csv',
            'instacart.order_products_prior': 'order_products__prior.csv',
            'instacart.order_products_train': 'order_products__train.csv',
        }

        for table_name, filename in tables.items():
            csv_path = os.path.join(instacart_dir, filename)
            self.import_csv(table_name, csv_path)

        # 合并 prior 和 train 为一张完整的订单商品表
        print("\n  合并订单商品表 (prior + train):")
        self.con.execute("DROP TABLE IF EXISTS instacart.order_products_all")
        self.con.execute("""
            CREATE TABLE instacart.order_products_all AS
            SELECT *, 'prior' AS dataset_type
            FROM instacart.order_products_prior
            UNION ALL
            SELECT *, 'train' AS dataset_type
            FROM instacart.order_products_train
        """)
        total = self.con.execute("SELECT COUNT(*) FROM instacart.order_products_all").fetchone()[0]
        print(f"  ✅ instacart.order_products_all: {total:,} 行")

    # ===== 京东商品数据层 =====
    def build_jd_layer(self):
        """构建京东商品数据层"""
        print("\n" + "=" * 70)
        print("构建京东商品数据层")
        print("=" * 70)

        jd_dir = os.path.join(self.data_base_dir, 'raw', 'product_data')

        self.create_schema('jd')

        tables = {
            'jd.products': 'jd_products.csv',
        }

        for table_name, filename in tables.items():
            csv_path = os.path.join(jd_dir, filename)
            if os.path.exists(csv_path):
                self.import_csv(table_name, csv_path)
            else:
                print(f"  ⚠️  文件不存在: {filename}")

    # ===== 创建跨平台统一视图 =====
    def create_unified_views(self):
        """创建跨平台统一分析视图"""
        print("\n" + "=" * 70)
        print("创建跨平台统一分析视图")
        print("=" * 70)

        self.create_schema('unified')

        # 1. 统一行为事件视图
        print("\n  1. 统一用户行为视图 (unified.user_behavior_events):")
        try:
            self.con.execute("DROP VIEW IF EXISTS unified.user_behavior_events")
            self.con.execute("""
                CREATE VIEW unified.user_behavior_events AS
                -- 淘宝行为数据
                SELECT
                    'taobao' AS platform,
                    CAST(user_id AS VARCHAR) AS user_id,
                    CAST(item_id AS VARCHAR) AS item_id,
                    CAST(category_id AS VARCHAR) AS category_id,
                    behavior_type AS event_type,
                    datetime AS event_time,
                    date AS event_date
                FROM taobao.user_behavior

                UNION ALL

                -- Olist 订单事件
                SELECT
                    'olist' AS platform,
                    CAST(c.customer_unique_id AS VARCHAR) AS user_id,
                    CAST(oi.product_id AS VARCHAR) AS item_id,
                    CAST(p.product_category_name AS VARCHAR) AS category_id,
                    'order' AS event_type,
                    o.order_purchase_timestamp AS event_time,
                    DATE(o.order_purchase_timestamp) AS event_date
                FROM olist.orders o
                JOIN olist.order_items oi ON o.order_id = oi.order_id
                JOIN olist.customers c ON o.customer_id = c.customer_id
                JOIN olist.products p ON oi.product_id = p.product_id
                WHERE o.order_status = 'delivered'

                UNION ALL

                -- Instacart 订单事件
                SELECT
                    'instacart' AS platform,
                    CAST(o.user_id AS VARCHAR) AS user_id,
                    CAST(op.product_id AS VARCHAR) AS item_id,
                    CAST(p.department_id AS VARCHAR) AS category_id,
                    'order' AS event_type,
                    CAST(o.order_hour_of_day AS TIMESTAMP) AS event_time,
                    DATE(o.order_dow) AS event_date
                FROM instacart.orders o
                JOIN instacart.order_products_all op ON o.order_id = op.order_id
                JOIN instacart.products p ON op.product_id = p.product_id
            """)
            count = self.con.execute("SELECT COUNT(*) FROM unified.user_behavior_events").fetchone()[0]
            print(f"    ✅ 统一行为视图创建成功，共 {count:,} 条记录")
        except Exception as e:
            print(f"    ⚠️  创建失败: {e}")

        # 2. 统一商品视图
        print("\n  2. 统一商品视图 (unified.products):")
        try:
            self.con.execute("DROP VIEW IF EXISTS unified.products")
            self.con.execute("""
                CREATE VIEW unified.products AS
                -- Olist 商品
                SELECT
                    'olist' AS platform,
                    product_id,
                    product_category_name_english AS category_name,
                    NULL AS product_name,
                    NULL AS price,
                    product_weight_g AS weight_g,
                    product_length_cm AS length_cm,
                    product_height_cm AS height_cm,
                    product_width_cm AS width_cm
                FROM olist.products p
                LEFT JOIN olist.category_translation ct
                    ON p.product_category_name = ct.product_category_name

                UNION ALL

                -- Instacart 商品
                SELECT
                    'instacart' AS platform,
                    CAST(product_id AS VARCHAR) AS product_id,
                    d.department AS category_name,
                    product_name,
                    NULL AS price,
                    NULL AS weight_g,
                    NULL AS length_cm,
                    NULL AS height_cm,
                    NULL AS width_cm
                FROM instacart.products p
                JOIN instacart.departments d ON p.department_id = d.department_id

                UNION ALL

                -- 京东商品
                SELECT
                    'jd' AS platform,
                    CAST(sku AS VARCHAR) AS product_id,
                    category AS category_name,
                    name AS product_name,
                    price,
                    NULL AS weight_g,
                    NULL AS length_cm,
                    NULL AS height_cm,
                    NULL AS width_cm
                FROM jd.products
            """)
            count = self.con.execute("SELECT COUNT(*) FROM unified.products").fetchone()[0]
            print(f"    ✅ 统一商品视图创建成功，共 {count:,} 条商品")
        except Exception as e:
            print(f"    ⚠️  创建失败: {e}")

    # ===== 数据库概览 =====
    def show_overview(self):
        """显示数据库中所有表的概览"""
        print("\n" + "=" * 70)
        print("📊 数据仓库概览")
        print("=" * 70)

        # 获取所有 schema
        schemas = self.con.execute("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'main')
            ORDER BY schema_name
        """).fetchall()

        total_tables = 0
        total_rows = 0

        for (schema_name,) in schemas:
            # 获取该 schema 下的所有表和视图
            tables = self.con.execute(f"""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                ORDER BY table_name
            """).fetchall()

            if not tables:
                continue

            print(f"\n📁 {schema_name} ({len(tables)} 个对象)")
            print("-" * 50)

            for table_name, table_type in tables:
                full_name = f"{schema_name}.{table_name}"
                try:
                    row_count = self.con.execute(f"SELECT COUNT(*) FROM {full_name}").fetchone()[0]
                    type_icon = "📊" if table_type == 'BASE TABLE' else "👁️"
                    print(f"  {type_icon} {table_name:<35} {row_count:>12,} 行")
                    total_tables += 1
                    total_rows += row_count
                except:
                    print(f"  ⚠️  {table_name:<35} (查询失败)")

        db_size_mb = os.path.getsize(self.db_path) / 1024 / 1024 if os.path.exists(self.db_path) else 0
        print(f"\n{'=' * 70}")
        print(f"总计: {total_tables} 个表/视图, 约 {total_rows:,} 条记录")
        print(f"数据库文件大小: {db_size_mb:.1f} MB")
        print(f"{'=' * 70}")

    # ===== 构建全部 =====
    def build_all(self):
        """构建完整数据仓库"""
        print("🚀 开始构建电商统一数据仓库\n")

        # 按顺序构建各数据层
        self.build_olist_layer()
        self.build_taobao_layer()
        self.build_amazon_layer()
        self.build_instacart_layer()
        self.build_jd_layer()

        # 创建统一视图
        self.create_unified_views()

        # 显示概览
        self.show_overview()

        print("\n✅ 数据仓库构建完成！")
        print(f"\n💡 使用方式:")
        print(f"  import duckdb")
        print(f"  con = duckdb.connect('{self.db_path}')")
        print(f"  con.sql('SELECT * FROM olist.orders_wide LIMIT 10').show()")


def main():
    db_path = r"E:\ecom_ai\ecom_ai.duckdb"
    data_base_dir = r"E:\ecom_ai\data"

    # 如果数据库已存在，先删除（重新构建）
    if os.path.exists(db_path):
        print(f"⚠️  数据库已存在，将删除并重建: {db_path}")
        os.remove(db_path)

    dw = EcomDataWarehouse(db_path, data_base_dir)

    try:
        dw.build_all()
    finally:
        dw.close()


if __name__ == "__main__":
    main()
