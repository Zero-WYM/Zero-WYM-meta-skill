#!/usr/bin/env python3
"""Zero-WYM-meta-skill · 三桶触发评测（零依赖，启发式）

从 SKILL.md 的 description 引号短语提取"触发指纹"词袋，对每个用例文本做
子串/分词重叠判定：重叠 >=1 实义词 => 预测触发；否则不触发。对照桶标签计分。

重要（诚实边界）：这是关键词/短语命中的启发式代理指标，验证 description 对
用例文本的覆盖，**不等于模型真实路由力**。报告与 stdout 均强制打印免责声明。
退出码 0 = pass_rate==1，否则 1。
"""
import argparse
import os
import sys
import json
import re

STOP = set(
    "的 了 我 你 他 她 它 这 那 一 一个 些 个 把 被 让 请 帮 想 要 看 着 上 下 中 "
    "和 与 或 在 到 去 来 怎么 如何 什么 为何 吗 呢 吧 啊 哦 是 有 没有 就 也 都 "
    "还 不 别 该 哪个 一下 这个 那个 我们 你们 他们 可以 需要 希望 帮我 给我 "
    "你的 我的 一个 进行 使用 通过 实现 提供 用于 基于 针对".split()
)
STOP.add("skill")  # 太泛，无区分度，停用


def tokens(s):
    toks = re.findall(r"[A-Za-z][A-Za-z0-9+#]*", s)
    toks += re.findall(r"[一-鿿]{2,}", s)
    out = []
    for t in toks:
        t = t.lower()
        if t in STOP:
            continue
        if len(t) == 1:
            continue
        out.append(t)
    return out


def extract_trigger_phrases(desc):
    # 抓取 description 中被引号包裹的短语（英文/中文引号）
    quoted = re.findall(r"[\"“”「」]([^\"“”「」]{2,40})[\"“”「」]", desc)
    return quoted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=".")
    ap.add_argument("--cases", default="evals/trigger_cases.json")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    skill_md = os.path.join(a.skill_dir, "SKILL.md")
    text = open(skill_md, encoding="utf-8").read()
    m = re.search(r"description:\s*(.+)", text)
    desc = m.group(1).strip() if m else text

    phrases = extract_trigger_phrases(desc)
    bow = set()
    for ph in phrases:
        for t in tokens(ph):
            bow.add(t)

    cases_path = (a.cases if os.path.isabs(a.cases)
                  else os.path.join(a.skill_dir, a.cases))
    data = json.load(open(cases_path, encoding="utf-8"))
    cases = data.get("cases", [])

    results = []
    correct = 0
    for c in cases:
        bucket = c["bucket"]
        txt = c["text"]
        overlap = set(tokens(txt)) & bow
        predict_trigger = len(overlap) > 0
        expected_trigger = (bucket == "should_trigger")
        ok = (predict_trigger == expected_trigger)
        if ok:
            correct += 1
        results.append({
            "bucket": bucket,
            "text": txt,
            "overlap": sorted(overlap),
            "predict_trigger": predict_trigger,
            "expected_trigger": expected_trigger,
            "pass": ok,
        })

    total = len(cases)
    pass_rate = (correct / total) if total else 0.0
    disc = ("注意：本评测为关键词/短语命中的启发式代理指标，验证 description 对用例"
            "文本的覆盖，不等于模型真实路由力。")

    if a.json:
        print(json.dumps({"pass_rate": pass_rate, "correct": correct,
                          "total": total, "results": results,
                          "disclaimer": disc}, ensure_ascii=False, indent=2))
    else:
        print("=== 三桶触发评测 ===")
        for r in results:
            print("[%s] (%s) 预测触发=%s 期望=%s 重叠=%s"
                  % ("OK" if r["pass"] else "XX", r["bucket"],
                     r["predict_trigger"], r["expected_trigger"], r["overlap"]))
            print("     文本: %s" % r["text"])
        print("\npass_rate = %d/%d = %.0f%%" % (correct, total, pass_rate * 100))
        print("免责:", disc)

    sys.exit(0 if pass_rate == 1 else 1)


if __name__ == "__main__":
    main()
