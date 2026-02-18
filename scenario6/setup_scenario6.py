#!/usr/bin/env python
"""Bootstrap Scenario 6 dependencies and configuration."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TORCH_INDEX_URL = "https://download.pytorch.org/whl/cu121"
PERSONAPLEX_REPO = "https://github.com/NVIDIA/personaplex.git"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


def repair_pip() -> None:
    """Ensure pip is functional, repairing via ensurepip if needed."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("pip appears broken; repairing via ensurepip...")
        run([sys.executable, "-m", "ensurepip", "--upgrade"])
        run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])


def ensure_venv(python_exe: str, venv_dir: Path, args: list[str]) -> int:
    if in_venv() or "--in-venv" in args:
        return 0

    if not venv_dir.exists():
        run([python_exe, "-m", "venv", str(venv_dir)])

    venv_python = venv_dir / "Scripts" / "python.exe" if os.name == "nt" else venv_dir / "bin" / "python"
    run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])

    rerun_args = [str(venv_python), __file__, "--in-venv"] + args
    return subprocess.call(rerun_args)


def ensure_env_file(env_example: Path, env_file: Path, hf_token: str | None) -> None:
    if not env_file.exists():
        shutil.copyfile(env_example, env_file)

    if hf_token:
        content = env_file.read_text(encoding="utf-8")
        updated = []
        replaced = False
        for line in content.splitlines():
            if line.startswith("HF_TOKEN="):
                updated.append(f"HF_TOKEN={hf_token}")
                replaced = True
            else:
                updated.append(line)
        if not replaced:
            updated.append(f"HF_TOKEN={hf_token}")
        env_file.write_text("\n".join(updated) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup Scenario 6 dependencies and .env")
    parser.add_argument("--python", default=sys.executable, help="Python executable to use")
    parser.add_argument("--venv-dir", default="venv", help="Virtual environment directory")
    parser.add_argument("--skip-torch", action="store_true", help="Skip installing PyTorch")
    parser.add_argument("--skip-moshi", action="store_true", help="Skip installing moshi package")
    parser.add_argument("--skip-requirements", action="store_true", help="Skip installing requirements.txt")
    parser.add_argument("--keep-clone", action="store_true", help="Keep the temporary personaplex clone")
    parser.add_argument("--hf-token", help="Optional Hugging Face token to write into .env")
    parser.add_argument("--in-venv", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if sys.version_info >= (3, 13):
        print("Python 3.13 is not supported by moshi/PersonaPlex.")
        print("Please use Python 3.10-3.12 (3.12 recommended) and re-run this script.")
        return 1

    repo_root = Path(__file__).resolve().parents[1]
    scenario_dir = repo_root / "scenario6"
    env_example = scenario_dir / ".env.example"
    env_file = scenario_dir / ".env"

    venv_dir = Path(args.venv_dir)
    if not venv_dir.is_absolute():
        venv_dir = repo_root / venv_dir

    if not args.in_venv:
        exit_code = ensure_venv(args.python, venv_dir, sys.argv[1:])
        if exit_code != 0:
            return exit_code
        if not in_venv():
            return 0

    if not shutil.which("git"):
        print("git is required to install the moshi package. Please install git and re-run.")
        return 1

    repair_pip()

    if not args.skip_torch:
        run([sys.executable, "-m", "pip", "install", "torch", "--index-url", TORCH_INDEX_URL])

    temp_dir = None
    try:
        if not args.skip_moshi:
            temp_dir = Path(tempfile.mkdtemp(prefix="personaplex-"))
            repo_dir = temp_dir / "personaplex"
            run(["git", "clone", PERSONAPLEX_REPO, str(repo_dir)])
            run([sys.executable, "-m", "pip", "install", str(repo_dir / "moshi" / ".")])

        if not args.skip_requirements:
            run([sys.executable, "-m", "pip", "install", "-r", str(scenario_dir / "requirements.txt")])

        ensure_env_file(env_example, env_file, args.hf_token)
    finally:
        if temp_dir and not args.keep_clone:
            shutil.rmtree(temp_dir, ignore_errors=True)

    print("Setup complete.")
    print("Next steps:")
    print("1) Set HF_TOKEN in scenario6/.env (if not set)")
    print("2) Accept the model license at https://huggingface.co/nvidia/personaplex-7b-v1")
    print("3) Run: python scenario6/app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
