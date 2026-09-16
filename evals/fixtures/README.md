# 夹具说明（fixtures）

除 agent_brief_v1.md 外，本目录所有文件均为**人工编写的合成样本（synthetic fixtures）**，
品牌名、链接、数据全部为虚构，仅用于评测，不对应任何真实商单或真实账号。

| 文件 | 用途 |
| --- | --- |
| deal_synthetic_v1.json | 合同要点样本；由 Agent 依 agent_brief_v1.md 转写生成 |
| delivery_full_v1.csv | 全部按约交付的正例 |
| delivery_hard_v1.csv | 缺交付、逾期、时长不足、必提词缺失、无法匹配记录的混合难例 |
| delivery_empty_v1.csv | 空记录边界例 |
