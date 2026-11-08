"""Isolated expansion-side prototype for ARC task ad5a6c1521b3.

The selected generator and canonical authority remain unchanged.  This proposal
adds one bounded episode-level parameter: after selecting the winning component
and filling its bounding rectangle, add the one adjacent column on the canonical
left side or on the alternative right side.  Every retained label is produced by
executing an exact materialized Racket program through the packet's protected
Racket bridge.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "ad5a6c1521b3"
PARAMETER = "expansion_side"
EXPANSION_SIDES = ("left", "right")
CANONICAL_DEFAULT = "left"
PROTOTYPE_VERSION = "expansion-side-v1"
CANONICAL_TEXT_SHA256 = (
    "496bd7e40e8a21d14819dad4ee11d045b3b58617cfdba55872f1daa1cd06d379"
)
N_TRAIN = 3
N_TEST = 1

# This is the only source site changed by the alternative.  Exact matching makes
# authority drift fail closed rather than silently editing a different program.
_CANONICAL_BOUNDS = """                  (c0 (max 0 (- (snd bb) 1)))
                  (r1 (nth bb 2))
                  (c1 (nth bb 3))"""
_RIGHT_BOUNDS = """                  (c0 (snd bb))
                  (r1 (nth bb 2))
                  (c1 (min (- (cols g) 1) (+ (nth bb 3) 1)))"""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return _sha256_bytes(payload)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer (not bool)")
    return seed


def validate_expansion_side(value: Any) -> str:
    if type(value) is not str or value not in EXPANSION_SIDES:
        raise ValueError(
            f"expansion_side must be one of {EXPANSION_SIDES}, got {value!r}"
        )
    return value


def choose_expansion_side(seed: Any) -> str:
    """Choose one hidden transformation setting for the complete episode."""
    seed = _validate_seed(seed)
    digest = hashlib.sha256(f"{PROTOTYPE_VERSION}:{seed}".encode()).digest()
    return EXPANSION_SIDES[int.from_bytes(digest[:8], "big") % len(EXPANSION_SIDES)]


def canonical_program(*, root: Path | str | None = None) -> str:
    """Load and hash-pin the exact selected canonical Racket authority."""
    root_path = Path(root).resolve() if root is not None else find_root(__file__)
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError(f"canonical row for {TASK_ID} has no program_solution")
                sources.add(program)
    if len(sources) != 1:
        raise ValueError(
            f"prototype requires one unambiguous canonical program, found {len(sources)}"
        )
    source = sources.pop()
    actual = _sha256_text(source)
    if actual != CANONICAL_TEXT_SHA256:
        raise ValueError(
            "canonical program changed; reassess the expansion edit point "
            f"({actual} != {CANONICAL_TEXT_SHA256})"
        )
    return source


def program_for(
    expansion_side: Any = CANONICAL_DEFAULT,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact original rule or its one-site side variant."""
    selected = validate_expansion_side(expansion_side)
    source = canonical_program(root=root)
    count = source.count(_CANONICAL_BOUNDS)
    if count != 1:
        raise ValueError(
            f"canonical rule drift: expected one expansion-bound block, found {count}"
        )
    if _RIGHT_BOUNDS in source:
        raise ValueError("canonical rule unexpectedly already contains right expansion")
    if selected == CANONICAL_DEFAULT:
        return source
    return source.replace(_CANONICAL_BOUNDS, _RIGHT_BOUNDS, 1)


def _rule_body(program: str) -> str:
    text = program.strip()
    prefix = "(rule! "
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("prototype program must be one plain (rule! BODY) form")
    return text[len(prefix) : -1].strip()


def _callable_program(program: str) -> str:
    # This task uses a body-form rule.  Reproduce rule!'s documented g/h/w
    # binding without depending on optional source-parser modules.
    body = _rule_body(program)
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def execute_outputs(
    bridge: RacketBridge,
    program: str,
    grids: Iterable[list[list[int]]],
) -> list[list[list[int]]]:
    """Apply one exact materialized Racket rule to every supplied input."""
    callable_text = _callable_program(program)
    outputs: list[list[list[int]]] = []
    for grid in grids:
        normalized = normalize_grid(grid)
        result = bridge.eval_text(f"({callable_text} {_grid_literal(normalized)})")
        outputs.append(normalize_grid(result))
    return outputs


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + drow, col + dcol)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(row for row, _ in points),
        min(col for _, col in points),
        max(row for row, _ in points),
        max(col for _, col in points),
    )


def _winner(components: list[set[tuple[int, int]]]) -> set[tuple[int, int]]:
    return max(components, key=lambda cells: (len(cells), sum(_bbox(cells)[:2])))


def _rectangles_overlap(
    first: tuple[int, int, int, int], second: tuple[int, int, int, int]
) -> bool:
    ar0, ac0, ar1, ac1 = first
    br0, bc0, br1, bc1 = second
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def input_supports_both_sides(grid: Any) -> bool:
    """Return whether both side settings are visible and collision-free."""
    try:
        normalized = normalize_grid(grid)
    except ValueError:
        return False
    height, width = len(normalized), len(normalized[0])
    counts = Counter(value for row in normalized for value in row)
    highest = max(counts.values())
    modes = [color for color, count in counts.items() if count == highest]
    if len(modes) != 1:
        return False
    background = modes[0]
    active: list[tuple[int, tuple[int, int, int, int]]] = []
    for color in sorted(counts):
        if color == background:
            continue
        components = _components(normalized, color)
        if len(components) < 2:
            continue
        winner = _winner(components)
        row0, col0, row1, col1 = _bbox(winner)
        if col0 <= 0 or col1 >= width - 1:
            return False
        for row in range(row0, row1 + 1):
            if normalized[row][col0 - 1] not in (background, color):
                return False
            if normalized[row][col1 + 1] not in (background, color):
                return False
        active.append((color, (row0, col0, row1, col1)))
    if not active:
        return False

    # Independent per-color actions must not overwrite each other's expanded
    # rectangles under either proposed setting.
    for side in EXPANSION_SIDES:
        expanded = []
        for color, (row0, col0, row1, col1) in active:
            if side == "left":
                rect = (row0, col0 - 1, row1, col1)
            else:
                rect = (row0, col0, row1, col1 + 1)
            expanded.append((color, rect))
        for index, (_, first) in enumerate(expanded):
            for _, second in expanded[index + 1 :]:
                if _rectangles_overlap(first, second):
                    return False
    return all(0 <= row < height for _, rect in active for row in (rect[0], rect[2]))


def episode_inputs(
    seed: Any,
    *,
    root: Path | str | None = None,
) -> tuple[list[list[list[int]]], str, str]:
    """Draw one deterministic four-profile episode safe for both settings."""
    seed = _validate_seed(seed)
    root_path = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root_path
    )
    profiles = tuple(generator.SCENE_PROFILES)
    if len(profiles) != N_TRAIN + N_TEST:
        raise ValueError(f"expected four selected profiles, found {len(profiles)}")
    bands = ("easy", "medium", "hard", "medium")
    grids: list[list[list[int]]] = []
    for index, (profile, band) in enumerate(zip(profiles, bands, strict=True)):
        grid = None
        for attempt in range(512):
            candidate_seed = 410_000 + seed * 131 + index * 1009 + attempt
            candidate = normalize_grid(
                generator.generate(
                    candidate_seed,
                    index,
                    difficulty=band,
                    scene_profile=profile,
                )
            )
            if generator.self_check(candidate, difficulty=band):
                continue
            if input_supports_both_sides(candidate):
                grid = candidate
                break
        if grid is None:
            raise RuntimeError(
                f"could not draw a two-sided-safe input for profile {profile!r}"
            )
        grids.append(grid)
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in grids}
    if len(fingerprints) != len(grids):
        raise RuntimeError("parametric input sampler produced a duplicate grid")
    return grids, str(generator_path), generator_sha


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden parameter, Racket source, seed, and query label."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": copy.deepcopy(episode["train"]),
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def build_episode(
    seed: Any,
    *,
    bridge: RacketBridge,
    root: Path | str | None = None,
    expansion_side: Any | None = None,
) -> dict[str, Any]:
    """Build a complete, parameter-consistent, Racket-labeled episode."""
    seed = _validate_seed(seed)
    selected = (
        choose_expansion_side(seed)
        if expansion_side is None
        else validate_expansion_side(expansion_side)
    )
    rival = next(value for value in EXPANSION_SIDES if value != selected)
    root_path = Path(root).resolve() if root is not None else find_root(__file__)
    grids, generator_path, generator_sha = episode_inputs(seed, root=root_path)
    selected_program = program_for(selected, root=root_path)
    rival_program = program_for(rival, root=root_path)
    selected_outputs = execute_outputs(bridge, selected_program, grids)
    rival_outputs = execute_outputs(bridge, rival_program, grids)
    pairs = [
        {"input": copy.deepcopy(grid), "output": output}
        for grid, output in zip(grids, selected_outputs, strict=True)
    ]
    differing_train = [
        index
        for index in range(N_TRAIN)
        if selected_outputs[index] != rival_outputs[index]
    ]
    query_differs = selected_outputs[N_TRAIN] != rival_outputs[N_TRAIN]
    status = "refuted_by_demonstrations" if differing_train else "ambiguous"
    return {
        "schema": "ad5a6c1521b3-parametric-episode-v1",
        "scope": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_selection": "seeded_once" if expansion_side is None else "explicit_once",
        "parameters": {PARAMETER: selected},
        "generator_path": generator_path,
        "generator_sha256": generator_sha,
        "program": selected_program,
        "program_sha256": _sha256_text(selected_program),
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "input_sha256": [_sha256_json(grid) for grid in grids],
        "rival": {
            "parameters": {PARAMETER: rival},
            "program": rival_program,
            "program_sha256": _sha256_text(rival_program),
            "predictions": rival_outputs,
            "status": status,
            "differing_train_indices": differing_train,
            "query_differs": query_differs,
        },
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_for_setting(setting: str, start: int, used: set[int]) -> int:
    setting = validate_expansion_side(setting)
    seed = _validate_seed(start)
    while seed in used or choose_expansion_side(seed) != setting:
        seed += 1
    return seed


def materialize(
    out_dir: Path | str,
    *,
    seed_start: int = 907,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Execute both settings and retain public/private hash-bound evidence."""
    seed_start = _validate_seed(seed_start)
    output = Path(out_dir)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence: {output}")
    output.mkdir(parents=True)
    root_path = Path(root).resolve() if root is not None else find_root(__file__)

    programs = {
        setting: program_for(setting, root=root_path) for setting in EXPANSION_SIDES
    }
    for setting, program in programs.items():
        path = output / "private" / "rules" / f"{setting}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program + ("" if program.endswith("\n") else "\n"), encoding="utf-8")

    summaries: list[dict[str, Any]] = []
    private_episodes: list[dict[str, Any]] = []
    used: set[int] = set()
    with RacketBridge(
        timeout=30, startup_timeout=60, max_calls_before_restart=128
    ) as bridge:
        for index, setting in enumerate(EXPANSION_SIDES):
            seed = _seed_for_setting(setting, seed_start + index, used)
            used.add(seed)
            episode = build_episode(seed, bridge=bridge, root=root_path)
            if episode["parameters"][PARAMETER] != setting:
                raise AssertionError("seed search returned the wrong parameter setting")
            if episode["rival"]["status"] != "refuted_by_demonstrations":
                raise AssertionError("demonstrations do not identify the selected setting")
            if episode["rival"]["differing_train_indices"] != list(range(N_TRAIN)):
                raise AssertionError("every demonstration must expose expansion_side")
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
                    "generator_sha256": episode["generator_sha256"],
                    "program_sha256": episode["program_sha256"],
                    "rival_status": episode["rival"]["status"],
                    "differing_train_indices": episode["rival"][
                        "differing_train_indices"
                    ],
                    "query_differs": episode["rival"]["query_differs"],
                    "public_path": public_path.as_posix(),
                    "private_path": private_path.as_posix(),
                    "public_sha256": _sha256_json(public),
                }
            )

        witness_input = private_episodes[0]["train"][0]["input"]
        witness_outputs = {
            setting: execute_outputs(bridge, programs[setting], [witness_input])[0]
            for setting in EXPANSION_SIDES
        }
    witness = {
        "input": witness_input,
        "outputs": witness_outputs,
        "outputs_differ": witness_outputs["left"] != witness_outputs["right"],
    }
    if not witness["outputs_differ"]:
        raise AssertionError("retained parameter witness does not distinguish settings")
    _write_json(output / "private" / "differing-witness.json", witness)

    source_path = Path(__file__).resolve()
    report = {
        "schema": "ad5a6c1521b3-parametric-evidence-v1",
        "status": "passed",
        "scope": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": PARAMETER,
            "allowed_values": list(EXPANSION_SIDES),
            "original_default": CANONICAL_DEFAULT,
            "selected_once_per_episode": True,
            "semantics": {
                "left": (
                    "after selecting the largest component (canonical tie-break), "
                    "fill its bounding rectangle plus one column on the left"
                ),
                "right": (
                    "after the same selection, fill its bounding rectangle plus "
                    "one column on the right"
                ),
            },
            "input_constraints": (
                "Every active winner has an empty, in-bounds adjacent column on "
                "both sides; same-setting expanded rectangles of distinct colors "
                "do not overlap. The selected generator's object roles, component "
                "selection, erasure, bbox fill, palette, and schedule are unchanged."
            ),
        },
        "canonical_program_sha256": CANONICAL_TEXT_SHA256,
        "prototype_source": str(source_path),
        "prototype_source_sha256": _sha256_bytes(source_path.read_bytes()),
        "episodes": summaries,
        "differing_witness": "private/differing-witness.json",
        "run_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric/expansion-side-v1",
        ],
        "limitations": [
            "This is an isolated proposal; canonical authority, RULE_HASH, and selected production generate() remain the original left-expansion task.",
            "Evidence covers two deterministic four-pair episodes and the opposite-side rival, not every seed or every conceivable alternative rule.",
            "The side is intentionally visible in every demonstration; this validates coherent episode-level parameterization rather than difficult latent-rule inference.",
        ],
    }
    _write_json(output / "report.json", report)

    files = {
        path.relative_to(output).as_posix(): {
            "sha256": _sha256_bytes(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "schema": "ad5a6c1521b3-parametric-manifest-v1",
        "scope": "prototype",
        "files": files,
    }
    _write_json(output / "manifest.json", manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=907)
    args = parser.parse_args()
    report = materialize(args.out, seed_start=args.seed_start)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
