#!/usr/bin/env python3
"""Run this generator's focused pytest file in a portable runtime overlay."""
from __future__ import annotations

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
TEST_FILE = TASK_HOME / "tests" / f"test_generator_{TASK_ID}.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-tests-") as tmp:
        overlay = Path(tmp)
        target = (
            overlay
            / "puzzle_generators"
            / "per_puzzle"
            / TASK_ID
            / "generator.py"
        )
        target.parent.mkdir(parents=True)
        namespace_init = "from pkgutil import extend_path\n__path__ = extend_path(__path__, __name__)\n"
        (overlay / "puzzle_generators" / "__init__.py").write_text(namespace_init)
        (overlay / "puzzle_generators" / "per_puzzle" / "__init__.py").write_text(
            namespace_init
        )
        (target.parent / "__init__.py").write_text("")
        shutil.copy2(TASK_HOME / "generator.py", target)
        (overlay / "scripts").symlink_to(REPO / "shared/tools", target_is_directory=True)
        env = dict(os.environ)
        path_entries = [str(overlay), str(REPO / "shared/runtime")]
        if env.get("PYTHONPATH"):
            path_entries.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(path_entries)
        env.setdefault("TERM", "dumb")
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(TEST_FILE)],
            cwd=REPO,
            env=env,
            check=False,
        )
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
