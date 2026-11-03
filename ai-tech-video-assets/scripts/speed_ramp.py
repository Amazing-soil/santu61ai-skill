"""Render a silent B-roll asset with a continuous source-time speed curve."""

import argparse
import json
import math
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


PRESETS = {
    "flash-in": [(0, 1), (.46, 1), (.65, .55), (1, .55)],
    "jump-cut": [(0, 1), (.43, 1), (.50, 3), (.57, 1), (1, 1)],
    "bullet-time": [(0, 1), (.38, 1), (.46, .28), (.57, .28), (.66, 1), (1, 1)],
    "montage": [(0, 1), (.25, 1), (.43, 2.5), (.62, .45), (.72, 1), (1, 1)],
    "hero-moment": [(0, 1), (.28, 2.4), (.43, .35), (.57, .35), (.72, 2.1), (1, 1)],
}


def parse_points(value):
    try:
        points = [tuple(map(float, pair.split(":"))) for pair in value.split(",")]
        positions, speeds = zip(*points)
        valid = (
            2 <= len(points) <= 24
            and positions[0] == 0
            and positions[-1] == 1
            and all(a < b for a, b in zip(positions, positions[1:]))
            and all(.1 <= speed <= 8 for speed in speeds)
        )
    except ValueError:
        valid = False
    if not valid:
        raise argparse.ArgumentTypeError(
            "Use 2–24 position:speed pairs, increasing positions from 0 to 1, speeds from 0.1 to 8."
        )
    return points


def source_duration(path):
    info = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=duration:format=duration", "-of", "json", str(path),
    ]))
    if not info.get("streams"):
        raise ValueError("Input has no video stream.")
    for duration in (info["streams"][0].get("duration"), info.get("format", {}).get("duration")):
        if duration not in (None, "N/A") and float(duration) > 0:
            return float(duration)
    raise ValueError("Input video duration is unavailable.")


def timing(points, duration):
    # Integrate dt / speed(t) over each source interval. Each interval meets
    # its neighbor with the same accumulated output time and playback speed.
    elapsed = 0.0
    keyframes = [{"source_offset": 0, "speed": points[0][1], "output_offset": 0}]
    terms = []
    for (left, start_speed), (right, end_speed) in zip(points, points[1:]):
        start = left * duration
        width = (right - left) * duration
        slope = (end_speed - start_speed) / width
        delta = f"(T-{start:.12g})"
        if abs(end_speed - start_speed) < 1e-8:
            term = f"{delta}/{start_speed:.12g}"
            length = width / start_speed
        else:
            term = f"log(1+({slope / start_speed:.12g})*{delta})/({slope:.12g})"
            length = math.log1p((end_speed - start_speed) / start_speed) / slope
        terms.append((right * duration, f"({elapsed:.12g}+{term})"))
        elapsed += length
        keyframes.append({"source_offset": right * duration, "speed": end_speed, "output_offset": elapsed})

    expression = terms[-1][1]
    for end, term in reversed(terms[:-1]):
        expression = f"if(lt(T,{end:.12g}),{term},{expression})"
    return expression, keyframes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    curves = parser.add_mutually_exclusive_group(required=True)
    curves.add_argument("--preset", choices=PRESETS)
    curves.add_argument("--points", type=parse_points, help="E.g. 0:1,0.4:1,0.5:0.3,1:1")
    parser.add_argument("--start", type=float, default=0, help="Source start in seconds")
    parser.add_argument("--end", type=float, help="Source end in seconds, default to stream duration")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--plan-only", action="store_true", help="Print timing JSON without rendering")
    args = parser.parse_args()

    try:
        source = args.input.resolve(strict=True)
        full_duration = source_duration(source)
        end = args.end if args.end is not None else full_duration
        if not (0 <= args.start < end <= full_duration + .001 and 1 <= args.fps <= 120):
            raise ValueError("Select a valid source range and an FPS between 1 and 120.")
        points = PRESETS[args.preset] if args.preset else args.points
        expression, keyframes = timing(points, end - args.start)
        frames = max(1, round(keyframes[-1]["output_offset"] * args.fps))
        if not args.plan_only:
            if not args.output or args.output.suffix.lower() != ".mp4":
                raise ValueError("Specify an MP4 output, or use --plan-only.")
            output = args.output.resolve()
            if output.exists():
                raise ValueError(f"Output already exists: {output}")
            filters = (
                f"setpts=PTS-STARTPTS,trim=start={args.start:.12g}:end={end:.12g},"
                f"settb=AVTB,setpts=PTS-STARTPTS,setpts='{expression}/TB',"
                f"tpad=stop=-1:stop_mode=clone,fps={args.fps},"
                "pad=ceil(iw/2)*2:ceil(ih/2)*2"
            )
            with TemporaryDirectory(dir=output.parent) as temporary:
                rendered = Path(temporary) / "render.mp4"
                subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-abort_on", "empty_output",
                    "-i", str(source), "-map", "0:v:0", "-an", "-vf", filters,
                    "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(rendered),
                ], check=True)
                # Exclusive publication on the same volume avoids replacing an existing asset.
                output.hardlink_to(rendered)

        print(json.dumps({
            "preset": args.preset, "source_start": args.start, "source_end": end,
            "fps": args.fps, "output_frames": frames, "output_duration": frames / args.fps,
            "keyframes": keyframes,
        }, indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"speed_ramp: {error}\n")


if __name__ == "__main__":
    main()
