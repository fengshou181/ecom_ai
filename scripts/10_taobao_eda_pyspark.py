# -*- coding: utf-8 -*-
"""
淘宝用户行为数据探索分析（PySpark版）
处理1亿+条用户行为数据
"""
import os
import time
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType, TimestampType
)


def create_spark_session():
    """创建 SparkSession"""
    spark = (
        SparkSession.builder
        .appName("TaobaoBehaviorEDA")
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

    # 转换时间戳为日期时间
    df = df.withColumn("datetime", F.from_unixtime(F.col("timestamp")).cast(TimestampType()))
    df = df.withColumn("date", F.to_date(F.col("datetime")))
    df = df.withColumn("hour", F.hour(F.col("datetime")))

    print(f"[{datetime.now()}] 数据加载完成")
    return df


def basic_stats(df):
    """基础统计信息"""
    print("\n" + "=" * 60)
    print("一、基础统计信息")
    print("=" * 60)

    # 总记录数
    total_count = df.count()
    print(f"总记录数: {total_count:,}")

    # 独立用户数
    user_count = df.select("user_id").distinct().count()
    print(f"独立用户数: {user_count:,}")

    # 独立商品数
    item_count = df.select("item_id").distinct().count()
    print(f"独立商品数: {item_count:,}")

    # 独立品类数
    category_count = df.select("category_id").distinct().count()
    print(f"独立品类数: {category_count:,}")

    # 时间范围
    time_range = df.agg(
        F.min("datetime").alias("min_time"),
        F.max("datetime").alias("max_time")
    ).collect()[0]
    print(f"时间范围: {time_range['min_time']} ~ {time_range['max_time']}")

    return {
        "total_count": total_count,
        "user_count": user_count,
        "item_count": item_count,
        "category_count": category_count,
        "min_time": time_range["min_time"],
        "max_time": time_range["max_time"]
    }


def behavior_analysis(df):
    """行为类型分析"""
    print("\n" + "=" * 60)
    print("二、行为类型分析")
    print("=" * 60)

    behavior_counts = df.groupBy("behavior_type").count()
    behavior_counts = behavior_counts.orderBy(F.col("count").desc())
    total = df.count()

    print(f"\n{'行为类型':<15} {'数量':>15} {'占比':>10}")
    print("-" * 45)
    for row in behavior_counts.collect():
        pct = row["count"] / total * 100
        print(f"{row['behavior_type']:<15} {row['count']:>15,} {pct:>9.2f}%")

    # 行为说明
    behavior_map = {
        "pv": "浏览商品详情页",
        "buy": "购买商品",
        "cart": "加入购物车",
        "fav": "收藏商品"
    }
    print("\n行为类型说明:")
    for k, v in behavior_map.items():
        print(f"  {k}: {v}")

    return behavior_counts


def conversion_funnel(df):
    """转化漏斗分析"""
    print("\n" + "=" * 60)
    print("三、转化漏斗分析")
    print("=" * 60)

    # 各环节用户数
    pv_users = df.filter(F.col("behavior_type") == "pv").select("user_id").distinct().count()
    fav_users = df.filter(F.col("behavior_type") == "fav").select("user_id").distinct().count()
    cart_users = df.filter(F.col("behavior_type") == "cart").select("user_id").distinct().count()
    buy_users = df.filter(F.col("behavior_type") == "buy").select("user_id").distinct().count()

    print(f"\n{'环节':<15} {'用户数':>12} {'转化率(相对浏览)':>18}")
    print("-" * 50)
    print(f"{'浏览(PV)':<15} {pv_users:>12,} {'100.00%':>18}")
    print(f"{'收藏(Fav)':<15} {fav_users:>12,} {fav_users/pv_users*100:>17.2f}%")
    print(f"{'加购(Cart)':<15} {cart_users:>12,} {cart_users/pv_users*100:>17.2f}%")
    print(f"{'购买(Buy)':<15} {buy_users:>12,} {buy_users/pv_users*100:>17.2f}%")

    # 购买转化率
    print(f"\n整体购买转化率: {buy_users/pv_users*100:.2f}%")

    return {
        "pv_users": pv_users,
        "fav_users": fav_users,
        "cart_users": cart_users,
        "buy_users": buy_users
    }


def time_analysis(df):
    """时间维度分析"""
    print("\n" + "=" * 60)
    print("四、时间维度分析")
    print("=" * 60)

    # 每日行为量
    print("\n--- 每日行为量趋势 ---")
    daily_stats = df.groupBy("date").count().orderBy("date")
    print(f"{'日期':<15} {'行为数':>15}")
    print("-" * 35)
    for row in daily_stats.collect():
        print(f"{str(row['date']):<15} {row['count']:>15,}")

    # 各小时行为分布
    print("\n--- 24小时行为分布 ---")
    hourly_stats = df.groupBy("hour").count().orderBy("hour")
    print(f"{'小时':<10} {'行为数':>15} {'占比':>10}")
    print("-" * 40)
    total = df.count()
    for row in hourly_stats.collect():
        pct = row["count"] / total * 100
        print(f"{row['hour']:>5}时   {row['count']:>15,} {pct:>9.2f}%")

    # 各行为类型的小时分布
    print("\n--- 各行为类型的24小时分布 ---")
    behavior_hourly = df.groupBy("behavior_type", "hour").count().orderBy("behavior_type", "hour")

    # 透视表展示
    behavior_hourly_pivot = behavior_hourly.groupBy("hour").pivot("behavior_type").sum("count").orderBy("hour")
    print(f"\n{'小时':<8} {'PV':>12} {'Cart':>12} {'Fav':>12} {'Buy':>12}")
    print("-" * 60)
    for row in behavior_hourly_pivot.collect():
        print(f"{row['hour']:>4}时   "
              f"{row.get('pv', 0):>12,} "
              f"{row.get('cart', 0):>12,} "
              f"{row.get('fav', 0):>12,} "
              f"{row.get('buy', 0):>12,}")

    return daily_stats, hourly_stats


def user_behavior_analysis(df):
    """用户行为深度分析"""
    print("\n" + "=" * 60)
    print("五、用户行为深度分析")
    print("=" * 60)

    # 每个用户的行为数统计
    user_behavior_count = df.groupBy("user_id").count()
    user_stats = user_behavior_count.agg(
        F.mean("count").alias("avg_behaviors"),
        F.stddev("count").alias("std_behaviors"),
        F.min("count").alias("min_behaviors"),
        F.max("count").alias("max_behaviors"),
        F.percentile_approx("count", [0.25, 0.5, 0.75, 0.9, 0.99]).alias("percentiles")
    ).collect()[0]

    print(f"\n用户行为数统计:")
    print(f"  平均行为数: {user_stats['avg_behaviors']:.2f}")
    print(f"  标准差: {user_stats['std_behaviors']:.2f}")
    print(f"  最少行为数: {user_stats['min_behaviors']}")
    print(f"  最多行为数: {user_stats['max_behaviors']:,}")

    pcts = user_stats["percentiles"]
    print(f"  25%分位数: {pcts[0]}")
    print(f"  50%分位数(中位数): {pcts[1]}")
    print(f"  75%分位数: {pcts[2]}")
    print(f"  90%分位数: {pcts[3]}")
    print(f"  99%分位数: {pcts[4]}")

    # 用户购买频次分析
    buy_df = df.filter(F.col("behavior_type") == "buy")
    buy_user_count = buy_df.select("user_id").distinct().count()
    buy_total = buy_df.count()
    avg_buy_per_user = buy_total / buy_user_count if buy_user_count > 0 else 0

    print(f"\n用户购买行为:")
    print(f"  购买用户数: {buy_user_count:,}")
    print(f"  总购买次数: {buy_total:,}")
    print(f"  人均购买次数: {avg_buy_per_user:.2f}")

    return user_stats


def top_items_analysis(df, top_n=20):
    """热门商品分析"""
    print("\n" + "=" * 60)
    print(f"六、热门商品 Top {top_n}")
    print("=" * 60)

    # 浏览量最高的商品
    top_pv_items = (
        df.filter(F.col("behavior_type") == "pv")
        .groupBy("item_id", "category_id")
        .count()
        .orderBy(F.col("count").desc())
        .limit(top_n)
    )

    print(f"\n--- 浏览量最高的商品 Top {top_n} ---")
    print(f"{'排名':<8} {'商品ID':>12} {'品类ID':>12} {'浏览量':>12}")
    print("-" * 50)
    for i, row in enumerate(top_pv_items.collect(), 1):
        print(f"{i:<8} {row['item_id']:>12} {row['category_id']:>12} {row['count']:>12,}")

    # 购买量最高的商品
    top_buy_items = (
        df.filter(F.col("behavior_type") == "buy")
        .groupBy("item_id", "category_id")
        .count()
        .orderBy(F.col("count").desc())
        .limit(top_n)
    )

    print(f"\n--- 购买量最高的商品 Top {top_n} ---")
    print(f"{'排名':<8} {'商品ID':>12} {'品类ID':>12} {'购买量':>12}")
    print("-" * 50)
    for i, row in enumerate(top_buy_items.collect(), 1):
        print(f"{i:<8} {row['item_id']:>12} {row['category_id']:>12} {row['count']:>12,}")

    return top_pv_items, top_buy_items


def top_categories_analysis(df, top_n=20):
    """热门品类分析"""
    print("\n" + "=" * 60)
    print(f"七、热门品类 Top {top_n}")
    print("=" * 60)

    # 各品类的行为分布
    category_stats = (
        df.groupBy("category_id")
        .pivot("behavior_type")
        .count()
        .na.fill(0)
    )

    # 按浏览量排序取Top N
    top_categories = category_stats.orderBy(F.col("pv").desc()).limit(top_n)

    print(f"\n{'排名':<6} {'品类ID':>12} {'PV':>12} {'Cart':>10} {'Fav':>10} {'Buy':>10} {'转化率':>10}")
    print("-" * 75)
    for i, row in enumerate(top_categories.collect(), 1):
        pv = row.get("pv", 0)
        buy = row.get("buy", 0)
        conversion = buy / pv * 100 if pv > 0 else 0
        print(f"{i:<6} {row['category_id']:>12} {pv:>12,} "
              f"{row.get('cart', 0):>10,} {row.get('fav', 0):>10,} "
              f"{buy:>10,} {conversion:>9.2f}%")

    return top_categories


def data_quality_check(df):
    """数据质量检查"""
    print("\n" + "=" * 60)
    print("八、数据质量检查")
    print("=" * 60)

    total = df.count()

    # 空值检查
    null_counts = df.select([
        F.count(F.when(F.col(c).isNull(), c)).alias(c)
        for c in ["user_id", "item_id", "category_id", "behavior_type", "timestamp"]
    ]).collect()[0]

    print(f"\n空值统计:")
    for col_name in ["user_id", "item_id", "category_id", "behavior_type", "timestamp"]:
        null_count = null_counts[col_name]
        pct = null_count / total * 100
        print(f"  {col_name}: {null_count:,} ({pct:.4f}%)")

    # 重复记录检查
    # 注意：完全重复的记录（同一用户同一商品同一行为同一时间）
    dup_count = total - df.dropDuplicates(["user_id", "item_id", "behavior_type", "timestamp"]).count()
    print(f"\n完全重复记录数: {dup_count:,} ({dup_count/total*100:.4f}%)")

    # 异常时间戳检查
    min_time = 1511539200  # 2017-11-25 00:00:00
    max_time = 1512316800  # 2017-12-04 00:00:00
    abnormal_time = df.filter(
        (F.col("timestamp") < min_time) | (F.col("timestamp") > max_time)
    ).count()
    print(f"异常时间戳记录数: {abnormal_time:,} ({abnormal_time/total*100:.4f}%)")

    # 异常行为类型
    valid_behaviors = ["pv", "buy", "cart", "fav"]
    invalid_behavior = df.filter(~F.col("behavior_type").isin(valid_behaviors)).count()
    print(f"无效行为类型记录数: {invalid_behavior:,} ({invalid_behavior/total*100:.4f}%)")

    return {
        "null_counts": null_counts,
        "dup_count": dup_count,
        "abnormal_time": abnormal_time,
        "invalid_behavior": invalid_behavior
    }


def save_summary(stats, output_path):
    """保存分析摘要到文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("淘宝用户行为数据探索分析报告\n")
        f.write("=" * 60 + "\n\n")

        f.write("一、基础统计信息\n")
        f.write("-" * 40 + "\n")
        f.write(f"总记录数: {stats['basic']['total_count']:,}\n")
        f.write(f"独立用户数: {stats['basic']['user_count']:,}\n")
        f.write(f"独立商品数: {stats['basic']['item_count']:,}\n")
        f.write(f"独立品类数: {stats['basic']['category_count']:,}\n")
        f.write(f"时间范围: {stats['basic']['min_time']} ~ {stats['basic']['max_time']}\n\n")

        f.write("二、转化漏斗\n")
        f.write("-" * 40 + "\n")
        f.write(f"浏览用户数: {stats['funnel']['pv_users']:,}\n")
        f.write(f"收藏用户数: {stats['funnel']['fav_users']:,}\n")
        f.write(f"加购用户数: {stats['funnel']['cart_users']:,}\n")
        f.write(f"购买用户数: {stats['funnel']['buy_users']:,}\n")
        f.write(f"整体购买转化率: {stats['funnel']['buy_users']/stats['funnel']['pv_users']*100:.2f}%\n\n")

        f.write("三、数据质量\n")
        f.write("-" * 40 + "\n")
        f.write(f"重复记录数: {stats['quality']['dup_count']:,}\n")
        f.write(f"异常时间戳: {stats['quality']['abnormal_time']:,}\n")
        f.write(f"无效行为类型: {stats['quality']['invalid_behavior']:,}\n")


def main():
    # 配置路径
    data_path = r"E:\ecom_ai\data\raw\taobao_behavior\UserBehavior.csv"
    output_dir = r"E:\ecom_ai\data\processed\taobao_behavior"
    os.makedirs(output_dir, exist_ok=True)

    start_time = time.time()
    print(f"[{datetime.now()}] 淘宝用户行为数据探索分析（PySpark版）开始")
    print(f"数据文件: {data_path}")

    # 创建 SparkSession
    spark = create_spark_session()
    print(f"Spark版本: {spark.version}")

    try:
        # 1. 加载数据
        df = load_data(spark, data_path)
        df.cache()  # 缓存数据加速后续操作

        # 2. 基础统计
        basic_stats_result = basic_stats(df)

        # 3. 行为类型分析
        behavior_counts = behavior_analysis(df)

        # 4. 转化漏斗
        funnel_result = conversion_funnel(df)

        # 5. 时间维度分析
        time_analysis(df)

        # 6. 用户行为分析
        user_behavior_analysis(df)

        # 7. 热门商品分析
        top_items_analysis(df, top_n=20)

        # 8. 热门品类分析
        top_categories_analysis(df, top_n=20)

        # 9. 数据质量检查
        quality_result = data_quality_check(df)

        # 保存摘要
        stats = {
            "basic": basic_stats_result,
            "funnel": funnel_result,
            "quality": quality_result
        }
        summary_path = os.path.join(output_dir, "eda_summary.txt")
        save_summary(stats, summary_path)
        print(f"\n分析摘要已保存至: {summary_path}")

    finally:
        # 停止 Spark
        spark.stop()

    elapsed = time.time() - start_time
    print(f"\n[{datetime.now()}] 分析完成，耗时: {elapsed:.2f}秒")


if __name__ == "__main__":
    main()
