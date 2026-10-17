# -*- coding: utf-8 -*-
"""
淘宝用户行为数据清洗脚本（PySpark版）
处理1亿+条用户行为数据的清洗工作
"""
import os
import time
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType, TimestampType
)
from pyspark.sql.window import Window


def create_spark_session():
    """创建 SparkSession"""
    spark = (
        SparkSession.builder
        .appName("TaobaoBehaviorDataCleaning")
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "8g")
        .config("spark.sql.shuffle.partitions", "200")
        .config("spark.driver.maxResultSize", "2g")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def load_data(spark, data_path):
    """加载淘宝用户行为数据"""
    schema = StructType([
        StructField("user_id", IntegerType(), nullable=False),
        StructField("item_id", IntegerType(), nullable=False),
        StructField("category_id", IntegerType(), nullable=False),
        StructField("behavior_type", StringType(), nullable=False),
        StructField("timestamp", LongType(), nullable=False),
    ])

    print(f"[{datetime.now()}] 正在加载数据: {data_path}")
    df = spark.read.csv(
        data_path,
        schema=schema,
        header=False,
        sep=",",
        mode="DROPMALFORMED"
    )
    print(f"[{datetime.now()}] 原始数据量: {df.count():,}")
    return df


def step1_remove_duplicates(df):
    """步骤1：去重"""
    print("\n" + "=" * 60)
    print("步骤1：去除重复记录")
    print("=" * 60)

    original_count = df.count()

    # 完全重复的记录（同一用户、商品、行为、时间戳）
    df_dedup = df.dropDuplicates(["user_id", "item_id", "behavior_type", "timestamp"])
    dedup_count = df_dedup.count()

    removed = original_count - dedup_count
    print(f"原始记录数: {original_count:,}")
    print(f"去重后记录数: {dedup_count:,}")
    print(f"去除重复数: {removed:,} ({removed/original_count*100:.4f}%)")

    return df_dedup


def step2_handle_missing_values(df):
    """步骤2：处理缺失值"""
    print("\n" + "=" * 60)
    print("步骤2：处理缺失值")
    print("=" * 60)

    original_count = df.count()

    # 统计各列缺失值
    null_counts = df.select([
        F.count(F.when(F.col(c).isNull(), c)).alias(c)
        for c in df.columns
    ]).collect()[0]

    print("各列缺失值统计:")
    for col_name in df.columns:
        print(f"  {col_name}: {null_counts[col_name]:,}")

    # 由于核心字段（user_id, item_id, behavior_type, timestamp）不能缺失，
    # 删除任何核心字段为空的记录
    df_clean = df.dropna(subset=["user_id", "item_id", "behavior_type", "timestamp"])
    clean_count = df_clean.count()

    removed = original_count - clean_count
    print(f"\n删除核心字段缺失记录: {removed:,}")
    print(f"清洗后记录数: {clean_count:,}")

    return df_clean


def step3_validate_behavior_type(df):
    """步骤3：验证行为类型"""
    print("\n" + "=" * 60)
    print("步骤3：验证行为类型")
    print("=" * 60)

    valid_behaviors = ["pv", "buy", "cart", "fav"]

    # 统计无效行为类型
    invalid_df = df.filter(~F.col("behavior_type").isin(valid_behaviors))
    invalid_count = invalid_df.count()

    print(f"有效行为类型: {valid_behaviors}")
    print(f"无效行为类型记录数: {invalid_count:,}")

    if invalid_count > 0:
        print("无效行为类型分布:")
        invalid_counts = invalid_df.groupBy("behavior_type").count().collect()
        for row in invalid_counts:
            print(f"  {row['behavior_type']}: {row['count']:,}")

    # 保留有效行为
    df_valid = df.filter(F.col("behavior_type").isin(valid_behaviors))
    print(f"清洗后记录数: {df_valid.count():,}")

    return df_valid


def step4_validate_timestamp(df):
    """步骤4：验证时间戳"""
    print("\n" + "=" * 60)
    print("步骤4：验证时间戳")
    print("=" * 60)

    # 数据集的时间范围：2017-11-25 到 2017-12-04
    min_valid_ts = 1511539200  # 2017-11-25 00:00:00
    max_valid_ts = 1512393599  # 2017-12-04 23:59:59

    # 统计异常时间戳
    abnormal_df = df.filter(
        (F.col("timestamp") < min_valid_ts) | (F.col("timestamp") > max_valid_ts)
    )
    abnormal_count = abnormal_df.count()
    total = df.count()

    print(f"有效时间范围: 2017-11-25 ~ 2017-12-04")
    print(f"异常时间戳记录数: {abnormal_count:,} ({abnormal_count/total*100:.4f}%)")

    if abnormal_count > 0:
        # 查看异常时间分布
        print("\n异常时间戳样本:")
        abnormal_df.select("timestamp").limit(10).show()

    # 保留有效时间范围内的数据
    df_valid = df.filter(
        (F.col("timestamp") >= min_valid_ts) & (F.col("timestamp") <= max_valid_ts)
    )
    print(f"\n清洗后记录数: {df_valid.count():,}")

    return df_valid


def step5_add_time_features(df):
    """步骤5：添加时间特征"""
    print("\n" + "=" * 60)
    print("步骤5：添加时间特征")
    print("=" * 60)

    # 转换时间戳
    df = df.withColumn("datetime", F.from_unixtime(F.col("timestamp")).cast(TimestampType()))
    df = df.withColumn("date", F.to_date(F.col("datetime")))
    df = df.withColumn("hour", F.hour(F.col("datetime")))
    df = df.withColumn("day_of_week", F.dayofweek(F.col("datetime")))  # 1=周日, 7=周六
    df = df.withColumn("is_weekend", F.when(F.col("day_of_week").isin([1, 7]), 1).otherwise(0))

    # 时间段划分
    df = df.withColumn(
        "time_period",
        F.when((F.col("hour") >= 0) & (F.col("hour") < 6), "凌晨")
        .when((F.col("hour") >= 6) & (F.col("hour") < 12), "上午")
        .when((F.col("hour") >= 12) & (F.col("hour") < 14), "中午")
        .when((F.col("hour") >= 14) & (F.col("hour") < 18), "下午")
        .when((F.col("hour") >= 18) & (F.col("hour") < 22), "晚上")
        .otherwise("深夜")
    )

    print("添加的时间特征:")
    print("  - datetime: 完整日期时间")
    print("  - date: 日期")
    print("  - hour: 小时 (0-23)")
    print("  - day_of_week: 星期几 (1=周日, 7=周六)")
    print("  - is_weekend: 是否周末 (1=是, 0=否)")
    print("  - time_period: 时间段 (凌晨/上午/中午/下午/晚上/深夜)")

    print(f"\n数据量: {df.count():,}")
    return df


def step6_filter_abnormal_users(df):
    """步骤6：过滤异常用户（可选）"""
    print("\n" + "=" * 60)
    print("步骤6：过滤异常用户行为")
    print("=" * 60)

    # 统计每个用户的行为数
    user_behavior_count = df.groupBy("user_id").count()
    total_users = user_behavior_count.count()

    # 计算分位数
    percentiles = user_behavior_count.stat.approxQuantile(
        "count", [0.99, 0.999, 0.9999], 0.01
    )
    print(f"用户行为数分位数:")
    print(f"  99%分位数: {percentiles[0]:.0f}")
    print(f"  99.9%分位数: {percentiles[1]:.0f}")
    print(f"  99.99%分位数: {percentiles[2]:.0f}")

    # 找出极端异常用户（行为数 > 99.99% 分位数）
    extreme_threshold = percentiles[2]
    extreme_users = user_behavior_count.filter(F.col("count") > extreme_threshold)
    extreme_count = extreme_users.count()

    print(f"\n极端异常用户数 (> {extreme_threshold:.0f} 次行为): {extreme_count:,} ({extreme_count/total_users*100:.4f}%)")

    # 查看异常用户的行为分布
    if extreme_count > 0 and extreme_count < 20:
        print("\n异常用户详情:")
        extreme_users.orderBy(F.col("count").desc()).show()

    # 保留异常用户（可能是真实的重度用户），仅做标记
    print("\n注意：保留所有用户，不主动过滤极端用户（可能是真实重度用户）")
    print("如需过滤，可使用 user_behavior_count 进行筛选")

    return df


def step7_save_clean_data(df, output_path):
    """步骤7：保存清洗后的数据"""
    print("\n" + "=" * 60)
    print("步骤7：保存清洗后的数据")
    print("=" * 60)

    # 保存为 Parquet 格式（列式存储，压缩率高，读取快）
    parquet_path = os.path.join(output_path, "cleaned.parquet")
    print(f"保存为 Parquet 格式: {parquet_path}")
    df.write.mode("overwrite").parquet(parquet_path)

    # 保存清洗后的数据统计
    stats = {
        "total_records": df.count(),
        "unique_users": df.select("user_id").distinct().count(),
        "unique_items": df.select("item_id").distinct().count(),
        "unique_categories": df.select("category_id").distinct().count(),
        "date_range": df.agg(
            F.min("date").alias("min_date"),
            F.max("date").alias("max_date")
        ).collect()[0]
    }

    print(f"\n清洗后数据统计:")
    print(f"  总记录数: {stats['total_records']:,}")
    print(f"  用户数: {stats['unique_users']:,}")
    print(f"  商品数: {stats['unique_items']:,}")
    print(f"  品类数: {stats['unique_categories']:,}")
    print(f"  日期范围: {stats['date_range']['min_date']} ~ {stats['date_range']['max_date']}")

    # 行为类型分布
    print(f"\n行为类型分布:")
    behavior_counts = df.groupBy("behavior_type").count().orderBy("behavior_type").collect()
    for row in behavior_counts:
        pct = row["count"] / stats["total_records"] * 100
        print(f"  {row['behavior_type']}: {row['count']:,} ({pct:.2f}%)")

    return stats


def save_cleaning_report(stats, report_path):
    """保存清洗报告"""
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("淘宝用户行为数据清洗报告\n")
        f.write("=" * 60 + "\n\n")

        f.write("一、清洗后数据统计\n")
        f.write("-" * 40 + "\n")
        f.write(f"总记录数: {stats['total_records']:,}\n")
        f.write(f"用户数: {stats['unique_users']:,}\n")
        f.write(f"商品数: {stats['unique_items']:,}\n")
        f.write(f"品类数: {stats['unique_categories']:,}\n")
        f.write(f"日期范围: {stats['date_range']['min_date']} ~ {stats['date_range']['max_date']}\n")

        f.write("\n二、存储格式\n")
        f.write("-" * 40 + "\n")
        f.write("格式: Parquet (列式存储，Snappy压缩)\n")
        f.write("优点: 高压缩率、快速读取、支持谓词下推\n")


def main():
    # 配置路径
    data_path = r"E:\ecom_ai\data\raw\taobao_behavior\UserBehavior.csv"
    output_dir = r"E:\ecom_ai\data\processed\taobao_behavior"
    os.makedirs(output_dir, exist_ok=True)

    start_time = time.time()
    print(f"[{datetime.now()}] 淘宝用户行为数据清洗开始")
    print(f"输入文件: {data_path}")
    print(f"输出目录: {output_dir}")

    # 创建 SparkSession
    spark = create_spark_session()
    print(f"Spark版本: {spark.version}")

    try:
        # 1. 加载数据
        df = load_data(spark, data_path)

        # 2. 去重
        df = step1_remove_duplicates(df)

        # 3. 处理缺失值
        df = step2_handle_missing_values(df)

        # 4. 验证行为类型
        df = step3_validate_behavior_type(df)

        # 5. 验证时间戳
        df = step4_validate_timestamp(df)

        # 6. 添加时间特征
        df = step5_add_time_features(df)

        # 7. 异常用户分析（保留所有用户）
        df = step6_filter_abnormal_users(df)

        # 8. 保存清洗后的数据
        stats = step7_save_clean_data(df, output_dir)

        # 保存清洗报告
        report_path = os.path.join(output_dir, "cleaning_report.txt")
        save_cleaning_report(stats, report_path)
        print(f"\n清洗报告已保存至: {report_path}")

    finally:
        spark.stop()

    elapsed = time.time() - start_time
    print(f"\n[{datetime.now()}] 数据清洗完成，耗时: {elapsed:.2f}秒")


if __name__ == "__main__":
    main()
