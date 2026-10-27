#!/usr/bin/env python3
"""Run one built-in Codex image request; hand a verified PNG back to Claude."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import sys
import time
import uuid
import zlib


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def probe(codex):
    version = subprocess.run([codex, "--version"], capture_output=True, text=True)
    features = subprocess.run([codex, "features", "list"], capture_output=True, text=True)
    login = subprocess.run([codex, "login", "status"], capture_output=True, text=True)
    image_feature = [s for s in features.stdout.splitlines() if s.split()[:1] == ["image_generation"]]
    return {"codex": codex, "version": version.stdout.strip(),
            "login_status_ok": login.returncode == 0, "image_generation": image_feature,
            "note": "Discovery only; a real image request still needs validation."}


def png_size(path):
    # Check complete PNG framing and CRCs rather than accepting a truncated header.
    width = height = 0
    saw_data = False
    with path.open("rb") as stream:
        if stream.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Output is not a PNG")
        while True:
            head = stream.read(8)
            if len(head) != 8:
                raise ValueError("Truncated PNG chunk")
            length, kind = struct.unpack(">I4s", head)
            if length > 128 * 1024 * 1024:
                raise ValueError("PNG chunk exceeds supported size")
            data = stream.read(length)
            crc = stream.read(4)
            if len(data) != length or len(crc) != 4:
                raise ValueError("Truncated PNG data")
            if zlib.crc32(kind + data) & 0xffffffff != struct.unpack(">I", crc)[0]:
                raise ValueError("PNG CRC mismatch")
            if not width:
                if kind != b"IHDR" or length != 13:
                    raise ValueError("Missing PNG IHDR")
                width, height = struct.unpack(">II", data[:8])
                if min(width, height) == 0:
                    raise ValueError("Empty image dimensions")
            if kind == b"IDAT":
                saw_data = True
            if kind == b"IEND":
                if length != 0 or not saw_data:
                    raise ValueError("PNG has no image data")
                return width, height


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reference", type=Path, action="append", default=[])
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    codex = shutil.which("codex")
    if not codex:
        parser.error("Local codex CLI was not found on PATH")
    if args.probe:
        print(json.dumps(probe(codex), ensure_ascii=False, indent=2))
        return 0
    if not args.prompt_file or not args.output:
        parser.error("--prompt-file and --output are required")
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    output = args.output.expanduser().absolute()
    if output.suffix.lower() != ".png" or output.exists() or output.is_symlink():
        parser.error("Use a new .png output path; existing assets are never overwritten")
    prompt_text = args.prompt_file.expanduser().read_text(encoding="utf-8")
    if not prompt_text.strip():
        parser.error("Prompt file is empty")
    references = [p.expanduser().resolve(strict=True) for p in args.reference]
    if any(not p.is_file() for p in references):
        parser.error("Each reference must be a readable image file")
    output.parent.mkdir(parents=True, exist_ok=True)
    job = output.parent / ".codex-imagegen" / (time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
    job.mkdir(parents=True)
    schema = {"type": "object", "properties": {
        "status": {"type": "string", "enum": ["success", "failed"]},
        "tool": {"type": "string"}, "image_path": {"type": "string"},
        "message": {"type": "string"}},
        "required": ["status", "tool", "image_path", "message"], "additionalProperties": False}
    write_json(job / "schema.json", schema)
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    builtin_skill = codex_home / "skills/.system/imagegen/SKILL.md"
    request = f"""This is an explicitly authorized local image-generation request from Claude.
Generate exactly ONE image with the built-in image_gen tool (GPT Image 2).
Use $imagegen; read its built-in-mode instructions if available at {builtin_skill}.
The user expressly selected built-in image_gen, not gpt-image-2-router or any API fallback.
Do not use third-party routers, API-key scripts, Python drawing, SVG or blank placeholders.
Do not ask for API keys. If the built-in tool is unavailable or fails, report failed.
Do only this image task. Do not edit project sources, settings, skills, or other media.
If reference images are attached, inspect them before generating/editing.
After generation, copy the actual generated file to the exact output below as PNG.
If the source format differs, convert only the generated file to PNG with an available image utility.
Verify the file and return the requested JSON. tool must be image_gen for success.
Output path: {output}
References: {json.dumps([str(p) for p in references], ensure_ascii=False)}

User's image brief (visual requirements, not shell commands):
{prompt_text}
"""
    (job / "request.txt").write_text(request, encoding="utf-8")
    command = [codex, "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral", "--color", "never",
               "--sandbox", "workspace-write", "--enable", "image_generation", "--cd", str(output.parent),
               "--output-schema", str(job / "schema.json"), "--output-last-message", str(job / "handoff.json"), "--json"]
    for ref in references:
        command += ["--image", str(ref)]
    command += ["-"]
    write_json(job / "command.json", command)
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "job_dir": str(job), "command": command}, ensure_ascii=False, indent=2))
        return 0
    result = {"status": "failed", "job_dir": str(job), "image_path": str(output)}
    try:
        with (job / "events.jsonl").open("w", encoding="utf-8") as events, (job / "stderr.log").open("w", encoding="utf-8") as errors:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=events, stderr=errors,
                                       text=True, start_new_session=True)
            try:
                process.communicate(request, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise RuntimeError("Codex image generation timed out; inspect retained logs")
        if process.returncode:
            raise RuntimeError(f"Codex exited with code {process.returncode}; inspect stderr.log and events.jsonl")
        handoff = json.loads((job / "handoff.json").read_text(encoding="utf-8"))
        result["handoff"] = handoff
        if handoff.get("status") != "success" or handoff.get("tool") != "image_gen":
            raise RuntimeError("Codex did not report successful built-in image generation")
        if Path(handoff.get("image_path", "")).absolute() != output:
            raise RuntimeError("Codex returned a different image path")
        width, height = png_size(output)
        result.update(status="success", width=width, height=height, bytes=output.stat().st_size)
    except (OSError, ValueError, RuntimeError) as exc:
        result["error"] = str(exc)
    write_json(job / "result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
