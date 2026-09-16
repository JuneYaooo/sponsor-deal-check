"""reconcile_deal.py 的单元测试：python3 -m unittest discover tests"""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import reconcile_deal as rd

AS_OF = date(2026, 9, 17)


def write(tmp_name: str, content: str, suffix: str) -> Path:
    tmp = Path(tempfile.mkdtemp())
    path = tmp / f"{tmp_name}{suffix}"
    path.write_text(content, encoding="utf-8")
    return path


DEAL_JSON = {
    "deal": {"brand": "测试品牌"},
    "deliverables": [
        {"id": "d1", "platform": "douyin", "type": "视频", "count": 1, "due_date": "2026-09-05",
         "must_mention": ["测试品牌"], "min_duration_sec": 30, "retention_days": 10},
    ],
    "payment_milestones": [{"id": "p2", "name": "尾款", "amount": 100, "condition": "delivered_all"}],
}


def make_post(**kwargs):
    base = {"post_id": "p1", "deliverable_id": "d1", "platform": "douyin", "type": "视频",
            "published_at": "2026-09-01", "url": "https://example.com/1",
            "caption": "测试品牌真好用", "duration_sec": "40"}
    base.update(kwargs)
    return base


class LoadTests(unittest.TestCase):
    def test_bad_json(self):
        path = write("deal", "{not json", ".json")
        with self.assertRaises(rd.SchemaError):
            rd.load_deal(path)

    def test_missing_deliverables(self):
        path = write("deal", json.dumps({"deal": {}}), ".json")
        with self.assertRaises(rd.SchemaError):
            rd.load_deal(path)

    def test_bad_date(self):
        deal = json.loads(json.dumps(DEAL_JSON))
        deal["deliverables"][0]["due_date"] = "09-05"
        path = write("deal", json.dumps(deal, ensure_ascii=False), ".json")
        with self.assertRaises(rd.SchemaError):
            rd.load_deal(path)

    def test_csv_missing_columns(self):
        path = write("d", "post_id,platform\n", ".csv")
        with self.assertRaises(rd.SchemaError):
            rd.load_delivery(path)


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.item = DEAL_JSON["deliverables"][0]

    def test_all_ok(self):
        # 发布于约定期内、保留 30 天（到 10-01，基准日 9-17 仍有效）
        item = {**self.item, "retention_days": 30}
        result = rd.check_deliverable(item, [make_post()], AS_OF)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["issues"], [])

    def test_warn_when_delivered_but_flawed(self):
        # 数量齐但逾期+时长不足 → 状态应降级为 WARN，而不是 ✅
        result = rd.check_deliverable(self.item, [make_post(published_at="2026-09-06", duration_sec="18")], AS_OF)
        self.assertEqual(result["status"], "WARN")
        kinds = {issue["kind"] for issue in result["issues"]}
        self.assertIn("逾期", kinds)
        self.assertIn("时长不足", kinds)

    def test_missing_delivery(self):
        result = rd.check_deliverable(self.item, [], AS_OF)
        self.assertEqual(result["status"], "MISSING")

    def test_overdue(self):
        result = rd.check_deliverable(self.item, [make_post(published_at="2026-09-06")], AS_OF)
        self.assertTrue(any(issue["kind"] == "逾期" for issue in result["issues"]))

    def test_missing_mention(self):
        result = rd.check_deliverable(self.item, [make_post(caption="没提品牌")], AS_OF)
        self.assertTrue(any(issue["kind"] == "必提词缺失" for issue in result["issues"]))

    def test_short_duration(self):
        result = rd.check_deliverable(self.item, [make_post(duration_sec="18")], AS_OF)
        self.assertTrue(any(issue["kind"] == "时长不足" for issue in result["issues"]))

    def test_retention_expired(self):
        result = rd.check_deliverable(self.item, [make_post(published_at="2026-09-01")], AS_OF)
        # 保留 10 天，9 月 11 日到期，基准日 9 月 17 日 → 已低于保留期
        self.assertTrue(any(issue["kind"] == "保留期" for issue in result["issues"]))


class MilestoneTests(unittest.TestCase):
    def test_delivered_all_gate(self):
        good = rd.check_deliverable(DEAL_JSON["deliverables"][0], [make_post()], AS_OF)
        results = rd.check_milestones(DEAL_JSON, [good], AS_OF)
        self.assertEqual(results[0]["state"], "达成·可申请")
        bad = rd.check_deliverable(DEAL_JSON["deliverables"][0], [], AS_OF)
        results = rd.check_milestones(DEAL_JSON, [bad], AS_OF)
        self.assertEqual(results[0]["state"], "未达成（存在缺失交付）")


class MatchTests(unittest.TestCase):
    def test_match_by_platform_type(self):
        deliverables = DEAL_JSON["deliverables"]
        posts = [{**make_post(), "deliverable_id": ""}]
        matched, unmatched = rd.match_posts(deliverables, posts)
        self.assertEqual(len(matched["d1"]), 1)
        self.assertEqual(unmatched, [])

    def test_unmatched_post(self):
        posts = [{**make_post(), "platform": "weibo", "deliverable_id": ""}]
        matched, unmatched = rd.match_posts(DEAL_JSON["deliverables"], posts)
        self.assertEqual(len(unmatched), 1)


class RunTests(unittest.TestCase):
    def test_end_to_end_and_exit_codes(self):
        deal = write("deal", json.dumps(DEAL_JSON, ensure_ascii=False), ".json")
        empty = write("d", "post_id,platform\n", ".csv")
        missing = deal.parent / "missing.json"  # 不创建，验证文件不存在 → 2
        self.assertEqual(rd.run([str(missing), str(empty)]), 2)
        self.assertEqual(rd.run([str(deal), str(empty)]), 3)  # 表头缺列 → 3
        out = deal.parent / "r.md"
        good_csv = write("d", "post_id,deliverable_id,platform,type,published_at,url,caption,duration_sec\n"
                             "p1,d1,douyin,视频,2026-09-01,https://example.com/1,测试品牌真好用,40\n", ".csv")
        self.assertEqual(rd.run([str(deal), str(good_csv), "-o", str(out)]), 0)
        self.assertIn("商单交付对账报告", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
