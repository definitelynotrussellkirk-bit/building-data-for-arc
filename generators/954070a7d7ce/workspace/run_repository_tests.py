"""Run the complete repository suite in a disposable, importable environment.

The runtime intentionally removes PYTHONPATH and disables user site-packages
before launching children. Merely putting repo/src on the parent's import path
is therefore insufficient for packet fixtures. A fresh venv plus an explicit
source .pth preserves the real subprocess isolation without editing shared code
or installing into the caller's interpreter. The caller's dependency site-packages
are explicitly reused (nested venvs do not inherit them). No packages are downloaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sysconfig
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[3]


def clean_environment() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["TERM"] = "dumb"
    env["NO_COLOR"] = "1"
    return env


def prepare_interpreter(repo: Path, destination: Path) -> Path:
    """Expose only this repo's source in a new venv; reuse is prohibited."""
    repo = repo.resolve()
    if not (repo / "src/arcpuzzles/__init__.py").is_file():
        raise ValueError(f"Not an ARCpuzzles source tree: {repo}")
    if destination.exists():
        raise FileExistsError(destination)
    env = clean_environment()
    subprocess.run([sys.executable, "-m", "venv", "--without-pip",
                    "--system-site-packages", str(destination)],
                   check=True, env=env, timeout=60, capture_output=True, text=True)
    executable = destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    purelib = subprocess.check_output(
        [str(executable), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        env=env, text=True, timeout=30).strip()
    source = str(repo / "src")
    if "\n" in source or "\r" in source:
        raise ValueError("Source path must not contain a newline")
    (Path(purelib) / "00_arcpuzzles_review_source.pth").write_text(source + "\n")
    dependencies = sorted({sysconfig.get_path("purelib"), sysconfig.get_path("platlib")})
    if any("\n" in path or "\r" in path for path in dependencies):
        raise ValueError("Dependency path must not contain a newline")
    (Path(purelib) / "01_review_dependencies.pth").write_text("\n".join(dependencies) + "\n")
    return executable


def run(args: argparse.Namespace) -> int:
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "isolated-repository-tests-v1", "source_directory": str(REPO),
              "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "python": sys.version, "runs": [], "status": "running",
              "environment_policy": "fresh system-site venv; repo/src and parent dependency-site .pth files; PYTHONPATH absent; PYTHONNOUSERSITE=1",
              "runtime_retained": False, "dependency_sites": sorted({sysconfig.get_path("purelib"), sysconfig.get_path("platlib")})}
    report_path = output / "report.json"

    def save() -> None:
        report_path.write_text(json.dumps(report, indent=2) + "\n")

    try:
        with tempfile.TemporaryDirectory(prefix="arcpuzzles-repo-tests-") as temporary:
            report["runtime_directory"] = temporary
            executable = prepare_interpreter(REPO, Path(temporary) / "venv")
            env = clean_environment()
            commands = [
                ("import-probe", [str(executable), "-c",
                    "import arcpuzzles; print(arcpuzzles.__file__)"], Path(temporary)),
                ("repository", [str(executable), "-m", "pytest", "-q"], REPO),
                ("task", [str(executable), "-m", "pytest", "-q",
                    "generators/954070a7d7ce/tests"], REPO),
            ]
            for name, command, cwd in commands:
                started = time.monotonic()
                log = output / f"{name}.log"
                timed_out = False
                with log.open("w") as stream:
                    try:
                        completed = subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                                                   stderr=subprocess.STDOUT, timeout=args.timeout)
                        exit_code = completed.returncode
                    except subprocess.TimeoutExpired:
                        timed_out, exit_code = True, None
                report["runs"].append({"name": name, "cwd": str(cwd), "argv": command,
                    "exit_code": exit_code, "timed_out": timed_out,
                    "elapsed_seconds": round(time.monotonic() - started, 3), "log": log.name})
                save()
                print(f"{name}: exit={exit_code}; log={log}", flush=True)
            report["status"] = "pass" if all(r["exit_code"] == 0 for r in report["runs"]) else "fail"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
    finally:
        save()
    return 0 if report["status"] == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new evidence directory")
    parser.add_argument("--timeout", type=float, default=600, help="per-suite seconds")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
