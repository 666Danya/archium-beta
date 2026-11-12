import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from archium_news import build_review, read_api, trusted_url, draft_title

NOW = datetime(2026, 11, 13, 10, tzinfo=timezone.utc)
ITEM = {"gid": "123456", "date": int(NOW.timestamp()) - 3600,
        "title": "Patch 2.2 is now available",
        "url": "https://store.steampowered.com/news/app/1643320/view/123456",
        "contents": "<p>Hello</p>"}


class NewsReviewTest(unittest.TestCase):
    def setUp(self):
        self.feed = {"appnews": {"appid": 1643320, "newsitems": [ITEM]}}
        self.posts = {"version": 1, "updated": "2026-11-08",
                      "posts": [{"id": "archium-orig", "title": "Old",
                                 "body": "Original news", "status": "published"}]}

    def test_prepare_preserves_original(self):
        new, candidates = build_review(self.feed, self.posts, NOW)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(new["posts"][1], self.posts["posts"][0])
        self.assertEqual(candidates[0]["category"], "S.T.A.L.K.E.R.")
        self.assertEqual(candidates[0]["status"], "published")
        self.assertIn("проверь", candidates[0]["body"])
        self.assertEqual(self.posts["updated"], "2026-11-08")

    def test_deduplicate_by_id(self):
        once, _ = build_review(self.feed, self.posts, NOW)
        twice, candidates = build_review(self.feed, once, NOW)
        self.assertEqual(twice, once)
        self.assertEqual(candidates, [])

    def test_ignore_stale_and_future(self):
        item = dict(ITEM, date=int(NOW.timestamp()) - 20 * 86400)
        self.assertFalse(read_api({"appnews": {"appid": 1643320, "newsitems": [item]}}, NOW))
        item["date"] = int(NOW.timestamp()) + 7200
        self.assertFalse(read_api({"appnews": {"appid": 1643320, "newsitems": [item]}}, NOW))

    def test_reject_untrusted_links(self):
        self.assertIsNone(trusted_url("http://store.steampowered.com/x"))
        self.assertIsNone(trusted_url("https://store.steampowered.com.evil.tld/x"))
        self.assertIsNone(trusted_url("https://evil.tld/"))

    def test_wrong_app_rejected(self):
        with self.assertRaises(ValueError):
            read_api({"appnews": {"appid": 999, "newsitems": [ITEM]}}, NOW)

    def test_feed_title_never_invents_fact(self):
        self.assertIn("2.2", draft_title("Patch 2.2 is now available"))
        self.assertIn("моддинга", draft_title("Zone Kit tools"))

    def test_too_many_posts_fail_safe(self):
        news = dict(self.posts, posts=[{"id": "p" + str(i)} for i in range(250)])
        with self.assertRaisesRegex(ValueError, "250"):
            build_review(self.feed, news, NOW)
