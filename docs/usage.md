# 使用与维护文档

## 命令

```bash
python3 scripts/reconcile_deal.py deal.json delivery.csv -o report.md --json summary.json --as-of 2026-09-17
```

## 参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `deal`（位置参数） | 必填 | 合同要点 deal.json，字段见 references/deal-schema.md |
| `delivery`（位置参数） | 必填 | 发布记录 delivery.csv |
| `-o, --output` | 打印到 stdout | Markdown 对账报告输出路径 |
| `--json` | 不输出 | 结构化 JSON（各交付物状态与问题列表） |
| `--as-of` | 今天 | 日期基准日（ISO 格式）；评测与复现时固定该值 |

## 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 成功 |
| 2 | 输入文件不存在 |
| 3 | 输入格式错误（非法 JSON、缺列、坏日期等，stderr 给中文原因） |

## 状态机

| 状态 | 含义 | 对 delivered_all 结款条件 |
| --- | --- | --- |
| ✅ OK | 数量齐且无任何问题 | 不阻塞 |
| ⚠️ WARN | 数量齐，但有逾期/时长不足/低于保留期 | 不阻塞（报告中明示） |
| ⛔ BLOCKED | 数量齐，但必提词缺失等验收阻塞项 | 阻塞 |
| ⚠️ PARTIAL | 交付不足额 | 阻塞 |
| ❌ MISSING | 零交付 | 阻塞 |

## 测试与评测

```bash
python3 -m unittest discover tests     # 14 项单元测试
python3 scripts/reconcile_deal.py evals/fixtures/deal_synthetic_v1.json \
    evals/fixtures/delivery_hard_v1.csv -o /tmp/h.md --as-of 2026-09-17
```

完整评测流程见 [evals/README.md](../evals/README.md)。
