# deal.json 与 delivery.csv 字段定义

## deal.json

```json
{
  "deal": {
    "brand": "品牌名", "creator_alias": "达人代称", "fee": 20000,
    "currency": "CNY", "sign_date": "2026-08-01"
  },
  "deliverables": [
    {
      "id": "d1",
      "platform": "douyin",
      "type": "视频",
      "count": 1,
      "due_date": "2026-09-05",
      "must_mention": ["品牌名", "活动主题"],
      "min_duration_sec": 30,
      "retention_days": 30
    }
  ],
  "payment_milestones": [
    {"id": "p1", "name": "预付 30%", "amount": 6000, "condition": "manual", "status": "received"},
    {"id": "p2", "name": "尾款 70%", "amount": 14000, "condition": "delivered_all"},
    {"id": "p3", "name": "保留期满释放", "amount": 0, "condition": "retention_confirmed"}
  ]
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| deliverables[].id / platform / type / count / due_date | 是 | 交付物五要素；due_date 为 ISO 日期 |
| deliverables[].must_mention | 否 | 必提词列表；按字面子串检查文案 |
| deliverables[].min_duration_sec | 否 | 视频最短秒数 |
| deliverables[].retention_days | 否 | 约定保留天数；按发布日 + N 与基准日比较 |
| payment_milestones[].condition | 是 | `manual` / `delivered_all` / `retention_confirmed` |
| payment_milestones[].status | 否 | 已收到的节点填 `received` |

## delivery.csv

| 列 | 必填 | 说明 |
| --- | --- | --- |
| post_id | 是 | 本地记录 ID |
| deliverable_id | 建议 | 对应交付物 id；缺省时按 platform+type 唯一匹配 |
| platform / type | 是 | 与 deal.json 中的写法保持一致 |
| published_at | 是 | ISO 日期 |
| url | 否 | 发布链接（只展示，不做真伪验证） |
| caption | 否 | 文案；必提词检查对象 |
| duration_sec | 否 | 视频时长秒数 |

隐私提醒：两个字段表都可能含商务敏感信息（报价、条款），请勿公开原件。
