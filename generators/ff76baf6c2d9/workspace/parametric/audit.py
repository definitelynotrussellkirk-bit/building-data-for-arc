"""Source-bound protected-Racket audit for the ff76baf6c2d9 family.

This is reviewer evidence, not acceptance.  It replays the exact native
qualification, tests a finite named shortcut family on demonstrations only,
and emits one wrong-intermediate causal witness whose reported labels are
executed by the protected Racket backend.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "ff76baf6c2d9"
PARAMETRIC_HOME = Path(__file__).resolve().parent
ROOT = PARAMETRIC_HOME.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]

from arcpuzzles import Catalog  # noqa: E402
from arcpuzzles.parametric_promotion import _check_execution, _ready  # noqa: E402
from arcpuzzles.parametric_worker import _grid, _real_evaluator  # noqa: E402
from arcpuzzles.review_parametric_admission import validate_sequential_witness  # noqa: E402


DEPENDENCY = {
    "step_a": (
        "For each multicolor source, locate its unique-color anchor and derive "
        "every carrier cell's signed row/column offset from that anchor."
    ),
    "intermediate": (
        "The input-derived mapping from anchor color to the source anchor "
        "coordinate, signed template offsets, and matching singleton targets."
    ),
    "step_b": (
        "Match each singleton by anchor color, choose the episode's horizontal "
        "offset policy for that anchor class, and stamp the template at the target."
    ),
    "why_b_depends_on_a": (
        "The target copy uses offsets measured from the unique anchor.  Replacing "
        "that anchor with the source's first cell changes the offsets and therefore "
        "changes protected-Racket output while leaving the input, targets, and "
        "episode setting fixed."
    ),
}

_ORIENTATION = """(if (= anchor-color
                                                                                          2)"""
_ANCHOR_BINDING = "(let ((anchor (fst anchors)))"
_WRONG_ANCHOR_BINDING = "(let ((anchor (fst cells)))"


def _replace_once(program: str, old: str, new: str, label: str) -> str:
    if type(program) is not str or program.count(old) != 1:
        raise ValueError(f"Expected exactly one {label} in the canonical program")
    return program.replace(old, new, 1)


def wrong_origin_program(program: str) -> str:
    """Ablate only the input-derived source anchor used for offset measurement."""
    return _replace_once(
        program,
        _ANCHOR_BINDING,
        _WRONG_ANCHOR_BINDING,
        "unique-anchor binding",
    )


def shortcut_programs(canonical_program: str) -> dict[str, str]:
    """Finite plausible shortcuts, all executable Racket programs."""
    return {
        "always_preserve": _replace_once(
            canonical_program, _ORIENTATION, "(if #f", "orientation branch"
        ),
        "always_mirror": _replace_once(
            canonical_program, _ORIENTATION, "(if #t", "orientation branch"
        ),
        "mirror_left_source": _replace_once(
            canonical_program,
            _ORIENTATION,
            "(if (< (* 2 (snd anchor)) (cols g))",
            "orientation branch",
        ),
        "mirror_right_source": _replace_once(
            canonical_program,
            _ORIENTATION,
            "(if (>= (* 2 (snd anchor)) (cols g))",
            "orientation branch",
        ),
        "identity": "(rule! (lambda (g) g))",
    }


def _load_prototype():
    path = PARAMETRIC_HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("_ff76_parametric_audit_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _setting_key(value: dict[str, str]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_qualification(path: Path):
    qualification_bytes = path.read_bytes()
    qualification = json.loads(qualification_bytes)
    if (
        qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
    ):
        raise ValueError("Expected this task's successful native qualification")

    contract, binding = _ready(Catalog(ROOT), TASK_ID)
    if qualification.get("contract") != contract:
        raise ValueError("Qualification contract differs from current source")
    if qualification.get("source_binding") != binding:
        raise ValueError("Qualification source binding differs from current source")

    execution_path = path.parent / "execution.json"
    execution_bytes = execution_path.read_bytes()
    if qualification.get("execution") != {
        "path": "execution.json",
        "sha256": _sha_bytes(execution_bytes),
    }:
        raise ValueError("Qualification execution evidence hash differs")
    execution = json.loads(execution_bytes)
    programs = _check_execution(execution, qualification["jobs"], binding, contract)
    if programs != qualification.get("programs"):
        raise ValueError("Qualification program map differs from execution")
    return qualification, qualification_bytes, execution, contract, binding


def _intermediate(prototype, grid):
    result = []
    for instruction in prototype._instructions(deepcopy(grid)):
        anchor = tuple(instruction["anchor"])
        first_cell = tuple(instruction["cells"][0])
        offsets = [
            [row - anchor[0], col - anchor[1], grid[row][col]]
            for row, col in instruction["cells"]
        ]
        wrong_offsets = [
            [row - first_cell[0], col - first_cell[1], grid[row][col]]
            for row, col in instruction["cells"]
        ]
        result.append(
            {
                "anchor_color": instruction["anchor_color"],
                "correct_anchor": list(anchor),
                "counterfactual_first_cell_anchor": list(first_cell),
                "signed_template_offsets": offsets,
                "counterfactual_offsets": wrong_offsets,
                "matching_targets": [list(target) for target in instruction["targets"]],
            }
        )
    return result


def run(qualification_path: Path, audit_path: Path, witness_path: Path) -> dict:
    for output in (audit_path, witness_path):
        if output.exists() or output.is_symlink():
            raise FileExistsError(output)

    qualification, qualification_bytes, execution, contract, binding = _read_qualification(
        qualification_path
    )
    prototype = _load_prototype()
    episodes = execution["episodes"]
    episode_programs = {
        _setting_key(episode["settings"]): episode["program"] for episode in episodes
    }
    if len(episode_programs) != 2:
        raise ValueError("Expected both declared setting programs")
    default_key = _setting_key(contract["default"])
    canonical_program = episode_programs[default_key]
    shortcuts = shortcut_programs(canonical_program)

    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    evaluations = 0

    def execute(program, grid):
        nonlocal evaluations
        evaluations += 1
        return _grid(apply(program, _grid(grid)))

    episode_reports = []
    witness_case = None
    try:
        for episode in episodes:
            selected_key = _setting_key(episode["settings"])
            other_key = next(key for key in episode_programs if key != selected_key)
            rivals = {"other_setting": episode_programs[other_key], **shortcuts}
            observations = {name: [] for name in rivals}
            # The minimum supported lesson has two demonstrations.  Query labels
            # are deliberately excluded from rival survival.
            for demo_index, pair in enumerate(episode["train"][:2]):
                reference = execute(episode["program"], pair["input"])
                if reference != pair["output"]:
                    raise ValueError("Qualified selected program no longer reproduces a demo")
                for name, program in rivals.items():
                    rival_output = execute(program, pair["input"])
                    observations[name].append(
                        {
                            "demo_index": demo_index,
                            "matches": rival_output == reference,
                            "output_sha256": _sha_bytes(
                                json.dumps(
                                    rival_output,
                                    sort_keys=True,
                                    separators=(",", ":"),
                                ).encode()
                            ),
                        }
                    )
            survivors = [
                name
                for name, rows in observations.items()
                if rows and all(row["matches"] for row in rows)
            ]
            if survivors:
                raise ValueError(
                    "Finite shortcut survived the minimum demonstrations: "
                    + ", ".join(survivors)
                )
            episode_reports.append(
                {
                    "seed": episode["seed"],
                    "settings": episode["settings"],
                    "demos_used": 2,
                    "queries_used_for_survival": 0,
                    "rival_program_sha256": {
                        name: hashlib.sha256(program.encode()).hexdigest()
                        for name, program in rivals.items()
                    },
                    "observations": observations,
                    "survivors": survivors,
                }
            )

        counterfactual = wrong_origin_program(canonical_program)
        default_episodes = [
            episode for episode in episodes if _setting_key(episode["settings"]) == default_key
        ]
        for episode in default_episodes:
            for pair in episode["train"] + episode["test"]:
                output = execute(canonical_program, pair["input"])
                try:
                    wrong = execute(counterfactual, pair["input"])
                except (ValueError, RuntimeError):
                    continue
                if output != wrong:
                    witness_case = {
                        "input": deepcopy(pair["input"]),
                        "settings": deepcopy(episode["settings"]),
                        "intermediate_value": _intermediate(prototype, pair["input"]),
                        "program": canonical_program,
                        "output": output,
                        "counterfactual_program": counterfactual,
                        "counterfactual_output": wrong,
                        "ablation": "wrong_intermediate",
                    }
                    break
            if witness_case is not None:
                break
    finally:
        bridge.close()

    if witness_case is None:
        raise ValueError("No changed-output wrong-anchor witness found in qualification episodes")
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("Audit requires protected Racket")

    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "task_id": TASK_ID,
        "source_binding": deepcopy(binding),
        "racket": {"backend": "racket", "protected": True},
        "runtime_identity": identity,
        **DEPENDENCY,
        "cases": [witness_case],
        "limits": (
            "One finite source-bound wrong-intermediate witness from qualification "
            "inputs; no universal depth or measured training-gain claim."
        ),
    }
    witness_path.parent.mkdir(parents=True, exist_ok=True)
    witness_bytes = (
        json.dumps(witness, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()
    witness_path.write_bytes(witness_bytes)

    progress = {
        "sequential_dependency": {
            **DEPENDENCY,
            "witness_path": witness_path.name,
        }
    }
    validation = validate_sequential_witness(
        progress,
        qualification,
        lambda _name: witness_bytes,
    )
    # Re-read current binding after every execution and before publishing claims.
    if _ready(Catalog(ROOT), TASK_ID) != (contract, binding):
        raise ValueError("Adapter source changed during audit")

    report = {
        "schema": "arcpuzzles-ff76baf6c2d9-parametric-audit-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "source_binding": binding,
        "qualification_sha256": _sha_bytes(qualification_bytes),
        "racket": identity,
        "episodes": episode_reports,
        "episodes_checked": len(episode_reports),
        "demonstration_labels_replayed": 2 * len(episode_reports),
        "finite_rival_count_per_episode": 6,
        "surviving_rivals": 0,
        "racket_evaluations": evaluations,
        "sequential_witness": {
            "path": witness_path.as_posix(),
            "sha256": _sha_bytes(witness_bytes),
            "validation": validation,
        },
        "limits": (
            "Finite declared settings, two qualification seeds per setting, and "
            "six named shortcut programs. Reviewer evidence only; no acceptance "
            "or training admission."
        ),
        "training_admitted": False,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--witness", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(
            args.qualification.resolve(),
            args.out.resolve(),
            args.witness.resolve(),
        )
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": type(error).__name__,
                    "message": str(error),
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": report["episodes_checked"],
                "surviving_rivals": report["surviving_rivals"],
                "racket_evaluations": report["racket_evaluations"],
                "audit": str(args.out),
                "witness": str(args.witness),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
