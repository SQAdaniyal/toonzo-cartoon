import unittest
from unittest.mock import patch

import cartoon
import config
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
