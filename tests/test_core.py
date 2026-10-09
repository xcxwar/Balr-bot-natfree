
import asyncio
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

import bot


class UsageLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = bot.DB(
            os.path.join(self.tmp.name, "test.sqlite3")
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_limits_are_separate_per_profile(self):
        for _ in range(4):
            self.db.consume("user-a", 1)

        self.assertFalse(self.db.allowed("user-a", 1)[0])
        self.assertTrue(self.db.allowed("user-a", 2)[0])
        self.assertTrue(self.db.allowed("user-a", 3)[0])

    def test_limits_are_separate_per_user(self):
        for _ in range(4):
            self.db.consume("user-a", 1)

        self.assertTrue(self.db.allowed("user-b", 1)[0])

    def test_profile_caps_match_requirements(self):
        self.assertEqual(bot.RATE_LIMITS[1], (4, 6 * 60 * 60))
        self.assertEqual(bot.RATE_LIMITS[2], (2, 4 * 60 * 60))
        self.assertEqual(bot.RATE_LIMITS[3], (3, 6 * 60 * 60))

    def test_window_expiry_restores_quota(self):
        self.db.consume("user-a", 1)

        with self.db.conn() as conn:
            conn.execute(
                "UPDATE usage SET created_at=? "
                "WHERE user_id=? AND profile_id=?",
                (
                    bot.time.time() - 7 * 60 * 60,
                    "user-a",
                    1,
                ),
            )

        self.assertTrue(self.db.allowed("user-a", 1)[0])

    def test_old_usage_schema_migrates(self):
        old_path = os.path.join(self.tmp.name, "old.sqlite3")
        import sqlite3

        with sqlite3.connect(old_path) as conn:
            conn.execute(
                "CREATE TABLE usage("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "user_id TEXT, created_at REAL)"
            )

        db = bot.DB(old_path)

        with db.conn() as conn:
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(usage)")
            }

        self.assertIn("profile_id", columns)


class ProfileBehaviorTests(unittest.TestCase):
    def test_owen_returns_exact_text_without_calling_provider(self):
        async def run():
            client = bot.AI()

            with patch.object(
                client,
                "one",
                new=AsyncMock(
                    side_effect=AssertionError(
                        "provider must not be called"
                    )
                ),
            ):
                result = await client.chat(
                    2,
                    [{"role": "user", "content": "hello"}],
                    "fa",
                )

            self.assertEqual(
                result,
                "این سرویس در حال حاضر غیرفعال است. "
                "لطفاً از یکی دیگر از مدل‌های هوش مصنوعی استفاده کنید.",
            )

        asyncio.run(run())

    def test_admin_is_numeric_id_only(self):
        self.assertTrue(bot.is_admin_user("955311935"))
        self.assertFalse(bot.is_admin_user("some_username"))
        self.assertFalse(bot.is_admin_user("123"))

    def test_missing_required_token_has_clear_error(self):
        async def run():
            with patch.object(bot, "BOT_TOKEN", ""):
                with self.assertRaisesRegex(
                    RuntimeError, "BALE_BOT_TOKEN"
                ):
                    await bot.main()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
