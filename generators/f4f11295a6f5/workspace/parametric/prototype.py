#!/usr/bin/env python3
"""Unapproved episode-level ``tile_color_mode`` prototype for f4f11295a6f5.

The selected canonical generator and Racket authority remain unchanged by this
module.  It preserves the original crop-as-mask / crop-as-tile reasoning and
adds one bounded rule parameter chosen once per complete episode:

``exact`` (canonical default)
    Every nonzero selector cell emits an exact copy of the multicolor crop.
``selector`` (proposed alternative)
    Every nonzero selector cell emits the crop's occupancy mask, recolored to
    the selector cell's own color.

Both Racket programs are materialized from the exact canonical source by one
guarded replacement.  Labels in retained evidence are executed by the bundled
Racket runtime, not trusted from a Python-only mirror.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "f4f11295a6f5"
SCHEMA = "f4f11295a6f5-tile-color-mode-prototype-v1"
PARAMETER_NAME = "tile_color_mode"
SETTINGS = ("exact", "selector")
DEFAULT_SETTING = "exact"
N_TRAIN = 3
N_TEST = 1

CANONICAL_SITE = "(if (!= 0 (at pat br bc)) (at pat pr pc) 0)"
ALTERNATIVE_SITE = (
    "(if (!= 0 (at pat br bc)) "
    "(if (!= 0 (at pat pr pc)) (at pat br bc) 0) 0)"
)

PARAMETERS = {
    PARAMETER_NAME: {
        "allowed": list(SETTINGS),
        "default": DEFAULT_SETTING,
        "meaning": (
            "Whether a selected output block copies the crop's exact colors "
            "or recolors its occupancy mask by the selector cell."
        ),
        "input_constraints": (
            "Lawful canonical-family inputs; retained episodes use at least two "
            "crop colors so demonstrations distinguish both settings."
        ),
    }
}

_BASE_PATTERNS = (
    (
        (1, 2),
        (0, 1),
    ),
    (
        (1, 2, 0),
        (0, 1, 2),
        (2, 0, 1),
    ),
    (
        (1, 0, 2, 1),
        (0, 3, 0, 2),
        (2, 1, 0, 3),
    ),
    (
        (1, 2, 0),
        (0, 1, 3),
        (2, 0, 1),
        (3, 1, 0),
    ),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return sha256_bytes(payload)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative plain Python integer")
    return seed


def _validate_setting(tile_color_mode: Any) -> str:
    if type(tile_color_mode) is not str or tile_color_mode not in SETTINGS:
        raise ValueError(f"tile_color_mode must be one of {SETTINGS}")
    return tile_color_mode


def root_path(root: str | Path | None = None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def load_generator(*, root: str | Path | None = None):
    return load_selected_generator(TASK_ID, root=root_path(root))


def canonical_program(*, root: str | Path | None = None) -> str:
    """Read the one selected canonical program and validate the edit site."""
    programs: list[str] = []
    with canonical_path(root_path(root)).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                programs.append(row["program_solution"])
    programs = list(dict.fromkeys(programs))
    if len(programs) != 1:
        raise ValueError(
            f"expected one canonical program for {TASK_ID}, found {len(programs)}"
        )
    source = programs[0]
    if source.count(CANONICAL_SITE) != 1:
        raise ValueError(
            "canonical program no longer has exactly one declared tile-color site"
        )
    if ALTERNATIVE_SITE in source:
        raise ValueError("canonical program unexpectedly contains alternative site")
    return source


def render_program(
    tile_color_mode: str = DEFAULT_SETTING,
    *,
    root: str | Path | None = None,
) -> str:
    """Instantiate exact Racket; ``exact`` is byte-identical to authority."""
    tile_color_mode = _validate_setting(tile_color_mode)
    source = canonical_program(root=root)
    if tile_color_mode == DEFAULT_SETTING:
        return source
    changed = source.replace(CANONICAL_SITE, ALTERNATIVE_SITE, 1)
    if changed == source or changed.count(ALTERNATIVE_SITE) != 1:
        raise AssertionError("failed to instantiate selector-colored tile rule")
    return changed


def choose_parameters(seed: int) -> dict[str, str]:
    """Draw the hidden rule exactly once for one episode."""
    _validate_seed(seed)
    return {PARAMETER_NAME: SETTINGS[seed % len(SETTINGS)]}


def _place_pattern(pattern: list[list[int]], rng: random.Random) -> list[list[int]]:
    pattern_h = len(pattern)
    pattern_w = len(pattern[0])
    height = pattern_h * pattern_h
    width = pattern_w * pattern_w
    top = rng.randint(0, height - pattern_h)
    left = rng.randint(0, width - pattern_w)
    grid = [[0] * width for _ in range(height)]
    for row in range(pattern_h):
        for column in range(pattern_w):
            grid[top + row][left + column] = pattern[row][column]
    return grid


def fixture_inputs(
    seed: int,
    *,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Return four setting-independent, lawful, multicolor family inputs."""
    _validate_seed(seed)
    generator, _source, _digest = load_generator(root=root)
    rng = random.Random(seed ^ 0xF4F11295)
    grids: list[list[list[int]]] = []
    for index, source in enumerate(_BASE_PATTERNS):
        palette = rng.sample(range(1, 10), 3)
        pattern = [
            [0 if value == 0 else palette[value - 1] for value in row]
            for row in source
        ]
        # A per-fixture fork keeps translations reproducible if fixture order
        # changes in a later prototype revision.
        grid = _place_pattern(pattern, random.Random(rng.randrange(1 << 63) ^ index))
        errors = generator.self_check(grid)
        if errors:
            raise RuntimeError(f"fixture {index} is outside task domain: {errors}")
        _coerced, features, analysis_errors = generator._scene_analysis(grid)
        if analysis_errors or features["color_count"] < 2:
            raise RuntimeError(
                f"fixture {index} does not distinguish tile-color settings"
            )
        grids.append(normalize_grid(grid))
    if len({json_sha256(grid) for grid in grids}) != len(grids):
        raise RuntimeError("fixture construction produced duplicate inputs")
    return grids


def _racket_datum(grid: list[list[int]]) -> str:
    normalized = normalize_grid(grid)
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in normalized
    ) + ")"


def _execute_with_bridge(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    function = strip_rule_wrapper(program)
    if not function.lstrip().startswith("(lambda"):
        raise ValueError("expected canonical rule! wrapper around a lambda")
    expression = f"({function} '{_racket_datum(grid)})"
    return normalize_grid(bridge.eval_text(expression))


def racket_outputs(
    grids: list[list[list[int]]],
    *,
    tile_color_mode: str = DEFAULT_SETTING,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    tile_color_mode = _validate_setting(tile_color_mode)
    program = render_program(tile_color_mode, root=root)
    with RacketBridge() as bridge:
        return [
            _execute_with_bridge(bridge, program, grid)
            for grid in grids
        ]


def _all_setting_outputs(
    grids: list[list[list[int]]],
    *,
    root: str | Path | None = None,
) -> dict[str, list[list[list[int]]]]:
    programs = {setting: render_program(setting, root=root) for setting in SETTINGS}
    outputs: dict[str, list[list[list[int]]]] = {}
    with RacketBridge() as bridge:
        for setting in SETTINGS:
            outputs[setting] = [
                _execute_with_bridge(bridge, programs[setting], grid)
                for grid in grids
            ]
    return outputs


def make_episode(
    seed: int,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Build one three-demo/one-query private episode from real Racket labels."""
    _validate_seed(seed)
    parameters = choose_parameters(seed)
    selected_setting = parameters[PARAMETER_NAME]
    rival_setting = next(setting for setting in SETTINGS if setting != selected_setting)
    grids = fixture_inputs(seed, root=root)
    outputs = _all_setting_outputs(grids, root=root)
    selected = outputs[selected_setting]
    rival = outputs[rival_setting]
    refuting = [
        index for index in range(N_TRAIN) if selected[index] != rival[index]
    ]
    query_differs = selected[N_TRAIN] != rival[N_TRAIN]
    if not refuting:
        raise RuntimeError("demonstrations fail to identify tile_color_mode")
    if not query_differs:
        raise RuntimeError("retained query does not exercise tile_color_mode")

    pairs = [
        {
            "input": deepcopy(grid),
            "output": deepcopy(output),
            "input_sha256": json_sha256(grid),
            "output_sha256": json_sha256(output),
        }
        for grid, output in zip(grids, selected)
    ]
    program = render_program(selected_setting, root=root)
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "prototype_status": "unapproved",
        "seed": seed,
        "parameters": parameters,
        "parameter_choice": "deterministic_once_per_episode",
        "parameter_draw_count": 1,
        "canonical_default": selected_setting == DEFAULT_SETTING,
        "program": program,
        "program_sha256": sha256_text(program),
        "program_normalized_hash_12": sha256_text(" ".join(program.split()))[:12],
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "rival": {
            "parameters": {PARAMETER_NAME: rival_setting},
            "program_sha256": sha256_text(render_program(rival_setting, root=root)),
            "refuting_demonstration_indices": refuting,
            "query_differs": query_differs,
        },
    }


def public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden semantics, source, seed, rivals, and query labels."""
    public = {
        "schema": "arc-parametric-challenge-v1",
        "task_id": episode["task_id"],
        "episode_id": sha256_text(
            f"{episode['task_id']}|public|{episode['seed']}"
        )[:16],
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
    }
    for pair in public["train"] + public["test"]:
        pair.pop("input_sha256", None)
        pair.pop("output_sha256", None)
    for pair in public["test"]:
        pair.pop("output", None)
    return public


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest_rows(out_dir: Path, paths: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(paths):
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(out_dir).as_posix(),
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    return rows


def build_evidence(
    seed: int,
    out_dir: str | Path,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Execute both settings and write a source-bound evidence bundle."""
    _validate_seed(seed)
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    root = root_path(root)
    generator, generator_path, generator_sha = load_generator(root=root)
    del generator

    seeds: dict[str, int] = {}
    candidate = seed
    while len(seeds) < len(SETTINGS):
        setting = choose_parameters(candidate)[PARAMETER_NAME]
        seeds.setdefault(setting, candidate)
        candidate += 1

    episodes = {
        setting: make_episode(setting_seed, root=root)
        for setting, setting_seed in seeds.items()
    }
    exact_program = render_program("exact", root=root)
    canonical = canonical_program(root=root)
    if exact_program != canonical:
        raise AssertionError("canonical-default prototype source is not byte-identical")

    created: list[Path] = []
    for setting in SETTINGS:
        rule_path = out_dir / "rules" / f"{setting}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(render_program(setting, root=root) + "\n", encoding="utf-8")
        created.append(rule_path)

        private_path = out_dir / "private" / f"episode_{setting}.json"
        public_path = out_dir / "public" / f"challenge_{setting}.json"
        _write_json(private_path, episodes[setting])
        _write_json(public_path, public_episode(episodes[setting]))
        created.extend((private_path, public_path))

    witness_grid = fixture_inputs(seed, root=root)[0]
    witness_outputs = {
        setting: racket_outputs(
            [witness_grid], tile_color_mode=setting, root=root
        )[0]
        for setting in SETTINGS
    }
    if witness_outputs["exact"] == witness_outputs["selector"]:
        raise AssertionError("setting-difference witness is not distinguishing")
    witness_path = out_dir / "setting_difference_witness.json"
    _write_json(
        witness_path,
        {
            "task_id": TASK_ID,
            "input": witness_grid,
            "outputs": witness_outputs,
            "program_sha256": {
                setting: sha256_text(render_program(setting, root=root))
                for setting in SETTINGS
            },
        },
    )
    created.append(witness_path)

    source_path = Path(__file__).resolve()
    report = {
        "schema": "arc-parametric-prototype-report-v1",
        "task_id": TASK_ID,
        "status": "verified_prototype",
        "approval": "unapproved; separate from selected canonical execution",
        "parameter": PARAMETERS,
        "settings_verified": list(SETTINGS),
        "canonical_default_byte_identical": True,
        "episode_seeds": seeds,
        "n_train": N_TRAIN,
        "n_test": N_TEST,
        "demonstrations_distinguish_rival": {
            setting: bool(
                episodes[setting]["rival"]["refuting_demonstration_indices"]
            )
            for setting in SETTINGS
        },
        "queries_differ_between_settings": {
            setting: episodes[setting]["rival"]["query_differs"]
            for setting in SETTINGS
        },
        "label_authority": "bundled real Racket runtime",
        "racket_runtime": racket_runtime_status(),
        "generator_path": generator_path.relative_to(root).as_posix(),
        "generator_sha256": generator_sha,
        "canonical_program_sha256": sha256_text(canonical),
        "prototype_path": source_path.relative_to(root).as_posix(),
        "prototype_sha256": sha256_bytes(source_path.read_bytes()),
        "limits": [
            "Only two bounded tile-color settings were evaluated.",
            "Four deterministic multicolor fixtures per episode are finite evidence, not universal induction.",
            "The alternative is proposed only; it is not selected, reviewed_safe, or approved for training.",
        ],
    }
    report_path = out_dir / "report.json"
    _write_json(report_path, report)
    created.append(report_path)

    manifest = {
        "schema": "arc-parametric-evidence-manifest-v1",
        "task_id": TASK_ID,
        "files": _manifest_rows(out_dir, created),
    }
    _write_json(out_dir / "manifest.json", manifest)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = build_evidence(args.seed, args.out)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
