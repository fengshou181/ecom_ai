# -*- coding: utf-8 -*-
"""命令行问答入口 + 5 库基准验证"""
import sys
import io
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from sql_chain import ask

BENCHMARK = [
    "olist 数据集的 GMV 总额是多少？",
    "amazon 评论的 5 星占比是多少？",
    "instacart 订单总数大约多少？",
    "淘宝 PV 到购买的转化率是多少？",
    "product_samples 里有多少条商品样本？",
]


def chat():
    print("电商数据问答 (输入 exit 退出)")
    while True:
        q = input("\n问> ").strip()
        if q.lower() in ("exit", "quit", ""):
            break
        r = ask(q)
        if r["error"]:
            print("出错:", r["error"])
            continue
        print("SQL:", r["sql"])
        print("答:", r["answer"])


def benchmark():
    t0 = time.time()
    ok = 0
    for q in BENCHMARK:
        t1 = time.time()
        r = ask(q)
        dt = time.time() - t1
        ok += 1 if (r["answer"] and not r["error"]) else 0
        print(f"[{dt:.1f}s] {q}\n  SQL: {r['sql']}\n  答: {r['answer'][:150]}\n  错: {r['error']}\n")
    print(f"基准结果: {ok}/{len(BENCHMARK)} 成功, 总耗时 {time.time() - t0:.1f}s")


if __name__ == "__main__":
    benchmark() if "--bench" in sys.argv else chat()
