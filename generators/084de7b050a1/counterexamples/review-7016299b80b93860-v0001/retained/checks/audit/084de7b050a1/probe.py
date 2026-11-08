from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import find_root, load_selected_generator  # noqa: E402

TASK_ID = "084de7b050a1"
ROOT = find_root(REPO)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def grid_sha(grid):
    body = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def attempt(label, *, seed=17, sample_index=3, difficulty="medium", overrides=None):
    overrides = dict(overrides or {})
    row = {
        "label": label,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
    }
    try:
        grid = GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)
        row.update(
            {
                "accepted": True,
                "shape": [len(grid), len(grid[0])],
                "grid_sha256": grid_sha(grid),
                "observed": GEN.observe_overrides(grid),
                "self_check": GEN.self_check(grid, difficulty=difficulty, meta={}),
            }
        )
    except Exception as exc:  # reproducibility record
        row.update({"accepted": False, "exception": type(exc).__name__, "message": str(exc)})
    return row


attempts = [
    attempt("baseline"),
    attempt("sample_index_bool_true", sample_index=True),
    attempt("sample_index_bool_false", sample_index=False),
    attempt("sample_index_negative", sample_index=-1),
    attempt("n_dots_bool_true", overrides={"n_dots": True}),
    attempt("n_dots_float_one", overrides={"n_dots": 1.0}),
    attempt("n_dots_string_one", overrides={"n_dots": "1"}),
]

payload = {
    "task_id": TASK_ID,
    "kind": "strict_scalar_contract_probe",
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "declared_rule_hash": getattr(GEN, "RULE_HASH", None),
    "command": ["python3", "review.py", "run", "python3", "../checks/audit/084de7b050a1/probe.py"],
    "payload_cwd": "repo",
    "attempts": attempts,
}
(HERE / "probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2, sort_keys=True))
