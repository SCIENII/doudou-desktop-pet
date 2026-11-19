"""Contracts for the four bundled skins and their offline asset builder."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


PROJECT = Path(__file__).resolve().parents[1]
SKINS = PROJECT / "doudou_pet" / "assets" / "skins"
SKIN_IDS = {"classic", "doctor", "programmer", "chef"}
BUILDER = PROJECT / "scripts" / "build_skins.py"

# Fingerprints of the original video sprites, independent of source-tree layout.
ORIGINALS = {
    "classic/idle.png": "e9dda993c5de4eae3a54fc204252bb621f349e202794e525170575267fcc05b6",
    "classic/wave.png": "699440ed3d59f9391849dfd8e7201564906699f58fe6a612336fcdd73558c269",
    "doctor/idle.png": "ba4d582771167a300fcc2aa8b1c61ec8f95e8c1d4409cf54867f904d9324b2ca",
    "doctor/wave.png": "ffd81f8089b0061bc943867134d278064be2d0509eaf07f5d7ccdb0f37570288",
}


def manifest(skin_id):
    return json.loads((SKINS / skin_id / "skin.json").read_text(encoding="utf-8"))


def pixels(path):
    with Image.open(path) as image:
        return image.convert("RGBA")


class AssetTests(unittest.TestCase):
    def test_all_four_skins_ship_with_manifests(self):
        self.assertEqual({path.parent.name for path in SKINS.glob("*/skin.json")}, SKIN_IDS)

    def test_manifests_reference_valid_png_basenames(self):
        for skin_id in sorted(SKIN_IDS):
            with self.subTest(skin=skin_id):
                self.assertTrue((SKINS / skin_id / "skin.json").is_file())
                data = manifest(skin_id)
                self.assertEqual(set(data), {"id", "name", "idle", "interact", "bubble"})
                self.assertEqual(data["id"], skin_id)
                self.assertIsInstance(data["name"], str)
                self.assertTrue(data["name"].strip())
                self.assertIsInstance(data["bubble"], str)
                self.assertTrue(data["bubble"].strip())
                self.assertIsInstance(data["interact"], list)
                self.assertGreaterEqual(len(data["interact"]), 2)
                for frame in data["interact"]:
                    self.assertEqual(set(frame), {"file", "ms"})
                    self.assertIs(type(frame["ms"]), int)
                    self.assertGreater(frame["ms"], 0)
                for filename in [data["idle"], *(f["file"] for f in data["interact"])]:
                    self.assertRegex(filename, r"^[a-z][a-z0-9_]*\.png$")
                    with Image.open(SKINS / skin_id / filename) as image:
                        self.assertEqual(image.format, "PNG")
                        image.verify()

    def test_original_idle_and_wave_are_byte_identical(self):
        for filename, digest in ORIGINALS.items():
            with self.subTest(asset=filename):
                path = SKINS / filename
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
    def test_original_idle_and_wave_are_used(self):
        for skin_id in ("classic", "doctor"):
            with self.subTest(skin=skin_id):
                self.assertTrue((SKINS / skin_id / "skin.json").is_file())
                data = manifest(skin_id)
                self.assertEqual(data["idle"], "idle.png")
                self.assertIn("wave.png", [frame["file"] for frame in data["interact"]])

    def test_frames_keep_transparency_and_fixed_feet(self):
        for skin_id in sorted(SKIN_IDS):
            with self.subTest(skin=skin_id):
                frames = sorted((SKINS / skin_id).glob("*.png"))
                self.assertTrue(frames)
                height, baseline = (272, 224) if skin_id == "doctor" else (240, 208)
                idle = pixels(SKINS / skin_id / manifest(skin_id)["idle"])
                feet = idle.crop((0, baseline - 16, 320, baseline)).tobytes()
                for frame in frames:
                    image = pixels(frame)
                    alpha = image.getchannel("A")
                    self.assertEqual(image.size, (320, height), frame.name)
                    self.assertEqual(alpha.getextrema(), (0, 255), frame.name)
                    self.assertEqual(alpha.getbbox()[3], baseline, frame.name)
                    self.assertEqual(image.crop((0, baseline - 16, 320, baseline)).tobytes(), feet, frame.name)

    def test_occupation_overlays_really_change_over_time(self):
        for skin_id, patch in (("programmer", (72, 144, 200, 192)), ("chef", (168, 56, 320, 184))):
            with self.subTest(skin=skin_id):
                self.assertTrue((SKINS / skin_id / "skin.json").is_file())
                data = manifest(skin_id)
                self.assertGreaterEqual(len(data["interact"]), 3)
                idle = pixels(SKINS / skin_id / data["idle"])
                original = pixels(SKINS / "classic" / "idle.png")
                self.assertNotEqual(idle.tobytes(), original.tobytes())
                frames = [pixels(SKINS / skin_id / f["file"]).crop(patch).tobytes() for f in data["interact"]]
                self.assertGreaterEqual(len(set(frames)), 3)

    def test_builder_recreates_shipped_frames_offline(self):
        self.assertTrue(BUILDER.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundle"
            sources = Path(tmp) / "sources"
            for skin_id in ("classic", "doctor"):
                shutil.copytree(SKINS / skin_id, sources / skin_id)
            subprocess.run(
                [sys.executable, str(BUILDER), "--output", str(output),
                 "--classic-source", str(sources / "classic"), "--doctor-source", str(sources / "doctor")],
                check=True, capture_output=True,
            )
            self.assertEqual(
                {p.relative_to(output) for p in output.glob("*/*")},
                {p.relative_to(SKINS) for p in SKINS.glob("*/*")},
            )
            for target in output.glob("*/*"):
                source = SKINS / target.relative_to(output)
                with self.subTest(asset=source.relative_to(SKINS)):
                    if target.suffix == ".png":
                        self.assertEqual(pixels(target).tobytes(), pixels(source).tobytes())
                    else:
                        self.assertEqual(target.read_bytes(), source.read_bytes())


if __name__ == "__main__":
    unittest.main()
