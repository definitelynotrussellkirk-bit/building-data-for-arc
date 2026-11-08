from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "acb1cae24892"
HERE = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
gen, source, generator_sha = load_selected_generator(TASK_ID, root=ROOT)


def call(*, seed, sample_index, difficulty=None, **overrides):
    return gen.generate(seed, sample_index, difficulty=difficulty, **overrides)


normal_args = {
    "seed": 41,
    "sample_index": 7,
    "difficulty": "medium",
    "n_colors": 2,
}
warm = call(**normal_args, palette_kind="warm")
cool = call(**normal_args, palette_kind="cool")
unknown = call(
    seed=0,
    sample_index=3,
    difficulty="easy",
    __override_contract_unknown_axis__=123,
)
degenerate_args = {
    "seed": 9,
    "sample_index": 2,
    "difficulty": "hard",
    "texture": "single_marker",
    "grid_h": 14,
    "grid_w": 14,
    "n_colors": 3,
}
degenerate = call(**degenerate_args)
try:
    call(seed=0, sample_index=3, difficulty="easy", grid_h=5)
except Exception as exc:  # exact advertised-domain rejection is the finding
    grid_h_5_error = {"type": type(exc).__name__, "message": str(exc)}
else:
    grid_h_5_error = None

racket_path = HERE / "racket.json"
racket = json.loads(racket_path.read_text(encoding="utf-8")) if racket_path.is_file() else None

record = {
    "schema": "arcpuzzles-audit-control-counterexample/1",
    "task_id": TASK_ID,
    "executed_rule_hash": racket.get("executed_rule_hash") if racket else None,
    "rule_text_sha256": racket.get("rule_text_sha256") if racket else None,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": generator_sha,
    "documented_domain": {
        "grid_h": "5..14",
        "grid_w": "5..14",
        "n_colors": "1..3",
        "palette_kind": "default|warm|cool|varied",
        "texture": "default|warm|cool|varied|single_marker|no_markers|markers_adjacent",
    },
    "normal_pair": {
        "base_call": normal_args,
        "warm_override": {"palette_kind": "warm"},
        "cool_override": {"palette_kind": "cool"},
        "warm_grid": warm,
        "cool_grid": cool,
        "identical": warm == cool,
        "warm_self_check": gen.self_check(warm, difficulty="medium", meta={}),
        "cool_self_check": gen.self_check(cool, difficulty="medium", meta={}),
        "input_file": "checks/audit/acb1cae24892/input.json",
        "racket_receipt": "checks/audit/acb1cae24892/racket.json",
        "actual_racket_output": (racket.get("results", [{}])[0].get("output") if racket else None),
        "racket_input_valid_output": (racket.get("results", [{}])[0].get("valid_output") if racket else None),
        "rival_output": None,
        "rival_reason": "This is an exact-control/API counterexample, not a rival-label claim.",
    },
    "unknown_key": {
        "call": {
            "seed": 0,
            "sample_index": 3,
            "difficulty": "easy",
            "overrides": {"__override_contract_unknown_axis__": 123},
        },
        "accepted": True,
        "grid": unknown,
        "self_check": gen.self_check(unknown, difficulty="easy", meta={}),
    },
    "degenerate_joint_override": {
        "call": degenerate_args,
        "grid": degenerate,
        "realized": {
            "grid_h": len(degenerate),
            "grid_w": len(degenerate[0]),
            "n_distinct_nonzero_colors": len({v for row in degenerate for v in row if v}),
        },
        "self_check_with_declared_texture": gen.self_check(
            degenerate, difficulty="hard", meta={"texture": "single_marker"}
        ),
        "belongs_to_documented_domain": True,
    },
    "advertised_grid_h_minimum": {
        "call": {
            "seed": 0,
            "sample_index": 3,
            "difficulty": "easy",
            "overrides": {"grid_h": 5},
        },
        "belongs_to_documented_domain": True,
        "error": grid_h_5_error,
    },
    "commands": [
        {
            "cwd": "WORK/repo",
            "argv": [
                "python3",
                "../checks/audit/acb1cae24892/build_reproducer.py",
            ],
            "note": "Executed through review.py run; runtime cwd is WORK/repo and script path is ../checks/audit/acb1cae24892/build_reproducer.py.",
        },
        {
            "cwd": "WORK/repo",
            "argv": [
                "python3", "-m", "arcpuzzles", "apply", TASK_ID,
                "--input", "../checks/audit/acb1cae24892/input.json",
                "--out", "../checks/audit/acb1cae24892/racket.json",
            ],
        },
    ],
}
(HERE / "control-counterexample.json").write_text(
    json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": generator_sha,
    "warm_equals_cool": warm == cool,
    "unknown_key_accepted": True,
    "degenerate_realized": record["degenerate_joint_override"]["realized"],
    "grid_h_5_error": grid_h_5_error,
}, sort_keys=True))
