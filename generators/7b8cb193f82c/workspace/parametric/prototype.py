"""Isolated outer-layer-color prototype for ARC task 7b8cb193f82c.

This is proposed evidence only.  It does not alter the selected production
``generate`` path, canonical authority, or RULE_HASH.  Every retained label is
produced by executing one exact materialized Racket program through the bundled
Racket bridge.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "7b8cb193f82c"
PARAMETER = "outer_color"
ALLOWED_OUTER_COLORS = (2, 3)
DEFAULT_OUTER_COLOR = 2
CANONICAL_TEXT_SHA256 = "1e2425379d5d08e4b3b618bb1d98883c8c582cacec276711cccf829c2a256767"
_CANONICAL_FRAGMENT = "(if (odd? d) 2 3)"
_ALTERNATIVE_FRAGMENT = "(if (odd? d) 3 2)"
PROTOTYPE_VERSION = "outer-color-v1"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode())


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer (not bool)")
    return seed


def validate_outer_color(outer_color: Any) -> int:
    if type(outer_color) is not int or outer_color not in ALLOWED_OUTER_COLORS:
        raise ValueError("outer_color must be the integer 2 or 3")
    return outer_color


def choose_outer_color(seed: Any) -> int:
    """Choose the hidden rule once for the whole episode."""
    seed = _validate_seed(seed)
    digest = hashlib.sha256(f"{PROTOTYPE_VERSION}:{seed}".encode()).digest()
    return ALLOWED_OUTER_COLORS[int.from_bytes(digest[:8], "big") % 2]


def canonical_program(*, root: Path | str | None = None) -> str:
    root_path = Path(root) if root is not None else find_root(__file__)
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError("prototype requires exactly one canonical program")
    source = sources.pop()
    if sha256_text(source) != CANONICAL_TEXT_SHA256:
        raise ValueError("canonical program changed; review the prototype again")
    return source


def program_for(outer_color: Any, *, root: Path | str | None = None) -> str:
    """Materialize exact default Racket or its one-site color-phase variant."""
    outer_color = validate_outer_color(outer_color)
    source = canonical_program(root=root)
    if source.count(_CANONICAL_FRAGMENT) != 1:
        raise ValueError("canonical edit point is absent or ambiguous")
    if outer_color == DEFAULT_OUTER_COLOR:
        return source
    return source.replace(_CANONICAL_FRAGMENT, _ALTERNATIVE_FRAGMENT)


def _rule_body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("prototype program must be one (rule! BODY) form")
    return text[len("(rule!") : -1].strip()


def execute_program(
    bridge: RacketBridge, program: str, grid: list[list[int]]
) -> list[list[int]]:
    """Execute a materialized program through the included Racket bridge."""
    normalized = normalize_grid(grid)
    bridge.define_grid("g", normalized)
    return normalize_grid(bridge.eval_text(_rule_body(program)))


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _draw_frame(
    grid: list[list[int]],
    top: int,
    left: int,
    hole_height: int,
    hole_width: int,
    thickness: int,
) -> None:
    frame_height = hole_height + 2 * thickness
    frame_width = hole_width + 2 * thickness
    for row in range(top, top + frame_height):
        for col in range(left, left + frame_width):
            grid[row][col] = 8
    for row in range(top + thickness, top + thickness + hole_height):
        for col in range(left + thickness, left + thickness + hole_width):
            grid[row][col] = 0


def _single_frame(
    rng: random.Random,
    height: int,
    width: int,
    depth: int,
    thickness: int,
) -> list[list[int]]:
    hole_height, hole_width = 2 * depth - 1, 2 * depth
    if rng.randrange(2):
        hole_height, hole_width = hole_width, hole_height
    frame_height = hole_height + 2 * thickness
    frame_width = hole_width + 2 * thickness
    grid = _blank(height, width)
    top = rng.randrange(height - frame_height + 1)
    left = rng.randrange(width - frame_width + 1)
    _draw_frame(grid, top, left, hole_height, hole_width, thickness)
    return grid


def _multi_frame(rng: random.Random) -> list[list[int]]:
    grid = _blank(14, 22)
    deep = (5, 6)
    shallow = (1, 2)
    if rng.randrange(2):
        deep = tuple(reversed(deep))
    if rng.randrange(2):
        shallow = tuple(reversed(shallow))
    first = (deep, 1, rng.randrange(14 - (deep[0] + 2) + 1))
    second = (shallow, 16, rng.randrange(14 - (shallow[0] + 2) + 1))
    if rng.randrange(2):
        first, second = second, first
        # Re-anchor after swapping so the footprints remain disjoint.
        first = (first[0], 1, first[2])
        second = (second[0], 13, second[2])
    for (hole_h, hole_w), left, top in (first, second):
        _draw_frame(grid, top, left, hole_h, hole_w, 1)
    return grid


def episode_inputs(seed: Any) -> list[list[list[int]]]:
    """Return three demonstrations and one query input, independent of rule value."""
    seed = _validate_seed(seed)
    rng = random.Random(f"{PROTOTYPE_VERSION}:inputs:{seed}")
    return [
        _single_frame(rng, 10, 12, depth=1, thickness=1),
        _single_frame(rng, 12, 14, depth=2, thickness=2),
        _multi_frame(rng),
        _single_frame(rng, 17, 20, depth=5, thickness=1),
    ]


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def build_episode(
    seed: Any,
    *,
    bridge: RacketBridge,
    root: Path | str | None = None,
    outer_color: Any | None = None,
) -> dict[str, Any]:
    """Build one complete episode with a single hidden rule setting."""
    seed = _validate_seed(seed)
    selected = choose_outer_color(seed) if outer_color is None else validate_outer_color(outer_color)
    rival = next(value for value in ALLOWED_OUTER_COLORS if value != selected)
    program = program_for(selected, root=root)
    rival_program = program_for(rival, root=root)
    inputs = episode_inputs(seed)
    outputs = [execute_program(bridge, program, grid) for grid in inputs]
    rival_outputs = [execute_program(bridge, rival_program, grid) for grid in inputs]
    pairs = [
        {"input": copy.deepcopy(grid), "output": output}
        for grid, output in zip(inputs, outputs)
    ]
    differing_train = [index for index in range(3) if outputs[index] != rival_outputs[index]]
    query_differs = outputs[3] != rival_outputs[3]
    status = "refuted_by_demonstrations" if differing_train else "ambiguous"
    return {
        "schema": "7b8cb193f82c-parametric-episode-v1",
        "scope": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_selection": "seeded_once" if outer_color is None else "explicit_once",
        "parameters": {PARAMETER: selected},
        "program": program,
        "program_sha256": sha256_text(program),
        "train": pairs[:3],
        "test": pairs[3:],
        "input_sha256": [sha256_json(grid) for grid in inputs],
        "rival": {
            "parameters": {PARAMETER: rival},
            "program": rival_program,
            "program_sha256": sha256_text(rival_program),
            "predictions": rival_outputs,
            "status": status,
            "differing_train_indices": differing_train,
            "query_differs": query_differs,
        },
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_for_setting(setting: int, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_outer_color(seed) != setting:
        seed += 1
    return seed


def materialize(
    out_dir: Path | str,
    *,
    seed_start: int = 731,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Execute both settings and retain public/private, source-bound evidence."""
    seed_start = _validate_seed(seed_start)
    output = Path(out_dir)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence directory: {output}")
    output.mkdir(parents=True)
    root_path = Path(root) if root is not None else find_root(__file__)

    programs = {setting: program_for(setting, root=root_path) for setting in ALLOWED_OUTER_COLORS}
    for setting, program in programs.items():
        path = output / "private" / "rules" / f"outer-{setting}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program + ("" if program.endswith("\n") else "\n"), encoding="utf-8")

    summaries: list[dict[str, Any]] = []
    used: set[int] = set()
    private_episodes: list[dict[str, Any]] = []
    with RacketBridge(timeout=15, startup_timeout=60, max_calls_before_restart=128) as bridge:
        for index, setting in enumerate(ALLOWED_OUTER_COLORS):
            seed = _seed_for_setting(setting, seed_start + index, used)
            used.add(seed)
            episode = build_episode(seed, bridge=bridge, root=root_path)
            if episode["parameters"][PARAMETER] != setting:
                raise AssertionError("seed search returned the wrong parameter setting")
            if episode["rival"]["status"] != "refuted_by_demonstrations":
                raise AssertionError("demonstrations failed to identify the selected setting")
            if not episode["rival"]["query_differs"]:
                raise AssertionError("query does not require the selected setting")

            public = public_challenge(episode)
            public_path = Path("public") / f"episode-{index:03d}.json"
            private_path = Path("private") / f"episode-{index:03d}.json"
            _write_json(output / public_path, public)
            _write_json(output / private_path, episode)
            private_episodes.append(episode)
            summaries.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "program_sha256": episode["program_sha256"],
                    "rival_status": episode["rival"]["status"],
                    "differing_train_indices": episode["rival"]["differing_train_indices"],
                    "query_differs": episode["rival"]["query_differs"],
                    "public_path": public_path.as_posix(),
                    "private_path": private_path.as_posix(),
                    "public_sha256": sha256_json(public),
                }
            )

    witness = {
        "input": private_episodes[0]["train"][0]["input"],
        "outer_2_output": execute_saved_output(private_episodes, 2, 0),
        "outer_3_output": execute_saved_output(private_episodes, 3, 0),
    }
    witness["outputs_differ"] = witness["outer_2_output"] != witness["outer_3_output"]
    _write_json(output / "private" / "differing-witness.json", witness)

    source_path = Path(__file__).resolve()
    report = {
        "schema": "7b8cb193f82c-parametric-evidence-v1",
        "status": "passed",
        "scope": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": PARAMETER,
            "allowed_values": list(ALLOWED_OUTER_COLORS),
            "original_default": DEFAULT_OUTER_COLOR,
            "selected_once_per_episode": True,
            "input_constraints": (
                "Inputs remain canonical-style zero backgrounds with closed color-8 rectangular "
                "frames; the parameter changes only whether inward depth 1 begins with 2 or 3."
            ),
        },
        "canonical_program_sha256": CANONICAL_TEXT_SHA256,
        "prototype_source": str(source_path),
        "prototype_source_sha256": sha256_bytes(source_path.read_bytes()),
        "episodes": summaries,
        "differing_witness": "private/differing-witness.json",
        "run_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric/outer-color-v1",
        ],
        "limitations": [
            "Proposed isolated prototype only; canonical generation and authority remain fixed to outer color 2.",
            "Evidence covers two deterministic episodes and one declared parameter rival, not every seed or every alternative rule.",
            "Any demonstration with a nonempty frame reveals this color parameter; the prototype does not test harder latent-parameter inference.",
        ],
    }
    _write_json(output / "report.json", report)

    files = {
        path.relative_to(output).as_posix(): sha256_bytes(path.read_bytes())
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "schema": "7b8cb193f82c-parametric-manifest-v1",
        "scope": "prototype",
        "files": files,
    }
    _write_json(output / "manifest.json", manifest)
    return report


def execute_saved_output(episodes: list[dict[str, Any]], setting: int, pair_index: int) -> list[list[int]]:
    """Read one retained setting prediction without reopening Racket."""
    validate_outer_color(setting)
    for episode in episodes:
        selected = episode["parameters"][PARAMETER]
        if selected == setting:
            return copy.deepcopy(episode["train"][pair_index]["output"])
        if episode["rival"]["parameters"][PARAMETER] == setting:
            return copy.deepcopy(episode["rival"]["predictions"][pair_index])
    raise ValueError(f"setting {setting} is absent from retained episodes")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=731)
    args = parser.parse_args()
    report = materialize(args.out, seed_start=args.seed_start)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
