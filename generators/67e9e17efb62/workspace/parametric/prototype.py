"""Unapproved peak-repetition rule prototype for ARC family 67e9e17efb62.

The canonical/default setting emits one maximum-length run.  The alternative
emits that peak run twice.  Every label and rival prediction is executed from
materialized Racket through the included bridge; this file does not import the
selected production generator.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys
import traceback
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK_ID = "67e9e17efb62"
PARAMETER = "peak_repetitions"
ALLOWED_VALUES = (1, 2)
DEFAULT_VALUE = 1
CANONICAL_TEXT_SHA256 = "1212a5180faaf8260ab3490d2b2cf153a607dd72076a17babe9a9e9b8637cb64"
_EDIT_POINT = "(range (- L 1) 0 -1)"
_ALTERNATIVE_EDIT = "(range L 0 -1)"


def digest(value: Any) -> str:
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def validate_peak_repetitions(value: Any) -> int:
    if type(value) is not int or value not in ALLOWED_VALUES:
        raise ValueError("peak_repetitions must be the literal integer 1 or 2")
    return value


def choose_peak_repetitions(seed: Any) -> int:
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    bit = int.from_bytes(
        hashlib.sha256(f"peak-repetitions-v1:{seed}".encode()).digest()[:8], "big"
    ) % 2
    return ALLOWED_VALUES[bit]


def example_seeds() -> tuple[int, int]:
    """Return the first deterministic seed for each setting, in setting order."""
    found: dict[int, int] = {}
    for seed in range(256):
        found.setdefault(choose_peak_repetitions(seed), seed)
        if set(found) == set(ALLOWED_VALUES):
            return found[1], found[2]
    raise RuntimeError("failed to find bounded example seeds for both settings")


def _canonical_source(*, root: Path) -> str:
    sources = set()
    with canonical_path(root).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError("prototype requires one unambiguous canonical program")
    source = sources.pop()
    if digest(source.encode()) != CANONICAL_TEXT_SHA256:
        raise ValueError("canonical text changed; review this prototype before reuse")
    return source


def render_program(peak_repetitions: Any, *, root=None) -> str:
    """Materialize exact canonical Racket at 1 and a one-edit variant at 2."""
    setting = validate_peak_repetitions(peak_repetitions)
    root_path = Path(root) if root is not None else find_root(__file__)
    source = _canonical_source(root=root_path)
    if setting == DEFAULT_VALUE:
        return source
    if source.count(_EDIT_POINT) != 1 or _ALTERNATIVE_EDIT in source:
        raise ValueError("canonical peak edit point is absent or ambiguous")
    return source.replace(_EDIT_POINT, _ALTERNATIVE_EDIT)


def execute(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Apply this prototype's pinned rule lambda through the real Racket bridge."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    source = program.strip()
    if not source.startswith("(rule! (lambda (g)") or not source.endswith(")"):
        raise ValueError("prototype executes only its pinned single-lambda rule")
    body = source[len("(rule!") : -1].strip()
    return normalize_grid(bridge.eval_text(f"({body} {literal})"))


def input_issues(grid) -> list[str]:
    """Recognize the unchanged single edge-bar input grammar used by the family."""
    try:
        grid = normalize_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    h, w = len(grid), len(grid[0])
    issues: list[str] = []
    if not 3 <= h <= 14:
        issues.append(f"height must be 3..14, got {h}")
    if not 5 <= w <= 23:
        issues.append(f"width must be 5..23, got {w}")
    top = grid[0]
    nonzero = [c for c, value in enumerate(top) if value != 0]
    if not nonzero:
        issues.append("top row must contain a nonzero bar")
    else:
        start, end = min(nonzero), max(nonzero)
        if nonzero != list(range(start, end + 1)):
            issues.append("bar must be contiguous")
        colors = {top[c] for c in nonzero}
        if len(colors) != 1:
            issues.append("bar must be monochrome")
        length = len(nonzero)
        if not 3 <= length <= 8:
            issues.append(f"bar length must be 3..8, got {length}")
        if length >= w:
            issues.append("bar must leave at least one zero")
        if not ((start == 0 and end < w - 1) or (end == w - 1 and start > 0)):
            issues.append("bar must touch exactly one horizontal edge")
    if any(value != 0 for row in grid[1:] for value in row):
        issues.append("all rows below the top row must be zero")
    return issues


def _make_grid(height: int, width: int, length: int, color: int, side: str):
    grid = [[0] * width for _ in range(height)]
    start = 0 if side == "left" else width - length
    for c in range(start, start + length):
        grid[0][c] = color
    issues = input_issues(grid)
    if issues:
        raise ValueError("prototype constructed an invalid grid: " + "; ".join(issues))
    return grid


def episode_inputs(seed: Any) -> list[list[list[int]]]:
    """Construct three demonstrations and one query independently of the rule value."""
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    rng = random.Random(f"peak-repetition-inputs-v1:{seed}")
    lengths = (3, 4, 6, 8)
    colors = rng.sample(range(1, 10), 4)
    grids = []
    for index, (length, color) in enumerate(zip(lengths, colors)):
        height = rng.randint(3, 14)
        width = rng.randint(max(5, length + 1), min(23, length + 8))
        side = ("left", "right")[(rng.randrange(2) + index) % 2]
        grids.append(_make_grid(height, width, length, color, side))
    return grids


def generate_episode(seed: Any, *, bridge: RacketBridge, root=None) -> dict[str, Any]:
    setting = choose_peak_repetitions(seed)
    rival_setting = 3 - setting
    program = render_program(setting, root=root)
    rival_program = render_program(rival_setting, root=root)
    inputs = episode_inputs(seed)
    pairs = [
        {"input": grid, "output": execute(bridge, program, grid)} for grid in inputs
    ]
    predictions = [execute(bridge, rival_program, grid) for grid in inputs]
    refutations = [
        index for index in range(3) if predictions[index] != pairs[index]["output"]
    ]
    query_disagreements = [0] if predictions[3] != pairs[3]["output"] else []
    status = (
        "refuted_on_demonstrations"
        if refutations
        else "ambiguous_query"
        if query_disagreements
        else "survived_all"
    )
    return {
        "schema": "arcpuzzles-parametric-prototype-episode-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {PARAMETER: setting},
        "program": program,
        "program_sha256": digest(program.encode()),
        "train": pairs[:3],
        "test": pairs[3:],
        "input_sha256": [digest(grid) for grid in inputs],
        "parameter_rivals": {
            "parameters": {PARAMETER: rival_setting},
            "program": rival_program,
            "program_sha256": digest(rival_program.encode()),
            "predictions": predictions,
            "status": status,
            "refuting_demonstrations": refutations,
            "query_disagreements": query_disagreements,
        },
    }


def public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden rule, seed, programs, rivals, and query labels."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", action="append", type=int)
    args = parser.parse_args(argv)
    root = find_root(__file__)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    seeds = args.seed if args.seed is not None else list(example_seeds())
    run: dict[str, Any] = {
        "schema": "arcpuzzles-parametric-prototype-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "cwd": str(Path.cwd()),
        "payload_argv": sys.argv,
        "python_executable": sys.executable,
        "seeds": seeds,
        "parameter": {
            "name": PARAMETER,
            "allowed_values": list(ALLOWED_VALUES),
            "default": DEFAULT_VALUE,
            "meaning": "number of maximum-length colored runs in the serialized rise-and-fall sequence",
            "input_constraints": "unchanged single monochrome edge bar; L is still the peak run length",
        },
        "limitations": [
            "Separate proposed prototype; no production parametric API or approval claim",
            "Finite evidence covers two deterministic episodes, not every seed or rival hypothesis",
            "The hidden setting is episode-level and must be inferred from demonstrations",
            "Only the peak multiplicity changes; input grammar, separators, wrapping, and padding remain fixed",
        ],
    }
    write_json(out / "run.json", run)
    try:
        source_paths = [
            Path(__file__),
            Path(__file__).with_name("README.md"),
            root
            / f"generators/{TASK_ID}/tests/test_parametric_peak_repetitions.py",
        ]
        run["prototype_source_hashes"] = {
            path.relative_to(root).as_posix(): digest(path.read_bytes())
            for path in source_paths
        }
        run["reference_text_sha256"] = CANONICAL_TEXT_SHA256
        programs = {
            setting: render_program(setting, root=root) for setting in ALLOWED_VALUES
        }
        run["programs"] = {}
        for setting, program in programs.items():
            path = out / f"program-peak-repetitions-{setting}.rkt"
            path.write_text(program)
            run["programs"][str(setting)] = {
                "path": path.name,
                "sha256": digest(path.read_bytes()),
                "stripped_sha256": digest(program.strip().encode()),
                "catalog_style_hash": digest(" ".join(program.split()).encode())[:12],
            }

        with RacketBridge() as bridge:
            run["racket_runtime"] = bridge.runtime_identity
            canonical = []
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute(bridge, programs[DEFAULT_VALUE], pair["input"])
                canonical.append(
                    {
                        **pair,
                        "input_sha256": digest(pair["input"]),
                        "executed_output": actual,
                        "canonical_label_matches": actual == pair["output"],
                    }
                )
            write_json(out / "canonical-default.json", canonical)

            episodes = []
            for index, seed in enumerate(seeds):
                episode = generate_episode(seed, bridge=bridge, root=root)
                private_path = out / "private" / f"episode-{index:03d}.json"
                public_path = out / "public" / f"episode-{index:03d}.json"
                write_json(private_path, episode)
                write_json(public_path, public_episode(episode))
                episodes.append(
                    {
                        "seed": seed,
                        "parameters": episode["parameters"],
                        "private_path": private_path.relative_to(out).as_posix(),
                        "private_sha256": digest(private_path.read_bytes()),
                        "public_path": public_path.relative_to(out).as_posix(),
                        "public_sha256": digest(public_path.read_bytes()),
                        "parameter_rival_status": episode["parameter_rivals"]["status"],
                        "refuting_demonstrations": episode["parameter_rivals"][
                            "refuting_demonstrations"
                        ],
                        "query_disagreements": episode["parameter_rivals"][
                            "query_disagreements"
                        ],
                    }
                )
            run["episodes"] = episodes

            witness = _make_grid(5, 8, 4, 7, "left")
            outputs = {
                str(setting): execute(bridge, program, witness)
                for setting, program in programs.items()
            }
            write_json(
                out / "peak-discriminator.json",
                {
                    "input": witness,
                    "input_sha256": digest(witness),
                    "outputs": outputs,
                    "disagrees": outputs["1"] != outputs["2"],
                    "lawful": not input_issues(witness),
                },
            )

        checks = {
            "canonical_default_exact": programs[DEFAULT_VALUE]
            == _canonical_source(root=root),
            "canonical_labels": all(row["canonical_label_matches"] for row in canonical),
            "both_parameter_settings": {
                episode["parameters"][PARAMETER] for episode in episodes
            }
            == set(ALLOWED_VALUES),
            "episode_parameter_rivals_refuted": all(
                episode["parameter_rival_status"] == "refuted_on_demonstrations"
                for episode in episodes
            ),
            "queries_disagree": all(
                episode["query_disagreements"] == [0] for episode in episodes
            ),
            "peak_discriminator": outputs["1"] != outputs["2"],
        }
        run.update(
            status="passed" if all(checks.values()) else "failed",
            checks=checks,
            canonical_labeled_records=len(canonical),
            canonical_unique_inputs=len({row["input_sha256"] for row in canonical}),
        )
        run["evidence_files"] = {
            path.relative_to(out).as_posix(): digest(path.read_bytes())
            for path in sorted(out.rglob("*"))
            if path.is_file() and path.name != "run.json"
        }
        write_json(out / "run.json", run)
        print(
            json.dumps(
                {
                    "status": run["status"],
                    "checks": checks,
                    "out": str(out),
                    "episodes": episodes,
                },
                indent=2,
            )
        )
        return 0 if all(checks.values()) else 1
    except Exception as exc:
        run.update(status="error", error=str(exc), traceback=traceback.format_exc())
        write_json(out / "run.json", run)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
