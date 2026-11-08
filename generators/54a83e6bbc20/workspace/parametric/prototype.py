"""An isolated, fixed-per-episode assembly-order extension of ARC 18447a8d.

The canonical setting keeps cyan-anchor order. The proposed setting reverses
the order of complete assembled bands without reflecting either jigsaw piece.
Racket produces every label; Python predictions are assertions and finite rivals.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
import sys
from typing import Any

from reviewer_support import (
    canonical_path, find_root, load_selected_generator,
    public_challenge_bytes, public_challenge_id,
)


TASK_ID = "54a83e6bbc20"
PROTOTYPE_VERSION = "1.0.0"
CANONICAL_RULE_HASH = "82f172ba82d3"
ALLOWED_ASSEMBLY_ORDERS = ("top_to_bottom", "bottom_to_top")
DEFAULT_ASSEMBLY_ORDER = ALLOWED_ASSEMBLY_ORDERS[0]
DIFFICULTY = "hard"
MAX_SPLIT_COUNT = 32
ATTEMPTS_PER_PAIR = 32
PROTOTYPE_DIR = Path(__file__).resolve().parent
_CANONICAL_ORIGIN = "(r0 (obj-r1 left))"
_REVERSED_ORIGIN = "(r0 (- h 1 (obj-r2 left)))"


def _validate_order(assembly_order: str) -> str:
    if type(assembly_order) is not str or assembly_order not in ALLOWED_ASSEMBLY_ORDERS:
        raise ValueError(f"assembly_order must be one of {ALLOWED_ASSEMBLY_ORDERS}")
    return assembly_order


def choose_assembly_order(seed: int) -> str:
    """Choose once, before sampling any demonstration or query."""
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer, not bool")
    return ALLOWED_ASSEMBLY_ORDERS[seed % 2]


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_source(root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as handle:
        sources = {
            row["program_solution"] for line in handle if line.strip()
            if (row := json.loads(line)).get("task_id") == TASK_ID
            and row.get("program_solution")
        }
    if len(sources) != 1:
        raise ValueError(f"expected one exact canonical program for {TASK_ID}")
    source = sources.pop()
    if normalized_hash(source) != CANONICAL_RULE_HASH:
        raise ValueError("canonical authority changed; re-review this prototype")
    return source


def racket_source(assembly_order: str, *, root: Path | str) -> str:
    """Preserve the exact canonical rule, changing only the output band origin."""
    order = _validate_order(assembly_order)
    source = _canonical_source(Path(root))
    if source.count(_CANONICAL_ORIGIN) != 1:
        raise ValueError("expected exactly one canonical output-origin clause")
    if order == DEFAULT_ASSEMBLY_ORDER:
        return source
    return source.replace(_CANONICAL_ORIGIN, _REVERSED_ORIGIN)


def materialize_rules(*, root: Path | str, out: Path | str | None = None) -> dict[str, str]:
    """Keep exact executable sources; refuse to replace conflicting rule files."""
    destination = PROTOTYPE_DIR / "racket" if out is None else Path(out)
    sources = {order: racket_source(order, root=root).encode() for order in ALLOWED_ASSEMBLY_ORDERS}
    for order, source in sources.items():
        path = destination / f"{order}.rkt"
        if path.is_symlink() or (path.exists() and path.read_bytes() != source):
            raise FileExistsError(f"conflicting retained rule: {path}")
    destination.mkdir(parents=True, exist_ok=True)
    for order, source in sources.items():
        path = destination / f"{order}.rkt"
        if not path.exists():
            with path.open("xb") as handle:
                handle.write(source)
    return {order: hashlib.sha256(source).hexdigest() for order, source in sources.items()}


def _apply_order(output: list[list[int]], assembly_order: str) -> list[list[int]]:
    order = _validate_order(assembly_order)
    result = copy.deepcopy(output)
    if order == "bottom_to_top":
        starts = list(range(1, len(output) - 1, 4))
        for target, origin in zip(starts, reversed(starts)):
            result[target:target + 3] = copy.deepcopy(output[origin:origin + 3])
    return result


def python_transform(grid: list[list[int]], assembly_order: str, *, root: Path | str) -> list[list[int]]:
    """Assertion mirror on the selected generator's validated input grammar."""
    order = _validate_order(assembly_order)
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    return _apply_order(generator.rule_mirror(grid), order)


def _racket_literal(value: Any) -> str:
    if type(value) is list:
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"expected an ARC integer literal, got {value!r}")
    return str(value)


def _racket_outputs(source: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the actual Racket rule, with no Python fallback."""
    from arc_repl.racket_bridge import RacketBridge

    source = source.strip()
    if not source.startswith("(rule! (lambda ") or not source.endswith(")"):
        raise ValueError("expected a plain (rule! (lambda ...)) source")
    body = source[len("(rule! "):-1].strip()
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define assembly-prototype-rule {body})")
        outputs = bridge.eval_text(f"(map assembly-prototype-rule '{_racket_literal(grids)})")
    if type(outputs) is not list or len(outputs) != len(grids):
        raise RuntimeError("Racket returned an unexpected number of output grids")
    return outputs


def _programs(*, root: Path | str) -> dict[str, Any]:
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    programs = {
        order: (lambda grid, order=order: _apply_order(generator.rule_mirror(grid), order))
        for order in ALLOWED_ASSEMBLY_ORDERS
    }
    # Lift each matching shortcut into both orders. Otherwise the order alone
    # could refute a shortcut without teaching the omitted shape relationship.
    for name, predict in generator.SEMANTIC_RIVALS.items():
        for order in ALLOWED_ASSEMBLY_ORDERS:
            programs[f"{name}@{order}"] = (
                lambda grid, predict=predict, order=order: _apply_order(predict(grid), order)
            )
    programs["flip_rows"] = lambda grid: list(reversed(generator.rule_mirror(grid)))
    programs["flip_columns"] = lambda grid: [list(reversed(row)) for row in generator.rule_mirror(grid)]
    programs["rotate_180"] = lambda grid: [list(reversed(row)) for row in reversed(generator.rule_mirror(grid))]

    def candidate_order(grid, reverse=False):
        analysis = generator._analysis(grid)
        if analysis["errors"]:
            raise ValueError("candidate-order rival requires a lawful scene")
        canonical = generator.rule_mirror(grid)
        result = [[7] * len(grid[0]) for _ in grid]
        indices = list(analysis["candidate_order"])
        if reverse:
            indices.reverse()
        for slot, left_index in enumerate(indices):
            result[1 + 4 * slot:4 + 4 * slot] = copy.deepcopy(
                canonical[1 + 4 * left_index:4 + 4 * left_index]
            )
        return result

    programs["candidate_order"] = candidate_order
    programs["candidate_order_reversed"] = lambda grid: candidate_order(grid, reverse=True)
    return programs


def analyze_rivals(episode: dict[str, Any], *, root: Path | str) -> dict[str, Any]:
    """Filter a finite program set on demonstrations; only then inspect queries."""
    if not episode.get("train") or not episode.get("test"):
        raise ValueError("rival analysis requires nonempty demonstration and query lists")
    programs = _programs(root=root)
    survivors, rejected = [], {}
    for name, predict in programs.items():
        for index, pair in enumerate(episode["train"]):
            if predict(pair["input"]) != pair["output"]:
                rejected[name] = index
                break
        else:
            survivors.append(name)
    queries = []
    for index, pair in enumerate(episode["test"]):
        agreeing, disagreeing = [], []
        for name in survivors:
            destination = agreeing if programs[name](pair["input"]) == pair["output"] else disagreeing
            destination.append(name)
        queries.append({
            "query_index": index,
            "agreeing_survivors": agreeing,
            "disagreeing_survivors": disagreeing,
            "identifiable": bool(survivors) and not disagreeing,
        })
    return {
        "rival_names": list(programs),
        "filtering_inputs": "demonstration inputs and outputs only",
        "demo_survivors": survivors,
        "demo_rejections": rejected,
        "queries": queries,
        "scope": "Finite declared program set; not universal identifiability or measured learning performance.",
    }


def _validate_count(name: str, value: int, minimum: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer, not bool")
    if not minimum <= value <= MAX_SPLIT_COUNT:
        raise ValueError(f"{name} must be in {minimum}..{MAX_SPLIT_COUNT}")
    return value


def build_episode(*, root: Path | str, seed: int, n_train: int = 3, n_test: int = 4) -> dict[str, Any]:
    """Return one independently counted, distinct, Racket-labelled episode.

    Three demonstrations retain the producer's equal-area and row-critical
    anchors. Sampling is bounded, and failed support/teaching raises explicitly.
    """
    order = choose_assembly_order(seed)
    _validate_count("n_train", n_train, 3)
    _validate_count("n_test", n_test, 1)
    root = Path(root).resolve()
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    if generator.RULE_HASH != CANONICAL_RULE_HASH:
        raise ValueError("selected generator authority differs from the prototype")
    pairs, seen = [], set()
    sample_index = duplicates = 0
    for split, requested in (("train", n_train), ("test", n_test)):
        accepted = 0
        for _ in range(ATTEMPTS_PER_PAIR * requested):
            index = sample_index
            sample_index += 1
            grid = generator.generate(seed, index, difficulty=DIFFICULTY)
            errors = generator.self_check(grid)
            if errors:
                raise ValueError(f"producer emitted an invalid {split} input: {errors}")
            key = tuple(tuple(row) for row in grid)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            pairs.append({"sample_index": index, "input": copy.deepcopy(grid),
                          "observed_axes": generator.observe_overrides(grid)})
            accepted += 1
            if accepted == requested:
                break
        else:
            raise RuntimeError(f"{split}: only {accepted}/{requested} distinct inputs after "
                               f"{ATTEMPTS_PER_PAIR * requested} attempts; no partial episode returned")
    source = racket_source(order, root=root)
    outputs = _racket_outputs(source, [pair["input"] for pair in pairs])
    expected = [_apply_order(generator.rule_mirror(pair["input"]), order) for pair in pairs]
    if outputs != expected:
        raise AssertionError(f"{order}: actual Racket labels disagree with the assertion mirror")
    for pair, output in zip(pairs, outputs):
        pair["output"] = copy.deepcopy(output)
    episode = {
        "schema": "arcpuzzles-parametric-jigsaw-order-episode-v1",
        "status": "prototype", "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION,
        "seed": seed, "parameters": {"assembly_order": order}, "difficulty": DIFFICULTY,
        "requested_counts": {"n_train": n_train, "n_test": n_test},
        "selected_generator_path": str(generator_path.relative_to(root)),
        "generator_sha256": generator_sha,
        "prototype_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "racket_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "rule_hash": normalized_hash(source), "label_source": "executed_racket",
        "sampling": {"attempts": sample_index, "duplicate_inputs_rejected": duplicates,
                     "distinct_inputs": len(seen), "attempt_budget_per_pair": ATTEMPTS_PER_PAIR},
        "train": pairs[:n_train], "test": pairs[n_train:],
    }
    evidence = analyze_rivals(episode, root=root)
    if order not in evidence["demo_survivors"] or not all(row["identifiable"] for row in evidence["queries"]):
        raise RuntimeError("demonstrations leave a query-changing rival; no ambiguous episode returned")
    episode["rival_analysis"] = evidence
    return episode


def write_public_challenges(episodes: Iterable[dict[str, Any]], *, out: Path | str) -> list[dict[str, str]]:
    """Export exact visible bytes under opaque content IDs, without overwrites."""
    payloads = {}
    for episode in episodes:
        public_id = public_challenge_id(episode)
        if public_id in payloads:
            raise ValueError(f"duplicate visible challenge: {public_id}")
        payloads[public_id] = public_challenge_bytes(episode)
    if not payloads:
        raise ValueError("at least one public challenge is required")
    destination = Path(out)
    rows = [{"public_id": key, "filename": f"{key}.json"} for key in sorted(payloads)]
    for row in rows:
        path = destination / row["filename"]
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"public destination already exists: {path}")
    destination.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for row in rows:
            path = destination / row["filename"]
            with path.open("xb") as handle:
                created.append(path)
                handle.write(payloads[row["public_id"]])
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", help="repeat for multiple episodes; default: 18 and 19")
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True, help="new private evidence JSON path")
    parser.add_argument("--write-public", type=Path, help="directory containing only visible challenge files")
    args = parser.parse_args(argv)
    private = args.out.resolve()
    if private.exists() or args.out.is_symlink():
        raise FileExistsError(f"private evidence already exists: {args.out}")
    if args.write_public is not None and private.is_relative_to(args.write_public.resolve()):
        raise ValueError("private evidence must be outside the public challenge directory")
    seeds = [18, 19] if args.seed is None else args.seed
    if len(set(seeds)) != len(seeds):
        raise ValueError("episode seeds must be distinct")
    root = find_root(__file__)
    _validate_count("n_train", args.n_train, 3)
    _validate_count("n_test", args.n_test, 1)
    rule_hashes = materialize_rules(root=root)
    episodes = [build_episode(root=root, seed=seed, n_train=args.n_train, n_test=args.n_test) for seed in seeds]
    rows = write_public_challenges(episodes, out=args.write_public) if args.write_public else []
    report = {
        "schema": "arcpuzzles-parametric-jigsaw-order-report-v1", "status": "prototype",
        "task_id": TASK_ID, "parent": {"split": "training", "task_id": "18447a8d"},
        "argv": list(sys.argv if argv is None else [str(Path(__file__)), *argv]),
        "cwd": str(Path.cwd()), "prototype_version": PROTOTYPE_VERSION,
        "canonical_rule_hash": CANONICAL_RULE_HASH, "racket_sha256": rule_hashes,
        "parameters": {"assembly_order": list(ALLOWED_ASSEMBLY_ORDERS)},
        "default": {"assembly_order": DEFAULT_ASSEMBLY_ORDER},
        "episodes": episodes, "public_files": rows,
        "private_public_mapping": [{"seed": ep["seed"], "parameters": ep["parameters"],
                                    "public_id": public_challenge_id(ep)} for ep in episodes],
        "variant_approved": False, "training_admitted": False,
        "limits": ["Fixed three-row, width-five prefix/suffix grammar; default episodes use four pieces.",
                   "n_train is 3..32; n_test is 1..32. Finite sampling can fail explicitly.",
                   "Identifiability is checked against 19 declared programs, not every possible solver.",
                   "No production parametric API, new safety approval, or measured learning claim."],
    }
    private.parent.mkdir(parents=True, exist_ok=True)
    with private.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
    print(json.dumps({"episodes": len(episodes), "counts": [args.n_train, args.n_test],
                      "racket_labels": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                      "query_checks": sum(len(ep["test"]) for ep in episodes),
                      "demo_survivors": [ep["rival_analysis"]["demo_survivors"] for ep in episodes],
                      "out": str(args.out), "public_files": rows}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
