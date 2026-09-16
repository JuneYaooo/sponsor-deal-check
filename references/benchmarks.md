# 对标：同类工具与本项目定位（2026-09-17 调研）

调研方法：公开网页搜索与产品主页阅读；引用版权归原作者所有，仅作定位说明。

## 需求证据

- MCN 机构用飞书多维表格自建商单管理系统："使用多维表格搭建商单管理系统，不同角色权限划分清晰，
  商务人员可同时协作"（[飞书 MCN 案例](https://www.feishu.cn/content/feishu-aiding-mcn-future-digital-HQ)）——
  每家都在重复搭表，说明通用模板解决不了"按单核对"。
- 品牌方流程文档要求达人提交结案报告后才能结款
  （例：[携程 MCN 合作流程](https://file.c-ctrip.com/files/6/portal/0AS3g12000a97dyns3371.pdf)），
  材料漏项直接拖慢回款。
- 海外同类品类已验证：[Sponsorship Manager](https://sponsorshipmanager.com/)、
  [CreatorsJet](https://www.creatorsjet.com/brand-deals-tracker)、
  [Notion 品牌合作模板](https://www.notion.com/templates/brand-deal-tracker-for-creators)
  均把 deliverables + deadlines + payments 当核心功能。

## 现有方案与差距

| 方案 | 定位 | 与本项目的差异 |
| --- | --- | --- |
| 飞书/Notion/Sheets 模板 | 人工记录状态 | 只记录不比对：合同要求与实际发布的差距仍靠人翻 |
| Sponsorship Manager 等 SaaS | 商单流水线管理 | 订阅制、数据上传第三方；本项目本地比对，零上传 |
| 结案报告代做服务 | 人工整理材料 | 按单计费；本项目确定性脚本，秒级出报告可反复跑 |

## 本项目立场

- 本地比对：合同与发布记录不出本机，不上传任何第三方。
- 状态诚实：WARN/BLOCKED 与 OK 分开，不粉饰缺口。
- 不越权：只做文本与日期比对，链接真伪与平台数据留给人工复核。
