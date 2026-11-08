"""Source-bound bounded audit for the divider receiver-action family.

This tool retains three kinds of evidence without accepting the prototype:

* a deterministic 64-seed census over every supported demonstration count;
* protected-Racket replay of both declared programs and the sequential witness;
* exact public projections whose filenames are their visible-byte SHA-256 IDs.

Run from the repository root through the packet wrapper, for example::

    python3 review.py run python3 \
      generators/9baf979683ef/workspace/parametric/audit.py \
      --out generators/9baf979683ef/workspace/parametric/evidence/current
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK_ID = "9baf979683ef"
ACTIONS = ("preserve", "absorb_color")

for candidate in (ROOT / "src", ROOT / "shared/runtime"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _load_prototype():
    path = HOME / "prototype.py"
    name = "_receiver_action_audit_" + _sha256(path.read_bytes())
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def _apply(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(program)} {_literal(grid)})")


def _step_b_program() -> str:
    """Return B alone, consuming whichever intermediate grid it is given."""
    return """(rule! (let* ((intermediate g)
                    (h (rows intermediate))
                    (w (cols intermediate))
                    (source-color?
                     (lambda (v)
                       (and (not (= v 0)) (not (= v 5)) (not (= v 9)))))
                    (touch-color
                     (lambda (obj)
                       (find-first
                        (lambda (color)
                          (and (source-color? color)
                               (for/or ((p (in-list (obj-cells obj))))
                                 (for/or ((d (in-list cardinal-deltas)))
                                   (let ((r (+ (first p) (first d)))
                                         (c (+ (second p) (second d))))
                                     (and (in-bounds? r c h w)
                                          (= (at intermediate r c) color)))))))
                        (grid-colors intermediate)))))
               (for/fold ((out intermediate))
                         ((obj (in-list
                                (filter (lambda (o) (= (obj-color o) 9))
                                        (objects intermediate 0)))))
                 (let ((color (touch-color obj)))
                   (if color
                       (paint-cells out (obj-cells obj) color)
                       out)))))"""


def _source_inventory() -> dict[str, Any]:
    paths = [
        HOME / "audit.py",
        HOME / "adapter.py",
        HOME / "prototype.py",
        HOME / "promotion.json",
        HOME / "canonical.rkt",
        ROOT / f"generators/{TASK_ID}/generator.py",
        ROOT / f"generators/{TASK_ID}/tests/test_parametric_receiver_action.py",
        ROOT / "shared/runtime/reviewer_support.py",
        ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
        ROOT / "shared/runtime/arc_repl/racket_bridge.py",
    ]
    rows = []
    for path in sorted(paths):
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"missing regular audit source: {path}")
        raw = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(raw),
                "sha256": _sha256(raw),
            }
        )
    return {
        "schema": "arcpuzzles-source-inventory-v1",
        "task_id": TASK_ID,
        "files": rows,
    }


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _bounded_sweep(proto, seeds: tuple[int, ...]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    episode_count = 0
    teaching_checks = 0
    labeled_pairs = 0
    contact_colors: set[int] = set()
    target_size_ranks: set[str] = set()
    target_horizontal_ranks: set[str] = set()
    receiver_counts: set[int] = set()
    dimensions: set[tuple[int, int]] = set()
    boundary_stress_count = 0

    for seed in seeds:
        episodes: dict[str, dict[str, Any]] = {}
        for action in ACTIONS:
            try:
                episode = proto.generate(seed, {"receiver_action": action}, 6, 4)
                episodes[action] = episode
                episode_count += 1
                labeled_pairs += len(episode["train"]) + len(episode["test"])
                grids = _inputs(episode)
                serialized = {
                    json.dumps(grid, sort_keys=True, separators=(",", ":"))
                    for grid in grids
                }
                if len(serialized) != 10:
                    raise AssertionError("episode inputs are not all distinct")
                for pair in episode["train"] + episode["test"]:
                    errors = proto.domain_errors(pair["input"])
                    if errors:
                        raise AssertionError("domain errors: " + "; ".join(errors))
                    expected = proto.transform(pair["input"], action)
                    if pair["output"] != expected:
                        raise AssertionError("Python label does not match transform")
                    observed = proto.observables(pair["input"])
                    contact_colors.add(observed["contact_color"])
                    target_size_ranks.add(observed["target_size_rank"])
                    target_horizontal_ranks.add(observed["target_horizontal_rank"])
                    receiver_counts.add(observed["receiver_count"])
                    dimensions.add((observed["height"], observed["width"]))
                    boundary_stress_count += int(
                        observed["height"] == 30
                        and observed["width"] == 30
                        and observed["touches_right_boundary"]
                    )
                for demos in range(2, 7):
                    report = proto.teaching_report(
                        episode["train"][:demos], episode["test"], action
                    )
                    teaching_checks += 1
                    if report["surviving_settings"] != [action]:
                        raise AssertionError(
                            f"setting survivors at {demos} demos: "
                            f"{report['surviving_settings']}"
                        )
                    if report["surviving_rivals"] or report["query_ambiguities"]:
                        raise AssertionError(
                            f"lesson ambiguity at {demos} demos: {report}"
                        )
            except Exception as exc:  # Retain the exact bounded failure.
                failures.append(
                    {
                        "seed": seed,
                        "settings": {"receiver_action": action},
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                )
        if set(episodes) == set(ACTIONS):
            if _inputs(episodes[ACTIONS[0]]) != _inputs(episodes[ACTIONS[1]]):
                failures.append(
                    {
                        "seed": seed,
                        "error": "InputMismatch",
                        "message": "matched settings did not receive identical inputs",
                    }
                )

    return {
        "schema": "arcpuzzles-receiver-action-sweep-v1",
        "task_id": TASK_ID,
        "seed_range": list(seeds),
        "seed_count": len(seeds),
        "episode_count": episode_count,
        "teaching_checks": teaching_checks,
        "labeled_pairs": labeled_pairs,
        "failures": failures,
        "coverage": {
            "contact_colors": sorted(contact_colors),
            "target_size_ranks": sorted(target_size_ranks),
            "target_horizontal_ranks": sorted(target_horizontal_ranks),
            "receiver_counts": sorted(receiver_counts),
            "dimensions": [list(item) for item in sorted(dimensions)],
            "boundary_stress_count": boundary_stress_count,
            "declared_rivals": list(proto.RIVAL_NAMES),
            "demonstration_counts": [2, 3, 4, 5, 6],
            "query_count": 4,
        },
        "scope": (
            "Finite deterministic census over the listed seeds and declared rivals; "
            "not a universal induction proof or owner acceptance."
        ),
    }


def _protected_racket(proto, seeds: tuple[int, ...]) -> tuple[dict[str, Any], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    label_evaluations = 0
    causal_evaluations = 0
    runtime: dict[str, Any] | None = None
    causal = proto.causal_witness(seed=seeds[0] if seeds else 0)
    causal_doc = copy.deepcopy(causal)

    if not seeds:
        return (
            {
                "schema": "arcpuzzles-receiver-action-protected-racket-v1",
                "task_id": TASK_ID,
                "seeds": [],
                "seed_count": 0,
                "label_evaluations": 0,
                "causal_evaluations": 0,
                "failures": [],
                "runtime": None,
            },
            causal_doc,
        )

    try:
        with RacketBridge(max_calls_before_restart=96) as bridge:
            runtime = bridge.runtime_identity
            for seed in seeds:
                grids = _inputs(
                    proto.generate(seed, {"receiver_action": "preserve"}, 6, 4)
                )
                for action in ACTIONS:
                    program = proto.program({"receiver_action": action})
                    for index, grid in enumerate(grids):
                        observed = _apply(bridge, program, grid)
                        label_evaluations += 1
                        expected = proto.transform(grid, action)
                        if observed != expected:
                            failures.append(
                                {
                                    "kind": "label_mismatch",
                                    "seed": seed,
                                    "settings": {"receiver_action": action},
                                    "pair_index": index,
                                }
                            )

            step_b = _step_b_program()
            protected = {
                "step_a_output": _apply(
                    bridge,
                    proto.program({"receiver_action": "preserve"}),
                    causal["input"],
                ),
                "full_output": _apply(
                    bridge,
                    proto.program({"receiver_action": "absorb_color"}),
                    causal["input"],
                ),
                "skip_a_output": _apply(bridge, step_b, causal["input"]),
                "wrong_intermediate_output": _apply(
                    bridge, step_b, causal["wrong_intermediate"]
                ),
            }
            causal_evaluations = 4
            expected = {
                "step_a_output": causal["intermediate"],
                "full_output": causal["final_output"],
                "skip_a_output": causal["skip_a_output"],
                "wrong_intermediate_output": causal["wrong_intermediate_output"],
            }
            for name, grid in expected.items():
                if protected[name] != grid:
                    failures.append(
                        {
                            "kind": "causal_mismatch",
                            "field": name,
                        }
                    )
            if protected["full_output"] == protected["skip_a_output"]:
                failures.append(
                    {
                        "kind": "causal_collapse",
                        "field": "skip_a_output",
                    }
                )
            if protected["full_output"] == protected["wrong_intermediate_output"]:
                failures.append(
                    {
                        "kind": "causal_collapse",
                        "field": "wrong_intermediate_output",
                    }
                )
            causal_doc.update(
                {
                    "step_a_program": proto.program(
                        {"receiver_action": "preserve"}
                    ),
                    "full_program": proto.program(
                        {"receiver_action": "absorb_color"}
                    ),
                    "step_b_program": step_b,
                    "protected_racket": protected,
                    "runtime": runtime,
                }
            )
    except Exception as exc:
        failures.append(
            {
                "kind": "protected_racket_error",
                "error": type(exc).__name__,
                "message": str(exc),
            }
        )

    report = {
        "schema": "arcpuzzles-receiver-action-protected-racket-v1",
        "task_id": TASK_ID,
        "seeds": list(seeds),
        "seed_count": len(seeds),
        "label_evaluations": label_evaluations,
        "causal_evaluations": causal_evaluations,
        "failures": failures,
        "runtime": runtime,
        "scope": (
            "Protected-Racket replay of both declared settings on ten distinct "
            "inputs per seed plus one four-evaluation sequential counterfactual."
        ),
    }
    return report, causal_doc


def _public_projections(proto, destination: Path, seeds: tuple[int, ...]) -> dict[str, Any]:
    public_dir = destination / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    ids: list[str] = []
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for seed in seeds[:2]:
        for action in ACTIONS:
            episode = proto.generate(seed, {"receiver_action": action}, 2, 1)
            public = proto.public_challenge(episode)
            raw = public_challenge_bytes(public)
            identifier = public_challenge_id(public)
            if _sha256(raw) != identifier:
                failures.append(
                    {"seed": seed, "action": action, "error": "identifier mismatch"}
                )
                continue
            path = public_dir / f"{identifier}.json"
            if path.exists() and path.read_bytes() != raw:
                failures.append(
                    {"seed": seed, "action": action, "error": "ID collision"}
                )
                continue
            path.write_bytes(raw)
            ids.append(identifier)
            decoded = raw.decode("utf-8")
            forbidden = [
                term
                for term in (
                    "receiver_action",
                    "absorb_color",
                    "program_solution",
                    "query_answers",
                    '"seed"',
                )
                if term in decoded
            ]
            if forbidden:
                failures.append(
                    {
                        "seed": seed,
                        "action": action,
                        "error": "private fields leaked",
                        "terms": forbidden,
                    }
                )
            records.append(
                {
                    "seed": seed,
                    "settings": {"receiver_action": action},
                    "id": identifier,
                    "bytes": len(raw),
                    "path": f"public/{identifier}.json",
                }
            )
    if len(ids) != len(set(ids)):
        failures.append({"error": "duplicate public identifier"})
    return {
        "schema": "arcpuzzles-receiver-action-public-projection-v1",
        "task_id": TASK_ID,
        "count": len(ids),
        "ids": ids,
        "records": records,
        "failures": failures,
        "scope": (
            "Each retained file contains labeled demonstrations and one unlabeled "
            "query only; filenames are SHA-256 of exact visible bytes."
        ),
    }


def _normalize_seeds(values: Iterable[int], name: str) -> tuple[int, ...]:
    result = tuple(values)
    if not result:
        return result
    if any(type(value) is not int or not 0 <= value <= 2**63 - 1 for value in result):
        raise ValueError(f"{name} must contain exact integer seeds in 0..2^63-1")
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must not contain duplicates")
    return result


def run_audit(
    destination: Path | str,
    *,
    seeds: Iterable[int] = range(64),
    racket_seeds: Iterable[int] = (0, 17),
) -> dict[str, Any]:
    """Write a new immutable evidence directory and return its summary."""
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"choose a new audit destination: {destination}")
    seed_tuple = _normalize_seeds(seeds, "seeds")
    racket_seed_tuple = _normalize_seeds(racket_seeds, "racket_seeds")
    if not seed_tuple:
        raise ValueError("at least one bounded-sweep seed is required")
    destination.mkdir(parents=True)

    proto = _load_prototype()
    sweep = _bounded_sweep(proto, seed_tuple)
    protected, causal = _protected_racket(proto, racket_seed_tuple)
    public = _public_projections(proto, destination, seed_tuple)
    sources = _source_inventory()

    _write_json(destination / "sweep.json", sweep)
    _write_json(destination / "protected-racket.json", protected)
    _write_json(destination / "causal-witness.json", causal)
    _write_json(destination / "public-projection.json", public)
    _write_json(destination / "sources.json", sources)

    status = (
        "pass"
        if not sweep["failures"]
        and not protected["failures"]
        and not public["failures"]
        else "fail"
    )
    summary = {
        "schema": "arcpuzzles-receiver-action-audit-v1",
        "task_id": TASK_ID,
        "status": status,
        "bounded_sweep": {
            key: sweep[key]
            for key in (
                "seed_count",
                "episode_count",
                "teaching_checks",
                "labeled_pairs",
                "failures",
            )
        },
        "protected_racket": {
            key: protected[key]
            for key in (
                "seed_count",
                "label_evaluations",
                "causal_evaluations",
                "failures",
            )
        },
        "public_projection": {
            "count": public["count"],
            "failures": public["failures"],
        },
        "source_file_count": len(sources["files"]),
        "scope": (
            "Reviewer-generated finite evidence only. Pass does not mean owner "
            "acceptance, universal learnability, or training admission."
        ),
    }
    _write_json(destination / "summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed-count", type=int, default=64)
    parser.add_argument("--racket-seed", type=int, action="append", default=None)
    args = parser.parse_args(argv)
    if not 1 <= args.seed_count <= 1024:
        parser.error("--seed-count must be in 1..1024")
    racket_seeds = tuple(args.racket_seed) if args.racket_seed is not None else (0, 17)
    summary = run_audit(
        args.out,
        seeds=range(args.seed_count),
        racket_seeds=racket_seeds,
    )
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
