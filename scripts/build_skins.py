"""Build the bundled skins offline with Pillow.

Run `python scripts/build_skins.py` from the project. The original sprites are
read from the adjacent video project when present, or from the bundled classic
and doctor skins in a standalone checkout. The two --*-source options can
instead point to directories containing those original sprites.
"""
import argparse
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw


PROJECT = Path(__file__).resolve().parents[1]
BUNDLED = PROJECT / "doudou_pet" / "assets" / "skins"
VIDEO_ART = PROJECT.parent / "素材" / "图片"
ORIGINAL_SOURCES = {
    "classic": (VIDEO_ART / "像素版" / "第1季" / "001-ai-buhui-sikao", "仓鼠豆豆"),
    "doctor": (VIDEO_ART / "文学人物" / "第1季" / "001-kongzi", "豆豆博士"),
}

# One cell matches one original video sprite pixel. Dots leave the base intact.
INK = "#0a0a14"
PIXEL = 8
KEYBOARD = (
    ".###########.",
    "#K1K2K3K4K5K#",
    "#K6K7K8K9K0K#",
    "#LKKMMMMKKLL#",
    ".###########.",
)
KEY_COLORS = {"#": INK, "K": "#34526e", "L": "#596988", "M": "#b4cada"}

HAT = (
    ".....####.....",
    "..###WWWW###..",
    ".#WWWWWWWWWW#.",
    "#WWWWWWWWWWWS#",
    "#WWWWSSWWWSSS#",
    ".##WSSSWWSS##.",
    "..#WWWWWWWS#..",
    "..#RRRRRRRR#..",
    "...########...",
)
HAT_COLORS = {"#": INK, "W": "#fff1e8", "S": "#bfd6df", "R": "#d85b51"}

PAN = (
    "....########.",
    "#####MMMMMMM#",
    "#hhh#KLLLLLK#",
    ".###.#KKKKK#.",
    "......#####..",
)
PAN_COLORS = {"#": INK, "K": "#344555", "M": "#9eafbb", "L": "#596a77", "h": "#c47634"}
SEED = (".#.", "#G#", "#D#", ".#.")
SEED_COLORS = {"#": "#5c3025", "G": "#ffdc83", "D": "#bb7541"}
BOOK = (
    ".#####.#####.",
    "#WPPPW#WPPPW#",
    "#WLLPW#WPLLW#",
    "#WPPPW#WPPPW#",
    "#RRRRR#RRRRR#",
    ".#####B#####.",
)
BOOK_COLORS = {"#": INK, "W": "#fff1e8", "P": "#ffdc83", "L": "#d59559", "R": "#b95044", "B": "#7e2553"}


def paint(base, x, y, rows, palette):
    """Stamp hard-edged square pixels without filtering or moving the base."""
    draw = ImageDraw.Draw(base)
    for sy, row in enumerate(rows, y):
        for sx, glyph in enumerate(row, x):
            if glyph != ".":
                left, top = sx * PIXEL, sy * PIXEL
                draw.rectangle((left, top, left + PIXEL - 1, top + PIXEL - 1), fill=palette[glyph])


def programming(base, lit="", done=False):
    image = base.copy()
    colors = {**KEY_COLORS}
    colors.update({key: "#81e6cf" if key in lit else "#a3b3c9" for key in "1234567890"})
    paint(image, 9, 19, KEYBOARD, colors)
    if done:
        paint(image, 25, 8, ("...G", "..G.", "GG..", ".G.."), {"G": "#6bdb9c"})
    return image


def cooking(base, rise=0, seeds=()):
    image = base.copy()
    paint(image, 9, 2, HAT, HAT_COLORS)
    paint(image, 22, 18 - rise, PAN, PAN_COLORS)
    for x, y in seeds:
        paint(image, x, y, SEED, SEED_COLORS)
    return image


def original_poses(output, skin_id, source=None):
    video_dir, prefix = ORIGINAL_SOURCES[skin_id]
    destination = output / skin_id
    paths = {}
    for pose in ("idle", "wave"):
        if source is None:
            upstream = video_dir / f"{prefix}_{pose}.png"
            source_path = upstream if upstream.is_file() else BUNDLED / skin_id / f"{pose}.png"
        else:
            upstream = source / f"{prefix}_{pose}.png"
            source_path = upstream if upstream.is_file() else source / f"{pose}.png"
        paths[destination / f"{pose}.png"] = source_path
        if not source_path.is_file():
            raise FileNotFoundError(f"Missing {skin_id} sprite: {source_path}")
    destination.mkdir(parents=True, exist_ok=True)
    for target, source_path in paths.items():
        if source_path.resolve() != target.resolve():
            shutil.copyfile(source_path, target)
    with Image.open(destination / "idle.png") as idle:
        return idle.convert("RGBA")


def write_manifest(output, skin_id, name, bubble, frames):
    data = {
        "id": skin_id,
        "name": name,
        "idle": "idle.png",
        "interact": [{"file": file, "ms": ms} for file, ms in frames],
        "bubble": bubble,
    }
    (output / skin_id / "skin.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n",
    )


def build(output, classic_source=None, doctor_source=None):
    classic = original_poses(output, "classic", classic_source)
    doctor = original_poses(output, "doctor", doctor_source)
    write_manifest(output, "classic", "原版豆豆", "嗨，你好呀！", (
        ("wave.png", 220), ("idle.png", 120), ("wave.png", 260),
    ))

    paint(doctor, 11, 19, BOOK, BOOK_COLORS)
    doctor.save(output / "doctor" / "book.png")
    write_manifest(output, "doctor", "豆豆博士", "让我翻翻书！", (
        ("wave.png", 240), ("book.png", 680),
    ))

    programmer_frames = (
        ("idle.png", 0, programming(classic)),
        ("type_left.png", 170, programming(classic, "127")),
        ("type_right.png", 150, programming(classic, "4590")),
        ("type_left.png", 145, None),
        ("type_right.png", 145, None),
        ("done.png", 440, programming(classic, "1234567890", done=True)),
    )
    chef_frames = (
        ("idle.png", 0, cooking(classic)),
        ("toss_low.png", 170, cooking(classic, rise=1, seeds=((28, 13), (32, 12)))),
        ("toss_high.png", 210, cooking(classic, seeds=((27, 8), (32, 10), (35, 7)))),
        ("toss_fall.png", 175, cooking(classic, seeds=((28, 14), (32, 13)))),
        ("serve.png", 400, cooking(classic, seeds=((29, 15),))),
    )
    for skin_id, name, bubble, frames in (
        ("programmer", "程序员豆豆", "跑通了！", programmer_frames),
        ("chef", "厨师豆豆", "葵花籽出锅啦！", chef_frames),
    ):
        folder = output / skin_id
        folder.mkdir(parents=True, exist_ok=True)
        for filename, _, image in frames:
            if image is not None:
                image.save(folder / filename)
        write_manifest(output, skin_id, name, bubble, ((filename, ms) for filename, ms, _ in frames if ms))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BUNDLED)
    parser.add_argument("--classic-source", type=Path)
    parser.add_argument("--doctor-source", type=Path)
    args = parser.parse_args()
    build(args.output, args.classic_source, args.doctor_source)


if __name__ == "__main__":
    main()
