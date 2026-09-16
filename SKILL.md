---
name: sponsor-deal-check
description: 把创作者或 MCN 自己的商单合同要点与实际发布记录做本地比对，输出缺失交付、逾期、必提词缺失、保留期倒计时和结款节点状态的对账报告；只做文本与日期比对，不访问平台、不验证链接真实性，用于验收与结案前自查。
---

# 商单交付对账

当用户要"对一下商单交付""这单能不能收尾款""结案材料齐不齐"时使用本 Skill。
交付物是一份状态诚实、逐条可核的对账报告，不是流量数据面板。

## 工作边界

- 只处理用户自备的合同要点与发布记录，全部本地比对，不需要任何平台授权或 API。
- 脚本只做文本与日期比对：链接是否真实可访问、平台数据是否达标，必须建议用户人工复核，
  不得替平台下"已验收"结论。
- 合同原文可能含敏感商务条款：转写只保留对账必需字段；提醒用户不要公开 deal.json 与
  delivery.csv 原件。
- 本工具不做税务、法律判断；违约金、罚款等条款影响请建议咨询专业人士。

## 默认流程

1. **转写合同**：把用户的合同要点（邮件、聊天记录、brief 文本）按
   [references/deal-schema.md](references/deal-schema.md) 转写为 deal.json——
   逐项对应交付物、必提词、保留期、结款节点，不虚构、不遗漏；转写结果给用户确认。
2. **整理交付记录**：请用户提供发布记录 CSV（列定义见 deal-schema.md）；
   没有记录时可以先跑空表看整体缺口。
3. **运行对账**：`python3 scripts/reconcile_deal.py deal.json delivery.csv -o 对账报告.md --json 汇总.json --as-of 基准日`。
   评测与复现时固定 --as-of 保证结果可复现；参数与退出码见 [docs/usage.md](docs/usage.md)。
4. **解释缺口**：逐条说明每个缺口的验收影响与补救动作（例如：必提词缺失属阻塞项，
   补发文案或与品牌方协商修改；WARN 项不阻塞结款但需说明）。
5. **结案自查**：报告末尾附结案材料清单；逐条打开链接人工复核后再发送品牌方。

## 状态口径

交付物状态：✅ OK（数量齐且合规）/ ⚠️ WARN（数量齐但有逾期、时长不足、低于保留期）/
⛔ BLOCKED（数量齐但必提词缺失等验收阻塞项）/ ⚠️ PARTIAL（交付不足额）/ ❌ MISSING（未交付）。
结款条件 `delivered_all` 要求全部交付物处于 OK/WARN。

支持文件：

- [references/deal-schema.md](references/deal-schema.md)：deal.json 与 delivery.csv 的字段定义和示例。
- [references/benchmarks.md](references/benchmarks.md)：与表格模板、SaaS 平台的定位对比。
- [docs/usage.md](docs/usage.md)：命令行参数、退出码与评测复现说明。
- [evals/README.md](evals/README.md)：评测证据入口。
