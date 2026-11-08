"""Isolated Racket-backed inset-depth episodes for ``dbecc530afd0``.

This is review evidence for a possible parameterized task family.  It is not
imported by the production generator and does not change canonical semantics.
Every retained label, including counterfactual labels, is executed by the
bundled Racket authority.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from itertools import combinations
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "dbecc530afd0"
INSET_DEPTHS = (1, 2)
DEFAULT_INSET_DEPTH = 1
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_DEMO_COUNT = 8
MAX_QUERY_COUNT = 8
MAX_PAIR_COUNT = 12
MAX_DRAW_ATTEMPTS_PER_PAIR = 64

_CANONICAL_PAINT_SITE = "((and (> r r1) (< r r2) (> c c1) (< c c2)) 2)"
_DEPTH_TWO_PAINT_SITE = (
    "((and (> r (+ r1 1)) (< r (- r2 1)) "
    "(> c (+ c1 1)) (< c (- c2 1))) 2)"
)


def sha256(value: str | bytes) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@lru_cache(maxsize=4)
def canonical_rule(*, root=None) -> str:
    """Return the one unique exact canonical Racket program for this task."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source:
                    raise ValueError("Canonical row is missing an exact program_solution.")
                sources.append(source)
    unique = set(sources)
    if not sources or len(unique) != 1:
        raise ValueError(
            "The inset-depth prototype requires one unique exact canonical rule; "
            f"found {len(sources)} rows and {len(unique)} unique sources."
        )
    return sources[0]


def validate_setting(inset_depth) -> int:
    """Validate and return one exact episode-wide inset depth."""
    if type(inset_depth) is not int or inset_depth not in INSET_DEPTHS:
        raise ValueError(
            f"inset_depth must be one of {INSET_DEPTHS}, as a Python int (not bool)"
        )
    return inset_depth


def program_for_depth(inset_depth=DEFAULT_INSET_DEPTH, *, root=None) -> str:
    """Materialize the exact Racket authority for one setting.

    Depth 1 is returned byte-for-byte from the canonical ledger.  Depth 2 makes
    one guarded structural substitution at the selected cell-paint predicate;
    rectangle detection, overlap composition, colors, and all other code stay
    identical.
    """
    inset_depth = validate_setting(inset_depth)
    source = canonical_rule(root=root)
    if inset_depth == DEFAULT_INSET_DEPTH:
        return source
    if source.count(_CANONICAL_PAINT_SITE) != 1:
        raise ValueError(
            "Canonical paint predicate changed; reassess the inset-depth prototype."
        )
    return source.replace(_CANONICAL_PAINT_SITE, _DEPTH_TWO_PAINT_SITE, 1)


def evaluate(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact program on one normalized grid through Racket."""
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected the selected task's native Racket lambda.")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def _validate_seed(seed) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative Python int (not bool)")
    return seed


def choose_inset_depth(seed) -> int:
    """Choose one setting once per episode without touching global RNG state."""
    seed = _validate_seed(seed)
    return INSET_DEPTHS[seed % len(INSET_DEPTHS)]


def validate_counts(demo_count, query_count) -> tuple[int, int]:
    """Validate independent episode counts within the bounded sampler support."""
    limits = (
        ("demo", demo_count, MAX_DEMO_COUNT),
        ("query", query_count, MAX_QUERY_COUNT),
    )
    for name, value, maximum in limits:
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError(
                f"{name}_count must be a Python int (not bool) in 1..{maximum}"
            )
    if demo_count + query_count > MAX_PAIR_COUNT:
        raise ValueError(
            f"combined count must not exceed {MAX_PAIR_COUNT} pairs per episode"
        )
    return demo_count, query_count


def _corners(rect: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, r2, c1, c2 = rect
    return {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}


def _all_rectangles(cells: set[tuple[int, int]]) -> list[tuple[int, int, int, int]]:
    by_row: dict[int, set[int]] = {}
    for row, col in cells:
        by_row.setdefault(row, set()).add(col)
    result: list[tuple[int, int, int, int]] = []
    rows = sorted(by_row)
    for r1, r2 in combinations(rows, 2):
        common = sorted(by_row[r1] & by_row[r2])
        for c1, c2 in combinations(common, 2):
            result.append((r1, r2, c1, c2))
    return result


def _single_rectangle(rng: random.Random) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    height = rng.randint(9, 15)
    width = rng.randint(9, 15)
    r1 = rng.randint(1, height - 6)
    r2 = rng.randint(r1 + 4, height - 2)
    c1 = rng.randint(1, width - 6)
    c2 = rng.randint(c1 + 4, width - 2)
    return height, width, [(r1, r2, c1, c2)]


def _two_separated_rectangles(
    rng: random.Random,
) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    """Construct two >=5x5 rectangles with disjoint row and column sets."""
    height = rng.randint(16, 18)
    width = rng.randint(16, 18)

    r1a = rng.randint(0, 1)
    r2a = rng.randint(r1a + 4, min(r1a + 6, 7))
    c1a = rng.randint(0, 1)
    c2a = rng.randint(c1a + 4, min(c1a + 6, 7))

    r2b = height - 1 - rng.randint(0, 1)
    r1b = rng.randint(max(8, r2b - 6), r2b - 4)
    c2b = width - 1 - rng.randint(0, 1)
    c1b = rng.randint(max(8, c2b - 6), c2b - 4)

    return height, width, [(r1a, r2a, c1a, c2a), (r1b, r2b, c1b, c2b)]


def _render_input(
    height: int,
    width: int,
    rectangles: list[tuple[int, int, int, int]],
) -> list[list[int]]:
    corner_cells: set[tuple[int, int]] = set()
    for rectangle in rectangles:
        r1, r2, c1, c2 = rectangle
        if r2 - r1 < 4 or c2 - c1 < 4:
            raise RuntimeError("Prototype rectangles must be at least 5x5.")
        corner_cells.update(_corners(rectangle))
    if len(corner_cells) != 4 * len(rectangles):
        raise RuntimeError("Prototype rectangles unexpectedly share a corner.")
    if sorted(_all_rectangles(corner_cells)) != sorted(rectangles):
        raise RuntimeError("Prototype construction created an accidental rectangle.")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in corner_cells:
        grid[row][col] = 4
    return grid


def generate_inputs(seed, count=DEFAULT_DEMO_COUNT + DEFAULT_QUERY_COUNT) -> list[list[list[int]]]:
    """Generate distinct deterministic shared-domain inputs independent of setting."""
    seed = _validate_seed(seed)
    if type(count) is not int or not 1 <= count <= MAX_PAIR_COUNT:
        raise ValueError(f"count must be a Python int (not bool) in 1..{MAX_PAIR_COUNT}")
    rng = random.Random(f"{TASK_ID}:inset-depth-inputs:{seed}")
    inputs: list[list[list[int]]] = []
    seen: set[str] = set()
    attempts = 0
    while len(inputs) < count:
        if attempts >= count * MAX_DRAW_ATTEMPTS_PER_PAIR:
            raise RuntimeError(
                f"distinct input support exhausted after {attempts} draws for count={count}"
            )
        attempts += 1
        index = len(inputs)
        if index % 2 == 0:
            height, width, rectangles = _single_rectangle(rng)
        else:
            height, width, rectangles = _two_separated_rectangles(rng)
        grid = _render_input(height, width, rectangles)
        identity = json.dumps(grid, separators=(",", ":"))
        if identity in seen:
            continue
        seen.add(identity)
        inputs.append(grid)
    return inputs


def generate_episode(
    bridge: RacketBridge,
    seed,
    *,
    inset_depth=None,
    demo_count=DEFAULT_DEMO_COUNT,
    query_count=DEFAULT_QUERY_COUNT,
) -> dict:
    """Choose one depth once and Racket-label independent demos and queries."""
    seed = _validate_seed(seed)
    demo_count, query_count = validate_counts(demo_count, query_count)
    chosen = choose_inset_depth(seed) if inset_depth is None else validate_setting(inset_depth)
    program = program_for_depth(chosen)
    pairs = [
        {"input": grid, "output": evaluate(bridge, program, grid)}
        for grid in generate_inputs(seed, demo_count + query_count)
    ]
    return {
        "seed": seed,
        "parameters": {"inset_depth": chosen},
        "counts": {"demonstrations": demo_count, "queries": query_count},
        "parameter_choice": (
            "seed_modulo_two" if inset_depth is None else "explicit_once_per_episode"
        ),
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": pairs,
    }


def public_challenge(episode: dict) -> dict:
    """Redact rule choice, programs, rival outputs, and query answer."""
    counts = episode.get("counts", {})
    demo_count, query_count = validate_counts(
        counts.get("demonstrations"), counts.get("queries")
    )
    pairs = episode.get("pairs")
    if type(pairs) is not list or len(pairs) != demo_count + query_count:
        raise ValueError("episode pairs do not match the declared count")
    return deepcopy(
        {
            "train": pairs[:demo_count],
            "test": [
                {"input": pair["input"]}
                for pair in pairs[demo_count:]
            ],
        }
    )


def analyze_episode(bridge: RacketBridge, episode: dict) -> dict:
    """Check each query against the opposite-depth rival using demos only."""
    pairs = episode["pairs"]
    counts = episode.get("counts", {})
    demo_count, query_count = validate_counts(
        counts.get("demonstrations"), counts.get("queries")
    )
    if len(pairs) != demo_count + query_count:
        raise ValueError("episode pairs do not match the declared count")
    chosen = validate_setting(episode["parameters"]["inset_depth"])
    rival_depth = next(depth for depth in INSET_DEPTHS if depth != chosen)
    rival_program = program_for_depth(rival_depth)
    rival_outputs = [evaluate(bridge, rival_program, pair["input"]) for pair in pairs]

    demonstration_indices = list(range(demo_count))
    query_indices = list(range(demo_count, demo_count + query_count))
    refutations = [
        index
        for index in demonstration_indices
        if rival_outputs[index] != pairs[index]["output"]
    ]

    def score(query_index: int) -> dict:
        rival = {
            "name": f"inset_depth={rival_depth}",
            "parameters": {"inset_depth": rival_depth},
            "refuting_demonstration_indices": refutations,
            "fits_demonstrations": not refutations,
            "query_differs": rival_outputs[query_index] != pairs[query_index]["output"],
        }
        ambiguous = rival["fits_demonstrations"] and rival["query_differs"]
        return {
            "query_index": query_index,
            "demonstration_indices": list(demonstration_indices),
            "rivals": [rival],
            "status": "ambiguous" if ambiguous else "no_ambiguity_found",
        }

    query_checks = [score(index) for index in query_indices]
    return {
        "status": (
            "ambiguous"
            if any(row["status"] == "ambiguous" for row in query_checks)
            else "no_ambiguity_found"
        ),
        "demonstration_indices": demonstration_indices,
        "query_indices": query_indices,
        "query_checks": query_checks,
        "counterfactual_outputs": {str(rival_depth): rival_outputs},
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_evidence(
    out,
    *,
    seed=0,
    demo_count=DEFAULT_DEMO_COUNT,
    query_count=DEFAULT_QUERY_COUNT,
    bridge=None,
) -> dict:
    """Materialize content-addressed public and private evidence in a new directory."""
    seed = _validate_seed(seed)
    demo_count, query_count = validate_counts(demo_count, query_count)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    report = {
        "schema": "dbecc530afd0-inset-depth-prototype-v2",
        "status": "incomplete",
        "scope": (
            "proposed task-local extension; not a canonical rule change or "
            "production approval"
        ),
        "parameter_spec": {
            "inset_depth": {
                "allowed": list(INSET_DEPTHS),
                "original_default": DEFAULT_INSET_DEPTH,
            }
        },
        "count_spec": {
            "demonstrations": {
                "requested": demo_count,
                "allowed": [1, MAX_DEMO_COUNT],
            },
            "queries": {
                "requested": query_count,
                "allowed": [1, MAX_QUERY_COUNT],
            },
            "combined_pair_limit": MAX_PAIR_COUNT,
            "distinct_draw_attempts_per_pair": MAX_DRAW_ATTEMPTS_PER_PAIR,
        },
        "choice_policy": (
            "One value per episode: [1,2][seed % 2]; two consecutive seeds "
            "cover both settings."
        ),
        "lesson_policy": (
            f"{demo_count} shared demonstrations followed by {query_count} distinct "
            "queries. Every label is executed through the episode's exact Racket "
            "program; rival checks use demonstrations only."
        ),
        "public_identity_policy": (
            "Public filenames are challenge-<sha256>.json, where the digest is over "
            "canonical visible demonstration pairs and query inputs only. Hidden "
            "settings, seeds, programs, and query answers are excluded."
        ),
        "input_domain": (
            "9..18 rows/columns, zero background, one or two complete yellow "
            "rectangles, no accidental rectangles, each rectangle at least 5x5."
        ),
        "limitations": (
            "Two consecutive seeds and the sole declared opposite-depth rival are "
            "checked. Counts are bounded to at most 8 demonstrations, 8 queries, "
            "and 12 total pairs. The sampler is a lawful subset, not a production API."
        ),
        "source_hashes": {
            "prototype.py": sha256(Path(__file__).read_bytes()),
            "canonical_racket": sha256(canonical_rule(root=root)),
        },
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "canonical_checks": [],
        "episodes": [],
    }

    try:
        with (nullcontext(bridge) if bridge is not None else RacketBridge()) as active:
            report["runtime"] = {
                "python": sys.version,
                "racket_version": active.eval_text("(version)"),
                "bridge_sha256": sha256(
                    Path(sys.modules[RacketBridge.__module__].__file__).read_bytes()
                ),
                "prelude_sha256": sha256(Path(active.prelude_path).read_bytes()),
            }

            for depth in INSET_DEPTHS:
                path = out / "private" / "rules" / f"inset-depth-{depth}.rkt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(program_for_depth(depth, root=root), encoding="utf-8")

            canonical_program = program_for_depth(DEFAULT_INSET_DEPTH, root=root)
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = evaluate(active, canonical_program, pair["input"])
                report["canonical_checks"].append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "input": pair["input"],
                        "expected": pair["output"],
                        "actual": actual,
                        "passed": actual == pair["output"],
                    }
                )

            all_inputs: set[str] = set()
            setting_witness = None
            pending = []
            for index in range(2):
                episode = generate_episode(
                    active,
                    seed + index,
                    demo_count=demo_count,
                    query_count=query_count,
                )
                scores = analyze_episode(active, episode)
                public = public_challenge(episode)
                payload = public_challenge_bytes(public)
                public_id = public_challenge_id(public)
                pending.append(
                    {
                        "public_id": public_id,
                        "public": public,
                        "payload": payload,
                        "episode": episode,
                        "scores": scores,
                    }
                )
                all_inputs.update(
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in episode["pairs"]
                )
                if setting_witness is None:
                    chosen = episode["parameters"]["inset_depth"]
                    rival = next(depth for depth in INSET_DEPTHS if depth != chosen)
                    setting_witness = {
                        "input": episode["pairs"][0]["input"],
                        "outputs": {
                            str(chosen): episode["pairs"][0]["output"],
                            str(rival): scores["counterfactual_outputs"][str(rival)][0],
                        },
                        "racket_hashes": {
                            str(depth): sha256(program_for_depth(depth, root=root))
                            for depth in INSET_DEPTHS
                        },
                    }

            public_ids = [row["public_id"] for row in pending]
            if len(public_ids) != len(set(public_ids)):
                raise RuntimeError("duplicate public challenge bytes/identifier")

            for artifact in sorted(pending, key=lambda row: row["public_id"]):
                public_id = artifact["public_id"]
                episode = artifact["episode"]
                scores = artifact["scores"]
                public_path = f"public/challenge-{public_id}.json"
                private_path = f"private/episodes/{public_id}.json"
                destination = out / public_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(artifact["payload"])
                _write_json(
                    out / private_path,
                    {**episode, "public_id": public_id, "rival_checks": scores},
                )
                report["episodes"].append(
                    {
                        "public_id": public_id,
                        "public_sha256": sha256(artifact["payload"]),
                        "public_bytes": len(artifact["payload"]),
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "counts": episode["counts"],
                        "racket_sha256": episode["racket_sha256"],
                        "public_path": public_path,
                        "private_path": private_path,
                        "status": scores["status"],
                        "demonstration_indices": scores["demonstration_indices"],
                        "query_indices": scores["query_indices"],
                        "query_checks": scores["query_checks"],
                    }
                )

            query_ambiguities = sum(
                check["status"] == "ambiguous"
                for row in report["episodes"]
                for check in row["query_checks"]
            )
            query_checks = sum(len(row["query_checks"]) for row in report["episodes"])
            canonical_passed = sum(row["passed"] for row in report["canonical_checks"])
            report["setting_witness"] = setting_witness
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "episodes": len(report["episodes"]),
                "demonstrations": len(report["episodes"]) * demo_count,
                "queries": len(report["episodes"]) * query_count,
                "episode_labels": len(report["episodes"]) * (demo_count + query_count),
                "counterfactual_labels": len(report["episodes"])
                * (demo_count + query_count),
                "query_checks": query_checks,
                "query_ambiguities": query_ambiguities,
                "unique_episode_inputs": len(all_inputs),
                "unique_public_challenges": len(set(public_ids)),
            }
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passed == len(report["canonical_checks"])
                and not query_ambiguities
                and len(report["episodes"]) == 2
                and len({
                    row["parameters"]["inset_depth"] for row in report["episodes"]
                }) == 2
                and len(set(public_ids)) == 2
                else "failed"
            )
            report["files"] = {
                str(path.relative_to(out)): {
                    "sha256": sha256(path.read_bytes()),
                    "bytes": path.stat().st_size,
                }
                for path in sorted(out.rglob("*"))
                if path.is_file()
            }
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        _write_json(out / "report.json", report)
        raise

    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="First of two consecutive episode seeds",
    )
    parser.add_argument(
        "--demo-count",
        type=int,
        default=DEFAULT_DEMO_COUNT,
        help=f"Demonstrations per episode (1..{MAX_DEMO_COUNT})",
    )
    parser.add_argument(
        "--query-count",
        type=int,
        default=DEFAULT_QUERY_COUNT,
        help=f"Queries per episode (1..{MAX_QUERY_COUNT})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="New evidence directory; existing paths are never overwritten",
    )
    args = parser.parse_args(argv)
    report = build_evidence(
        args.out,
        seed=args.seed,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return int(report["status"] != "no_ambiguity_found")


if __name__ == "__main__":
    raise SystemExit(main())
