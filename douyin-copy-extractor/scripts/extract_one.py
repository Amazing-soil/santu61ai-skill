#!/usr/bin/env python3
"""Extract one Douyin video's metadata/audio and run the locked GPU ASR step."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


ALLOWED_DOMAINS = (
    "v.douyin.com,douyin.com,*.douyin.com,*.douyinvod.com,*.douyinpic.com"
)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36"
)
META_JS = r"""
(() => {
  const heading = document.querySelector('h1') || document.querySelector('h2');
  let node = heading;
  const candidates = [];
  for (let depth = 0; node && depth < 8; depth += 1, node = node.parentElement) {
    for (const anchor of node.querySelectorAll('a')) {
      const value = (anchor.innerText || '').trim();
      if (value && !candidates.includes(value)) candidates.push(value);
    }
  }
  const videos = Array.from(document.querySelectorAll('video'));
  const duration = Math.max(0, ...videos.map(v => Number.isFinite(v.duration) ? v.duration : 0));
  return JSON.stringify({
    url: location.href,
    publish_copy: (heading?.innerText || '').trim(),
    duration,
    author_candidates: candidates.slice(0, 30)
  });
})()
"""


class ExtractError(RuntimeError):
    pass


def browser_command(session: str, *parts: str, stdin: str | None = None) -> str:
    env = os.environ.copy()
    env["AGENT_BROWSER_CONTENT_BOUNDARIES"] = "0"
    env["AGENT_BROWSER_ALLOWED_DOMAINS"] = ALLOWED_DOMAINS
    result = subprocess.run(
        ["npx", "--yes", "agent-browser", "--session", session, *parts],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise ExtractError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def close_browser(session: str) -> None:
    try:
        browser_command(session, "close")
    except Exception:
        pass


def parse_eval(output: str) -> dict[str, Any]:
    try:
        value: Any = json.loads(output)
        if isinstance(value, str):
            value = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ExtractError(f"无法解析页面元数据：{output[:300]}") from exc
    if not isinstance(value, dict):
        raise ExtractError("页面元数据不是 JSON object。")
    return value


def pick_author(candidates: list[Any], publish_copy: str) -> str:
    rejected = (
        "登录",
        "关注",
        "抖音",
        "推荐",
        "展开",
        "用户协议",
        "隐私政策",
        "个人观点",
        "仅供参考",
    )
    for item in candidates:
        value = str(item).strip()
        if not value or value.startswith("#") or value == publish_copy:
            continue
        if len(value) > 40 or any(word in value for word in rejected):
            continue
        return value
    return "未知"


def get_media_url(session: str, work_id: str) -> str:
    for attempt in range(3):
        raw = browser_command(session, "network", "requests", "--json")
        try:
            payload = json.loads(raw)
            requests = payload["data"]["requests"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ExtractError("无法解析浏览器网络请求。") from exc
        audio_urls = [
            item.get("url", "")
            for item in requests
            if item.get("mimeType") == "video/mp4"
            and "media-audio" in item.get("url", "")
        ]
        if audio_urls:
            return audio_urls[-1]
        video_urls = [
            item.get("url", "")
            for item in requests
            if item.get("mimeType") == "video/mp4"
            and "media-video" in item.get("url", "")
        ]
        if video_urls:
            return video_urls[-1]
        progressive_urls = [
            item.get("url", "")
            for item in requests
            if item.get("mimeType") == "video/mp4"
            and ".douyinvod.com/" in item.get("url", "")
            and "media-audio" not in item.get("url", "")
        ]
        matching = [url for url in progressive_urls if f"__vid={work_id}" in url]
        if matching:
            return matching[-1]
        if progressive_urls:
            return progressive_urls[-1]
        if attempt < 2:
            browser_command(session, "wait", "4000")
    raise ExtractError("未发现主视频媒体请求。")


def download_audio(url: str, canonical_url: str, target: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"Referer": canonical_url, "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
    if target.stat().st_size < 1024:
        raise ExtractError("下载的音频文件异常过小。")


def ffprobe_duration(media: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(media),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def duration_label(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    return f"{total // 60:02d}:{total % 60:02d}"


def run_asr(token: str, media: Path, output: Path) -> None:
    pipeline = Path(__file__).with_name("pipeline.py")
    with output.open("w", encoding="utf-8") as stream:
        result = subprocess.run(
            [
                sys.executable,
                str(pipeline),
                "transcribe",
                "--token",
                token,
                "--media",
                str(media),
                "--language",
                "zh",
            ],
            stdout=stream,
            text=True,
        )
    if result.returncode != 0:
        raise ExtractError("GPU 转写失败。")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--job-dir", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--fallback-copy", default="")
    args = parser.parse_args()

    job_dir = Path(args.job_dir).expanduser().resolve()
    if not job_dir.is_dir() or not job_dir.name.startswith("douyin-copy-extractor-"):
        raise ExtractError("job_dir 不是受控抖音提取任务目录。")
    audio = job_dir / "media.mp4"
    raw_asr = job_dir / "raw_asr.json"

    try:
        browser_command(args.session, "open", args.url)
        browser_command(args.session, "wait", "6000")
        metadata = parse_eval(browser_command(args.session, "eval", "--stdin", stdin=META_JS))
        canonical = str(metadata.get("url", ""))
        match = re.fullmatch(r"https://www\.douyin\.com/video/(\d+)", canonical)
        if not match:
            raise ExtractError(f"未解析到标准抖音作品 URL：{canonical}")
        # Reopen the canonical detail page so the player consistently emits
        # its separate DASH audio request after a short-link redirect.
        browser_command(args.session, "open", canonical)
        browser_command(args.session, "wait", "6000")
        metadata = parse_eval(browser_command(args.session, "eval", "--stdin", stdin=META_JS))
        publish_copy = str(metadata.get("publish_copy", "")).strip() or args.fallback_copy.strip()
        if not publish_copy:
            raise ExtractError("页面缺少发布文案。")
        audio_url = get_media_url(args.session, match.group(1))
        download_audio(audio_url, canonical, audio)
        actual_duration = ffprobe_duration(audio)
        run_asr(args.token, audio, raw_asr)
        raw = json.loads(raw_asr.read_text(encoding="utf-8"))
        result = {
            "basic_info": {
                "platform": "抖音",
                "author": pick_author(
                    list(metadata.get("author_candidates", [])), publish_copy
                ),
                "duration": duration_label(
                    actual_duration or float(metadata.get("duration", 0.0))
                ),
                "work_id": match.group(1),
                "source_url": canonical,
            },
            "publish_copy": publish_copy,
            "raw_transcript": str(raw.get("text", "")).strip(),
            "segment_count": len(raw.get("segments", [])),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        close_browser(args.session)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExtractError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
