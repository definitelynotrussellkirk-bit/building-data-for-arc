"""Task-local height-threshold parameterization for ``cf4fdf474ad5``.

The selected production generator and canonical authority remain unchanged.  This
prototype varies one hidden episode setting: the maximum eligible component
height is 5, canonical 8, or 9.  All other ordering clauses remain identical.
"""
from __future__ import annotations

from functools import cache
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "cf4fdf474ad5"
HEIGHT_LIMITS = (5, 8, 9)
DEFAULT_MAX_HEIGHT = 8
STATUS = "proposed task-local prototype; not production-approved"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _validate_max_height(value: Any) -> int:
    if type(value) is not int:
        raise TypeError("max_height must be one of 5, 8, or 9; bool is forbidden")
    if value not in HEIGHT_LIMITS:
        raise ValueError("max_height must be one of 5, 8, or 9")
    return value


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer in 0..2**63-1; bool is forbidden")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer in 1..16; bool is forbidden")
    if not 1 <= value <= 16:
        raise ValueError(f"{name} must be in 1..16")
    return value


@cache
def canonical_program() -> str:
    """Return the unique canonical authority while preserving exact bytes."""
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str):
                    raise TypeError("canonical program_solution must be a string")
                programs.add(program)
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, found {len(programs)}")
    program = programs.pop()
    marker = "(<= hh 8)"
    if program.count(marker) != 1:
        raise ValueError(
            f"canonical program must contain exactly one {marker!r} threshold site"
        )
    return program


def program_for(max_height: int = DEFAULT_MAX_HEIGHT) -> str:
    """Materialize exact executable Racket for one bounded setting."""
    limit = _validate_max_height(max_height)
    program = canonical_program()
    if limit == DEFAULT_MAX_HEIGHT:
        return program
    return program.replace("(<= hh 8)", f"(<= hh {limit})", 1)


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    value = normalize_grid(grid)
    height = len(value)
    width = len(value[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            if value[row][column] == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_column = stack.pop()
                cells.append((current_row, current_column))
                for delta_row, delta_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_column = current_column + delta_column
                    if (
                        0 <= next_row < height
                        and 0 <= next_column < width
                        and value[next_row][next_column] != 0
                        and (next_row, next_column) not in seen
                    ):
                        seen.add((next_row, next_column))
                        stack.append((next_row, next_column))
            rows = [cell[0] for cell in cells]
            columns = [cell[1] for cell in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(columns), max(columns)
            box_height = bottom - top + 1
            box_width = right - left + 1
            components.append(
                {
                    "top": top,
                    "left": left,
                    "bottom": bottom,
                    "right": right,
                    "height": box_height,
                    "width": box_width,
                    "area": box_height * box_width,
                    "green": sum(value[r][c] == 3 for r, c in cells),
                }
            )
    return components


def python_apply(
    grid: Sequence[Sequence[int]], max_height: int = DEFAULT_MAX_HEIGHT
) -> list[list[int]]:
    """Independent Python semantic mirror for prototype audits."""
    limit = _validate_max_height(max_height)
    value = normalize_grid(grid)
    eligible = [component for component in _components(value) if component["height"] <= limit]
    if not eligible:
        raise ValueError(f"input has no component with height <= {limit}")
    chosen = min(
        eligible,
        key=lambda component: (
            -component["green"],
            component["area"],
            component["top"],
            component["left"],
        ),
    )
    return [
        row[chosen["left"] : chosen["right"] + 1]
        for row in value[chosen["top"] : chosen["bottom"] + 1]
    ]


def execute_program(bridge, program: str, grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Execute exact ``(rule! ...)`` text through the protected Racket bridge."""
    if not isinstance(program, str) or not program.lstrip().startswith("(rule!"):
        raise ValueError("program must be exact (rule! ...) Racket text")
    value = normalize_grid(grid)
    bridge.define_grid("height_threshold_grid", value)
    callable_rule = wrap_rule(program)
    result = bridge.eval_text(f"({callable_rule} height_threshold_grid)")
    return normalize_grid(result)


def settings_for_seed(seed: int) -> dict[str, int]:
    """Choose one hidden setting deterministically before sampling inputs."""
    value = _validate_seed(seed)
    return {"max_height": HEIGHT_LIMITS[value % len(HEIGHT_LIMITS)]}


def _stream_seed(seed: int, stream: str) -> int:
    raw = hashlib.sha256(f"{TASK_ID}:height-threshold:{stream}:{seed}".encode()).digest()
    return int.from_bytes(raw[:8], "big") & (2**63 - 1)


def _grid_key(grid: Sequence[Sequence[int]]) -> str:
    return json.dumps(normalize_grid(grid), separators=(",", ":"))


def _draw_inputs(seed: int, count: int, stream: str) -> list[list[list[int]]]:
    generation_seed = _stream_seed(seed, stream)
    difficulties = ("easy", "medium", "hard", None)
    inputs: list[list[list[int]]] = []
    seen: set[str] = set()
    attempt = 0
    max_attempts = max(128, count * 64)
    while len(inputs) < count and attempt < max_attempts:
        slot = len(inputs)
        grid = GEN.generate(
            generation_seed,
            attempt,
            difficulty=difficulties[slot % len(difficulties)],
        )
        errors = GEN.self_check(grid)
        if errors:
            raise RuntimeError(
                "selected generator returned an unlawful prototype input: "
                + "; ".join(errors)
            )
        normalized = normalize_grid(grid)
        outputs = {_grid_key(python_apply(normalized, limit)) for limit in HEIGHT_LIMITS}
        if len(outputs) != len(HEIGHT_LIMITS):
            attempt += 1
            continue
        key = _grid_key(normalized)
        if key not in seen:
            seen.add(key)
            inputs.append(normalized)
        attempt += 1
    if len(inputs) != count:
        raise RuntimeError(
            f"could not draw {count} distinct teaching inputs for {stream!r} "
            f"within {max_attempts} attempts"
        )
    return inputs


def generate_episode(
    seed: int,
    max_height: int,
    *,
    demos: int,
    queries: int,
) -> dict[str, Any]:
    """Return deterministic Python-claimed pairs for independent Racket review."""
    seed = _validate_seed(seed)
    limit = _validate_max_height(max_height)
    demos = _validate_count("demos", demos)
    queries = _validate_count("queries", queries)
    demo_inputs = _draw_inputs(seed, demos, "demo")
    query_inputs = _draw_inputs(seed, queries, "query")
    all_keys = [_grid_key(grid) for grid in demo_inputs + query_inputs]
    if len(set(all_keys)) != len(all_keys):
        raise RuntimeError("demo/query streams produced a duplicate input")
    train = [
        {"input": grid, "output": python_apply(grid, limit)} for grid in demo_inputs
    ]
    test = [
        {"input": grid, "output": python_apply(grid, limit)} for grid in query_inputs
    ]
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(limit),
    }


def identify_setting(demonstrations: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Fit the three declared settings using demonstration labels only."""
    demos = list(demonstrations)
    if not demos:
        raise ValueError("at least one demonstration is required")
    mismatches: dict[int, list[int]] = {}
    for limit in HEIGHT_LIMITS:
        bad: list[int] = []
        for index, pair in enumerate(demos):
            if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
                raise ValueError("each demonstration must contain input and output")
            if python_apply(pair["input"], limit) != normalize_grid(pair["output"]):
                bad.append(index)
        mismatches[limit] = bad
    return {
        "survivors": [limit for limit in HEIGHT_LIMITS if not mismatches[limit]],
        "mismatching_demonstrations": mismatches,
    }


def public_projection(episode: dict[str, Any]) -> dict[str, Any]:
    """Project an episode to exact model-visible challenge content."""
    return {
        "train": [
            {
                "input": normalize_grid(pair["input"]),
                "output": normalize_grid(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": normalize_grid(pair["input"])} for pair in episode["test"]
        ],
    }


def _sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _source_hashes() -> dict[str, str]:
    home = Path(__file__).resolve().parent
    paths = {
        "generator.py": Path(GENERATOR_PATH).resolve(),
        "prototype.py": home / "prototype.py",
        "adapter.py": home / "adapter.py",
        "promotion.json": home / "promotion.json",
    }
    result: dict[str, str] = {}
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        result[name] = _sha256(path.read_bytes())
    return result


def write_evidence(
    out_dir: str | Path,
    *,
    seeds: Iterable[int] = (0, 1, 2),
    demos: int = 1,
    queries: int = 4,
) -> dict[str, Any]:
    """Write public challenges and private protected-Racket receipts.

    Generation, visible-payload deduplication, finite-setting checks, and every
    Racket execution finish before the destination is created. Existing output
    paths are never modified.
    """
    from arc_repl.racket_bridge import RacketBridge

    out = Path(out_dir)
    if out.exists():
        raise FileExistsError(f"evidence destination already exists: {out}")
    demos = _validate_count("demos", demos)
    queries = _validate_count("queries", queries)
    seed_values = list(seeds)
    if not seed_values:
        raise ValueError("at least one evidence seed is required")
    seed_values = [_validate_seed(seed) for seed in seed_values]

    pending: list[dict[str, Any]] = []
    visible_ids: set[str] = set()
    for seed in seed_values:
        settings = settings_for_seed(seed)
        limit = settings["max_height"]
        episode = generate_episode(seed, limit, demos=demos, queries=queries)
        public = public_projection(episode)
        identifier = public_challenge_id(public)
        raw = public_challenge_bytes(public)
        if identifier in visible_ids:
            raise ValueError(
                "duplicate visible challenge detected before evidence destination creation"
            )
        visible_ids.add(identifier)
        pending.append(
            {
                "seed": seed,
                "settings": settings,
                "episode": episode,
                "public": public,
                "public_id": identifier,
                "public_bytes": raw,
            }
        )

    programs = {limit: program_for(limit) for limit in HEIGHT_LIMITS}
    program_records = {
        limit: {"source": source, "sha256": _sha256(source)}
        for limit, source in programs.items()
    }
    source_hashes = _source_hashes()
    verified: list[dict[str, Any]] = []

    with RacketBridge() as bridge:
        runtime_identity = dict(bridge.runtime_identity)
        if (
            runtime_identity.get("backend") != "racket"
            or runtime_identity.get("protected") is not True
        ):
            raise RuntimeError("evidence requires a protected Racket backend")

        for item in pending:
            episode = item["episode"]
            chosen = item["settings"]["max_height"]
            pairs = episode["train"] + episode["test"]
            inputs = [pair["input"] for pair in pairs]
            executed = {
                limit: [
                    execute_program(bridge, programs[limit], grid)
                    for grid in inputs
                ]
                for limit in HEIGHT_LIMITS
            }
            claimed = [normalize_grid(pair["output"]) for pair in pairs]
            if executed[chosen] != claimed:
                raise AssertionError(
                    f"protected Racket labels diverge from Python claims for max_height={chosen}"
                )

            mismatches: dict[int, list[int]] = {}
            query_disagreements: dict[int, list[int]] = {}
            for limit in HEIGHT_LIMITS:
                mismatches[limit] = [
                    index
                    for index, (candidate, expected) in enumerate(
                        zip(executed[limit][:demos], executed[chosen][:demos])
                    )
                    if candidate != expected
                ]
                query_disagreements[limit] = [
                    index
                    for index, (candidate, expected) in enumerate(
                        zip(executed[limit][demos:], executed[chosen][demos:])
                    )
                    if candidate != expected
                ]
            survivors = [limit for limit in HEIGHT_LIMITS if not mismatches[limit]]
            if survivors != [chosen]:
                raise AssertionError(
                    f"demonstrations leave finite survivors {survivors}, expected {[chosen]}"
                )
            expected_query_differences = list(range(queries))
            for limit in HEIGHT_LIMITS:
                if limit == chosen:
                    if query_disagreements[limit]:
                        raise AssertionError("chosen program disagrees with its own query labels")
                elif query_disagreements[limit] != expected_query_differences:
                    raise AssertionError(
                        f"query set does not distinguish max_height={chosen} from {limit} "
                        "on every query"
                    )

            public = {
                "train": [
                    {"input": inputs[index], "output": executed[chosen][index]}
                    for index in range(demos)
                ],
                "test": [
                    {"input": inputs[demos + index]}
                    for index in range(queries)
                ],
            }
            public_bytes = public_challenge_bytes(public)
            public_id = public_challenge_id(public)
            if public_bytes != item["public_bytes"] or public_id != item["public_id"]:
                raise AssertionError(
                    "protected Racket verification changed visible challenge bytes"
                )

            identification = {
                "survivors": survivors,
                "mismatching_demonstrations": mismatches,
                "query_disagreement_indices": query_disagreements,
            }
            private = {
                "schema": "cf4fdf474ad5-height-threshold-private-v1",
                "status": STATUS,
                "task_id": TASK_ID,
                "public_id": public_id,
                "public_sha256": _sha256(public_bytes),
                "seed": item["seed"],
                "settings": item["settings"],
                "counts": {"demos": demos, "queries": queries},
                "canonical_rule_hash": GEN.RULE_HASH,
                "selected_program_sha256": program_records[chosen]["sha256"],
                "programs": program_records,
                "query_outputs": executed[chosen][demos:],
                "identification": identification,
                "runtime_identity": runtime_identity,
                "source_sha256": source_hashes,
                "label_execution": {
                    "engine": "protected_racket",
                    "program_count": len(HEIGHT_LIMITS),
                    "input_count": len(inputs),
                    "evaluation_count": len(HEIGHT_LIMITS) * len(inputs),
                    "python_claims_matched": True,
                },
                "limitations": [
                    "task-local proposed prototype; no production approval or training admission",
                    "finite identifiability covers only max_height values 5, 8, and 9",
                    "evidence covers only the listed seed and requested counts",
                ],
            }
            private_bytes = _pretty_json_bytes(private)
            verified.append(
                {
                    "public_bytes": public_bytes,
                    "public_id": public_id,
                    "private_bytes": private_bytes,
                    "receipt": {
                        "public_id": public_id,
                        "public_sha256": _sha256(public_bytes),
                        "private_sha256": _sha256(private_bytes),
                        "seed": item["seed"],
                        "settings": item["settings"],
                        "counts": {"demos": demos, "queries": queries},
                        "selected_program_sha256": program_records[chosen]["sha256"],
                        "racket_evaluations": len(HEIGHT_LIMITS) * len(inputs),
                    },
                }
            )

    ordered = sorted(verified, key=lambda row: row["public_id"])
    manifest = {
        "schema": "cf4fdf474ad5-height-threshold-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": "max_height",
            "values": list(HEIGHT_LIMITS),
            "default": DEFAULT_MAX_HEIGHT,
            "input_constraints": "unchanged selected four-patch generator grammar",
        },
        "counts": {"demos": demos, "queries": queries},
        "program_sha256": {
            str(limit): record["sha256"] for limit, record in program_records.items()
        },
        "source_sha256": source_hashes,
        "racket": runtime_identity,
        "episodes": [row["receipt"] for row in ordered],
        "verification": {
            "all_labels_protected_racket": True,
            "finite_survivor_count_per_episode": 1,
            "all_queries_distinguish_each_rival": True,
            "public_names_derive_from_visible_bytes": True,
            "duplicate_visible_payloads_rejected_before_write": True,
        },
        "limitations": [
            "prototype evidence is not an acceptance record",
            "the declared three-setting family is finite and intentionally narrow",
        ],
    }

    out.mkdir(parents=True)
    (out / "public").mkdir()
    (out / "private").mkdir()
    (out / "rules").mkdir()
    for limit, source in programs.items():
        (out / "rules" / f"max-height-{limit}.rkt").write_text(
            source, encoding="utf-8"
        )
    for row in ordered:
        name = f"{row['public_id']}.json"
        (out / "public" / name).write_bytes(row["public_bytes"])
        (out / "private" / name).write_bytes(row["private_bytes"])
    (out / "manifest.json").write_bytes(_pretty_json_bytes(manifest))
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Materialize protected-Racket height-threshold prototype evidence"
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", type=int, default=1)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=(args.seeds if args.seeds is not None else [0, 1, 2]),
        demos=args.demos,
        queries=args.queries,
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
