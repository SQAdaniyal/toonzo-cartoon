import unittest
from unittest.mock import Mock, patch

import cartoon
import config
import script_gen
from main import (
    _is_duplicate_title,
    _script_fingerprint,
    generate_unique_topics,
)


class CartoonPipelineTests(unittest.TestCase):
    def test_brand_name_is_configured_for_toonzo(self):
        self.assertEqual(config.CHANNEL_NAME, "ToonZo Official")

    def test_duplicate_titles_are_rejected(self):
        history = [{"title": "Milo and Tilly's Lost Star"}]
        self.assertTrue(_is_duplicate_title("Milo & Tilly's Lost Star!", history))
        self.assertFalse(_is_duplicate_title("The Lantern That Wouldn't Glow", history))

    def test_script_fingerprint_ignores_punctuation_and_case(self):
        self.assertEqual(
            _script_fingerprint("Milo found a star!"),
            _script_fingerprint("MILO found a star"),
        )

    def test_topic_generator_retries_duplicate_candidates(self):
        with patch(
            "main.script_gen.generate_topics",
            side_effect=[
                ["Old adventure", "A new forest mystery"],
                ["A new forest mystery", "The kite above the clouds"],
            ],
        ) as generate:
            topics = generate_unique_topics(
                2, "short", ["Old adventure"], {}, additional_topics=[]
            )

        self.assertEqual(topics, ["A new forest mystery", "The kite above the clouds"])
        self.assertEqual(generate.call_count, 2)

    def test_json_parser_accepts_fenced_complete_json(self):
        self.assertEqual(script_gen._parse_json('```json\n{"title":"A New Kite"}\n```'),
                         {"title": "A New Kite"})

    def test_json_generation_retries_malformed_response(self):
        with patch(
            "script_gen._ask_gemini",
            side_effect=["{\"title\":", "{\"title\":\"A New Kite\"}"],
        ) as ask:
            value = script_gen._generate_json("prompt", "test package")

        self.assertEqual(value, {"title": "A New Kite"})
        self.assertEqual(ask.call_count, 2)
        self.assertEqual(ask.call_args_list[0].args, ("prompt", 0))
        self.assertEqual(ask.call_args_list[1].args[1], 1)

    def test_local_topics_are_unique_and_skip_used_ideas(self):
        with patch(
            "script_gen._generate_json",
            side_effect=RuntimeError("Gemini quota exhausted"),
        ):
            topics = script_gen.generate_topics(
                5, "short", ["A paper kite that has drifted into a patch of tall grass in the sunny meadow"]
            )

        self.assertEqual(len(topics), 5)
        self.assertEqual(len(set(topics)), 5)
        self.assertNotIn(
            "A paper kite that has drifted into a patch of tall grass in the sunny meadow",
            topics,
        )

    def test_local_script_fallback_produces_valid_short_package(self):
        with patch(
            "script_gen._generate_json",
            side_effect=RuntimeError("Gemini quota exhausted"),
        ):
            package = script_gen.generate_script(
                "A paper kite that has drifted into a patch of tall grass in the sunny meadow",
                "short",
            )

        self.assertEqual(len(package["scenes"]), 5)
        self.assertEqual(
            package["script"],
            " ".join(scene["narration"] for scene in package["scenes"]),
        )
        self.assertLessEqual(
            len(package["script"].split()), config.SHORT_TARGET_WORDS
        )
        self.assertTrue(package["title"].endswith("#Shorts"))

    def test_local_script_fallback_produces_long_episode_length(self):
        with patch(
            "script_gen._generate_json",
            side_effect=RuntimeError("Gemini quota exhausted"),
        ):
            package = script_gen.generate_script(
                "A paper kite that has drifted into a patch of tall grass in the sunny meadow",
                "long",
            )

        self.assertGreaterEqual(len(package["scenes"]), 8)
        self.assertLessEqual(len(package["scenes"]), 12)
        self.assertGreaterEqual(len(package["script"].split()), config.LONG_TARGET_WORDS)
        self.assertEqual(
            package["script"],
            " ".join(scene["narration"] for scene in package["scenes"]),
        )

    def test_quota_exhaustion_skips_retries_for_that_model(self):
        script_gen._QUOTA_BLOCKED_MODELS.clear()
        script_gen._UNAVAILABLE_MODELS.clear()
        quota_response = Mock(
            status_code=429,
            text='{"error":{"message":"You exceeded your current quota"}}',
        )
        try:
            with patch(
                "script_gen.requests.post",
                side_effect=[quota_response, quota_response, quota_response],
            ) as post:
                with self.assertRaises(RuntimeError):
                    script_gen._ask_gemini("prompt")
                self.assertEqual(post.call_count, len(script_gen.MODELS))
                with self.assertRaises(RuntimeError):
                    script_gen._ask_gemini("prompt")
                self.assertEqual(post.call_count, len(script_gen.MODELS))
        finally:
            script_gen._QUOTA_BLOCKED_MODELS.clear()
            script_gen._UNAVAILABLE_MODELS.clear()

    def test_unavailable_models_are_not_retried_for_every_video(self):
        script_gen._QUOTA_BLOCKED_MODELS.clear()
        script_gen._UNAVAILABLE_MODELS.clear()
        unavailable = Mock(status_code=503, text="temporarily unavailable")
        try:
            with (
                patch(
                    "script_gen.requests.post",
                    side_effect=[unavailable] * (len(script_gen.MODELS) * 3),
                ) as post,
                patch("script_gen.time.sleep"),
            ):
                with self.assertRaises(RuntimeError):
                    script_gen._ask_gemini("first prompt")
                self.assertEqual(post.call_count, len(script_gen.MODELS) * 3)
                with self.assertRaises(RuntimeError):
                    script_gen._ask_gemini("next prompt")
                self.assertEqual(post.call_count, len(script_gen.MODELS) * 3)
        finally:
            script_gen._QUOTA_BLOCKED_MODELS.clear()
            script_gen._UNAVAILABLE_MODELS.clear()

    def test_gemini_switches_models_after_unavailable_response(self):
        successful_response = Mock(
            status_code=200,
            json=lambda: {
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {"parts": [{"text": '{"title":"A New Kite"}'}]},
                    }
                ]
            },
        )
        with (
            patch(
                "script_gen.requests.post",
                side_effect=[
                    Mock(status_code=503, text="temporarily unavailable"),
                    Mock(status_code=503, text="temporarily unavailable"),
                    Mock(status_code=503, text="temporarily unavailable"),
                    successful_response,
                ],
            ) as post,
            patch("script_gen.time.sleep"),
        ):
            result = script_gen._ask_gemini("prompt")

        self.assertEqual(result, '{"title":"A New Kite"}')
        self.assertEqual(post.call_count, 4)
        self.assertIn(script_gen.MODELS[0], post.call_args_list[0].args[0])
        self.assertIn(script_gen.MODELS[0], post.call_args_list[1].args[0])
        self.assertIn(script_gen.MODELS[0], post.call_args_list[2].args[0])
        self.assertIn(script_gen.MODELS[1], post.call_args_list[3].args[0])
        self.assertEqual(
            post.call_args_list[3].kwargs["json"]["generationConfig"]["responseMimeType"],
            "application/json",
        )

    def test_scene_renders_a_composited_frame_at_requested_size(self):
        scene = {
            "narration": "Milo and Tilly found a tiny glowing seed.",
            "setting": "forest clearing",
            "action": "a glowing seed",
            "mood": "surprised",
        }
        clip = cartoon._scene_clip(scene, 0, 0.5, (320, 180), "A TINY GLOWING SEED")
        try:
            frame = clip.get_frame(0.25)
        finally:
            clip.close()

        self.assertEqual(frame.shape, (180, 320, 3))


if __name__ == "__main__":
    unittest.main()
