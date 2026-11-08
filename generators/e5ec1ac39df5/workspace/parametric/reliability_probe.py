from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "e5ec1ac39df5"
ROOT = find_root(__file__)


def main() -> None:
    generator, path, digest = load_selected_generator(TASK, root=ROOT)
    failures = []
    draws = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(100):
            draws += 1
            try:
                grid = generator.generate(seed, seed, difficulty=difficulty)
                errors = generator.self_check(grid, difficulty=difficulty)
                if errors:
                    failures.append({"difficulty": difficulty, "seed": seed, "errors": errors})
            except Exception as exc:
                failures.append(
                    {
                        "difficulty": difficulty,
                        "seed": seed,
                        "exception": type(exc).__name__,
                        "message": str(exc),
                    }
                )
    report = {
        "schema": "arcpuzzles-bounded-generator-reliability-v1",
        "task_id": TASK,
        "generator_path": str(path.relative_to(ROOT)),
        "generator_sha256": digest,
        "draws": draws,
        "failures": failures,
        "passed": not failures,
    }
    out = ROOT.parent / "checks/e5ec1ac39df5-reliability/report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
