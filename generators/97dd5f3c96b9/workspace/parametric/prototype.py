"""Bounded episode-level connector-color prototype for task 97dd5f3c96b9.

The production generator and canonical rule stay unchanged.  This task-local
prototype varies one hidden episode setting: connector interiors either retain
each pair's marker color (the exact canonical rule) or use a fixed color 8/9.
Endpoints always retain their original marker colors.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from functools import cache
from pathlib import Path
import sys
from typing import Any

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "97dd5f3c96b9"
ROOT = find_root(__file__)
GENERATOR_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_SOURCE.is_file():
    raise FileNotFoundError(GENERATOR_SOURCE)
GENERATOR_SHA256 = hashlib.sha256(GENERATOR_SOURCE.read_bytes()).hexdigest()
_GEN_NAME = "_connector_color_selected_" + GENERATOR_SHA256[:16]
_GEN_SPEC = importlib.util.spec_from_file_location(_GEN_NAME, GENERATOR_SOURCE)
if _GEN_SPEC is None or _GEN_SPEC.loader is None:
    raise ImportError(f"cannot load selected generator at {GENERATOR_SOURCE}")
GEN = importlib.util.module_from_spec(_GEN_SPEC)
_GEN_SPEC.loader.exec_module(GEN)

CONNECTOR_COLORS = ("pair_color", "fixed_8", "fixed_9")
DEFAULT_CONNECTOR_COLOR = "pair_color"
STATUS = "proposed task-local prototype; not production-approved"


def _validate_connector_color(connector_color: Any) -> str:
    if type(connector_color) is not str:
        raise TypeError(
            "connector_color must be one of " + ", ".join(CONNECTOR_COLORS)
        )
    if connector_color not in CONNECTOR_COLORS:
        raise ValueError(
            "connector_color must be one of " + ", ".join(CONNECTOR_COLORS)
        )
    return connector_color


@cache
def canonical_program() -> str:
    """Return the unique authoritative source, preserving its exact bytes."""
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
        raise ValueError(
            f"expected one canonical program for {TASK_ID}, found {len(programs)}"
        )
    return programs.pop()


def _fixed_program(connector: int) -> str:
    if connector not in (8, 9):
        raise ValueError("fixed connector must be 8 or 9")
    return (
        "(rule! (let ((connector "
        + str(connector)
        + ")) "
        "(define (paint-interior grid cells) "
        "(for/fold ((out grid)) ((p (in-list cells))) "
        "(if (in-bounds? (first p) (second p) (rows out) (cols out)) "
        "(set-cell out (first p) (second p) connector) out))) "
        "(for/fold ((out g)) ((color (in-list (grid-colors g 0)))) "
        "(let ((cells (find-color g color))) "
        "(if (= (length cells) 2) "
        "(let ((a (first cells)) (b (second cells))) "
        "(cond "
        "((= (first a) (first b)) "
        "(paint-interior out "
        "(for/list ((c (in-range (+ (min (second a) (second b)) 1) "
        "(max (second a) (second b))))) "
        "(list (first a) c)))) "
        "((= (second a) (second b)) "
        "(paint-interior out "
        "(for/list ((r (in-range (+ (min (first a) (first b)) 1) "
        "(max (first a) (first b))))) "
        "(list r (second a))))) "
        "(else out))) out)))))"
    )


def program_for(connector_color: str = DEFAULT_CONNECTOR_COLOR) -> str:
    """Materialize exact executable Racket for one bounded setting."""
    setting = _validate_connector_color(connector_color)
    if setting == "pair_color":
        return canonical_program()
    return _fixed_program(8 if setting == "fixed_8" else 9)


def _scene(grid: Any) -> dict[str, Any]:
    errors, scene = GEN._analyze(grid)
    if errors or scene is None:
        raise ValueError(
            "prototype input violates canonical grammar: " + "; ".join(errors)
        )
    return scene


def python_apply(grid: Any, connector_color: str = DEFAULT_CONNECTOR_COLOR) -> list[list[int]]:
    """Independent Python semantic mirror for prototype audits."""
    setting = _validate_connector_color(connector_color)
    scene = _scene(grid)
    if setting == "pair_color":
        return normalize_grid(GEN.rule_mirror(grid))

    connector = 8 if setting == "fixed_8" else 9
    output = normalize_grid(grid)
    for pair in scene["pairs"]:
        for row, column in pair["span"][1:-1]:
            output[row][column] = connector
    return output


def execute_program(bridge, program: str, grid: Any) -> list[list[int]]:
    """Execute exact ``(rule! ...)`` text through the protected Racket bridge."""
    if not isinstance(program, str) or not program.lstrip().startswith("(rule!"):
        raise ValueError("program must be exact (rule! ...) Racket text")
    _scene(grid)
    bridge.define_grid("connector_color_grid", normalize_grid(grid))
    callable_rule = wrap_rule(program)
    result = bridge.eval_text(f"({callable_rule} connector_color_grid)")
    return normalize_grid(result)


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


def settings_for_seed(seed: int) -> dict[str, str]:
    """Choose one hidden setting deterministically before drawing inputs."""
    value = _validate_seed(seed)
    return {"connector_color": CONNECTOR_COLORS[value % len(CONNECTOR_COLORS)]}


def _input_seed(seed: int) -> int:
    import hashlib

    raw = hashlib.sha256(f"{TASK_ID}:connector-color:{seed}".encode()).digest()
    return int.from_bytes(raw[:8], "big") & (2**63 - 1)


def _episode_inputs(seed: int, total: int) -> list[list[list[int]]]:
    profiles = tuple(GEN.SCENE_PROFILES)
    difficulties = ("easy", "medium", "hard", None)
    generation_seed = _input_seed(seed)
    inputs: list[list[list[int]]] = []
    seen: set[str] = set()
    attempt = 0
    max_attempts = max(64, total * 64)
    while len(inputs) < total and attempt < max_attempts:
        slot = len(inputs)
        grid = GEN.generate(
            generation_seed,
            attempt,
            difficulty=difficulties[slot % len(difficulties)],
            scene_profile=profiles[slot % len(profiles)],
        )
        errors = GEN.self_check(grid)
        if errors:
            raise RuntimeError(
                "selected generator returned an unlawful prototype input: "
                + "; ".join(errors)
            )
        normalized = normalize_grid(grid)
        key = json.dumps(normalized, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            inputs.append(normalized)
        attempt += 1
    if len(inputs) != total:
        raise RuntimeError(
            f"could not draw {total} distinct lawful inputs in {max_attempts} attempts"
        )
    return inputs


def generate_episode(
    seed: int,
    connector_color: str,
    *,
    demos: int,
    queries: int,
) -> dict[str, Any]:
    """Return deterministic Python-claimed pairs for independent Racket review."""
    seed = _validate_seed(seed)
    setting = _validate_connector_color(connector_color)
    demos = _validate_count("demos", demos)
    queries = _validate_count("queries", queries)
    inputs = _episode_inputs(seed, demos + queries)
    pairs = [
        {"input": grid, "output": python_apply(grid, setting)}
        for grid in inputs
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(setting),
    }


def _sha256(data: bytes | str) -> str:
    import hashlib

    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _public_projection(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {
                "input": normalize_grid(pair["input"]),
                "output": normalize_grid(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": normalize_grid(pair["input"])}
            for pair in episode["test"]
        ],
    }


def _source_hashes() -> dict[str, str]:
    paths = [
        GENERATOR_SOURCE,
        __file__,
        str(__file__).replace("prototype.py", "adapter.py"),
        str(__file__).replace("prototype.py", "promotion.json"),
    ]
    result: dict[str, str] = {}
    for raw in paths:
        from pathlib import Path

        path = Path(raw).resolve()
        if path.is_file():
            result[str(path.relative_to(ROOT))] = _sha256(path.read_bytes())
    return result


def write_evidence(
    out_dir,
    *,
    seeds=(0, 1, 2),
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    """Write public challenges and private protected-Racket receipts atomically enough.

    All generation, duplicate checks, and Racket verification finish before the
    destination is created.  Existing destinations are never modified.
    """
    from pathlib import Path

    from arc_repl.racket_bridge import RacketBridge
    from reviewer_support import public_challenge_bytes, public_challenge_id

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
        setting = settings["connector_color"]
        episode = generate_episode(
            seed,
            setting,
            demos=demos,
            queries=queries,
        )
        public = _public_projection(episode)
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

    programs = {setting: program_for(setting) for setting in CONNECTOR_COLORS}
    program_records = {
        setting: {"source": source, "sha256": _sha256(source)}
        for setting, source in programs.items()
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
            chosen = item["settings"]["connector_color"]
            pairs = episode["train"] + episode["test"]
            inputs = [pair["input"] for pair in pairs]
            executed = {
                setting: [
                    execute_program(bridge, programs[setting], grid)
                    for grid in inputs
                ]
                for setting in CONNECTOR_COLORS
            }
            claimed = [normalize_grid(pair["output"]) for pair in pairs]
            if executed[chosen] != claimed:
                raise AssertionError(
                    f"protected Racket labels diverge from Python claims for {chosen}"
                )

            rival_checks: dict[str, Any] = {}
            survivors: list[str] = []
            for setting in CONNECTOR_COLORS:
                demo_matches = [
                    candidate == expected
                    for candidate, expected in zip(
                        executed[setting][:demos], executed[chosen][:demos]
                    )
                ]
                matches_all = all(demo_matches)
                if matches_all:
                    survivors.append(setting)
                query_disagreements = [
                    index
                    for index, (candidate, expected) in enumerate(
                        zip(
                            executed[setting][demos:],
                            executed[chosen][demos:],
                        )
                    )
                    if candidate != expected
                ]
                rival_checks[setting] = {
                    "matches_all_demonstrations": matches_all,
                    "distinguishing_demonstration_indices": [
                        index for index, matches in enumerate(demo_matches) if not matches
                    ],
                    "query_disagreement_indices": query_disagreements,
                }
            if survivors != [chosen]:
                raise AssertionError(
                    f"demonstrations leave finite survivors {survivors}, expected {[chosen]}"
                )
            expected_query_differences = list(range(queries))
            for setting in CONNECTOR_COLORS:
                if setting != chosen and rival_checks[setting][
                    "query_disagreement_indices"
                ] != expected_query_differences:
                    raise AssertionError(
                        f"query set does not distinguish {chosen} from {setting} on every query"
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
                raise AssertionError("protected Racket verification changed visible challenge bytes")

            private = {
                "schema": "97dd5f3c96b9-connector-color-private-v1",
                "status": STATUS,
                "task_id": TASK_ID,
                "public_id": public_id,
                "public_sha256": _sha256(public_bytes),
                "seed": item["seed"],
                "settings": item["settings"],
                "counts": {"demos": demos, "queries": queries},
                "generator_source": str(GENERATOR_SOURCE.relative_to(ROOT)),
                "generator_sha256": GENERATOR_SHA256,
                "canonical_rule_hash": GEN.RULE_HASH,
                "selected_program_sha256": program_records[chosen]["sha256"],
                "programs": program_records,
                "query_answers": executed[chosen][demos:],
                "rival_checks": rival_checks,
                "runtime_identity": runtime_identity,
                "source_hashes": source_hashes,
                "label_execution": {
                    "engine": "protected_racket",
                    "program_count": len(CONNECTOR_COLORS),
                    "input_count": len(inputs),
                    "evaluation_count": len(CONNECTOR_COLORS) * len(inputs),
                    "python_claims_matched": True,
                },
                "limitations": [
                    "task-local proposed prototype; no production approval or training admission",
                    "finite identifiability covers only pair_color, fixed_8, and fixed_9",
                    "evidence covers only the listed seeds and requested counts",
                ],
            }
            private_bytes = _pretty_json_bytes(private)
            verified.append(
                {
                    "public": public,
                    "public_bytes": public_bytes,
                    "public_id": public_id,
                    "private": private,
                    "private_bytes": private_bytes,
                    "receipt": {
                        "public_id": public_id,
                        "public_sha256": _sha256(public_bytes),
                        "private_sha256": _sha256(private_bytes),
                        "seed": item["seed"],
                        "settings": item["settings"],
                        "counts": {"demos": demos, "queries": queries},
                        "selected_program_sha256": program_records[chosen]["sha256"],
                    },
                }
            )

    manifest = {
        "schema": "97dd5f3c96b9-connector-color-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": "connector_color",
            "values": list(CONNECTOR_COLORS),
            "default": DEFAULT_CONNECTOR_COLOR,
            "input_constraints": "unchanged production generator grammar",
        },
        "counts": {"demos": demos, "queries": queries},
        "program_sha256": {
            setting: record["sha256"] for setting, record in program_records.items()
        },
        "source_hashes": source_hashes,
        "racket": runtime_identity,
        "episodes": [row["receipt"] for row in sorted(verified, key=lambda x: x["public_id"])],
        "verification": {
            "all_labels_protected_racket": True,
            "finite_survivor_count_per_episode": 1,
            "all_queries_distinguish_each_rival": True,
            "public_names_derive_from_visible_bytes": True,
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
    for setting, source in programs.items():
        (out / "rules" / f"{setting}.rkt").write_text(source, encoding="utf-8")
    for row in verified:
        name = f"challenge-{row['public_id']}.json"
        (out / "public" / name).write_bytes(row["public_bytes"])
        (out / "private" / name).write_bytes(row["private_bytes"])
    (out / "manifest.json").write_bytes(_pretty_json_bytes(manifest))
    return manifest


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Materialize protected-Racket connector-color prototype evidence"
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", type=int, default=2)
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
