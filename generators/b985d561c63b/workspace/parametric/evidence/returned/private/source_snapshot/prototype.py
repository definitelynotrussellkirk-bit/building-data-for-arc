#!/usr/bin/env python3
"""Proposed episode-level stamp-anchor parameter for b985d561c63b.

This is a task-local authoring prototype, not a production generator change.
It selects one anchor per complete episode, generates inputs independently of
that hidden choice, and obtains every retained label and rival prediction by
executing exact, hash-pinned Racket through the bundled bridge.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "b985d561c63b"
VERSION = "proposed-stamp-anchor-v1"
ALLOWED_STAMP_ANCHORS = ("top_left", "bottom_right")
DEFAULT_STAMP_ANCHOR = "top_left"
CANONICAL_RULE_HASH = "c86839f15a5d"
CANONICAL_SHA256 = "d28ede61a9c78ba345f33b47b9db17b0ea2334f382d7c6f17c8a1ec9cb6ef51a"

# The replacement is deliberately narrow and reversible.  The default returns
# the canonical source byte-for-byte; only the target-origin calculation moves.
CANONICAL_ANCHOR_SITE = """               (let ((rmin (min-of first region))
                     (cmin (min-of second region)))
                 (for* ((dr (range 0 th)) (dc (range 0 tw)))
                       (let ((nr (+ rmin dr))
                             (nc (+ cmin dc)))"""
ALTERNATIVE_ANCHOR_SITE = """               (let ((rmax (max-of first region))
                     (cmax (max-of second region)))
                 (for* ((dr (range 0 th)) (dc (range 0 tw)))
                       (let ((nr (+ 1 (- rmax th) dr))
                             (nc (+ 1 (- cmax tw) dc)))"""
_DIFFICULTIES = (None, "easy", "medium", "hard")


def _sha256(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid):
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")


def _validate_anchor(stamp_anchor):
    if type(stamp_anchor) is not str:
        raise TypeError("stamp_anchor must be text")
    if stamp_anchor not in ALLOWED_STAMP_ANCHORS:
        raise ValueError(f"stamp_anchor must be one of {ALLOWED_STAMP_ANCHORS}")
    return stamp_anchor


def _check_canonical_source(source):
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_ANCHOR_SITE) != 1:
        raise ValueError("canonical source must contain exactly one anchor site")
    return source


def canonical_source(*, root=None):
    root = find_root(__file__) if root is None else Path(root)
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(stamp_anchor=DEFAULT_STAMP_ANCHOR, *, root=None, source=None):
    stamp_anchor = _validate_anchor(stamp_anchor)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if stamp_anchor == DEFAULT_STAMP_ANCHOR:
        return canonical
    alternative = canonical.replace(
        CANONICAL_ANCHOR_SITE,
        ALTERNATIVE_ANCHOR_SITE,
        1,
    )
    if alternative.count(ALTERNATIVE_ANCHOR_SITE) != 1:
        raise AssertionError("bottom-right anchor edit was not unique")
    return alternative


def restore_canonical_rule(source):
    if not isinstance(source, str):
        raise TypeError("Racket source must be text")
    if _sha256(source) == CANONICAL_SHA256:
        return _check_canonical_source(source)
    if source.count(ALTERNATIVE_ANCHOR_SITE) != 1:
        raise ValueError("source is neither the canonical nor proposed anchor rule")
    return _check_canonical_source(
        source.replace(ALTERNATIVE_ANCHOR_SITE, CANONICAL_ANCHOR_SITE, 1)
    )


def rule_callable(source):
    """Convert one validated `(rule! (lambda ...))` body to a callable lambda."""
    restore_canonical_rule(source)
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    return source[len("(rule! ") : -1]


def execute_rule(source, grid, *, bridge=None):
    grid = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _components(points):
    remaining = set(points)
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending = [start]
        component = []
        while pending:
            row, col = pending.pop()
            component.append((row, col))
            for neighbor in (
                (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
        components.append(component)
    return components


def _bbox(cells):
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows) + 1, max(cols) + 1


def python_mirror(grid, *, stamp_anchor=DEFAULT_STAMP_ANCHOR):
    """Independent executable mirror used only to cross-check Racket labels."""
    stamp_anchor = _validate_anchor(stamp_anchor)
    grid = normalize_grid(grid)
    source = [
        (row, col)
        for row, cells in enumerate(grid)
        for col, value in enumerate(cells)
        if value not in (0, 5)
    ]
    gray = [
        (row, col)
        for row, cells in enumerate(grid)
        for col, value in enumerate(cells)
        if value == 5
    ]
    if not source or not gray:
        raise ValueError("input needs a colored source and at least one gray target")
    sr0, sc0, sr1, sc1 = _bbox(source)
    template_h, template_w = sr1 - sr0, sc1 - sc0
    result = [list(row) for row in grid]
    for region in _components(gray):
        rr0, rc0, rr1, rc1 = _bbox(region)
        if rr1 - rr0 < template_h or rc1 - rc0 < template_w:
            raise ValueError("target is smaller than source bounding box")
        if stamp_anchor == "top_left":
            target_r0, target_c0 = rr0, rc0
        else:
            target_r0, target_c0 = rr1 - template_h, rc1 - template_w
        for dr in range(template_h):
            for dc in range(template_w):
                result[target_r0 + dr][target_c0 + dc] = grid[sr0 + dr][sc0 + dc]
    return result


def _load_generator(root):
    path = Path(root) / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"{TASK_ID}_parametric_input_generator", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import selected generator at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _input_seed(episode_seed, slot, attempt):
    material = f"{TASK_ID}:{VERSION}:input:{episode_seed}:{slot}:{attempt}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") & (2**63 - 1)


def generated_inputs(seed, *, root=None):
    """Create four parameter-independent lawful inputs from the selected sampler."""
    _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator = _load_generator(root)
    rows = []
    seen = set()
    for slot, difficulty in enumerate(_DIFFICULTIES):
        for attempt in range(100):
            input_seed = _input_seed(seed, slot, attempt)
            grid = generator.generate(
                input_seed,
                slot,
                difficulty=difficulty,
                template_style="dense",
                extra_rows=1,
                extra_cols=1,
            )
            errors = generator.self_check(grid, difficulty=difficulty)
            if errors:
                raise AssertionError(f"selected generator self_check failed: {errors}")
            digest = grid_sha256(grid)
            if digest in seen:
                continue
            observation = generator.observe_overrides(grid)
            required = {"template_style": "dense", "extra_rows": 1, "extra_cols": 1}
            if any(observation[key] != value for key, value in required.items()):
                raise AssertionError(f"selected sampler violated required witness controls: {observation}")
            seen.add(digest)
            rows.append({
                "fixture_id": f"generated-{slot}",
                "input": grid,
                "input_sha256": digest,
                "input_observation": observation,
                "generator_call": {
                    "seed": input_seed,
                    "sample_index": slot,
                    "difficulty": difficulty,
                    "overrides": required,
                    "attempt": attempt,
                },
            })
            break
        else:
            raise AssertionError(f"could not obtain a unique input for slot {slot}")
    return rows


def parameters_for_seed(seed):
    _validate_seed(seed)
    return {"stamp_anchor": random.Random(seed).choice(ALLOWED_STAMP_ANCHORS)}


def make_episode(seed, *, root=None, bridge=None):
    _validate_seed(seed)
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge):
    root = find_root(__file__) if root is None else Path(root).resolve()
    canonical = canonical_source(root=root)
    rules = {
        anchor: materialize_rule(anchor, source=canonical)
        for anchor in ALLOWED_STAMP_ANCHORS
    }
    inputs = generated_inputs(seed, root=root)
    outputs = {
        anchor: [
            execute_rule(source, pair["input"], bridge=bridge)
            for pair in inputs
        ]
        for anchor, source in rules.items()
    }
    for anchor, anchor_outputs in outputs.items():
        for pair, output in zip(inputs, anchor_outputs, strict=True):
            mirror = python_mirror(pair["input"], stamp_anchor=anchor)
            if output != mirror:
                raise AssertionError(
                    f"Racket/Python disagreement for {anchor} on {pair['fixture_id']}"
                )

    target = parameters["stamp_anchor"]
    pairs = [
        {
            **copy.deepcopy(pair),
            "output": output,
            "output_sha256": grid_sha256(output),
        }
        for pair, output in zip(inputs, outputs[target], strict=True)
    ]
    rival_rows = []
    ambiguities = []
    for rival_anchor in ALLOWED_STAMP_ANCHORS:
        demo_mismatches = [
            index for index in range(3)
            if outputs[rival_anchor][index] != outputs[target][index]
        ]
        query_mismatches = [0] if outputs[rival_anchor][3] != outputs[target][3] else []
        status = (
            "refuted_by_demonstrations" if demo_mismatches
            else "ambiguous_query" if query_mismatches
            else "matches_episode"
        )
        row = {
            "stamp_anchor": rival_anchor,
            "racket_sha256": _sha256(rules[rival_anchor]),
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": outputs[rival_anchor][:3],
            "query_predictions": outputs[rival_anchor][3:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    other = next(row for row in rival_rows if row["stamp_anchor"] != target)
    if other["demonstration_mismatch_indices"] != [0, 1, 2]:
        raise AssertionError("every demonstration must refute the other anchor")
    if other["query_mismatch_indices"] != [0]:
        raise AssertionError("query must distinguish the two anchors")

    source = rules[target]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice(('top_left', 'bottom_right')) before all pairs"
        ),
        "input_constraints_depend_on_parameter": False,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "racket_callable": rule_callable(source),
        "racket_callable_sha256": _sha256(rule_callable(source)),
        "racket_path": f"private/rules/stamp-anchor-{target}.rkt",
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": 8,
    }


def public_challenge(episode):
    return copy.deepcopy({
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    })


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _files_manifest(out):
    rows = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name != "report.json"):
        rows.append({
            "path": path.relative_to(out).as_posix(),
            "sha256": _sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        })
    return rows


def write_evidence(seeds, *, out, root=None):
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        with RacketBridge() as bridge:
            canonical = canonical_source(root=root)
            canonical_checks = []
            for row in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical, row["input"], bridge=bridge)
                canonical_checks.append({
                    "split": row["split"],
                    "pair_index": row["pair_index"],
                    "matches": actual == row["output"],
                    "input_sha256": grid_sha256(row["input"]),
                    "expected_sha256": grid_sha256(row["output"]),
                    "actual_sha256": grid_sha256(actual),
                })
            if not canonical_checks or not all(row["matches"] for row in canonical_checks):
                raise AssertionError("canonical default failed canonical pair replay")

            episodes = [make_episode(seed, root=root, bridge=bridge) for seed in seeds]
            witness = generated_inputs(seeds[0], root=root)[0]["input"]
            witness_outputs = {
                anchor: execute_rule(
                    materialize_rule(anchor, source=canonical), witness, bridge=bridge
                )
                for anchor in ALLOWED_STAMP_ANCHORS
            }

        source_snapshot = out / "private" / "source_snapshot"
        source_snapshot.mkdir(parents=True, exist_ok=True)
        for source_path in (
            Path(__file__),
            root / "generators" / TASK_ID / "tests" / "test_parametric_anchor.py",
            root / "generators" / TASK_ID / "workspace" / "parametric" / "README.md",
            root / "generators" / TASK_ID / "generator.py",
        ):
            if source_path.is_file():
                (source_snapshot / source_path.name).write_bytes(source_path.read_bytes())

        rule_dir = out / "private" / "rules"
        rule_dir.mkdir(parents=True, exist_ok=True)
        for anchor in ALLOWED_STAMP_ANCHORS:
            (rule_dir / f"stamp-anchor-{anchor}.rkt").write_text(
                materialize_rule(anchor, source=canonical), encoding="utf-8"
            )

        rows = []
        for episode in episodes:
            seed = episode["seed"]
            private_path = Path("private") / f"episode-{seed:03d}.json"
            public_path = Path("public") / f"episode-{seed:03d}.json"
            _write_json(out / private_path, episode)
            _write_json(out / public_path, public_challenge(episode))
            rows.append({
                "seed": seed,
                "stamp_anchor": episode["parameters"]["stamp_anchor"],
                "private_path": private_path.as_posix(),
                "public_path": public_path.as_posix(),
                "racket_sha256": episode["racket_sha256"],
                "ambiguities": len(episode["ambiguities"]),
            })

        _write_json(out / "private" / "canonical_replay.json", canonical_checks)
        _write_json(out / "private" / "distinguishing_witness.json", {
            "input": witness,
            "input_sha256": grid_sha256(witness),
            "outputs_by_stamp_anchor": witness_outputs,
            "output_sha256_by_stamp_anchor": {
                anchor: grid_sha256(output)
                for anchor, output in witness_outputs.items()
            },
            "different": len({_json(value) for value in witness_outputs.values()}) == 2,
        })
        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "status": "proposed_unapproved",
            "approved": False,
            "parameter": {
                "name": "stamp_anchor",
                "allowed_values": list(ALLOWED_STAMP_ANCHORS),
                "original_default": DEFAULT_STAMP_ANCHOR,
                "selected_once_per_episode": True,
                "input_constraints_depend_on_parameter": False,
            },
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "canonical_source_sha256": CANONICAL_SHA256,
            "prototype_sha256": _sha256(Path(__file__).read_bytes()),
            "episodes": rows,
            "counts": {
                "episodes": len(episodes),
                "demonstrations": 3 * len(episodes),
                "queries": len(episodes),
                "settings_covered": len({row["stamp_anchor"] for row in rows}),
                "canonical_pairs_checked": len(canonical_checks),
                "ambiguous_parameter_rivals": sum(row["ambiguities"] for row in rows),
                "racket_rule_applications": 8 * len(episodes) + len(canonical_checks) + 2,
            },
            "limits": [
                "finite evidence for the declared two anchor settings and retained seeds",
                "the selected production sampler is constrained to dense sources with one-cell surplus",
                "declared parameter rivals do not prove universal rule identifiability",
                "prototype status does not change canonical approval or production APIs",
            ],
        }
        report["files"] = _files_manifest(out)
        _write_json(out / "report.json", report)
        return report
    except Exception as exc:
        _write_json(out / "failure.json", {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "seeds": list(seeds),
        })
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
