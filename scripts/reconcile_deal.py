#!/usr/bin/env python3
"""把商单合同要求与实际交付记录做本地比对，输出缺口对账报告。

输入：
  deal.json     合同要点（交付物、必提词、保留期、结款节点）
  delivery.csv  实际发布记录（post_id, deliverable_id, platform, type,
                published_at, url, caption, duration_sec）
输出：
  Markdown 对账报告（-o）与结构化 JSON（--json）。

只做文本与日期比对，不访问平台验证链接真实性；链接需人工复核。
日期比较基于 --as-of 指定的基准日（默认今天）。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

VERSION = "0.1.1"

DELIVERY_COLUMNS = ["post_id", "deliverable_id", "platform", "type", "published_at", "url", "caption", "duration_sec"]
CLOSEOUT_CHECKLIST = [
    "发布链接清单（对账报告已自动生成，见各交付物明细）",
    "发布后 7 天数据截图（播放/阅读、互动）",
    "品牌方确认验收的聊天或邮件记录",
    "结案说明（合作执行情况与数据总结）",
]


class SchemaError(ValueError):
    pass


def parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"日期字段 {field} 无法解析：{value!r}（需要 ISO 格式 YYYY-MM-DD）") from exc


def parse_int(value, field: str, default=None) -> int | None:
    if value in (None, ""):
        if default is None:
            return None
        return default
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"数字字段 {field} 无法解析：{value!r}") from exc


def load_deal(path: Path) -> dict:
    try:
        deal = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"deal.json 不是合法 JSON：{exc.msg}（第 {exc.lineno} 行）") from exc
    if not deal.get("deliverables"):
        raise SchemaError("deal.json 缺少 deliverables（交付物清单）")
    for item in deal["deliverables"]:
        for field in ("id", "platform", "type", "count", "due_date"):
            if item.get(field) in (None, ""):
                raise SchemaError(f"交付物 {item.get('id', '?')} 缺少字段 {field}")
        parse_date(item["due_date"], f"{item['id']}.due_date")
        item["count"] = parse_int(item["count"], f"{item['id']}.count")
        if item["count"] is None or item["count"] < 1:
            raise SchemaError(f"交付物 {item['id']} 的 count 必须 ≥1")
        item.setdefault("must_mention", [])
        item.setdefault("retention_days", None)
        item.setdefault("min_duration_sec", None)
    return deal


def load_delivery(path: Path) -> list[dict]:
    posts: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise SchemaError("delivery.csv 是空表：缺少表头")
        missing = [col for col in ("post_id", "platform", "type", "published_at") if col not in reader.fieldnames]
        if missing:
            raise SchemaError("delivery.csv 缺少必需列：" + "、".join(missing))
        for row in reader:
            if not any((value or "").strip() for value in row.values()):
                continue
            row["published_at"] = parse_date(row.get("published_at"), "published_at").isoformat()
            row["duration_sec"] = parse_int(row.get("duration_sec"), "duration_sec")
            posts.append(row)
    return posts


def match_posts(deliverables: list[dict], posts: list[dict]) -> tuple[dict[str, list[dict]], list[dict]]:
    matched: dict[str, list[dict]] = {item["id"]: [] for item in deliverables}
    unmatched: list[dict] = []
    for post in posts:
        target = (post.get("deliverable_id") or "").strip()
        if target and target in matched:
            matched[target].append(post)
            continue
        candidates = [
            item for item in deliverables
            if item["platform"] == (post.get("platform") or "").strip()
            and item["type"] == (post.get("type") or "").strip()
        ]
        if len(candidates) == 1:
            matched[candidates[0]["id"]].append(post)
        else:
            unmatched.append(post)
    return matched, unmatched


def check_deliverable(item: dict, posts: list[dict], as_of: date) -> dict:
    issues: list[dict] = []
    required = item["count"]
    delivered = len(posts)
    blocking = False
    if delivered >= required:
        status = "OK"  # 后续按问题降级：BLOCKED / WARN
    else:
        status = "PARTIAL" if delivered else "MISSING"
        blocking = True

    due = parse_date(item["due_date"], f"{item['id']}.due_date")
    for post in posts:
        published = parse_date(post["published_at"], "published_at")
        if published > due:
            issues.append({"kind": "逾期", "post": post["post_id"], "detail": f"发布 {published} 晚于约定 {due}"})

    for phrase in item["must_mention"]:
        if not any(phrase in (post.get("caption") or "") for post in posts):
            issues.append({"kind": "必提词缺失", "post": "-", "detail": f"「{phrase}」未出现在任何已发布文案", "blocking": True})
            blocking = True

    if item["min_duration_sec"] is not None:
        for post in posts:
            duration = post.get("duration_sec")
            try:
                duration = int(str(duration)) if duration not in (None, "") else None
            except (TypeError, ValueError):
                duration = None
            if duration is not None and duration < item["min_duration_sec"]:
                issues.append({"kind": "时长不足", "post": post["post_id"],
                               "detail": f"{duration}s < 约定 {item['min_duration_sec']}s"})

    retention_notes: list[dict] = []
    if item["retention_days"]:
        for post in posts:
            published = parse_date(post["published_at"], "published_at")
            expire = published + timedelta(days=int(item["retention_days"]))
            remaining = (expire - as_of).days
            retention_notes.append({
                "post": post["post_id"], "expire": expire.isoformat(), "remaining_days": remaining,
                "state": "保留中" if remaining >= 0 else "已低于约定保留期",
            })
            if remaining < 0:
                issues.append({"kind": "保留期", "post": post["post_id"],
                               "detail": f"保留期已于 {expire.isoformat()} 结束"})

    if delivered >= required:
        if blocking:
            status = "BLOCKED"  # 数量齐但存在必提词缺失等验收阻塞项
        elif issues:
            status = "WARN"     # 数量齐但存在逾期/时长不足/低于保留期

    return {
        "id": item["id"], "platform": item["platform"], "type": item["type"],
        "required": required, "delivered": delivered, "status": status,
        "due_date": due.isoformat(), "issues": issues, "retention": retention_notes,
        "posts": [post.get("url") or post.get("post_id") for post in posts],
    }


def check_milestones(deal: dict, checks: list[dict], as_of: date) -> list[dict]:
    # 结款条件 delivered_all：数量齐且无验收阻塞项（WARN 类问题不阻塞，但会在报告中明示）
    all_delivered = all(check["status"] in ("OK", "WARN") for check in checks)
    all_retained = all(
        note["remaining_days"] >= 0
        for check in checks for note in check["retention"]
    ) if any(check["retention"] for check in checks) else None
    results = []
    for milestone in deal.get("payment_milestones", []):
        condition = milestone.get("condition", "manual")
        if milestone.get("status") == "received":
            state = "已收到"
        elif condition == "delivered_all":
            state = "达成·可申请" if all_delivered else "未达成（存在缺失交付）"
        elif condition == "retention_confirmed":
            if all_retained is None:
                state = "需人工确认（合同未约定保留期）"
            else:
                state = "达成·可申请" if all_retained else "未达成（存在低于保留期的内容）"
        else:
            state = "需人工确认"
        results.append({
            "id": milestone.get("id", "-"), "name": milestone.get("name", "-"),
            "amount": milestone.get("amount"), "condition": condition, "state": state,
        })
    return results


def build_report(deal: dict, checks: list[dict], unmatched: list[dict],
                 milestones: list[dict], as_of: date) -> str:
    brand = deal.get("deal", {}).get("brand", "未命名品牌")
    lines = [
        "# 商单交付对账报告",
        "",
        f"品牌：{brand} ｜ 基准日：{as_of.isoformat()} ｜ 交付物 {len(checks)} 项，"
        f"已发布记录 {sum(check['delivered'] for check in checks)} 条",
        "",
        "## 交付对账",
        "",
    ]
    for check in checks:
        mark = {"OK": "✅", "WARN": "⚠️", "BLOCKED": "⛔", "PARTIAL": "⚠️", "MISSING": "❌"}[check["status"]]
        lines.append(f"### {mark} {check['id']}｜{check['platform']}·{check['type']}"
                     f"｜已交付 {check['delivered']}/{check['required']}｜约定期 {check['due_date']}")
        lines.append("")
        if check["status"] != "OK":
            lines.append(f"- 交付缺口：{'缺少 ' + str(check['required'] - check['delivered']) + ' 条' if check['delivered'] else '完全未交付'}")
        if not check["issues"] and check["status"] == "OK":
            lines.append("- 必提词、时长、时限均符合约定。")
        for issue in check["issues"]:
            lines.append(f"- [{issue['kind']}] {issue['post']}：{issue['detail']}")
        for note in check["retention"]:
            lines.append(f"- [保留期] {note['post']}：{note['state']}"
                         f"（截止 {note['expire']}，剩余 {note['remaining_days']} 天）")
        if check["posts"]:
            lines.append("- 发布链接：" + "；".join(check["posts"]))
        lines.append("")

    if unmatched:
        lines += ["## 未匹配的发布记录", ""]
        for post in unmatched:
            lines.append(f"- {post.get('post_id')}｜{post.get('platform')}·{post.get('type')}"
                         f"｜发布 {post.get('published_at')}——无法对应到合同交付物，请核对 deliverable_id")
        lines.append("")

    lines += ["## 结款节点", ""]
    if milestones:
        for milestone in milestones:
            amount = f"（{milestone['amount']}）" if milestone.get("amount") else ""
            lines.append(f"- {milestone['name']}{amount}：{milestone['state']}（条件 {milestone['condition']}）")
    else:
        lines.append("- 合同未登记结款节点。")
    lines.append("")

    lines += ["## 结案报告清单", ""]
    for entry in CLOSEOUT_CHECKLIST:
        lines.append(f"- [ ] {entry}")
    lines += [
        "",
        "## 边界说明",
        "",
        "- 本报告只对本地记录做文本与日期比对；链接真实性与平台数据以人工复核为准，",
        "  建议在发送结案材料前逐条打开链接确认。",
        f"- 版本 {VERSION}。输入文件含商务信息，请勿把 deal.json 与 delivery.csv 原件公开分享。",
    ]
    return "\n".join(lines) + "\n"


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deal", type=Path, help="合同要点 deal.json")
    parser.add_argument("delivery", type=Path, help="发布记录 delivery.csv")
    parser.add_argument("-o", "--output", type=Path, help="Markdown 报告输出路径")
    parser.add_argument("--json", type=Path, help="结构化 JSON 输出路径")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(),
                        help="日期基准日（ISO 格式），默认今天")
    args = parser.parse_args(argv)

    for path in (args.deal, args.delivery):
        if not path.is_file():
            print(f"输入文件不存在：{path}", file=sys.stderr)
            return 2
    try:
        deal = load_deal(args.deal)
        posts = load_delivery(args.delivery)
    except SchemaError as exc:
        print(f"输入格式错误：{exc}", file=sys.stderr)
        return 3

    matched, unmatched = match_posts(deal["deliverables"], posts)
    checks = [check_deliverable(item, matched[item["id"]], args.as_of) for item in deal["deliverables"]]
    milestones = check_milestones(deal, checks, args.as_of)
    report = build_report(deal, checks, unmatched, milestones, args.as_of)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    if args.json:
        payload = {
            "version": VERSION,
            "as_of": args.as_of.isoformat(),
            "deliverables": [{key: check[key] for key in ("id", "status", "required", "delivered", "issues")}
                             for check in checks],
            "unmatched_posts": [post.get("post_id") for post in unmatched],
            "milestones": milestones,
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
