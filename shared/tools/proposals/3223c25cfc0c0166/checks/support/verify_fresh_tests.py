"""Run focused tests with fresh Python dependencies and fresh replayed sources.

This wrapper exists so RESULTS can record a packet-relative invocation while
retaining the exact separate checkout cwd, dependency origins and test commands.
It never applies a patch and never imports the original review's puzzle code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-work", type=Path, required=True)
    parser.add_argument("--expected-generator-sha256", required=True)
    parser.add_argument("--racket", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fresh = args.fresh_work.resolve()
    repo = fresh / "repo"
    generator = repo / "generators/520fe6e64fb6/generator.py"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    receipt = {"schema": "arcpuzzles-fresh-focused-tests-v1", "status": "running",
               "fresh_work": str(fresh), "payload_cwd": str(repo), "commands": [],
               "expected_generator_sha256": args.expected_generator_sha256,
               "driver_sha256": sha(Path(__file__)), "driver_argv": sys.argv,
               "driver_cwd": str(Path.cwd()), "tests_run": False}
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    env["PYTHONNOUSERSITE"] = "1"
    env["RACKET_PATH"] = str(args.racket.absolute())
    env["PATH"] = str(args.racket.absolute().parent) + os.pathsep + env.get("PATH", "")

    def run(argv, name, cwd, run_env=env):
        completed = subprocess.run(argv, cwd=cwd, env=run_env, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log = out / f"{name}.log"
        log.write_text(completed.stdout)
        receipt["commands"].append({"argv": argv, "cwd": str(cwd),
                                    "exit_code": completed.returncode,
                                    "log": log.name, "log_sha256": sha(log)})
        if completed.returncode:
            raise RuntimeError(f"{name} failed with exit {completed.returncode}; see {log}")
        return completed.stdout

    try:
        actual = sha(generator)
        receipt["generator_sha256"] = actual
        if actual != args.expected_generator_sha256:
            raise ValueError("fresh generator differs from the verified final source")
        if (fresh / ".venv").exists():
            raise ValueError("fresh dependency environment already exists")
        run([sys.executable, "-m", "venv", "--system-site-packages", "--without-pip",
             str(fresh / ".venv")], "venv", fresh)
        python = str(fresh / ".venv/bin/python")
        run([sys.executable, "-m", "pip", "--python", python, "install", "--no-cache-dir",
             "pytest==9.1.1"], "dependencies", fresh)
        test_env = dict(env)
        test_env["PYTHONPATH"] = os.pathsep.join(str(repo / relative)
            for relative in ("shared/runtime", "src", "shared/tools"))
        probe = """import json, sys, pytest, numpy, PIL, reviewer_support, arcpuzzles
print(json.dumps({'python':sys.executable,'sys_path':sys.path,'pytest':pytest.__file__,
'numpy':numpy.__file__,'PIL':PIL.__file__,'reviewer_support':reviewer_support.__file__,
'arcpuzzles':arcpuzzles.__file__}))"""
        origins = json.loads(run([python, "-c", probe], "import-origins", repo, test_env))
        for key in ("reviewer_support", "arcpuzzles"):
            if not Path(origins[key]).resolve().is_relative_to(repo):
                raise ValueError(f"{key} imported outside fresh checkout")
        if not Path(origins["pytest"]).resolve().is_relative_to(fresh / ".venv"):
            raise ValueError("pytest did not come from the fresh dependency environment")
        receipt["import_origins"] = origins
        receipt["environment"] = {key: test_env[key] for key in
                                   ("PYTHONPATH", "PYTHONNOUSERSITE", "RACKET_PATH")}
        receipt["racket_binary_sha256"] = sha(args.racket)
        receipt["tests_run"] = True
        output = run([python, "-m", "pytest", "--import-mode=importlib",
                      "generators/520fe6e64fb6/tests", "-q",
                      "--junitxml=" + str(out / "junit.xml")], "pytest", repo, test_env)
        receipt["test_summary"] = output.strip().splitlines()[-1]
        receipt["junit_sha256"] = sha(out / "junit.xml")
        if sha(generator) != actual:
            raise ValueError("fresh generator changed during testing")
        receipt["status"] = "passed"
        print(json.dumps({"status": "passed", "generator_sha256": actual,
                          "test_summary": receipt["test_summary"]}))
        return 0
    except BaseException as exc:
        receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        (out / "result.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
