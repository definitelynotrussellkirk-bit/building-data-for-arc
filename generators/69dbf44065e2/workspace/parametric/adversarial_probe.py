#!/usr/bin/env python3
"""Bounded adversarial probe for the turn-after-down-smear family.

This is intentionally reusable: it attacks declared setting identification,
plausible partial/wrong-order solvers, color shortcuts, count boundaries,
30x30/thin geometry, exact numeric types, and optional protected-Racket parity.
It emits one compact source-bound JSON report; finite success is not a proof of
universal uniqueness.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
TASK_HOME = HOME.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER = _load("_probe_69db_adapter", HOME / "adapter.py")
PROTO = _load("_probe_69db_proto", HOME / "prototype.py")
TURNS = ("none", "left", "right")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _serial(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _changed(left, right) -> int:
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def _resume_after_blockers(grid):
    source = PROTO.validate_grid(grid)
    out = deepcopy(source)
    for row, col, value in PROTO.seeds(source):
        for rr in range(row + 1, len(source)):
            if source[rr][col] == 0 and out[rr][col] == 0:
                out[rr][col] = value
    return out


def _one_step_down(grid):
    source = PROTO.validate_grid(grid)
    out = deepcopy(source)
    for row, col, value in PROTO.seeds(source):
        if row + 1 < len(source) and source[row + 1][col] == 0:
            out[row + 1][col] = value
    return out


def _walls_as_seeds(grid):
    source = PROTO.validate_grid(grid)
    out = PROTO.down_smear(source)
    for row, values in enumerate(source):
        for col, value in enumerate(values):
            if value != 5:
                continue
            rr = row + 1
            while rr < len(source) and source[rr][col] == 0:
                out[rr][col] = 5
                rr += 1
    return out


def _ignore_stage_a_blockers(grid, turn):
    source = PROTO.validate_grid(grid)
    down = PROTO.down_smear(source)
    if turn == "none":
        return down
    out = deepcopy(down)
    delta = -1 if turn == "left" else 1
    width = len(source[0])
    for row, col, value in PROTO.seeds(source):
        end = PROTO.endpoint(source, row, col)
        if end == row:
            continue
        cc = col + delta
        while 0 <= cc < width and source[end][cc] == 0:
            out[end][cc] = value
            cc += delta
    return out


def _one_cell_turn(grid, turn):
    source = PROTO.validate_grid(grid)
    down = PROTO.down_smear(source)
    if turn == "none":
        return down
    out = deepcopy(down)
    delta = -1 if turn == "left" else 1
    for row, col, value in PROTO.seeds(source):
        end = PROTO.endpoint(source, row, col)
        cc = col + delta
        if end != row and 0 <= cc < len(source[0]) and down[end][cc] == 0:
            out[end][cc] = value
    return out


def _longest_only(grid, turn):
    source = PROTO.validate_grid(grid)
    down = PROTO.down_smear(source)
    if turn == "none":
        return down
    active = []
    for row, col, value in PROTO.seeds(source):
        end = PROTO.endpoint(source, row, col)
        if end != row:
            active.append((end - row, row, col, end, value))
    if not active:
        return down
    _, _, col, end, value = max(active)
    out = deepcopy(down)
    delta = -1 if turn == "left" else 1
    cc = col + delta
    while 0 <= cc < len(source[0]) and down[end][cc] == 0:
        out[end][cc] = value
        cc += delta
    return out


def _rivals(turn):
    if turn == "none":
        return {
            "one_step_down": _one_step_down,
            "resume_after_blockers": _resume_after_blockers,
            "walls_as_seeds": _walls_as_seeds,
        }
    opposite = "right" if turn == "left" else "left"
    return {
        "skip_stage_a": lambda grid: PROTO.skip_stage_a(grid, turn),
        "wrong_order": lambda grid: PROTO.wrong_order(grid, turn),
        "ignore_stage_a_blockers": lambda grid: _ignore_stage_a_blockers(grid, turn),
        "one_cell_turn": lambda grid: _one_cell_turn(grid, turn),
        "longest_only": lambda grid: _longest_only(grid, turn),
        "opposite_turn": lambda grid: PROTO.solve(grid, opposite),
        "canonical_only": lambda grid: PROTO.solve(grid, "none"),
    }


def _permute_colors(grid, shift: int):
    palette = (1, 2, 3, 4, 6, 7, 8, 9)
    mapping = {value: palette[(index + shift) % len(palette)] for index, value in enumerate(palette)}
    inverse = {target: source for source, target in mapping.items()}
    changed = [[mapping.get(value, value) for value in row] for row in grid]
    return changed, inverse


def _map_colors(grid, mapping):
    return [[mapping.get(value, value) for value in row] for row in grid]


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _protected_racket(seeds: int):
    if seeds <= 0:
        return {"evaluations": 0, "counterfactuals": 0, "runtime": None}
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    wrapped = {turn: wrap_rule(ADAPTER.program({"turn": turn})) for turn in TURNS}
    skip = {
        turn: wrap_rule((HOME / f"skip-a-{turn}.rkt").read_text())
        for turn in ("left", "right")
    }
    evaluations = 0
    counterfactuals = 0
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise AssertionError("protected Racket required")
        for seed in range(seeds):
            for turn in TURNS:
                episode = ADAPTER.generate(seed, {"turn": turn}, 2, 4)
                for pair in [*episode["train"], *episode["test"]]:
                    actual = bridge.eval_text(f"({wrapped[turn]} {_literal(pair['input'])})")
                    evaluations += 1
                    if actual != pair["output"]:
                        raise AssertionError(("Racket/Python mismatch", seed, turn))
                if turn != "none":
                    pair = episode["test"][0]
                    alternate = bridge.eval_text(f"({skip[turn]} {_literal(pair['input'])})")
                    counterfactuals += 1
                    if alternate == pair["output"]:
                        raise AssertionError(("skip-A did not change output", seed, turn))
        return {
            "evaluations": evaluations,
            "counterfactuals": counterfactuals,
            "runtime": {key: identity[key] for key in (
                "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"
            ) if key in identity},
        }
    finally:
        bridge.close()


def run(seed_count: int, racket_seeds: int) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 512:
        raise ValueError("seed_count must be 1..512")
    if type(racket_seeds) is not int or not 0 <= racket_seeds <= min(seed_count, 32):
        raise ValueError("racket_seeds must be 0..min(seed_count,32)")

    ambiguity = []
    equivalent = []
    declared_checks = 0
    rival_checks = 0
    color_controls = 0
    api_checks = 0
    size_counts: dict[str, int] = {}
    fixed_30_signatures = set()
    min_changed = {turn: 10**9 for turn in TURNS}
    max_changed = {turn: 0 for turn in TURNS}

    for seed in range(seed_count):
        episodes = {
            turn: ADAPTER.generate(seed, {"turn": turn}, 2, 4)
            for turn in TURNS
        }
        inputs = {
            turn: [pair["input"] for split in ("train", "test") for pair in episodes[turn][split]]
            for turn in TURNS
        }
        if not (inputs["none"] == inputs["left"] == inputs["right"]):
            raise AssertionError(("inputs not matched", seed))
        if len({_serial(grid) for grid in inputs["none"]}) != 6:
            raise AssertionError(("duplicate input", seed))

        for grid in inputs["none"]:
            key = f"{len(grid)}x{len(grid[0])}"
            size_counts[key] = size_counts.get(key, 0) + 1
            if len(grid) == len(grid[0]) == 30:
                facts = ADAPTER.dependency_facts(grid, "left")
                fixed_30_signatures.add(_serial(facts["active_endpoints"]))

        for turn, episode in episodes.items():
            demonstrations = episode["train"]
            queries = episode["test"]
            survivors = [
                candidate for candidate in TURNS
                if all(ADAPTER.solve(pair["input"], candidate) == pair["output"] for pair in demonstrations)
            ]
            declared_checks += len(TURNS) * len(demonstrations)
            if survivors != [turn]:
                ambiguity.append({"seed": seed, "turn": turn, "kind": "declared", "survivors": survivors})

            for name, rival in _rivals(turn).items():
                demo_fit = all(rival(pair["input"]) == pair["output"] for pair in demonstrations)
                query_changes = [rival(pair["input"]) != pair["output"] for pair in queries]
                rival_checks += len(demonstrations) + len(queries)
                if demo_fit and any(query_changes):
                    ambiguity.append({"seed": seed, "turn": turn, "kind": name})
                elif demo_fit and not any(query_changes):
                    equivalent.append({"seed": seed, "turn": turn, "kind": name})

            for pair in [*demonstrations, *queries]:
                changed = _changed(pair["input"], pair["output"])
                min_changed[turn] = min(min_changed[turn], changed)
                max_changed[turn] = max(max_changed[turn], changed)

        # Crossed nuisance control: color permutation keeps endpoint geometry
        # fixed and must commute with all three programs.
        for index, grid in enumerate(inputs["none"][:3]):
            recolored, inverse = _permute_colors(grid, (seed + index) % 7 + 1)
            for turn in TURNS:
                recovered = _map_colors(ADAPTER.solve(recolored, turn), inverse)
                if recovered != ADAPTER.solve(grid, turn):
                    raise AssertionError(("color shortcut", seed, index, turn))
                color_controls += 1

        # Independent count boundaries and invalid exact types.
        for demos, queries in ((2, 1), (2, 4), (6, 1), (6, 4)):
            episode = ADAPTER.generate(seed, {"turn": "left"}, demos, queries)
            if len(episode["train"]) != demos or len(episode["test"]) != queries:
                raise AssertionError("count drift")
            api_checks += 1

    if ambiguity:
        raise AssertionError(f"teaching ambiguity: {ambiguity[:3]}")
    required_sizes = {"30x30", "7x24", "24x7"}
    if not required_sizes <= set(size_counts):
        raise AssertionError(f"missing stress sizes: {required_sizes - set(size_counts)}")
    if len(fixed_30_signatures) < max(4, seed_count // 4):
        raise AssertionError("30x30 intermediate lacked seed diversity")

    malformed_rejections = 0
    for call in (
        lambda: ADAPTER.program({}),
        lambda: ADAPTER.program({"turn": "up"}),
        lambda: ADAPTER.generate(0, {"turn": "left"}, True, 4),
        lambda: ADAPTER.generate(0, {"turn": "left"}, 2, 5),
        lambda: ADAPTER.solve([[True]], "left"),
        lambda: ADAPTER.solve([[0, 1], [0]], "left"),
    ):
        try:
            call()
        except (TypeError, ValueError):
            malformed_rejections += 1
        else:
            raise AssertionError("malformed request accepted")

    # Public-byte privacy and query-order independence at the adapter boundary.
    from reviewer_support import public_challenge_bytes, public_challenge_id
    private_invariance = 0
    visible_changes = 0
    sample = ADAPTER.generate(123, {"turn": "right"}, 2, 4)
    ids = []
    for pair in sample["test"]:
        visible = {"train": deepcopy(sample["train"]), "test": [{"input": deepcopy(pair["input"])}]}
        before = public_challenge_bytes(visible)
        identifier = public_challenge_id(visible)
        ids.append(identifier)
        private = {**visible, "settings": {"turn": "left"}, "answer": pair["output"], "future": sample["test"]}
        if public_challenge_bytes(private) != before or public_challenge_id(private) != identifier:
            raise AssertionError("private metadata changed public bytes")
        private_invariance += 1
        changed = deepcopy(visible)
        changed["test"][0]["input"][0][0] = 9 if changed["test"][0]["input"][0][0] != 9 else 8
        if public_challenge_id(changed) == identifier:
            raise AssertionError("visible mutation did not change public ID")
        visible_changes += 1
    if len(ids) != len(set(ids)):
        raise AssertionError("query public IDs collided")

    racket = _protected_racket(racket_seeds)
    files = [
        HOME / "adapter.py", HOME / "prototype.py", HOME / "promotion.json",
        HOME / "canonical.rkt", HOME / "turn-left.rkt", HOME / "turn-right.rkt",
        HOME / "skip-a-left.rkt", HOME / "skip-a-right.rkt", HOME / "adversarial_probe.py",
        HOME / "README.md", TASK_HOME / "generator.py",
    ]
    return {
        "schema": "arcpuzzles-69dbf44065e2-adversarial-probe-v1",
        "status": "passed",
        "task_id": "69dbf44065e2",
        "source_sha256": {path.relative_to(TASK_HOME.parent.parent).as_posix(): _sha(path) for path in files},
        "settings": list(TURNS),
        "seed_count": seed_count,
        "episodes": seed_count * len(TURNS),
        "pairs": seed_count * len(TURNS) * 6,
        "declared_program_demo_evaluations": declared_checks,
        "plausible_rival_evaluations": rival_checks,
        "color_permutation_controls": color_controls,
        "count_boundary_episodes": api_checks,
        "malformed_rejections": malformed_rejections,
        "size_counts": dict(sorted(size_counts.items())),
        "fixed_30_intermediate_signatures": len(fixed_30_signatures),
        "changed_cell_range": {turn: [min_changed[turn], max_changed[turn]] for turn in TURNS},
        "behavior_equivalent_rival_rows": equivalent[:16],
        "teaching_ambiguities": ambiguity,
        "public_projection": {
            "private_invariance_checks": private_invariance,
            "visible_positive_controls": visible_changes,
            "distinct_query_ids": len(ids),
        },
        "protected_racket": racket,
        "limits": (
            "Finite declared/rival search over deterministic seeds; it does not prove universal "
            "uniqueness or owner acceptance. Shared preview verification is run separately."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--racket-seeds", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run(args.seeds, args.racket_seeds)
    payload = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
