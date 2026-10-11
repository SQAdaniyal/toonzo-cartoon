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
                    successful_response,
                ],
            ) as post,
            patch("script_gen.time.sleep"),
        ):
            result = script_gen._ask_gemini("prompt")

        self.assertEqual(result, '{"title":"A New Kite"}')
        self.assertEqual(post.call_count, 3)
        self.assertIn(script_gen.MODELS[0], post.call_args_list[0].args[0])
        self.assertIn(script_gen.MODELS[0], post.call_args_list[1].args[0])
        self.assertIn(script_gen.MODELS[1], post.call_args_list[2].args[0])
        self.assertEqual(
            post.call_args_list[2].kwargs["json"]["generationConfig"]["responseMimeType"],
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
