#!/usr/bin/env python3
"""ARCHIUM: collect Steam news into a review-only update of news.json.

Uses Python stdlib only. Does NOT publish, push, or make any GitHub API calls.
Any GitHub publishing requires a HUMAN to merge a PR created by the workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

APP_ID = 1643320
STEAM_API = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
VALID_HOSTS = {"store.steampowered.com", "steamcommunity.com", "www.stalker2.com", "stalker2.com", "www.gsc-game.com", "gsc-game.com"}
MAX_NEW = 5
MAX_AGE_DAYS = 14


class _Cleaner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "br", "div"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plaintext(value: str, size: int = 300) -> str:
    c = _Cleaner()
    c.feed(str(value or ""))
    return re.sub(r"\s+", " ", unescape("".join(c.parts))).strip()[:size]


def trusted_url(raw: str) -> str | None:
    try:
        p = urlsplit(str(raw))
        if p.scheme != "https" or p.hostname not in VALID_HOSTS or p.username or p.password:
            return None
        return str(raw)
    except ValueError:
        return None


def draft_title(original: str) -> str:
    # Only describe the type of publication; NEVER invent details or translate unverified facts.
    line = original.strip()
    low = line.lower()
    version = re.search(r"\b(?:patch|update|hotfix)\s*(v?\d+(?:\.\d+){0,3})\b", line, re.I)
    if version:
        return f"S.T.A.L.K.E.R. 2: сообщение об обновлении {version.group(1)}"
    if "patch" in low or "hotfix" in low:
        return "S.T.A.L.K.E.R. 2: опубликована информация об исправлениях"
    if "mod" in low or "zone kit" in low:
        return "S.T.A.L.K.E.R. 2: новости инструментов моддинга"
    if "expansion" in low or "dlc" in low or "cost of hope" in low:
        return "S.T.A.L.K.E.R. 2: новости дополнений"
    if "event" in low or "community" in low:
        return "S.T.A.L.K.E.R. 2: сообщение для сообщества"
    return "S.T.A.L.K.E.R. 2: новая публикация в Steam"


def read_api(payload: dict, now: datetime, days: int = MAX_AGE_DAYS) -> list[dict]:
    data = payload.get("appnews", {})
    if data.get("appid") not in (APP_ID, str(APP_ID)):
        raise ValueError("Ответ API относится не к приложению S.T.A.L.K.E.R. 2")
    items = data.get("newsitems", [])
    if not isinstance(items, list):
        raise ValueError("Некорректный список новостей Steam")
    existing = set()
    found = []
    for item in items:
        if not isinstance(item, dict):
            continue
        gid = str(item.get("gid", "")).strip()
        title = plaintext(item.get("title", ""), 180)
        url = trusted_url(str(item.get("url", "")))
        if not gid or not title or not url:
            continue
        try:
            timestamp = int(item.get("date"))
            published = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (TypeError, ValueError, OSError, OverflowError):
            continue
        if not now - timedelta(days=days) <= published <= now + timedelta(minutes=30):
            continue
        key = "steam1643320-" + hashlib.sha256(gid.encode()).hexdigest()[:18]
        if key in existing:
            continue
        existing.add(key)
        found.append({
            "id": key, "date": published.strftime("%Y-%m-%d"), "category": "S.T.A.L.K.E.R.",
            "title": draft_title(title),
            "intro": "В новостной ленте Steam для S.T.A.L.K.E.R. 2 появилась публикация. Подробности — по ссылке на первоисточник.",
            "body": ("Первоначальный заголовок: «" + title[:160] + "». "
                     "Это автоматическая заготовка ARCHIUM, а не подтверждённая редакционная статья. "
                     "Перед одобрением проверь содержание сообщения, дату и официальность автора; "
                     "при необходимости переведи заголовок и добавь точные детали своими словами."),
            "art": "news", "image": "", "page": "", "link": url,
            "status": "published", "pinned": False, "telegram_announce": False,
            "source_kind": "Steam news feed / requires editorial review",
        })
    return sorted(found, key=lambda x: (x["date"], x["id"]), reverse=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_review(feed: dict, current_news: dict, now: datetime, days: int = MAX_AGE_DAYS) -> tuple[dict, list[dict]]:
    posts = current_news.get("posts")
    if current_news.get("version") != 1 or not isinstance(posts, list):
        raise ValueError("news.json должен содержать version:1 и массив posts")
    old_ids = {str(x.get("id", "")) for x in posts if isinstance(x, dict)}
    old_links = {str(x.get("link", "")) for x in posts if isinstance(x, dict)}
    new_posts = [x for x in read_api(feed, now, days) if x["id"] not in old_ids and x["link"] not in old_links][:MAX_NEW]
    if not new_posts:
        return current_news, []
    if len(posts) + len(new_posts) > 250:
        raise ValueError("В news.json будет более 250 записей: нужен ручной перенос старых публикаций в архив")
    # news.json gets changed ONLY on a review branch, and becomes public ONLY on human merge.
    result = dict(current_news)
    result["posts"] = new_posts + posts
    result["updated"] = now.strftime("%Y-%m-%d")
    return result, new_posts


def fetch_steam() -> dict:
    params = urlencode({"appid": APP_ID, "count": 40, "maxlength": 0, "format": "json"})
    req = Request(STEAM_API + "?" + params,
                  headers={"User-Agent": "ARCHIUM-news-review/1.0 (+https://github.com/666Danya/archium-beta)", "Accept": "application/json"})
    with urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError("Steam returned HTTP " + str(response.status))
        return json.load(response)


def main():
    p = argparse.ArgumentParser(description="Prepare a review-only ARCHIUM news update; never publishes")
    p.add_argument("--news", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--fixture", type=Path, help="Use local JSON fixture; no network calls")
    p.add_argument("--now", help="UTC ISO timestamp for deterministic testing")
    p.add_argument("--days", type=int, default=MAX_AGE_DAYS)
    args = p.parse_args()
    if not 1 <= args.days <= 30:
        p.error("--days must be 1..30")
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        p.error("--now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    feed = load_json(args.fixture) if args.fixture else fetch_steam()
    updated, drafts = build_review(feed, load_json(args.news), now, args.days)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if drafts:
        args.output.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        # Preserve exact source formatting when there are no candidates.
        args.output.write_bytes(args.news.read_bytes())
    report = ["# ARCHIUM · новости на проверку", "", f"Новых кандидатов: **{len(drafts)}**.",
              "", "Все новости — **на подтверждение редактору**. Это автоматически составленные нейтральные черновики, не подтверждённые публикации.",
              "", "Перед слиянием PR проверь дату, ссылку, факты и автора, поправь русский текст и только затем одобри.", ""]
    for x in drafts:
        report += [f"## {x['title']}", f"Дата: {x['date']} · Источник: {x['link']}", f"ID: {x['id']}", ""]
    args.report.write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"new_count": len(drafts), "ids": [x["id"] for x in drafts]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
