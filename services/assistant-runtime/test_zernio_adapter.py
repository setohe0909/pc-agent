import asyncio
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.adapters.zernio_adapter import ZernioAdapter


class ZernioAdapterPostTests(unittest.TestCase):
    def setUp(self):
        self._old_key = os.environ.get("ZERNIO_API_KEY")
        os.environ["ZERNIO_API_KEY"] = "sk_test"

    def tearDown(self):
        if self._old_key is None:
            os.environ.pop("ZERNIO_API_KEY", None)
        else:
            os.environ["ZERNIO_API_KEY"] = self._old_key

    def test_media_items_only_include_public_urls(self):
        adapter = ZernioAdapter()

        result = adapter._build_media_items({
            "media_urls": [
                "data:image/png;base64,abc",
                "https://cdn.example.com/photo.png",
                "https://cdn.example.com/video.mp4?token=1",
            ]
        })

        self.assertEqual(result, [
            {"url": "https://cdn.example.com/photo.png", "type": "image"},
            {"url": "https://cdn.example.com/video.mp4?token=1", "type": "video"},
        ])

    def test_publish_post_uses_zernio_create_post_contract(self):
        async def scenario():
            adapter = ZernioAdapter()
            sent = {}

            async def fake_resolve(platform, post):
                return "acc_123"

            async def fake_post(path, data):
                sent["path"] = path
                sent["data"] = data
                return True

            adapter._resolve_account_id = fake_resolve
            adapter._z_post = fake_post

            ok = await adapter.publish_post({
                "platform": "instagram",
                "content": "Hola mundo",
                "media_urls": ["https://cdn.example.com/photo.png"],
            })

            self.assertTrue(ok)
            self.assertEqual(sent["path"], "/posts")
            self.assertEqual(sent["data"]["publishNow"], True)
            self.assertEqual(sent["data"]["platforms"], [{"platform": "instagram", "accountId": "acc_123"}])
            self.assertEqual(sent["data"]["mediaItems"], [{"url": "https://cdn.example.com/photo.png", "type": "image"}])

        asyncio.run(scenario())

    def test_multiple_accounts_without_explicit_account_id_blocks_write(self):
        async def scenario():
            adapter = ZernioAdapter()
            adapter._accounts_cache = [
                {"_id": "acc_1", "platform": "instagram", "isActive": True},
                {"_id": "acc_2", "platform": "instagram", "isActive": True},
            ]

            called = False

            async def fake_post(path, data):
                nonlocal called
                called = True
                return True

            adapter._z_post = fake_post

            ok = await adapter.publish_post({"platform": "instagram", "content": "No publicar ambiguo"})

            self.assertFalse(ok)
            self.assertFalse(called)

        asyncio.run(scenario())

    def test_get_comments_source_zernio_uses_inbox_comments_contract(self):
        async def scenario():
            adapter = ZernioAdapter()
            calls = []

            async def fake_get(path, params=None):
                calls.append((path, params))
                if path == "/inbox/comments":
                    return {
                        "data": [
                            {
                                "id": "post_1",
                                "platform": "instagram",
                                "accountId": "acc_1",
                                "permalink": "https://instagram.com/p/1",
                            }
                        ]
                    }
                if path == "/inbox/comments/post_1":
                    return {
                        "comments": [
                            {
                                "id": "comment_1",
                                "message": "INFO por favor",
                                "createdTime": "2026-05-19T12:00:00Z",
                                "from": {"username": "buyer_1"},
                                "platform": "instagram",
                            }
                        ]
                    }
                return None

            adapter._z_get = fake_get

            comments = await adapter.get_comments("instagram", "latest_post", data_source="zernio")

            self.assertEqual(calls[0][0], "/inbox/comments")
            self.assertEqual(calls[0][1]["platform"], "instagram")
            self.assertEqual(calls[1], ("/inbox/comments/post_1", {"accountId": "acc_1"}))
            self.assertEqual(comments[0]["source"], "zernio")
            self.assertEqual(comments[0]["user"], "buyer_1")
            self.assertEqual(comments[0]["text"], "INFO por favor")

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
