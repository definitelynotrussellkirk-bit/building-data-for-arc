#!/usr/bin/env python3
"""Task-local anchor-color parametric prototype for ARC task 2c1567aea733.

The production generator and canonical rule remain unchanged. This proposed
prototype keeps the same reasoning structure—select one colored object as the
anchor, then translate every color vertically until its top row matches the
anchor's original top row—while varying the anchor color once per episode.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "2c1567aea733"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "anchor_color"
ALLOWED_ANCHORS = (1, 2, 4)
DEFAULT_ANCHOR = 1
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
STATUS = "proposed task-local prototype; not production-approved"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent


def _canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    matches = []
    with canonical_path(Path(root)).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical task {TASK_ID}, found {len(matches)}")
    return matches[0]


def _validate_anchor(anchor_color: Any) -> int:
    if type(anchor_color) is not int:
        raise TypeError("anchor_color must be a literal integer")
    if anchor_color not in ALLOWED_ANCHORS:
        raise ValueError(f"anchor_color must be one of {ALLOWED_ANCHORS}")
    return anchor_color


def choose_anchor(seed: int) -> int:
    """Choose one hidden anchor exactly once from an episode seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be a literal integer")
    return ALLOWED_ANCHORS[seed % len(ALLOWED_ANCHORS)]


def program_for(
    anchor_color: int = DEFAULT_ANCHOR,
    *,
    root: Path | str = ROOT,
) -> str:
    """Return the complete Racket program for one declared anchor setting."""
    anchor_color = _validate_anchor(anchor_color)
    canonical = _canonical_record(root=root)["program_solution"]
    if anchor_color == DEFAULT_ANCHOR:
        return canonical
    needle = "(find-color g 1)"
    if canonical.count(needle) != 1:
        raise RuntimeError("canonical anchor lookup changed unexpectedly")
    return canonical.replace(needle, f"(find-color g {anchor_color})")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_grid(grid: Any) -> dict[int, set[tuple[int, int]]]:
    if type(grid) is not list or not 5 <= len(grid) <= 30:
        raise ValueError("prototype grid must have 5..30 rows")
    if not grid or type(grid[0]) is not list or not 10 <= len(grid[0]) <= 30:
        raise ValueError("prototype grid must have 10..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("prototype grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be literal ARC colors 0..9")

    by_color: dict[int, set[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value:
                by_color.setdefault(value, set()).add((row_index, col_index))
    if set(by_color) != set(ALLOWED_ANCHORS):
        raise ValueError("prototype palette must be exactly {0,1,2,4}")

    extents = {
        color: (
            min(col for _, col in cells),
            max(col for _, col in cells),
        )
        for color, cells in by_color.items()
    }
    for index, left_color in enumerate(ALLOWED_ANCHORS):
        for right_color in ALLOWED_ANCHORS[index + 1 :]:
            left = extents[left_color]
            right = extents[right_color]
            if not (left[1] < right[0] or right[1] < left[0]):
                raise ValueError("color column extents must be pairwise disjoint")

    tops = {min(row for row, _ in cells) for cells in by_color.values()}
    if len(tops) != len(ALLOWED_ANCHORS):
        raise ValueError("prototype inputs require three distinct color top rows")
    return by_color


def grid_sha256(grid: list[list[int]]) -> str:
    return _sha256_bytes(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def apply_python(
    grid: list[list[int]],
    anchor_color: int = DEFAULT_ANCHOR,
) -> list[list[int]]:
    """Independent mirror; reject collisions/clipping instead of dropping cells."""
    anchor_color = _validate_anchor(anchor_color)
    by_color = _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    anchor_top = min(row for row, _ in by_color[anchor_color])
    output = [[0] * width for _ in range(height)]
    for color, cells in by_color.items():
        color_top = min(row for row, _ in cells)
        shift = anchor_top - color_top
        for row, col in cells:
            new_row = row + shift
            if not 0 <= new_row < height:
                raise ValueError(
                    f"anchor_color={anchor_color} would clip color {color}"
                )
            if output[new_row][col] != 0:
                raise ValueError("anchor alignment would create a collision")
            output[new_row][col] = color
    if sum(value != 0 for row in output for value in row) != sum(
        value != 0 for row in grid for value in row
    ):
        raise ValueError("anchor alignment did not preserve every foreground cell")
    return output


def _callable_text(program: str) -> str:
    from puzzle_generators.rule_wrap import strip_rule_wrapper

    return strip_rule_wrapper(program)


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    return f"({_callable_text(program)} {_grid_literal(grid)})"


def execute_racket(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(application(program, grid))


def load_parent(*, root: Path | str = ROOT):
    from reviewer_support import load_selected_generator

    return load_selected_generator(TASK_ID, root=Path(root))


def _validate_pair_count(pair_count: Any) -> int:
    if type(pair_count) is not int:
        raise TypeError("pair_count must be a literal integer")
    if not 2 <= pair_count <= 12:
        raise ValueError("pair_count must be in 2..12")
    return pair_count


def _validate_counts(demo_count: Any, query_count: Any) -> tuple[int, int]:
    if type(demo_count) is not int:
        raise TypeError("demo_count must be a literal integer")
    if type(query_count) is not int:
        raise TypeError("query_count must be a literal integer")
    if not 1 <= demo_count <= 8:
        raise ValueError("demo_count must be in 1..8")
    if not 1 <= query_count <= 8:
        raise ValueError("query_count must be in 1..8")
    if demo_count + query_count > 12:
        raise ValueError("demo_count + query_count must not exceed 12")
    return demo_count, query_count


def sample_inputs(
    seed: int,
    *,
    pair_count: int = DEFAULT_DEMO_COUNT + DEFAULT_QUERY_COUNT,
    root: Path | str = ROOT,
) -> tuple[list[list[int]], ...]:
    """Sample unique copied-shape inputs independently of the hidden anchor."""
    if type(seed) is not int:
        raise TypeError("episode seed must be a literal integer")
    pair_count = _validate_pair_count(pair_count)
    parent, _path, _sha = load_parent(root=root)
    namespace = int(
        hashlib.sha256(f"{TASK_ID}:anchor-inputs:{seed}".encode()).hexdigest()[:16],
        16,
    )
    accepted: list[list[list[int]]] = []
    seen: set[str] = set()
    profiles = ("copied_irregular", "copied_rectangles")
    for attempt in range(max(96, pair_count * 24)):
        grid = parent.generate(
            namespace,
            attempt,
            difficulty="medium",
            grid_h=10,
            grid_w=10,
            scene_profile=profiles[attempt % len(profiles)],
        )
        if parent.self_check(grid) != []:
            continue
        try:
            outputs = [apply_python(grid, anchor) for anchor in ALLOWED_ANCHORS]
        except ValueError:
            continue
        if len({grid_sha256(output) for output in outputs}) != len(ALLOWED_ANCHORS):
            continue
        digest = grid_sha256(grid)
        if digest in seen:
            continue
        seen.add(digest)
        accepted.append(grid)
        if len(accepted) == pair_count:
            return tuple(accepted)
    raise RuntimeError(
        f"could not sample {pair_count} unique total anchor-color inputs within retry budget"
    )


def build_episode(
    seed: int,
    *,
    anchor_color: int | None = None,
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Build one deterministic private episode with an episode-fixed rule."""
    if type(seed) is not int:
        raise TypeError("episode seed must be a literal integer")
    demo_count, query_count = _validate_counts(demo_count, query_count)
    selected = choose_anchor(seed) if anchor_color is None else _validate_anchor(anchor_color)
    grids = sample_inputs(
        seed,
        pair_count=demo_count + query_count,
        root=root,
    )
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in grids
    ]
    return {
        "meta": {
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "episode_seed": seed,
            PARAMETER_NAME: selected,
            "demo_count": demo_count,
            "query_count": query_count,
        },
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
    }


def score_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Check query identifiability using demonstrations only."""
    if not isinstance(episode, dict) or not isinstance(episode.get("meta"), dict):
        raise ValueError("episode must contain private meta")
    chosen = _validate_anchor(episode["meta"].get(PARAMETER_NAME))
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not train or type(test) is not list or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
                raise ValueError(f"{split} pair {index} is not fully labeled")
            if pair["output"] != apply_python(pair["input"], chosen):
                raise ValueError(f"{split} pair {index} label disagrees with chosen anchor")

    rivals = [anchor for anchor in ALLOWED_ANCHORS if anchor != chosen]
    query_checks = []
    for query_index, query in enumerate(test):
        rival_rows = []
        for rival in rivals:
            mismatches = [
                index
                for index, pair in enumerate(train)
                if apply_python(pair["input"], rival) != pair["output"]
            ]
            rival_rows.append(
                {
                    "anchor_color": rival,
                    "status": (
                        "refuted_by_demonstrations"
                        if mismatches
                        else "survives_demonstrations"
                    ),
                    "demonstration_mismatches": mismatches,
                    "query_disagrees": (
                        apply_python(query["input"], rival) != query["output"]
                    ),
                }
            )
        identifiable = all(
            row["status"] == "refuted_by_demonstrations" for row in rival_rows
        )
        query_checks.append(
            {
                "query_index": query_index,
                "status": "identifiable" if identifiable else "ambiguous",
                "rivals": rival_rows,
            }
        )
    return {
        "status": (
            "identifiable"
            if all(row["status"] == "identifiable" for row in query_checks)
            else "ambiguous"
        ),
        "chosen_anchor_color": chosen,
        "query_checks": query_checks,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes

    return json.loads(public_challenge_bytes(episode).decode("utf-8"))


def public_filename(episode: dict[str, Any]) -> str:
    from reviewer_support import public_challenge_id

    return f"challenge-{public_challenge_id(episode)}.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _source_bindings(root: Path) -> dict[str, str]:
    candidates = [
        Path(__file__).resolve(),
        HERE / "README.md",
        root / "generators" / TASK_ID / "generator.py",
        root / "generators" / TASK_ID / "tests" / "test_parametric_anchor_color.py",
        root / "generators" / TASK_ID / "tests" / "test_parametric_public_names.py",
        canonical_path(root),
    ]
    return {
        path.resolve().relative_to(root.resolve()).as_posix(): _sha256_file(path)
        for path in candidates
        if path.is_file()
    }


def _write_manifest(
    out: Path,
    *,
    status: str,
    public_challenges: list[dict[str, Any]],
    private_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    files = []
    for path in sorted(out.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        files.append(
            {
                "path": path.relative_to(out).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    report_path = out / "report.json"
    manifest = {
        "schema": "2c1567aea733-anchor-color-manifest-v1",
        "status": status,
        "report_sha256": _sha256_file(report_path) if report_path.is_file() else None,
        "public_challenges": public_challenges,
        "private_evidence": private_evidence,
        "files": files,
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def write_evidence(
    out: Path | str,
    *,
    seeds: tuple[int, ...] | list[int] = (0, 1, 2),
    demo_count: int = DEFAULT_DEMO_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path | str = ROOT,
    racket_path: str | None = None,
) -> dict[str, Any]:
    """Materialize complete Racket-backed evidence for every anchor setting."""
    import os
    import sys

    from arc_repl.isolated_verifier import verify_candidate
    from reviewer_support import canonical_pairs, public_challenge_bytes, public_challenge_id

    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private" / "rules").mkdir(parents=True)
    (out / "private" / "racket").mkdir(parents=True)
    (out / "private" / "episodes").mkdir(parents=True)

    root = Path(root).resolve()
    demo_count, query_count = _validate_counts(demo_count, query_count)
    report: dict[str, Any] = {
        "schema": "2c1567aea733-anchor-color-evidence-v1",
        "status": "running",
        "scope": STATUS,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_ANCHORS),
            "original_default": DEFAULT_ANCHOR,
            "selection": "ALLOWED_ANCHORS[episode_seed % 3], chosen once per episode",
        },
        "input_constraints": [
            "production palette {0,1,2,4} with pairwise-disjoint horizontal extents",
            "three distinct starting top rows so every anchor setting changes the answer",
            "retained sampler uses one copied shape across colors so every setting is total",
        ],
        "invariant_reasoning": [
            "group every nonzero cell by its color",
            "read the chosen anchor color's original top row",
            "translate each color vertically as one object while preserving columns and shape",
            "make every color top equal the anchor top",
        ],
        "source_sha256": {},
        "runtime": None,
        "programs": [],
        "episodes": [],
        "summary": None,
        "limitations": [
            "This task-local prototype does not modify production generation or approval.",
            "Retained inputs use copied shapes to avoid undefined clipping under alternate anchors.",
            "Identifiability is checked against the two declared alternate anchor settings, not every imaginable program.",
        ],
        "invocation": {
            "argv": list(sys.argv),
            "cwd": str(Path.cwd()),
            "python_executable": sys.executable,
            "python_version": sys.version,
        },
    }
    _write_json(out / "report.json", report)
    public_rows: list[dict[str, Any]] = []
    private_rows: list[dict[str, Any]] = []

    try:
        if type(seeds) not in (tuple, list) or not seeds:
            raise ValueError("seeds must be a nonempty tuple or list")
        if any(type(seed) is not int for seed in seeds):
            raise TypeError("every episode seed must be a literal integer")
        selected_anchors = [choose_anchor(seed) for seed in seeds]
        if set(selected_anchors) != set(ALLOWED_ANCHORS):
            raise ValueError("retained seeds must cover anchor colors 1, 2, and 4")

        report["source_sha256"] = _source_bindings(root)
        chosen_racket = racket_path if racket_path is not None else os.environ.get("RACKET_PATH", "")
        binary = Path(chosen_racket).expanduser().resolve(strict=True)
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise FileNotFoundError(f"Racket path is not an executable file: {binary}")
        report["runtime"] = {
            "backend": "racket",
            "public_api": "arc_repl.isolated_verifier.verify_candidate",
            "racket_path": str(binary),
            "racket_sha256": _sha256_file(binary),
        }

        episodes = [
            build_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
            )
            for seed in seeds
        ]
        episode_inputs = [
            pair["input"]
            for episode in episodes
            for pair in episode["train"] + episode["test"]
        ]
        canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
        predictions: dict[int, list[list[list[int]]]] = {}
        canonical_outputs: list[list[list[int]]] = []
        python_matches = 0

        for anchor in ALLOWED_ANCHORS:
            program = program_for(anchor, root=root)
            rule_rel = f"private/rules/anchor-{anchor}.rkt"
            receipt_rel = f"private/racket/anchor-{anchor}.json"
            (out / rule_rel).write_text(program + "\n", encoding="utf-8")
            canary = {
                "input": episode_inputs[0],
                "output": apply_python(episode_inputs[0], anchor),
            }
            test_inputs = list(episode_inputs)
            if anchor == DEFAULT_ANCHOR:
                test_inputs.extend(pair["input"] for pair in canonical)
            receipt = verify_candidate(
                {
                    "train": [canary],
                    "test": [{"input": grid} for grid in test_inputs],
                },
                program,
                racket_path=str(binary),
            )
            _write_json(
                out / receipt_rel,
                {
                    "anchor_color": anchor,
                    "program_sha256": _sha256_bytes(program.encode("utf-8")),
                    "canary": canary,
                    "input_sha256": [grid_sha256(grid) for grid in test_inputs],
                    "receipt": receipt,
                },
            )
            if receipt.get("status") != "pass" or receipt.get("backend") != "racket":
                raise RuntimeError(
                    f"Racket execution failed for anchor_color={anchor}: {receipt.get('error')}"
                )
            outputs = receipt["test_outputs"]
            episode_outputs = outputs[: len(episode_inputs)]
            for grid, actual in zip(episode_inputs, episode_outputs, strict=True):
                expected = apply_python(grid, anchor)
                if actual != expected:
                    raise RuntimeError(
                        f"Racket/Python mismatch for anchor_color={anchor}"
                    )
                python_matches += 1
            predictions[anchor] = episode_outputs
            if anchor == DEFAULT_ANCHOR:
                canonical_outputs = outputs[len(episode_inputs) :]
                if len(canonical_outputs) != len(canonical):
                    raise RuntimeError("default Racket canonical output count mismatch")
                for pair, actual in zip(canonical, canonical_outputs, strict=True):
                    if actual != pair["output"] or actual != apply_python(pair["input"], anchor):
                        raise RuntimeError("default Racket program changed a canonical label")
                    python_matches += 1

            report["programs"].append(
                {
                    "anchor_color": anchor,
                    "canonical_default": anchor == DEFAULT_ANCHOR,
                    "source": program,
                    "sha256": _sha256_bytes(program.encode("utf-8")),
                    "path": rule_rel,
                    "execution_path": receipt_rel,
                }
            )

        public_ids: set[str] = set()
        offset = 0
        query_rival_checks = 0
        ambiguous_queries = 0
        for template in episodes:
            pair_count = len(template["train"]) + len(template["test"])
            chosen = template["meta"][PARAMETER_NAME]
            selected_outputs = predictions[chosen][offset : offset + pair_count]
            inputs = [pair["input"] for pair in template["train"] + template["test"]]
            labeled = [
                {"input": grid, "output": output}
                for grid, output in zip(inputs, selected_outputs, strict=True)
            ]
            episode = {
                "meta": dict(template["meta"]),
                "train": labeled[:demo_count],
                "test": labeled[demo_count:],
            }
            score = score_episode(episode)
            query_rival_checks += sum(
                len(query["rivals"]) for query in score["query_checks"]
            )
            ambiguous_queries += sum(
                query["status"] != "identifiable" for query in score["query_checks"]
            )
            if score["status"] != "identifiable":
                raise RuntimeError(
                    f"episode seed {template['meta']['episode_seed']} is ambiguous"
                )

            public_id = public_challenge_id(episode)
            if public_id in public_ids:
                raise RuntimeError(f"duplicate visible public challenge id: {public_id}")
            public_ids.add(public_id)
            public_rel = f"public/challenge-{public_id}.json"
            public_bytes = public_challenge_bytes(episode)
            (out / public_rel).write_bytes(public_bytes)
            private_rel = (
                f"private/episodes/seed-{template['meta']['episode_seed']}-"
                f"anchor-{chosen}.json"
            )
            _write_json(
                out / private_rel,
                {
                    "episode": episode,
                    "score": score,
                    "program_sha256": next(
                        row["sha256"] for row in report["programs"]
                        if row["anchor_color"] == chosen
                    ),
                    "public_id": public_id,
                    "public_path": public_rel,
                },
            )
            public_row = {
                "id": public_id,
                "path": public_rel,
                "sha256": _sha256_bytes(public_bytes),
            }
            private_row = {
                "path": private_rel,
                "sha256": _sha256_file(out / private_rel),
            }
            public_rows.append(public_row)
            private_rows.append(private_row)
            report["episodes"].append(
                {
                    "episode_seed": template["meta"]["episode_seed"],
                    "anchor_color": chosen,
                    "demo_count": demo_count,
                    "query_count": query_count,
                    "public_id": public_id,
                    "public_path": public_rel,
                    "private_path": private_rel,
                    "score_status": score["status"],
                }
            )
            offset += pair_count

        witness_input = episode_inputs[0]
        witness_outputs = {
            str(anchor): predictions[anchor][0] for anchor in ALLOWED_ANCHORS
        }
        if len({grid_sha256(output) for output in witness_outputs.values()}) != 3:
            raise RuntimeError("cross-setting witness outputs are not pairwise distinct")
        witness_rel = "private/cross-setting-witness.json"
        _write_json(
            out / witness_rel,
            {
                "task_id": TASK_ID,
                "input": witness_input,
                "input_sha256": grid_sha256(witness_input),
                "outputs": witness_outputs,
                "outputs_pairwise_distinct": True,
                "checked_by": "all three complete Racket programs",
            },
        )
        private_rows.append(
            {"path": witness_rel, "sha256": _sha256_file(out / witness_rel)}
        )

        episode_pairs = len(episode_inputs)
        report["summary"] = {
            "episodes": len(episodes),
            "demonstrations": len(episodes) * demo_count,
            "queries": len(episodes) * query_count,
            "episode_pairs": episode_pairs,
            "racket_episode_labels": episode_pairs * len(ALLOWED_ANCHORS),
            "canonical_default_labels": len(canonical),
            "racket_canaries": len(ALLOWED_ANCHORS),
            "python_mirror_matches": python_matches,
            "query_rival_checks": query_rival_checks,
            "ambiguous_queries": ambiguous_queries,
        }
        report["canonical_default_exact_program_match"] = (
            program_for(DEFAULT_ANCHOR, root=root)
            == _canonical_record(root=root)["program_solution"]
        )
        report["status"] = "passed"
        _write_json(out / "report.json", report)
        _write_manifest(
            out,
            status="passed",
            public_challenges=public_rows,
            private_evidence=private_rows,
        )
        return report
    except Exception as exc:
        report["status"] = "error"
        report["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        _write_json(out / "report.json", report)
        _write_manifest(
            out,
            status="error",
            public_challenges=public_rows,
            private_evidence=private_rows,
        )
        return report



# Native promotion interface -------------------------------------------------

_NATIVE_DEMO_SIZES = (
    (14, 18), (15, 19), (16, 20), (17, 21), (18, 22), (19, 23),
)
_NATIVE_QUERY_SIZES = ((20, 24), (22, 25), (24, 27), (30, 30))
_NATIVE_PERMUTATIONS = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
_NATIVE_SMALL_PATTERNS = (
    frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (0, 3)}),
    frozenset({(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1), (3, 1), (0, 3), (3, 3)}),
)
_NATIVE_LARGE_PATTERNS = (
    frozenset(
        {(row, 0) for row in range(8)}
        | {(7, col) for col in range(8)}
        | {(0, 7), (2, 6), (4, 5), (6, 4)}
    ),
    frozenset(
        {(row, row) for row in range(8)}
        | {(row, 7 - row) for row in range(8)}
        | {(0, col) for col in range(4)}
        | {(7, col) for col in range(4, 8)}
    ),
    frozenset(
        {(0, col) for col in range(8)}
        | {(7, col) for col in range(8)}
        | {(row, 3) for row in range(1, 7)}
        | {(row, 4) for row in (2, 4, 6)}
        | {(3, 0), (5, 7)}
    ),
)


def _native_settings(value: Any) -> int:
    if type(value) is not dict or set(value) != {PARAMETER_NAME}:
        raise ValueError("settings must contain only anchor_color")
    return _validate_anchor(value[PARAMETER_NAME])


def _native_request(seed: Any, demos: Any, queries: Any) -> tuple[int, int, int]:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    return seed, demos, queries


def _transform_pattern(
    points: frozenset[tuple[int, int]], extent: int, code: int
) -> frozenset[tuple[int, int]]:
    transformed = set(points)
    if code & 1:
        transformed = {(row, extent - 1 - col) for row, col in transformed}
    if code & 2:
        transformed = {(extent - 1 - row, col) for row, col in transformed}
    if code & 4:
        transformed = {(col, row) for row, col in transformed}
    rows = {row for row, _ in transformed}
    cols = {col for _, col in transformed}
    if min(rows) != 0 or max(rows) != extent - 1 or min(cols) != 0 or max(cols) != extent - 1:
        raise AssertionError("native shape transform lost its declared extent")
    return frozenset(transformed)


def _native_grid(seed: int, slot: int, *, query: bool) -> list[list[int]]:
    sizes = _NATIVE_QUERY_SIZES if query else _NATIVE_DEMO_SIZES
    height, width = sizes[slot]
    extent = 8 if (query and slot == 3) else 4
    patterns = _NATIVE_LARGE_PATTERNS if extent == 8 else _NATIVE_SMALL_PATTERNS
    tops = (0, (height - extent) // 2, height - extent)
    lefts = (0, (width - extent) // 2, width - extent)
    permutation = _NATIVE_PERMUTATIONS[(slot + (seed % 3) + (1 if query else 0)) % 3]
    colors = ALLOWED_ANCHORS
    grid = [[0] * width for _ in range(height)]
    for color_index, color in enumerate(colors):
        top = tops[permutation[color_index]]
        left = lefts[color_index]
        pattern = patterns[(color_index + slot + seed) % len(patterns)]
        pattern = _transform_pattern(pattern, extent, (seed >> (color_index * 3)) + slot)
        for row, col in pattern:
            if grid[top + row][left + col] != 0:
                raise AssertionError("native color extents overlapped")
            grid[top + row][left + col] = color
    _validate_grid(grid)
    outputs = [apply_python(grid, anchor) for anchor in ALLOWED_ANCHORS]
    if len({grid_sha256(output) for output in outputs}) != len(ALLOWED_ANCHORS):
        raise AssertionError("native input does not distinguish all anchor settings")
    return grid


def native_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    seed, _demos, _queries = _native_request(seed, 2, 1)
    demos = [_native_grid(seed, index, query=False) for index in range(6)]
    queries = [_native_grid(seed, index, query=True) for index in range(4)]
    digests = [grid_sha256(grid) for grid in demos + queries]
    if len(digests) != len(set(digests)):
        raise AssertionError("native episode contains duplicate inputs")
    return {"train": demos, "test": queries}


def program(settings: Any) -> str:
    return program_for(_native_settings(settings))


def generate(
    seed: int,
    settings: Any,
    demos: int = DEFAULT_DEMO_COUNT,
    queries: int = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    anchor = _native_settings(settings)
    seed, demos, queries = _native_request(seed, demos, queries)
    inputs = native_inputs(seed)
    train = [
        {"input": [row[:] for row in grid], "output": apply_python(grid, anchor)}
        for grid in inputs["train"][:demos]
    ]
    test = [
        {"input": [row[:] for row in grid], "output": apply_python(grid, anchor)}
        for grid in inputs["test"][:queries]
    ]
    return {"train": train, "test": test, "program_solution": program(settings)}


def align_to_target_top(grid: list[list[int]], target_top: int) -> list[list[int]]:
    by_color = _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    if type(target_top) is not int or not 0 <= target_top < height:
        raise ValueError("target_top must be a valid exact row")
    output = [[0] * width for _ in range(height)]
    for color, cells in by_color.items():
        color_top = min(row for row, _ in cells)
        shift = target_top - color_top
        for row, col in cells:
            new_row = row + shift
            if not 0 <= new_row < height:
                raise ValueError("target top would clip a color")
            if output[new_row][col]:
                raise ValueError("target top would create a collision")
            output[new_row][col] = color
    return output


def native_rival_output(grid: list[list[int]], hypothesis: str) -> list[list[int]]:
    by_color = _validate_grid(grid)
    tops = sorted(min(row for row, _ in cells) for cells in by_color.values())
    if hypothesis == "highest_top":
        return align_to_target_top(grid, tops[0])
    if hypothesis == "median_top":
        return align_to_target_top(grid, tops[1])
    if hypothesis == "lowest_top":
        return align_to_target_top(grid, tops[2])
    if hypothesis == "mean_top":
        return align_to_target_top(grid, sum(tops) // len(tops))
    if hypothesis == "identity":
        return [row[:] for row in grid]
    if hypothesis.startswith("anchor_"):
        return apply_python(grid, int(hypothesis.split("_", 1)[1]))
    raise ValueError(f"unknown native rival: {hypothesis}")

def _parse_seed_list(value: str) -> tuple[int, ...]:
    try:
        seeds = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise ValueError("--seeds must be a comma-separated integer list") from exc
    if not seeds:
        raise ValueError("--seeds must not be empty")
    return seeds


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--racket-path")
    args = parser.parse_args(argv)
    report = write_evidence(
        args.out,
        seeds=_parse_seed_list(args.seeds),
        demo_count=args.demo_count,
        query_count=args.query_count,
        racket_path=args.racket_path,
    )
    print(json.dumps({
        "status": report["status"],
        "report": str(args.out / "report.json"),
        "summary": report.get("summary"),
        "error": report.get("error"),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
