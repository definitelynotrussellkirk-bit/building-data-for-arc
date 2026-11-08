#!/usr/bin/env python3
"""Proposed episode-level rule parameters for Mirror Inside the Frame.

This module is an authoring prototype. Every label and rival prediction comes
from the included RacketBridge; it does not implement a Python output oracle.
The canonical per-puzzle generator and its approval contract are unaffected.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
from pathlib import Path
import random
import shlex
import subprocess
import sys
import traceback
from typing import Any

from arc_repl import racket_bridge
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
import reviewer_support
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "72f0b65569a4"
PROTOTYPE_VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
CANONICAL_SHA256 = "3ca01023e0730d43844cac3ece57bfa2b777270780c3509e52b25eb23b0d7934"
AXES = ("vertical", "horizontal")
OUTPUT_COLORS = (7, 2)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def value_hash(value: Any) -> str:
    return sha256_bytes(json_bytes(value))


def _integer(value: Any, name: str, *, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        raise ValueError(f"{name} must be an integer" + (f" >= {minimum}" if minimum is not None else ""))
    return value


@dataclass(frozen=True)
class Parameters:
    """The original/default setting is vertical reflection with orange paint."""

    axis: str = "vertical"
    output_color: int = 7

    def __post_init__(self) -> None:
        if type(self.axis) is not str or self.axis not in AXES:
            raise ValueError(f"axis must be one of {AXES}")
        if type(self.output_color) is not int or self.output_color not in OUTPUT_COLORS:
            raise ValueError(f"output_color must be one of {OUTPUT_COLORS}; booleans are not colors")

    @property
    def key(self) -> str:
        return f"{self.axis}-{self.output_color}"


def all_parameters() -> tuple[Parameters, ...]:
    return tuple(Parameters(axis, color) for axis, color in itertools.product(AXES, OUTPUT_COLORS))


def _rng(seed: int, label: str) -> random.Random:
    _integer(seed, "seed")
    digest = hashlib.sha256(f"{TASK_ID}:parametric-v1:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def sample_parameters(seed: int) -> Parameters:
    """Draw once per episode, with streams separate from every input draw."""
    return Parameters(
        _rng(seed, "parameter:axis").choice(AXES),
        _rng(seed, "parameter:output_color").choice(OUTPUT_COLORS),
    )


def canonical_program() -> str:
    source = (HERE / "canonical_rule.rkt").read_text(encoding="utf-8")
    if sha256_bytes(source.encode()) != CANONICAL_SHA256:
        raise ValueError("The prototype's exact canonical program snapshot changed")
    return source


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError("The bounded Racket template does not match its pinned source")
    return source.replace(old, new, 1)


def materialize_program(parameters: Parameters = Parameters()) -> str:
    """Emit exact executable Racket, retaining the canonical default bytes."""
    if not isinstance(parameters, Parameters):
        raise TypeError("parameters must be a Parameters instance")
    source = canonical_program()
    target = "r mc"
    if parameters.axis == "horizontal":
        source = _replace_once(
            source,
            "(let ((mc (- (+ (obj-c1 frame) (obj-c2 frame)) c)))",
            "(let ((mr (- (+ (obj-r1 frame) (obj-r2 frame)) r)))",
        )
        source = _replace_once(
            source,
            "(and (> mc (obj-c1 frame)) (< mc (obj-c2 frame)) (= (at acc r mc) 0))",
            "(and (> mr (obj-r1 frame)) (< mr (obj-r2 frame)) (= (at acc mr c) 0))",
        )
        source = _replace_once(source, "(set-cell acc r mc 7)", "(set-cell acc mr c 7)")
        target = "mr c"
    if parameters.output_color != 7:
        source = _replace_once(
            source, f"(set-cell acc {target} 7)",
            f"(set-cell acc {target} {parameters.output_color})",
        )
    return source


def sample_input(seed: int, pair_index: int) -> list[list[int]]:
    """Parameter-independent, lawful one-frame inputs with a teaching witness.

    A corner yellow has two empty axis-specific targets and an empty diagonal
    partner. Thus the two axes give distinct productive behavior. Other marks
    exercise occupied mirror pairs and marks on both center axes. This is input
    construction only; labels are always executed in Racket.
    """
    _integer(pair_index, "pair_index", minimum=0)
    rng = _rng(seed, f"input:{pair_index}")
    branch = pair_index % 3
    sizes = (7, 9) if branch == 2 else ((6, 7, 8, 9, 10) if branch == 1 else (5, 6, 7, 8, 9, 10))
    fh, fw = rng.choice(sizes), rng.choice(sizes)
    r0, c0 = rng.randint(1, 3), rng.randint(1, 3)
    height, width = r0 + fh + rng.randint(1, 3), c0 + fw + rng.randint(1, 3)
    grid = [[0] * width for _ in range(height)]
    for r in range(r0, r0 + fh):
        for c in range(c0, c0 + fw):
            if r in (r0, r0 + fh - 1) or c in (c0, c0 + fw - 1):
                grid[r][c] = 1
    r1, c1 = r0 + fh - 1, c0 + fw - 1
    corners = {(r0 + 1, c0 + 1), (r0 + 1, c1 - 1), (r1 - 1, c0 + 1), (r1 - 1, c1 - 1)}
    anchor = rng.choice(sorted(corners))
    reserved_empty = corners - {anchor}
    marks = {anchor}
    if branch == 1:
        # A 2x2 orbit gives occupied destinations along both possible axes.
        r, c = r0 + 2, c0 + 2
        marks.update({(r, c), (r, c0 + c1 - c), (r0 + r1 - r, c), (r0 + r1 - r, c0 + c1 - c)})
    elif branch == 2:
        rm, cm = (r0 + r1) // 2, (c0 + c1) // 2
        marks.update({(rm, c0 + 2), (r0 + 2, cm), (rm, cm)})
    available = [
        (r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)
        if (r, c) not in marks and (r, c) not in reserved_empty
    ]
    rng.shuffle(available)
    count = rng.randint(max(3, len(marks)), min(7, len(marks) + len(available)))
    marks.update(available[:count - len(marks)])
    if marks & reserved_empty:
        raise AssertionError("input construction consumed its distinguishing witness")
    for r, c in marks:
        grid[r][c] = 4
    return grid


def witness_input() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 8):
            if r in (1, 5) or c in (1, 7):
                grid[r][c] = 1
    grid[2][2] = 4
    return grid


def _grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list) or not value or any(not isinstance(row, list) or not row for row in value):
        raise ValueError("Racket inputs and outputs must be nonempty integer grids")
    if len({len(row) for row in value}) != 1 or any(type(c) is not int or not 0 <= c <= 9 for row in value for c in row):
        raise ValueError("Racket inputs and outputs must be rectangular with integer colors 0..9")
    return value


def rule_application(source: str, grid: list[list[int]]) -> str:
    _grid(grid)
    # These four exact source strings contain ordinary Racket and need only g.
    # The general shared wrapper imports scripts.* from a staged runtime, which
    # is unavailable in this directly runnable task workspace. Do not broaden
    # this tiny application adapter into a second generic rule normalizer.
    if source not in tuple(materialize_program(p) for p in all_parameters()):
        raise ValueError("Only the four pinned parametric rule templates can be applied")
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    body = source[len("(rule!"):-1]
    return f"(let ([g {literal}]) {body})"


class RacketOracle:
    """A reusable bridge plus exact-call evidence; no fallback output engine."""

    def __init__(self) -> None:
        self.root = find_root(__file__)
        for module in (racket_bridge, reviewer_support):
            if not Path(module.__file__).resolve().is_relative_to(self.root):
                raise ImportError(f"{module.__name__} belongs to another checkout")
        self.bridge = RacketBridge(timeout=10.0, max_calls_before_restart=128)
        self.executions: list[dict[str, Any]] = []
        self.cache: dict[tuple[str, str], list[list[int]]] = {}
        self.cache_hits = 0

    def evaluate(self, parameters: Parameters, grid: list[list[int]]) -> list[list[int]]:
        _grid(grid)
        source = materialize_program(parameters)
        source_hash, input_hash = sha256_bytes(source.encode()), value_hash(grid)
        key = source_hash, input_hash
        if key in self.cache:
            self.cache_hits += 1
            return copy.deepcopy(self.cache[key])
        expression = rule_application(source, grid)
        output = _grid(self.bridge.eval_text(expression))
        if (len(output), len(output[0])) != (len(grid), len(grid[0])):
            raise ValueError("The executed rule unexpectedly changed grid dimensions")
        self.executions.append({
            "execution_index": len(self.executions), "backend": "RacketBridge.eval_text",
            "parameters": asdict(parameters), "program_sha256": source_hash,
            "input": copy.deepcopy(grid), "input_sha256": input_hash,
            "output": copy.deepcopy(output), "output_sha256": value_hash(output),
            "expression": expression, "expression_sha256": sha256_bytes(expression.encode()),
        })
        self.cache[key] = copy.deepcopy(output)
        return copy.deepcopy(output)

    def close(self) -> None:
        self.bridge.shutdown()


def rival_status(differing_train: list[int], differing_test: list[int]) -> str:
    if differing_train:
        return "refuted_by_demonstrations"
    return "ambiguous" if differing_test else "survived_all"


def build_episode(
    seed: int, parameters: Parameters = Parameters(), *, oracle: RacketOracle,
    n_train: int = 3, n_test: int = 1, parameter_selection: str = "fixed/default",
) -> dict[str, Any]:
    """Fix the settings once, then label every demo, query, and parameter rival."""
    _integer(seed, "seed")
    _integer(n_train, "n_train", minimum=1)
    _integer(n_test, "n_test", minimum=1)
    if n_train > 8 or n_test > 4:
        raise ValueError("This bounded prototype allows at most 8 demonstrations and 4 queries")
    inputs = [sample_input(seed, index) for index in range(n_train + n_test)]
    predictions = {p.key: [oracle.evaluate(p, grid) for grid in inputs] for p in all_parameters()}
    selected = predictions[parameters.key]
    pairs = [{"input": copy.deepcopy(grid), "output": copy.deepcopy(out)} for grid, out in zip(inputs, selected)]
    rivals = []
    for rival in all_parameters():
        if rival == parameters:
            continue
        prediction = predictions[rival.key]
        train_diff = [i for i in range(n_train) if prediction[i] != selected[i]]
        query_diff = [i for i in range(n_test) if prediction[n_train + i] != selected[n_train + i]]
        rivals.append({
            "parameters": asdict(rival), "program_sha256": sha256_bytes(materialize_program(rival).encode()),
            "status": rival_status(train_diff, query_diff),
            "differing_train_indices": train_diff, "differing_test_indices": query_diff,
            "predictions": {"train": prediction[:n_train], "test": prediction[n_train:]},
        })
    if any(row["status"] != "refuted_by_demonstrations" for row in rivals):
        raise ValueError("This episode does not distinguish every declared parameter rival in demonstrations")
    public = {
        "train": copy.deepcopy(pairs[:n_train]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in pairs[n_train:]],
    }
    return {
        "schema": "mirror-parametric-episode-v1", "status": "prototype",
        "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION,
        "seed": seed, "parameters": asdict(parameters), "parameter_selection": parameter_selection,
        "parameters_fixed_for_all_pairs": True,
        "program": materialize_program(parameters),
        "program_sha256": sha256_bytes(materialize_program(parameters).encode()),
        "train": pairs[:n_train], "test": pairs[n_train:],
        "public": public, "public_sha256": value_hash(public),
        "input_draws": [{"pair_index": i, "input_sha256": value_hash(grid)} for i, grid in enumerate(inputs)],
        "rival_results": rivals, "all_parameter_rivals_refuted": True,
        "label_backend": "RacketBridge.eval_text (content-addressed reuse within this run)",
    }


def check_canonical(oracle: RacketOracle) -> dict[str, Any]:
    ledger = canonical_path(oracle.root)
    rows = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    if not rows or any(row.get("program_solution") != canonical_program() for row in rows):
        raise ValueError("The exact default program differs from current canonical authority")
    results = []
    for pair in canonical_pairs(TASK_ID, root=oracle.root):
        output = oracle.evaluate(Parameters(), pair["input"])
        passed = output == pair["output"]
        results.append({**pair, "executed_output": output, "passed": passed})
        if not passed:
            raise ValueError("Executed canonical default disagrees with a canonical label")
    return {
        "status": "passed", "canonical_program_byte_identical": True,
        "canonical_program_sha256": CANONICAL_SHA256,
        "canonical_normalized_sha256": sha256_bytes(" ".join(canonical_program().split()).encode()),
        "canonical_ledger": str(ledger.relative_to(oracle.root)),
        "canonical_records_sha256": value_hash(rows), "checked_pairs": len(results), "pairs": results,
    }


def check_witness(oracle: RacketOracle) -> dict[str, Any]:
    grid = witness_input()
    outputs = {p.key: oracle.evaluate(p, grid) for p in all_parameters()}
    comparisons = []
    for left, right in itertools.combinations(all_parameters(), 2):
        differences = [
            {"row": r, "column": c, "left": outputs[left.key][r][c], "right": outputs[right.key][r][c]}
            for r in range(len(grid)) for c in range(len(grid[0]))
            if outputs[left.key][r][c] != outputs[right.key][r][c]
        ]
        comparisons.append({"left": asdict(left), "right": asdict(right), "differences": differences})
        if not differences:
            raise ValueError("The lawful witness did not separate a declared pair of settings")
    return {"status": "passed", "input": grid, "outputs": outputs, "pairwise_comparisons": comparisons}


def source_bindings(root: Path) -> dict[str, str]:
    paths = list(HERE.glob("*.py")) + list(HERE.glob("*.rkt")) + list(HERE.glob("README.md"))
    test_path = HERE.parent.parent / "tests/test_parametric_mirror.py"
    if test_path.is_file():
        paths.append(test_path)
    paths.extend(Path(module.__file__).resolve() for module in (racket_bridge, reviewer_support))
    prelude = Path(racket_runtime_status()["prelude_path"]).parent
    paths.extend(prelude.rglob("*.rkt"))
    return {str(path.relative_to(root)): sha256_bytes(path.read_bytes()) for path in sorted(set(paths))}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def invocation() -> dict[str, Any]:
    return {
        "cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
        "payload_command": shlex.join([sys.executable, *sys.argv]),
        "python_version": sys.version,
    }


def save_evidence(
    out: Path, episodes: list[dict[str, Any]], oracle: RacketOracle,
    canonical: dict[str, Any], witness: dict[str, Any],
) -> dict[str, Any]:
    private = out / "private"
    private.mkdir(parents=True, exist_ok=True)
    for i, episode in enumerate(episodes):
        public_path = Path("public") / f"episode-{i:03d}.json"
        _write_json(out / public_path, episode["public"])
        episode["public_path"] = str(public_path)
    for parameters in all_parameters():
        path = private / "rules" / f"{parameters.key}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(materialize_program(parameters), encoding="utf-8")
    _write_json(private / "episodes.json", episodes)
    _write_json(private / "canonical_check.json", canonical)
    _write_json(private / "witness.json", witness)
    with (private / "executions.jsonl").open("w", encoding="utf-8") as handle:
        for execution in oracle.executions:
            handle.write(json_bytes(execution).decode() + "\n")
    runtime = racket_runtime_status()
    binary = Path(runtime["resolved_binary"])
    version = subprocess.run([str(binary), "--version"], text=True, capture_output=True, check=True)
    summary = {
        "schema": "mirror-parametric-evidence-v1", "status": "passed", "scope": "prototype",
        "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION, "exit_status": 0,
        "episode_count": len(episodes), "seeds": sorted({episode["seed"] for episode in episodes}),
        "settings_exercised": [asdict(p) for p in all_parameters()],
        "demonstration_pairs": sum(len(ep["train"]) for ep in episodes),
        "query_pairs": sum(len(ep["test"]) for ep in episodes),
        "parameter_rival_comparisons": sum(len(ep["rival_results"]) for ep in episodes),
        "all_parameter_rivals_refuted": all(ep["all_parameter_rivals_refuted"] for ep in episodes),
        "ambiguities": 0, "canonical_pairs_checked": canonical["checked_pairs"],
        "witness_setting_pairs_distinguished": len(witness["pairwise_comparisons"]),
        "actual_racket_evaluations": len(oracle.executions), "execution_cache_hits": oracle.cache_hits,
        "invocation": invocation(), "source_hashes": source_bindings(oracle.root),
        "program_hashes": {p.key: sha256_bytes(materialize_program(p).encode()) for p in all_parameters()},
        "runtime": {**runtime, "binary_sha256": sha256_bytes(binary.read_bytes()), "version_stdout": version.stdout.strip()},
        "main_generator_dependency": False,
        "limits": [
            "This is a proposed task-local prototype, not a production parametric API or approval.",
            "Evidence covers the retained seeds, four bounded settings, declared parameter rivals, and small input grammar only.",
            "Inputs contain one isolated complete frame and yellow marks; permissive canonical behavior on other scenes is not studied.",
            "The distinguishing corner witness is an intentional teaching constraint and limits this sampler's support.",
            "Share only individual public/episode-NNN.json challenges; every other file is private authoring evidence.",
        ],
    }
    _write_json(private / "receipt.json", summary)
    files = {
        str(path.relative_to(out)): sha256_bytes(path.read_bytes())
        for path in sorted(out.rglob("*")) if path.is_file()
    }
    _write_json(out / "manifest.json", {"schema": "mirror-parametric-files-v1", "scope": "private authoring evidence", "files": files})
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="execute all four settings, canonical labels, and a separating witness")
    verify.add_argument("--seed", type=int, action="append", help="repeat for multiple deterministic episode seeds; default: 0 and 17")
    verify.add_argument("--out", required=True, type=Path, help="new output directory; evidence is private except public challenges")
    episode = commands.add_parser("episode", help="materialize one fixed-parameter episode and its rival checks")
    episode.add_argument("--seed", required=True, type=int)
    episode.add_argument("--axis", choices=AXES)
    episode.add_argument("--output-color", type=int, choices=OUTPUT_COLORS)
    episode.add_argument("--sample-parameters", action="store_true", help="choose the settings once from the episode seed")
    episode.add_argument("--train", default=3, type=int)
    episode.add_argument("--test", default=1, type=int)
    episode.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == "episode" and args.sample_parameters and (args.axis is not None or args.output_color is not None):
        parser.error("--sample-parameters cannot be combined with explicit parameter values")
    out = args.out.resolve()
    if out.exists():
        parser.error(f"Output already exists; use a new directory: {out}")
    out.mkdir(parents=True)
    oracle = None
    try:
        oracle = RacketOracle()
        canonical, witness = check_canonical(oracle), check_witness(oracle)
        if args.command == "verify":
            seeds = args.seed if args.seed is not None else [0, 17]
            episodes = [
                build_episode(seed, p, oracle=oracle, parameter_selection="enumerated setting fixed per episode")
                for seed in seeds for p in all_parameters()
            ]
        else:
            p = sample_parameters(args.seed) if args.sample_parameters else Parameters(args.axis or "vertical", 7 if args.output_color is None else args.output_color)
            episodes = [build_episode(
                args.seed, p, oracle=oracle, n_train=args.train, n_test=args.test,
                parameter_selection="seeded once" if args.sample_parameters else "fixed/default",
            )]
        summary = save_evidence(out, episodes, oracle, canonical, witness)
        print(json.dumps({key: summary[key] for key in (
            "status", "scope", "episode_count", "seeds", "actual_racket_evaluations",
            "canonical_pairs_checked", "parameter_rival_comparisons", "ambiguities",
        )}, sort_keys=True))
        return 0
    except Exception as exc:
        _write_json(out / "private/failure.json", {
            "status": "error", "scope": "prototype", "exit_status": 2,
            "invocation": invocation(), "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "completed_executions": [] if oracle is None else oracle.executions,
        })
        print(f"Prototype failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if oracle is not None:
            oracle.close()


if __name__ == "__main__":
    raise SystemExit(main())
