"""Export 9:16 caption overlays, a safe-area guide, or captions with a timed SFX track."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unicodedata


SCENES = {
    "hook": ("开头钩子", "A-6aa4aac921b4", r"\fry-65\fscy75\t(0,300,\fry0\fscy100)"),
    "emphasis": ("注意重点", "A-95dcb57c5091", r"\frx70\t(0,270,\frx0)"),
    "question": ("疑问", "A-1e39cca5e2c4", r"\frz-9\fscx78\fscy78\t(0,160,\frz5\fscx110\fscy110)\t(160,310,\frz0\fscx100\fscy100)"),
    "turn": ("突然转折", "A-fb35198a9fbf", r"\frz8\fscx124\fscy124\t(0,100,\frz-6)\t(100,210,\frz3)\t(210,340,\frz0\fscx100\fscy100)"),
    "reveal": ("出现信息", "A-fc9d1154aa6d", r"\frx-85\t(0,330,\frx0)"),
    "data": ("数据相关", "A-e2fb7b7806a4", r"\frz-12\fscx82\fscy82\t(0,430,\frz0\fscx100\fscy100)"),
    "awkward": ("尴尬", "A-7616a68c58f6", r"\fscx65\fscy65\t(0,230,\fscx108\fscy108)\t(230,350,\fscx100\fscy100)"),
    "knowledge": ("知识点", "A-fb34e5ff5986", r"\blur8\t(0,320,\blur0)\fad(260,130)"),
    "shock": ("震惊", "A-ff7f59e45a26", r"\blur12\fscx124\fscy124\t(0,300,\blur0\fscx100\fscy100)\fad(130,150)"),
    "word-zoom": ("逐字放大", "A-3adee630d553", r"\fscx75\fscy75\t(0,190,\fscx112\fscy112)\t(190,360,\fscx100\fscy100)"),
}
DEFAULT_LAYOUT = {
    "safe_rect": [90, 210, 875, 1510],
    "eye_y": 640,
    "anchor_x": 480,
    "hook_y": 365,
    "focus_y": 960,
    "caption_y": 1320,
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clock(seconds):
    ticks = round(seconds * 100)
    return f"{ticks//360000}:{ticks//6000%60:02d}:{ticks//100%60:02d}.{ticks%100:02d}"


def safe_text(value):
    if not isinstance(value, str) or not value.strip() or re.search(r"[{}\\\r\n]", value):
        raise ValueError("Caption lines must be nonempty text without braces, backslashes or line breaks.")
    return value.strip()


def dialogue(start, end, style, tags, content, layer=1):
    return f"Dialogue: {layer},{clock(start)},{clock(end)},{style},,0,0,0,,{{{tags}}}{content}"


def ass_header(font):
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H26000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def layout_for(path):
    layout = DEFAULT_LAYOUT | (read_json(path) if path else {})
    left, top, right, bottom = layout["safe_rect"]
    if not (0 <= left < layout["anchor_x"] < right <= 1080 and
            0 <= top < layout["hook_y"] < layout["eye_y"] < layout["focus_y"] <
            layout["caption_y"] < bottom <= 1920):
        raise ValueError("Layout anchors must be ordered and stay inside the safe rectangle.")
    return layout


def caption_events(start, end, text, x, y, font_size, width, color="FFFFFF", motion=""):
    columns = sum(1 if unicodedata.east_asian_width(c) in ("F", "W", "A") else .62 for c in text)
    size = min(font_size, int(width / columns))
    if size < 36:
        raise ValueError(f"Split this caption into shorter cues: {text}")
    placement = rf"\pos({x},{y})\fs{size}"
    return [
        dialogue(start, end, "Main", placement + r"\1c&H000000&\1a&H26&\blur9" + motion, text, 0)
        .replace(rf"\pos({x},{y})", rf"\pos({x+3},{y+6})", 1),
        dialogue(start, end, "Main", placement + rf"\1c&H{color}&" + motion, text),
    ]


def vector(start, end, path, color, alpha="00", layer=0):
    return dialogue(start, end, "Main", rf"\an7\pos(0,0)\p1\1c&H{color}&\1a&H{alpha}&", path, layer)


def box(start, end, x1, y1, x2, y2, color, alpha="00"):
    return vector(start, end, f"m {x1} {y1} l {x2} {y1} {x2} {y2} {x1} {y2}", color, alpha)


def safe_guide(layout, duration):
    left, top, right, bottom = layout["safe_rect"]
    x = layout["anchor_x"]
    events = [
        box(0, duration, 0, 0, 1080, top, "6451CF", "A8"),
        box(0, duration, 0, bottom, 1080, 1920, "6451CF", "88"),
        box(0, duration, 0, top, left, bottom, "6451CF", "A8"),
        box(0, duration, right, top, 1080, bottom, "6451CF", "88"),
        box(0, duration, left, top, right, top+4, "8CE51D"),
        box(0, duration, left, bottom-4, right, bottom, "8CE51D"),
        box(0, duration, left, top, left+4, bottom, "8CE51D"),
        box(0, duration, right-4, top, right, bottom, "8CE51D"),
        box(0, duration, left, layout["eye_y"], right, layout["eye_y"]+4, "D365F6"),
    ]
    for key, label, size in [
        ("hook_y", "开头钩子", 60), ("eye_y", "眼睛参考线", 41),
        ("focus_y", "重点字", 72), ("caption_y", "常规口播字幕", 49),
    ]:
        events += caption_events(0, duration, label, x, layout[key], size, right-left-40)
    if 1080-right >= 160:
        events += caption_events(0, duration, "控件区", (right+1080)//2, 1150, 39, 1080-right-20)
    if 1920-bottom >= 110:
        events += caption_events(0, duration, "底部界面预留", 540, (bottom+1920)//2, 43, 820)
    return events


def preview_background(mode, layout, duration):
    events = [box(0, duration, 0, 0, 1080, 1920, "201810")]
    if mode == "safe-area":
        x, y = layout["anchor_x"], layout["eye_y"]
        head = f"m {x} {y-175} b {x+210} {y-175} {x+210} {y+225} {x} {y+225} b {x-210} {y+225} {x-210} {y-175} {x} {y-175}"
        shoulders = f"m {x-315} 1530 l {x-290} {y+345} {x-145} {y+245} {x+145} {y+245} {x+290} {y+345} {x+315} 1530"
        events.extend((vector(0, duration, shoulders, "604B34"), vector(0, duration, head, "8E7253")))
    else:
        title = "口播字幕 · 字体与重点字" if mode == "typography" else "动态字幕 · 音效搭配"
        events += caption_events(0, duration, title, 540, 225, 50, 910, "F2C483")
        events.append(box(0, duration, 126, 296, 954, 300, "705036"))
    return events


def audio_library(explicit):
    local = Path(r"D:\矩阵获客\音效素材库")
    for root in (explicit, os.environ.get("SANTU_SFX_DIR"), local):
        if root and (Path(root) / "index.json").is_file():
            root = Path(root).resolve()
            return root, {asset["asset_id"]: asset for asset in read_json(root / "index.json")["assets"]}
        if root == explicit and explicit:
            raise ValueError(f"index.json is missing from {root}")
    raise ValueError("Supply --sfx-library or set SANTU_SFX_DIR to the downloaded sound-library directory.")


def cue_events(cues, mode, layout, library, gain):
    root, index = audio_library(library) if mode == "dynamic" else (None, {})
    events, sounds, timeline = [], [], []
    x, y = layout["anchor_x"], layout["caption_y"]
    left, _, right, _ = layout["safe_rect"]
    width = 2 * min(x-left, right-x) - 32
    previous_end = 0
    for cue in cues:
        start, end = round(float(cue["start"]), 2), round(float(cue["end"]), 2)
        if not (math.isfinite(end) and previous_end <= start < end):
            raise ValueError("Cues must be sorted, non-overlapping, and have finite positive durations.")
        previous_end = end
        text = safe_text(cue["text"])
        row = {"start": start, "end": end, "text": text}
        if mode == "typography":
            focus = cue.get("focus")
            if focus:
                focus = safe_text(focus)
                row["focus"] = focus
                events += caption_events(start, end, text, x, y-77, 55, width,
                                         motion=r"\fscx106\fscy106\t(0,240,\fscx100\fscy100)")
                events += caption_events(start, end, focus, x, y, 88, width / 1.12, "65D3F6",
                                         r"\fscx82\fscy82\t(0,180,\fscx112\fscy112)\t(180,310,\fscx100\fscy100)")
            else:
                events += caption_events(start, end, text, x, y, 64, width)
        else:
            scene = cue["scene"]
            label, asset_id, motion = SCENES[scene]
            asset_id = cue.get("asset_id", asset_id)
            asset = index[asset_id]
            wav = (root / asset["file"]).resolve(strict=True)
            if not wav.is_relative_to(root) or wav.suffix.lower() != ".wav" or not asset.get("ready_for_agent"):
                raise ValueError(f"Unusable asset: {asset_id}")
            row.update(scene=scene, scene_label=label, asset_id=asset_id, gain_db=gain,
                       sound_start=start, sound_end=min(end, start+asset["duration_seconds"]))
            sounds.append((wav, start, end-start))
            motion_y = layout["hook_y"] if scene == "hook" else layout["focus_y"]
            if scene == "word-zoom":
                # Stagger per-character scale transforms while preserving the line layout.
                content = "".join(
                    rf"{{\fscx75\fscy75\t({i*65},{i*65+190},\fscx111\fscy111)\t({i*65+190},{i*65+310},\fscx100\fscy100)}}" + char
                    for i, char in enumerate(text)
                )
                size = min(80, int(width / (max(1, len(text))*1.12)))
                if size < 36:
                    raise ValueError(f"Split this caption into shorter cues: {text}")
                events.append(dialogue(start, end, "Main", rf"\pos({x},{motion_y})\fs{size}\1c&H65D3F6&", content))
            else:
                events += caption_events(start, end, text, x, motion_y, 86, width/1.25, "65D3F6", motion)
        timeline.append(row)
    if not timeline:
        raise ValueError("Provide at least one cue.")
    return events, sounds, timeline


def ffmpeg(root, args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", *args], cwd=root, check=True)


def render_audio(root, sounds, gain, duration):
    chains = []
    for i, (wav, start, span) in enumerate(sounds):
        length = min(span, float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav),
        ])))
        fade = min(.06, length / 4)
        chains.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={length},"
                      f"afade=t=out:st={length-fade}:d={fade},volume={gain}dB,"
                      f"adelay={round(start*48000)}S:all=1[a{i}]")
    chains.append("".join(f"[a{i}]" for i in range(len(sounds))) +
                  f"amix=inputs={len(sounds)}:normalize=0,alimiter=limit=0.9:level=0:latency=1,"
                  f"apad,atrim=duration={duration}[mix]")
    ffmpeg(root, [arg for wav, _, _ in sounds for arg in ("-i", str(wav))] +
           ["-filter_complex", ";".join(chains), "-map", "[mix]", "-c:a", "pcm_s16le", "sfx.wav"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preset", choices=("typography", "safe-area", "dynamic"))
    parser.add_argument("output", type=Path, help="New output directory")
    parser.add_argument("--cues", type=Path, help="JSON array of timed cues")
    parser.add_argument("--layout", type=Path, help="Optional 1080x1920 layout JSON overrides")
    parser.add_argument("--font", help="Font family or full face name")
    parser.add_argument("--font-file", type=Path, help="Load a local OTF, TTF, OTC or TTC for this render")
    parser.add_argument("--sfx-library", type=Path)
    parser.add_argument("--gain-db", type=float, default=-12)
    parser.add_argument("--duration", type=float, help="Guide or composition duration in seconds")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--overlay", action="store_true", help="Also render a transparent MOV")
    parser.add_argument("--preview", action="store_true", help="Also render an MP4 preview")
    args = parser.parse_args()

    try:
        output = args.output.resolve()
        if output.exists() or not 1 <= args.fps <= 120 or not -60 <= args.gain_db <= 0:
            raise ValueError("Use a new output directory, FPS in 1–120 and gain in -60–0 dB.")
        layout = layout_for(args.layout)
        font = args.font or ("Noto Serif SC" if args.preset == "typography" else "Noto Sans SC")
        if re.search(r"[,\r\n]", font):
            raise ValueError("Use a single font family without commas.")
        font_file = None
        if args.font_file:
            if not args.font:
                raise ValueError("Specify --font with the face name from --font-file.")
            font_file = args.font_file.resolve(strict=True)
            if not font_file.is_file() or font_file.suffix.lower() not in (".otf", ".ttf", ".otc", ".ttc"):
                raise ValueError("--font-file must be an OTF, TTF, OTC or TTC file.")
        duration = args.duration
        if args.preset == "safe-area":
            duration = 6 if duration is None else duration
            events, sounds, timeline = safe_guide(layout, duration), [], []
        else:
            if not args.cues:
                raise ValueError("Specify --cues for typography and dynamic presets.")
            events, sounds, timeline = cue_events(read_json(args.cues), args.preset, layout, args.sfx_library, args.gain_db)
            duration = timeline[-1]["end"] if duration is None else duration
        if not (math.isfinite(duration) and duration > 0 and (not timeline or duration >= timeline[-1]["end"])):
            raise ValueError("Duration must be positive and include all cues.")

        output.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=output.parent) as temporary:
            root = Path(temporary)
            font_filter = ""
            if font_file and (args.preview or args.overlay):
                fonts = root / "fonts"
                fonts.mkdir()
                shutil.copyfile(font_file, fonts / font_file.name)
                font_filter = ":fontsdir=fonts"
            (root / "overlay.ass").write_text(ass_header(font) + "\n".join(events) + "\n", encoding="utf-8")
            handoff = {"preset": args.preset, "canvas": [1080, 1920], "fps": args.fps,
                       "duration": duration, "font": font, "layout": layout, "cues": timeline}
            if font_file:
                handoff["font_file"] = font_file.name
            write_json(root / "timeline.json", handoff)
            if sounds:
                render_audio(root, sounds, args.gain_db, duration)
            base = f"color=c=0x101820:s=1080x1920:r={args.fps}:d={duration}"
            if args.overlay:
                ffmpeg(root, ["-f", "lavfi", "-i", base + ",format=rgba,colorchannelmixer=aa=0",
                             "-vf", f"ass=overlay.ass{font_filter}:alpha=1",
                             "-c:v", "qtrle", "-pix_fmt", "argb", "overlay.mov"])
            if args.preview:
                preview_events = preview_background(args.preset, layout, duration) + events
                (root / "preview.ass").write_text(ass_header(font) + "\n".join(preview_events) + "\n", encoding="utf-8")
                audio = ["-i", "sfx.wav", "-map", "0:v", "-map", "1:a", "-c:a", "aac"] if sounds else ["-an"]
                ffmpeg(root, ["-f", "lavfi", "-i", base, *audio, "-vf", f"ass=preview.ass{font_filter}",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "preview.mp4"])
                (root / "preview.ass").unlink()
            output.mkdir()
            for child in root.iterdir():
                if child.is_file():
                    shutil.move(child, output / child.name)
        print(output)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"talking_head_presets: {error}\n")


if __name__ == "__main__":
    main()
