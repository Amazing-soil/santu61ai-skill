#!/usr/bin/env python3
"""Single-job, GPU-only runtime guard for Douyin copy extraction."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR = Path(
    os.environ.get(
        "DOUYIN_COPY_EXTRACTOR_STATE_DIR",
        Path.home() / ".cache" / "douyin-copy-extractor",
    )
).expanduser()
ACTIVE_DIR = STATE_DIR / "active"
OWNER_FILE = ACTIVE_DIR / "owner.json"
JOB_PREFIX = "douyin-copy-extractor-"

TOP_LEVEL_FIELDS = {"basic_info", "publish_copy", "corrected_transcript"}
BASIC_INFO_FIELDS = {
    "platform",
    "author",
    "duration",
    "work_id",
    "source_url",
}


class PipelineError(RuntimeError):
    pass


def dump_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_owner() -> dict[str, Any]:
    if not OWNER_FILE.is_file():
        raise PipelineError("没有可用的活动任务；请先执行 begin。")
    try:
        value = json.loads(OWNER_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"活动锁损坏：{exc}") from exc
    if not isinstance(value, dict):
        raise PipelineError("活动锁格式错误。")
    return value


def require_owner(token: str) -> dict[str, Any]:
    owner = read_owner()
    if owner.get("token") != token:
        raise PipelineError("token 与当前活动任务不匹配。")
    return owner


def job_dir_for(owner: dict[str, Any]) -> Path:
    raw = owner.get("job_dir")
    if not isinstance(raw, str) or not raw:
        raise PipelineError("活动锁缺少 job_dir。")
    job_dir = Path(raw).expanduser().resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if job_dir.parent != temp_root or not job_dir.name.startswith(JOB_PREFIX):
        raise PipelineError(f"拒绝清理非受控目录：{job_dir}")
    return job_dir


def path_in_job(owner: dict[str, Any], value: str, *, must_exist: bool) -> Path:
    job_dir = job_dir_for(owner)
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = job_dir / path
    path = path.resolve()
    if path != job_dir and job_dir not in path.parents:
        raise PipelineError(f"文件必须位于当前 job_dir：{job_dir}")
    if must_exist and not path.is_file():
        raise PipelineError(f"文件不存在：{path}")
    return path


def cleanup(owner: dict[str, Any]) -> None:
    job_dir = job_dir_for(owner)
    cleanup_errors: list[str] = []
    try:
        if job_dir.exists():
            shutil.rmtree(job_dir)
    except OSError as exc:
        cleanup_errors.append(f"删除 job_dir 失败：{exc}")
    try:
        if ACTIVE_DIR.exists():
            shutil.rmtree(ACTIVE_DIR)
    except OSError as exc:
        cleanup_errors.append(f"释放任务锁失败：{exc}")
    if cleanup_errors:
        raise PipelineError("；".join(cleanup_errors))


def command_begin(args: argparse.Namespace) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + args.wait_seconds
    while True:
        try:
            ACTIVE_DIR.mkdir()
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                owner = read_owner()
                raise PipelineError(
                    "已有视频正在处理，严格单并发已阻止本任务。"
                    f" started_at={owner.get('started_at', 'unknown')}"
                )
            time.sleep(1)

    token = uuid.uuid4().hex
    try:
        job_dir = Path(tempfile.mkdtemp(prefix=JOB_PREFIX)).resolve()
        owner = {
            "token": token,
            "job_dir": str(job_dir),
            "started_at": utc_now(),
            "source": args.source,
        }
        OWNER_FILE.write_text(
            json.dumps(owner, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        shutil.rmtree(ACTIVE_DIR, ignore_errors=True)
        raise

    dump_json(owner)
    return 0


def probe_mlx() -> dict[str, Any]:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise PipelineError("当前设备不是 Apple Silicon。")
    try:
        import mlx.core as mx
        import mlx_whisper  # noqa: F401
    except ImportError as exc:
        raise PipelineError(
            "Apple Silicon GPU 可用，但缺少 mlx-whisper；安装：python3 -m pip install mlx-whisper"
        ) from exc

    mx.set_default_device(mx.gpu)
    check = mx.sum(mx.ones((1024, 1024), dtype=mx.float16))
    mx.eval(check)
    info = mx.device_info(mx.gpu)
    return {
        "available": True,
        "engine": "mlx-whisper",
        "device": "Metal GPU",
        "device_info": info,
        "default_model": "mlx-community/whisper-large-v3-turbo",
    }


def probe_cuda() -> dict[str, Any]:
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        raise PipelineError("未检测到 NVIDIA GPU。")
    try:
        import ctranslate2
        import faster_whisper  # noqa: F401
    except ImportError as exc:
        raise PipelineError(
            "检测到 NVIDIA GPU，但缺少 faster-whisper/CTranslate2；安装：python3 -m pip install faster-whisper"
        ) from exc
    if ctranslate2.get_cuda_device_count() < 1:
        raise PipelineError("CTranslate2 未检测到可用 CUDA 设备。")
    name = subprocess.run(
        [nvidia_smi, "--query-gpu=name,memory.total", "--format=csv,noheader"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "available": True,
        "engine": "faster-whisper",
        "device": "CUDA GPU",
        "device_info": name,
        "default_model": "large-v3",
    }


def select_gpu(engine: str) -> dict[str, Any]:
    failures: list[str] = []
    probes = []
    if engine in {"auto", "mlx"}:
        probes.append(probe_mlx)
    if engine in {"auto", "cuda"}:
        probes.append(probe_cuda)
    for probe in probes:
        try:
            return probe()
        except PipelineError as exc:
            failures.append(str(exc))
    raise PipelineError(
        "GPU 硬门槛未满足，已拒绝 CPU 降级。" + " | ".join(failures)
    )


def command_probe(args: argparse.Namespace) -> int:
    dump_json(select_gpu(args.engine))
    return 0


def normalize_audio(media: Path, wav: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PipelineError("缺少 ffmpeg；macOS 安装：brew install ffmpeg")
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(media),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise PipelineError(f"ffmpeg 音轨规范化失败：{result.stderr.strip()}")


def segment_payload(segment: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "start": round(float(segment.start), 3),
        "end": round(float(segment.end), 3),
        "text": str(segment.text).strip(),
    }
    for name in ("avg_logprob", "no_speech_prob"):
        attr = getattr(segment, name, None)
        if attr is not None:
            value[name] = round(float(attr), 5)
    return value


def transcribe_mlx(wav: Path, model_name: str, language: str) -> dict[str, Any]:
    import mlx.core as mx
    import mlx_whisper

    mx.set_default_device(mx.gpu)
    result = mlx_whisper.transcribe(
        str(wav),
        path_or_hf_repo=model_name,
        language=language,
        word_timestamps=True,
    )
    segments = []
    for segment in result.get("segments", []):
        item = {
            "start": round(float(segment.get("start", 0.0)), 3),
            "end": round(float(segment.get("end", 0.0)), 3),
            "text": str(segment.get("text", "")).strip(),
        }
        for name in ("avg_logprob", "no_speech_prob"):
            if segment.get(name) is not None:
                item[name] = round(float(segment[name]), 5)
        segments.append(item)
    return {
        "engine": "mlx-whisper",
        "device": "Metal GPU",
        "model": model_name,
        "language": result.get("language", language),
        "text": str(result.get("text", "")).strip(),
        "segments": segments,
    }


def transcribe_cuda(wav: Path, model_name: str, language: str) -> dict[str, Any]:
    from faster_whisper import WhisperModel

    model = WhisperModel(
        model_name,
        device="cuda",
        compute_type="float16",
        num_workers=1,
    )
    segment_iter, info = model.transcribe(
        str(wav),
        language=language,
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
        condition_on_previous_text=True,
    )
    segments = [segment_payload(segment) for segment in segment_iter]
    return {
        "engine": "faster-whisper",
        "device": "CUDA GPU FP16",
        "model": model_name,
        "language": getattr(info, "language", language),
        "language_probability": round(
            float(getattr(info, "language_probability", 0.0)), 5
        ),
        "text": "".join(item["text"] for item in segments).strip(),
        "segments": segments,
    }


def command_transcribe(args: argparse.Namespace) -> int:
    owner = require_owner(args.token)
    media = path_in_job(owner, args.media, must_exist=True)
    gpu = select_gpu(args.engine)
    job_dir = job_dir_for(owner)
    with tempfile.TemporaryDirectory(prefix="asr-", dir=job_dir) as work:
        wav = Path(work) / "normalized.wav"
        normalize_audio(media, wav)
        if gpu["engine"] == "mlx-whisper":
            result = transcribe_mlx(wav, args.mlx_model, args.language)
        else:
            result = transcribe_cuda(wav, args.cuda_model, args.language)
    dump_json(result)
    return 0


def load_and_validate_record(owner: dict[str, Any], record_value: str) -> dict[str, Any]:
    record_path = path_in_job(owner, record_value, must_exist=True)
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"record.json 读取失败：{exc}") from exc
    if not isinstance(record, dict):
        raise PipelineError("最终记录必须是 JSON object。")
    fields = set(record)
    if fields != TOP_LEVEL_FIELDS:
        raise PipelineError(
            f"最终记录顶层字段必须恰好是 {sorted(TOP_LEVEL_FIELDS)}，当前为 {sorted(fields)}。"
        )
    basic = record["basic_info"]
    if not isinstance(basic, dict) or set(basic) != BASIC_INFO_FIELDS:
        raise PipelineError(
            f"basic_info 字段必须恰好是 {sorted(BASIC_INFO_FIELDS)}。"
        )
    for key, value in basic.items():
        if not isinstance(value, str) or not value.strip():
            raise PipelineError(f"basic_info.{key} 必须是非空字符串。")
    if basic["platform"] != "抖音":
        raise PipelineError("basic_info.platform 必须是“抖音”。")
    if not basic["work_id"].isdigit():
        raise PipelineError("basic_info.work_id 必须是纯数字作品 ID。")
    if not basic["source_url"].startswith("https://www.douyin.com/video/"):
        raise PipelineError("basic_info.source_url 必须是标准抖音作品 URL。")
    for key in ("publish_copy", "corrected_transcript"):
        value = record[key]
        if not isinstance(value, str) or not value.strip():
            raise PipelineError(f"{key} 必须是非空字符串。")
    if len(record["corrected_transcript"].strip()) < 20:
        raise PipelineError("corrected_transcript 过短，请检查是否完整。")
    serialized = json.dumps(record, ensure_ascii=False)
    forbidden = ("file://", str(job_dir_for(owner)), JOB_PREFIX)
    if any(marker in serialized for marker in forbidden):
        raise PipelineError("最终记录包含本地临时路径，拒绝输出。")
    return record


def command_validate(args: argparse.Namespace) -> int:
    owner = require_owner(args.token)
    dump_json(load_and_validate_record(owner, args.record))
    return 0


def command_finish(args: argparse.Namespace) -> int:
    owner = require_owner(args.token)
    record = load_and_validate_record(owner, args.record)
    cleanup(owner)
    dump_json(record)
    return 0


def command_abort(args: argparse.Namespace) -> int:
    owner = require_owner(args.token)
    cleanup(owner)
    dump_json({"aborted": True, "temporary_files_removed": True})
    return 0


def command_status(_: argparse.Namespace) -> int:
    if not ACTIVE_DIR.exists():
        dump_json({"active": False})
        return 0
    owner = read_owner()
    dump_json(
        {
            "active": True,
            "started_at": owner.get("started_at"),
            "job_dir": owner.get("job_dir"),
            "source": owner.get("source"),
        }
    )
    return 0


def command_recover(args: argparse.Namespace) -> int:
    owner = read_owner()
    started_raw = owner.get("started_at")
    if not isinstance(started_raw, str):
        raise PipelineError("活动锁缺少 started_at，拒绝自动恢复。")
    try:
        started = datetime.fromisoformat(started_raw)
    except ValueError as exc:
        raise PipelineError("started_at 格式错误，拒绝自动恢复。") from exc
    age = (datetime.now(timezone.utc) - started).total_seconds()
    if age < args.older_than_seconds:
        raise PipelineError(
            f"活动任务仅存在 {int(age)} 秒，未达到恢复阈值 {args.older_than_seconds} 秒。"
        )
    cleanup(owner)
    dump_json({"recovered": True, "temporary_files_removed": True, "age": int(age)})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="抖音文案提取：全局单任务锁、GPU 转写和临时文件清理。"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    begin = sub.add_parser("begin", help="创建单条任务并获取全局锁")
    begin.add_argument("--source", required=True, help="抖音分享文本或链接")
    begin.add_argument("--wait-seconds", type=int, default=0)
    begin.set_defaults(func=command_begin)

    probe = sub.add_parser("probe", help="检查 GPU 硬门槛")
    probe.add_argument("--engine", choices=("auto", "mlx", "cuda"), default="auto")
    probe.set_defaults(func=command_probe)

    transcribe = sub.add_parser("transcribe", help="在 GPU 上转写 job_dir 内的媒体")
    transcribe.add_argument("--token", required=True)
    transcribe.add_argument("--media", required=True)
    transcribe.add_argument("--language", default="zh")
    transcribe.add_argument("--engine", choices=("auto", "mlx", "cuda"), default="auto")
    transcribe.add_argument(
        "--mlx-model", default="mlx-community/whisper-large-v3-turbo"
    )
    transcribe.add_argument("--cuda-model", default="large-v3")
    transcribe.set_defaults(func=command_transcribe)

    validate = sub.add_parser("validate", help="校验只含文案的最终 JSON")
    validate.add_argument("--token", required=True)
    validate.add_argument("--record", required=True)
    validate.set_defaults(func=command_validate)

    finish = sub.add_parser("finish", help="最终校验、清理临时文件并释放锁")
    finish.add_argument("--token", required=True)
    finish.add_argument("--record", required=True)
    finish.set_defaults(func=command_finish)

    abort = sub.add_parser("abort", help="中止任务、清理临时文件并释放锁")
    abort.add_argument("--token", required=True)
    abort.set_defaults(func=command_abort)

    status = sub.add_parser("status", help="查看是否有活动任务")
    status.set_defaults(func=command_status)

    recover = sub.add_parser("recover", help="清理已超过阈值的异常遗留任务")
    recover.add_argument("--older-than-seconds", type=int, default=7200)
    recover.set_defaults(func=command_recover)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (PipelineError, OSError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
