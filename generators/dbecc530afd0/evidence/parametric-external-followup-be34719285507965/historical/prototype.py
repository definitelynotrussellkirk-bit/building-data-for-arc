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
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK_ID = "dbecc530afd0"
INSET_DEPTHS = (1, 2)
DEFAULT_INSET_DEPTH = 1

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


def generate_inputs(seed) -> list[list[list[int]]]:
    """Generate four deterministic, shared-domain inputs independent of setting."""
    seed = _validate_seed(seed)
    rng = random.Random(f"{TASK_ID}:inset-depth-inputs:{seed}")
    inputs: list[list[list[int]]] = []
    for index in range(4):
        if index % 2 == 0:
            height, width, rectangles = _single_rectangle(rng)
        else:
            height, width, rectangles = _two_separated_rectangles(rng)
        inputs.append(_render_input(height, width, rectangles))
    return inputs


def generate_episode(
    bridge: RacketBridge,
    seed,
    *,
    inset_depth=None,
) -> dict:
    """Choose one depth once and obtain all four labels from that Racket program."""
    seed = _validate_seed(seed)
    chosen = choose_inset_depth(seed) if inset_depth is None else validate_setting(inset_depth)
    program = program_for_depth(chosen)
    pairs = [
        {"input": grid, "output": evaluate(bridge, program, grid)}
        for grid in generate_inputs(seed)
    ]
    return {
        "seed": seed,
        "parameters": {"inset_depth": chosen},
        "parameter_choice": (
            "seed_modulo_two" if inset_depth is None else "explicit_once_per_episode"
        ),
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": pairs,
    }


def public_challenge(episode: dict) -> dict:
    """Redact rule choice, programs, rival outputs, and query answer."""
    return deepcopy(
        {
            "train": episode["pairs"][:3],
            "test": [{"input": episode["pairs"][3]["input"]}],
        }
    )


def analyze_episode(bridge: RacketBridge, episode: dict) -> dict:
    """Check the sole opposite-depth rival under production and all rotations."""
    pairs = episode["pairs"]
    chosen = validate_setting(episode["parameters"]["inset_depth"])
    rival_depth = next(depth for depth in INSET_DEPTHS if depth != chosen)
    rival_program = program_for_depth(rival_depth)
    rival_outputs = [evaluate(bridge, rival_program, pair["input"]) for pair in pairs]

    def score(query_index: int) -> dict:
        demonstration_indices = [index for index in range(4) if index != query_index]
        refutations = [
            index
            for index in demonstration_indices
            if rival_outputs[index] != pairs[index]["output"]
        ]
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
            "demonstration_indices": demonstration_indices,
            "rivals": [rival],
            "status": "ambiguous" if ambiguous else "no_ambiguity_found",
        }

    return {
        "production": score(3),
        "rotations": [score(index) for index in range(4)],
        "counterfactual_outputs": {str(rival_depth): rival_outputs},
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_evidence(out, *, seed=0, bridge=None) -> dict:
    """Materialize private/public evidence into a new directory only."""
    seed = _validate_seed(seed)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    report = {
        "schema": "dbecc530afd0-inset-depth-prototype-v1",
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
        "choice_policy": (
            "One value per episode: [1,2][seed % 2]; two consecutive seeds "
            "cover both settings."
        ),
        "lesson_policy": (
            "Three demonstrations followed by one query; every input is a "
            "depth witness and all four single-query rotations are checked."
        ),
        "input_domain": (
            "9..18 rows/columns, zero background, one or two complete yellow "
            "rectangles, no accidental rectangles, each rectangle at least 5x5."
        ),
        "limitations": (
            "Two consecutive seeds and the sole declared opposite-depth rival "
            "are checked. The sampler is a bounded lawful subset, not a production API."
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
            for index in range(2):
                episode = generate_episode(active, seed + index)
                scores = analyze_episode(active, episode)
                public_path = f"public/episode-{index + 1:03d}.json"
                private_path = f"private/episode-{index + 1:03d}.json"
                _write_json(out / public_path, public_challenge(episode))
                _write_json(out / private_path, {**episode, "rival_checks": scores})
                report["episodes"].append(
                    {
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "racket_sha256": episode["racket_sha256"],
                        "public_path": public_path,
                        "private_path": private_path,
                        "production": scores["production"],
                        "rotations": scores["rotations"],
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

            production_ambiguities = sum(
                row["production"]["status"] == "ambiguous"
                for row in report["episodes"]
            )
            rotation_ambiguities = sum(
                rotation["status"] == "ambiguous"
                for row in report["episodes"]
                for rotation in row["rotations"]
            )
            canonical_passed = sum(
                row["passed"] for row in report["canonical_checks"]
            )
            report["setting_witness"] = setting_witness
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "episodes": 2,
                "demonstrations": 6,
                "queries": 2,
                "episode_labels": 8,
                "counterfactual_labels": 8,
                "production_ambiguities": production_ambiguities,
                "rotation_ambiguities": rotation_ambiguities,
                "query_rotations": 8,
                "unique_episode_inputs": len(all_inputs),
            }
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passed == len(report["canonical_checks"])
                and not production_ambiguities
                and not rotation_ambiguities
                and len({
                    row["parameters"]["inset_depth"] for row in report["episodes"]
                }) == 2
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
        "--out",
        type=Path,
        required=True,
        help="New evidence directory; existing paths are never overwritten",
    )
    args = parser.parse_args(argv)
    report = build_evidence(args.out, seed=args.seed)
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
