#!/usr/bin/env python3
"""Run the frozen and added task tests in a portable source-bound overlay.

The review packet stores portable ``scripts`` under ``shared/tools``, shared
runtime modules under ``shared/runtime``, and canonical data under
``shared/data``. This helper copies the selected generator and task tests into
an ephemeral staged layout, records their hashes, and runs pytest there without
modifying the frozen fixture or shared runtime.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve()
TASK_HOME = HERE.parent.parent
REPO = HERE.parents[3]
TASK_ID = TASK_HOME.name


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or [])
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-portable-") as tmp:
        overlay = Path(tmp)
        target = (
            overlay
            / "puzzle_generators"
            / "per_puzzle"
            / TASK_ID
            / "generator.py"
        )
        target.parent.mkdir(parents=True)
        namespace_init = (
            "from pkgutil import extend_path\n"
            "__path__ = extend_path(__path__, __name__)\n"
        )
        (overlay / "puzzle_generators" / "__init__.py").write_text(
            namespace_init
        )
        (overlay / "puzzle_generators" / "per_puzzle" / "__init__.py").write_text(
            namespace_init
        )
        (target.parent / "__init__.py").write_text("")
        shutil.copy2(TASK_HOME / "generator.py", target)
        (overlay / "scripts").symlink_to(
            REPO / "shared/tools", target_is_directory=True
        )

        portable_task = overlay / "task"
        portable_tests = portable_task / "tests"
        shutil.copytree(TASK_HOME / "tests", portable_tests)
        (portable_task / "data").symlink_to(
            REPO / "shared/data", target_is_directory=True
        )

        manifest = {
            "task_id": TASK_ID,
            "generator_sha256": _sha256(TASK_HOME / "generator.py"),
            "tests": {
                path.name: _sha256(path)
                for path in sorted((TASK_HOME / "tests").glob("test_*.py"))
            },
            "staged_generator": str(target),
            "staged_tests": str(portable_tests),
        }
        print(json.dumps(manifest, sort_keys=True))

        env = dict(os.environ)
        path_entries = [str(overlay), str(REPO / "shared/runtime")]
        if env.get("PYTHONPATH"):
            path_entries.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(path_entries)
        env.setdefault("TERM", "dumb")
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(portable_tests),
            *argv,
        ]
        completed = subprocess.run(
            command,
            cwd=portable_task,
            env=env,
            check=False,
        )
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
