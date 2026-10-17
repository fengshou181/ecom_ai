# -*- coding: utf-8 -*-
"""RAG 评测脚本：跑 cases.yaml，输出执行成功率/结果准确率/P50/P95 延迟/平均重试次数，并生成 Markdown 报告。

用法：
  conda run -n pds python rag/evals/run_eval.py            # 全量 30 条
  conda run -n pds python rag/evals/run_eval.py --smoke    # 每库第一条，共 5 条（冒烟）
"""
import sys
import io
import time
import statistics
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RAG_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAG_DIR))

import yaml
from sql_chain import ask

TARGETS = {"exec_success": 0.90, "accuracy": 0.75, "p50_s": 15.0, "p95_s": 40.0, "avg_retries": 0.5}


def check_case(case, r):
    """返回 (exec_ok, correct, actual)。correct 为 None 表示该题无期望值不参与准确率。"""
    df = r["dataframe"]
    exec_ok = (not r["error"]) and df is not None and len(df) > 0
    if not exec_ok:
        return False, False if (case.get("expected_value") is not None or case.get("expected_text")) else None, r["error"] or "空结果"
    row0 = df.iloc[0].tolist()
    actual = str(row0[0])
    if case.get("expected_text"):
        want = str(case["expected_text"]).lower()
        return True, want in str(row0[0]).lower(), actual
    if case.get("expected_value") is not None:
        try:
            got = float(row0[-1])
        except (TypeError, ValueError):
            return True, False, str(row0[-1])
        want = float(case["expected_value"])
        tol = float(case.get("tolerance", 0.01))
        ok = abs(got - want) <= max(abs(want) * tol, 1e-9)
        return True, ok, str(got)
    return True, None, actual


def percentile(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    k = max(0, min(len(sorted_vals) - 1, round(p * len(sorted_vals) + 0.5) - 1))
    return sorted_vals[k]


def main():
    cases = yaml.safe_load((RAG_DIR / "evals" / "cases.yaml").read_text(encoding="utf-8"))
    if "--smoke" in sys.argv:
        seen, picked = set(), []
        for c in cases:
            if c["db"] not in seen:
                seen.add(c["db"])
                picked.append(c)
        cases = picked

    records = []
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        try:
            r = ask(c["question"])
        except Exception as e:
            r = {"answer": "", "sql": "", "dataframe": None, "error": f"未捕获异常: {e}", "attempts": 0}
        dt = time.time() - t0
        exec_ok, correct, actual = check_case(c, r)
        records.append({
            "case": c, "exec_ok": exec_ok, "correct": correct, "actual": actual,
            "elapsed": dt, "attempts": r.get("attempts", 0), "sql": r.get("sql", ""), "error": r.get("error", ""),
        })
        mark = "✓" if (exec_ok and correct is not False) else "✗"
        print(f"[{i}/{len(cases)}] {mark} {c['id']} ({dt:.1f}s, 尝试{r.get('attempts', 0)}次) 实际={actual[:60]}")

    n = len(records)
    exec_oks = [r for r in records if r["exec_ok"]]
    judged = [r for r in records if r["correct"] is not None]
    corrects = [r for r in judged if r["correct"]]
    lat = sorted(r["elapsed"] for r in records)
    retries = [max(0, r["attempts"] - 1) for r in records]

    m_exec = len(exec_oks) / n
    m_acc = len(corrects) / len(judged) if judged else 0.0
    m_p50 = percentile(lat, 0.50)
    m_p95 = percentile(lat, 0.95)
    m_retry = sum(retries) / n

    def mark(val, target, higher_better=True):
        ok = val >= target if higher_better else val <= target
        return "✅" if ok else "❌"

    summary = [
        f"执行成功率: {len(exec_oks)}/{n} = {m_exec:.1%} {mark(m_exec, TARGETS['exec_success'])}（目标≥{TARGETS['exec_success']:.0%}）",
        f"结果准确率: {len(corrects)}/{len(judged)} = {m_acc:.1%} {mark(m_acc, TARGETS['accuracy'])}（目标≥{TARGETS['accuracy']:.0%}）",
        f"P50 延迟: {m_p50:.1f}s {mark(m_p50, TARGETS['p50_s'], False)}（目标≤{TARGETS['p50_s']:.0f}s）",
        f"P95 延迟: {m_p95:.1f}s {mark(m_p95, TARGETS['p95_s'], False)}（目标≤{TARGETS['p95_s']:.0f}s）",
        f"平均重试次数: {m_retry:.2f} {mark(m_retry, TARGETS['avg_retries'], False)}（目标≤{TARGETS['avg_retries']}）",
    ]
    print("\n".join(["", "===== 指标汇总 ====="] + summary))

    # Markdown 报告
    out_dir = RAG_DIR.parent / "docs" / "benchmark"
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# RAG 评测报告（{today}）",
        "",
        f"- 用例数：{n}（rag/evals/cases.yaml）",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 配置：{__import__('config').OLLAMA_MODEL} / top_k={__import__('config').RETRIEVE_TOP_K}",
        "",
        "## 指标汇总",
        "",
        "| 指标 | 结果 | 目标 | 达标 |",
        "|------|------|------|------|",
        f"| 执行成功率 | {m_exec:.1%}（{len(exec_oks)}/{n}） | ≥{TARGETS['exec_success']:.0%} | {mark(m_exec, TARGETS['exec_success'])} |",
        f"| 结果准确率 | {m_acc:.1%}（{len(corrects)}/{len(judged)}） | ≥{TARGETS['accuracy']:.0%} | {mark(m_acc, TARGETS['accuracy'])} |",
        f"| P50 延迟 | {m_p50:.1f}s | ≤{TARGETS['p50_s']:.0f}s | {mark(m_p50, TARGETS['p50_s'], False)} |",
        f"| P95 延迟 | {m_p95:.1f}s | ≤{TARGETS['p95_s']:.0f}s | {mark(m_p95, TARGETS['p95_s'], False)} |",
        f"| 平均重试次数 | {m_retry:.2f} | ≤{TARGETS['avg_retries']} | {mark(m_retry, TARGETS['avg_retries'], False)} |",
        "",
        "## 用例明细",
        "",
        "| 用例 | 库 | 执行 | 正确 | 耗时 | 重试 | 实际值 |",
        "|------|----|------|------|------|------|--------|",
    ]
    for r in records:
        c = r["case"]
        e = "✓" if r["exec_ok"] else "✗"
        k = "—" if r["correct"] is None else ("✓" if r["correct"] else "✗")
        lines.append(f"| {c['id']} | {c['db']} | {e} | {k} | {r['elapsed']:.1f}s | {max(0, r['attempts']-1)} | {r['actual'][:40]} |")
    fails = [r for r in records if (not r["exec_ok"]) or r["correct"] is False]
    if fails:
        lines += ["", "## 失败用例明细", ""]
        for r in fails:
            c = r["case"]
            expect = c.get("expected_text", c.get("expected_value", "—"))
            lines += [
                f"### {c['id']}",
                f"- 问题：{c['question']}",
                f"- 期望：{expect}，实际：{r['actual'][:200]}",
                f"- 生成 SQL：`{r['sql'][:300]}`",
                f"- 错误：{r['error'][:300] or '（执行成功但结果不符）'}",
                "",
            ]
    report = out_dir / f"{today}{'-smoke' if '--smoke' in sys.argv else ''}.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告已写入 {report}")


if __name__ == "__main__":
    main()
