# 评测（Evals V1）

本目录保存 sponsor-deal-check 的行为证据：题集、量表、运行协议、真实产物与逐题判断。

## 评测分层

1. **脚本行为层**：对 `evals/fixtures/` 的合成夹具运行 `scripts/reconcile_deal.py`
   （日期基准统一 `--as-of 2026-09-17`），逐条核对 [cases_v1.jsonl](cases_v1.jsonl) 的
   required/forbidden 原子检查。脚本为确定性比对，case b5 显式验证哈希一致。
2. **Agent 工作流层**：Agent 把 [agent_brief_v1.md](fixtures/agent_brief_v1.md)（合成 brief）
   转写为 [deal_synthetic_v1.json](fixtures/deal_synthetic_v1.json)，脚本可直接消费
   （case b6），按 [rubric_v1.md](rubric_v1.md) 三维度判定。

## 当前状态（2026-09-17，v0.1.1）

- 8/8 用例通过，0 硬失败；逐题判断见 [judgments_v1.jsonl](judgments_v1.jsonl)，
  汇总见 [summary_v1.json](summary_v1.json)。
- 两轮真实失败与修复见 [iteration_notes.md](iteration_notes.md)：单元测试抓到时长字段
  类型崩溃；人工检查报告发现"数量齐但有逾期/时长问题仍标 ✅"，状态机升级为
  OK/WARN/BLOCKED/PARTIAL/MISSING 五态并补回归用例。
- 夹具全部为合成样本（见 [fixtures/README.md](fixtures/README.md)），品牌、链接、金额均为虚构。
- 已知限制：判定为开发 Agent 自评（model_only），未独立人工复核；必提词为字面匹配、
  保留期按本地日期推算，边界见 iteration_notes.md。

## 复现

命令与参数见 [docs/usage.md](../docs/usage.md)；脚本层全程离线，无需任何 API 密钥。
