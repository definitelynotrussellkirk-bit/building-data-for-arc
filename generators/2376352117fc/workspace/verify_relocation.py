"""Exercise the final generator/Racket oracle with original-source reads denied.

Builds the repository's supported portable runtime in /tmp, copies the verified
Racket runtime there, and uses the existing Landlock wrapper (with /opt allowed
for the system Python environment). No source, venv or runtime tree is returned.
Only hash manifests, commands, guard logs and bounded probe evidence are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--racket-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--guard", choices=("landlock", "none"), default="landlock",
                    help="none checks relocation, but does NOT deny original-source reads")
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    tid = "2376352117fc"
    gp = root / f"generators/{tid}/generator.py"
    with tempfile.TemporaryDirectory(prefix="translation-isolated-") as temp:
        stage = Path(temp)
        prepare_runtime(Catalog(root), stage, tid)
        shutil.copy2(Path(__file__).with_name("probe_translation.py"), stage / "probe_translation.py")
        shutil.copytree(args.racket_root.resolve(), stage / "vendor/racket")
        guard_source = (root / "tools/deny_predecessor_reads.py").read_text()
        guard_source = guard_source.replace("'/usr', '/lib'", "'/opt', '/usr', '/lib'")
        (stage / "deny_reads.py").write_text(guard_source)
        (stage / "guard_probe.py").write_text('''import pathlib, runpy, sys
source = pathlib.Path(sys.argv.pop(1))
try:
    source.read_bytes()
except PermissionError:
    print("Original generator read denied:", source, flush=True)
else:
    raise AssertionError("Original generator remains readable")
sys.argv[0] = "probe_translation.py"
runpy.run_path("probe_translation.py", run_name="__main__")
''')
        command = [sys.executable, "-I", "deny_reads.py", sys.executable, "-I", "guard_probe.py", str(gp),
                   "--root", ".", "--out", "evidence", "--seeds", "8", "--racket", "--expect-improved"]
        if args.guard == "none":
            command = [sys.executable, "-I", "probe_translation.py", "--root", ".",
                       "--out", "evidence", "--seeds", "8", "--racket", "--expect-improved"]
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env["RACKET_PATH"] = str(stage / "vendor/racket/bin/racket")
        env["PATH"] = str(stage / "vendor/racket/bin") + os.pathsep + env.get("PATH", "")
        result = subprocess.run(command, cwd=stage, env=env, capture_output=True, text=True, timeout=180)
        (out / "stdout.log").write_text(result.stdout)
        (out / "stderr.log").write_text(result.stderr)
        shutil.copy2(stage / "RUNTIME_MANIFEST.json", out / "RUNTIME_MANIFEST.json")
        shutil.copy2(stage / "deny_reads.py", out / "deny_reads.py")
        shutil.copy2(stage / "guard_probe.py", out / "guard_probe.py")
        if (stage / "evidence").is_dir():
            shutil.copytree(stage / "evidence", out / "evidence")
        source_hash = hashlib.sha256(gp.read_bytes()).hexdigest()
        staged_hash = hashlib.sha256((stage / f"puzzle_generators/per_puzzle/{tid}/generator.py").read_bytes()).hexdigest()
        receipt = {"schema": "translation-relocation-v1", "guard_mode": args.guard, "runtime_directory": str(stage),
            "argv": command, "exit_code": result.returncode, "generator_sha256": source_hash,
            "staged_generator_sha256": staged_hash, "source_hash_matches": source_hash == staged_hash,
            "original_read_denied": "Original generator read denied:" in result.stdout,
            "landlock_enabled": "predecessor reads denied" in result.stdout,
            "isolated_python": True, "racket_runtime_copied": True,
            "allowlist_adjustment": ("/opt allowed for the preinstalled Python interpreter/dependencies; /mnt denied when Landlock starts"
                                     if args.guard == "landlock" else
                                     "none: no filesystem guard; original source remains readable")}
        (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))
        guard_ok = args.guard == "none" or receipt["original_read_denied"]
        return 0 if result.returncode == 0 and guard_ok and source_hash == staged_hash else 1


if __name__ == "__main__":
    raise SystemExit(main())
