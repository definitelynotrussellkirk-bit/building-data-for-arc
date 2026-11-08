#!/usr/bin/env python3
"""Isolated shift-distance prototype for ``db95939a5dd0``.

The canonical task moves each two-colour compound's upper colour left by one
and lower colour right by one.  This prototype keeps every object role,
component relation, colour rule, and fresh-background composition unchanged;
it varies only the horizontal shift distance once per episode:

* ``1`` (default/original): byte-derived from selected canonical authority.
* ``2`` (proposed): the same program with the two displacement literals set to 2.

Production generator authority is not changed by this prototype.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import random
from pathlib import Path
from typing import Any


TASK_ID = "db95939a5dd0"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "shift_distance"
DEFAULT_SHIFT_DISTANCE = 1
ALLOWED_SHIFT_DISTANCES = (DEFAULT_SHIFT_DISTANCE, 2)
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "integer",
        "allowed": list(ALLOWED_SHIFT_DISTANCES),
        "default": DEFAULT_SHIFT_DISTANCE,
        "chosen": "once per episode from the deterministic episode seed",
        "invariants": (
            "mode-colour background; 1-2 disconnected two-colour compounds; "
            "upper class shifts left and lower class shifts right; output is a "
            "fresh background canvas"
        ),
        "input_constraints": (
            "every foreground cell has at least shift_distance horizontal "
            "clearance and shifted destinations are collision-free"
        ),
    }
}

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_AUTHORITY_REL = Path(
    "shared/data/base/solutions/training/4364c1c4__db95939a5dd0.json"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _validate_distance(value: Any) -> int:
    if type(value) is not int:
        raise TypeError(
            f"{PARAMETER_NAME} must be an integer (not {type(value).__name__})"
        )
    if value not in ALLOWED_SHIFT_DISTANCES:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SHIFT_DISTANCES}, got {value}"
        )
    return value


def canonical_program() -> str:
    """Read the selected canonical target text used for the default setting."""
    payload = json.loads((_repo_root() / _AUTHORITY_REL).read_text())
    source = payload["racket_target"]["target_code"]
    if not isinstance(source, str) or not source.startswith("(rule!"):
        raise ValueError("selected canonical target_code is missing or malformed")
    if source.count("(- (second p) 1)") != 1:
        raise ValueError("canonical left-shift literal is not unique")
    if source.count("(+ (second p) 1)") != 1:
        raise ValueError("canonical right-shift literal is not unique")
    return source


def program_for(distance: Any) -> str:
    """Materialize exact Racket text for one bounded setting."""
    distance = _validate_distance(distance)
    source = canonical_program()
    if distance == DEFAULT_SHIFT_DISTANCE:
        return source
    return source.replace(
        "(- (second p) 1)", f"(- (second p) {distance})"
    ).replace(
        "(+ (second p) 1)", f"(+ (second p) {distance})"
    )


def racket_callable(distance: Any) -> str:
    """Return the selected rule's lambda without importing parser tooling."""
    source = program_for(distance).strip()
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("materialized program is not a single (rule! ...) form")
    callable_text = source[len(prefix) : -1].strip()
    if not callable_text.startswith("(lambda ") or not callable_text.endswith(")"):
        raise ValueError("materialized rule body is not a lambda")
    return callable_text


class RacketRuleExecutor:
    """Execute one materialized setting through one persistent Racket bridge."""

    def __init__(self, distance: Any):
        from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule

        self.distance = _validate_distance(distance)
        self._apply_rule = _apply_rule
        self._bridge, self._fn_name = _open_bridge_with_rule(
            racket_callable(self.distance)
        )
        proc = getattr(self._bridge, "_proc", None)
        if proc is None or proc.pid is None:
            self._bridge.shutdown()
            raise RuntimeError("Racket bridge did not expose a live process")
        self._bridge_pid = int(proc.pid)
        self.call_count = 0
        self._closed = False

    @property
    def bridge_pid(self) -> int:
        return self._bridge_pid

    @property
    def closed(self) -> bool:
        return self._closed

    def apply(self, grid: list[list[int]]) -> list[list[int]]:
        if self._closed:
            raise RuntimeError("RacketRuleExecutor is closed")
        output = self._apply_rule(self._bridge, self._fn_name, grid)
        proc = getattr(self._bridge, "_proc", None)
        if proc is None or proc.pid != self._bridge_pid:
            raise RuntimeError("Racket bridge restarted during retained evidence")
        expected = apply_python(grid, self.distance)
        if output != expected:
            raise AssertionError(
                f"Racket/Python mismatch for shift distance {self.distance}"
            )
        self.call_count += 1
        return output

    def close(self) -> None:
        if self._closed:
            return
        self._bridge.shutdown()
        self._closed = True

    def __enter__(self) -> "RacketRuleExecutor":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()


def choose_shift_distance(seed: Any) -> int:
    """Choose the hidden setting exactly once from an episode seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    payload = f"{TASK_ID}|shift-distance|{PROTOTYPE_VERSION}|{seed}".encode()
    index = hashlib.sha256(payload).digest()[0] % len(ALLOWED_SHIFT_DISTANCES)
    return ALLOWED_SHIFT_DISTANCES[index]


def _mode_nonzero(grid: list[list[int]]) -> int:
    values = [value for row in grid for value in row if value != 0]
    if not values:
        return 0
    counts = {value: values.count(value) for value in set(values)}
    return max(counts, key=counts.get)


def _components(grid: list[list[int]]) -> tuple[int, list[list[tuple[int, int]]]]:
    bg = _mode_nonzero(grid)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == bg or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != bg
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return bg, components


def _classes(
    grid: list[list[int]], cells: list[tuple[int, int]]
) -> tuple[int, list[tuple[int, int]], int, list[tuple[int, int]]] | None:
    by_colour: dict[int, list[tuple[int, int]]] = {}
    for r, c in cells:
        by_colour.setdefault(grid[r][c], []).append((r, c))
    if len(by_colour) != 2:
        return None
    ordered = sorted(by_colour.items(), key=lambda item: min(r for r, _ in item[1]))
    (top, top_cells), (bottom, bottom_cells) = ordered
    return top, top_cells, bottom, bottom_cells


def _connected(cells: list[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    seen = set(stack)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARD:
            point = (r + dr, c + dc)
            if point in remaining and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == remaining


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be integer colour 0..9"]
    return []


def domain_errors(grid: Any, *, distance: Any) -> list[str]:
    """Validate the bounded prototype domain for one distance setting."""
    distance = _validate_distance(distance)
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    bg, components = _components(grid)
    flat = [value for row in grid for value in row]
    if flat.count(bg) <= max((flat.count(value) for value in set(flat) if value != bg), default=0):
        errors.append("background must be the strict mode")
    if not 1 <= len(components) <= 2:
        errors.append("expected one or two compounds")
    destinations: set[tuple[int, int]] = set()
    for index, cells in enumerate(components):
        split = _classes(grid, cells)
        if split is None:
            errors.append(f"compound {index} must have exactly two colours")
            continue
        top, top_cells, bottom, bottom_cells = split
        if not _connected(top_cells) or not _connected(bottom_cells):
            errors.append(f"compound {index} colour classes must be connected")
        if max(r for r, _ in top_cells) >= min(r for r, _ in bottom_cells):
            errors.append(f"compound {index} colours must be vertically stacked")
        for colour, class_cells, dc in (
            (top, top_cells, -distance),
            (bottom, bottom_cells, distance),
        ):
            for r, c in class_cells:
                nc = c + dc
                if not 0 <= nc < w:
                    errors.append(
                        f"compound {index} colour {colour} clips at distance {distance}"
                    )
                    continue
                point = (r, nc)
                if point in destinations:
                    errors.append(f"shift collision at {point}")
                destinations.add(point)
    return errors


def apply_python(grid: list[list[int]], distance: Any) -> list[list[int]]:
    """Independent debug mirror; retained labels are produced by Racket."""
    distance = _validate_distance(distance)
    errors = domain_errors(grid, distance=distance)
    if errors:
        raise ValueError(errors[0])
    bg, components = _components(grid)
    out = [[bg for _ in row] for row in grid]
    for cells in components:
        split = _classes(grid, cells)
        assert split is not None
        top, top_cells, bottom, bottom_cells = split
        for r, c in top_cells:
            out[r][c - distance] = top
        for r, c in bottom_cells:
            out[r][c + distance] = bottom
    return out


def _paint(
    grid: list[list[int]],
    origin: tuple[int, int],
    cells: tuple[tuple[int, int], ...],
    colour: int,
) -> None:
    r0, c0 = origin
    for dr, dc in cells:
        grid[r0 + dr][c0 + dc] = colour


_RECT_2X3 = tuple((r, c) for r in range(2) for c in range(3))
_NOTCH_RIGHT = tuple(cell for cell in _RECT_2X3 if cell != (1, 2))
_NOTCH_LEFT = tuple(cell for cell in _RECT_2X3 if cell != (0, 0))


def make_input(seed: Any, pair_index: Any) -> list[list[int]]:
    """Construct one canonical-lawful input with two-cell shift clearance."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(pair_index) is not int:
        raise TypeError("pair_index must be an integer (not bool)")
    if pair_index < 0:
        raise ValueError("pair_index must be nonnegative")
    material = hashlib.sha256(
        f"{TASK_ID}|prototype-input|{PROTOTYPE_VERSION}|{seed}|{pair_index}".encode()
    ).digest()
    rng = random.Random(int.from_bytes(material[:8], "big"))
    colours = rng.sample(range(1, 10), 5)
    bg, a_top, a_bottom, b_top, b_bottom = colours
    grid = [[bg] * 14 for _ in range(14)]

    shapes = (_RECT_2X3, _NOTCH_RIGHT, _NOTCH_LEFT)
    top_a = shapes[pair_index % len(shapes)]
    bottom_a = shapes[(pair_index + 1) % len(shapes)]
    top_b = shapes[(pair_index + 2) % len(shapes)]
    bottom_b = shapes[(pair_index + 3) % len(shapes)]
    col_a = 3 + pair_index % 2
    col_b = 8 + (pair_index // 2) % 2
    _paint(grid, (1, col_a), top_a, a_top)
    _paint(grid, (3, col_a), bottom_a, a_bottom)
    _paint(grid, (7, col_b), top_b, b_top)
    _paint(grid, (9, col_b), bottom_b, b_bottom)

    for distance in ALLOWED_SHIFT_DISTANCES:
        errors = domain_errors(grid, distance=distance)
        if errors:
            raise AssertionError(f"constructed invalid distance-{distance} input: {errors}")
    if apply_python(grid, 1) == apply_python(grid, 2):
        raise AssertionError("constructed input does not distinguish distances")
    return grid


def build_episode(seed: Any, distance: Any = None) -> dict[str, Any]:
    """Build a complete private episode using the Python debug mirror."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    selected = choose_shift_distance(seed) if distance is None else _validate_distance(distance)
    pairs = []
    for pair_index in range(4):
        grid = make_input(seed, pair_index)
        pairs.append({"input": grid, "output": apply_python(grid, selected)})
    return {
        "schema": "arc-parametric-shift-distance-private-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {PARAMETER_NAME: selected},
        "racket_program": program_for(selected),
        "demos": pairs[:3],
        "query": pairs[3],
    }


def parameter_rival_findings(episode: dict[str, Any]) -> dict[str, dict[str, Any]]:
    selected = _validate_distance(episode["parameters"][PARAMETER_NAME])
    findings: dict[str, dict[str, Any]] = {}
    for rival in ALLOWED_SHIFT_DISTANCES:
        if rival == selected:
            continue
        refuted = [
            index
            for index, pair in enumerate(episode["demos"])
            if apply_python(pair["input"], rival) != pair["output"]
        ]
        findings[str(rival)] = {
            "fits_all_demos": not refuted,
            "refuted_demo_indices": refuted,
            "changes_query": (
                apply_python(episode["query"]["input"], rival)
                != episode["query"]["output"]
            ),
        }
    return findings


def public_filename(challenge):
    """Name only visible examples, never settings, seeds or query answers."""
    demos = challenge.get("train", challenge.get("demos"))
    queries = challenge.get("test", challenge.get("query"))
    if isinstance(queries, dict): queries = [queries]
    visible = {"train": [{"input": p["input"], "output": p["output"]} for p in demos],
               "test": [{"input": p["input"]} for p in queries]}
    digest = hashlib.sha256(json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return "challenge-" + digest + ".json"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove seed, hidden parameter, program text, and query answer."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "demos": deepcopy(episode["demos"]),
        "query": {"input": deepcopy(episode["query"]["input"])},
    }


def materialize_rules(out_dir: Path) -> dict[int, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for distance in ALLOWED_SHIFT_DISTANCES:
        path = out_dir / f"shift_distance_{distance}.rkt"
        path.write_text(program_for(distance) + "\n")
        result[distance] = path
    return result


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _grid_sha256(grid: list[list[int]]) -> str:
    return _sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _first_seed_for(distance: int) -> int:
    for seed in range(10_000):
        if choose_shift_distance(seed) == distance:
            return seed
    raise AssertionError(f"no seed selects distance {distance}")


def build_racket_evidence(out_dir: Path) -> dict[str, Any]:
    """Execute canonical checks and one complete episode per setting in Racket."""
    import os
    import sys
    from contextlib import ExitStack

    from reviewer_support import canonical_pairs, load_selected_generator

    out_dir = Path(out_dir).resolve()
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {out_dir}")
    (out_dir / "private" / "episodes").mkdir(parents=True)
    (out_dir / "private" / "programs").mkdir(parents=True)
    (out_dir / "public").mkdir(parents=True)

    root = _repo_root()
    _gen, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    programs = materialize_rules(out_dir / "private" / "programs")
    program_rows = {
        str(distance): {
            "path": str(path.relative_to(out_dir)),
            "sha256": _sha256_bytes(program_for(distance).encode()),
            "text": program_for(distance),
        }
        for distance, path in programs.items()
    }
    receipts: list[dict[str, Any]] = []

    with ExitStack() as stack:
        executors = {
            distance: stack.enter_context(RacketRuleExecutor(distance))
            for distance in ALLOWED_SHIFT_DISTANCES
        }

        def execute(
            distance: int, grid: list[list[int]], label: str
        ) -> list[list[int]]:
            output = executors[distance].apply(grid)
            receipts.append(
                {
                    "label": label,
                    "distance": distance,
                    "bridge_pid": executors[distance].bridge_pid,
                    "program_sha256": _sha256_bytes(
                        program_for(distance).encode()
                    ),
                    "input_sha256": _grid_sha256(grid),
                    "output_sha256": _grid_sha256(output),
                    "input": grid,
                    "output": output,
                }
            )
            return output

        canonical_checks = []
        for index, pair in enumerate(
            canonical_pairs(TASK_ID, root=root, labeled_only=True)
        ):
            actual = execute(1, pair["input"], f"canonical-{index}-distance-1")
            canonical_checks.append(
                {
                    "index": index,
                    "passed": actual == pair["output"],
                    "expected_sha256": _grid_sha256(pair["output"]),
                    "actual_sha256": _grid_sha256(actual),
                }
            )
        if not all(row["passed"] for row in canonical_checks):
            raise AssertionError("default shift distance failed canonical parity")

        episode_rows = []
        for distance in ALLOWED_SHIFT_DISTANCES:
            seed = _first_seed_for(distance)
            episode = build_episode(seed, distance=distance)
            for index, pair in enumerate([*episode["demos"], episode["query"]]):
                pair["output"] = execute(
                    distance,
                    pair["input"],
                    f"episode-{distance}-pair-{index}",
                )
            findings = parameter_rival_findings(episode)
            if any(row["fits_all_demos"] for row in findings.values()):
                raise AssertionError(
                    "episode demonstrations do not identify distance"
                )
            public = public_challenge(episode)
            private_path = (
                out_dir / "private" / "episodes" / f"distance-{distance}.json"
            )
            public_path = out_dir / "public" / public_filename(public)
            private_payload = {
                "episode": episode,
                "parameter_spec": PARAMETER_SPEC,
                "parameter_rival_findings": findings,
                "checks": {
                    "parameter_chosen_once_per_episode": True,
                    "all_labels_from_executed_racket": True,
                    "python_mirror_parity": True,
                    "demos_refute_every_alternative": True,
                    "query_answer_private": True,
                },
            }
            _write_json(private_path, private_payload)
            _write_json(public_path, public)
            episode_rows.append(
                {
                    "distance": distance,
                    "seed": seed,
                    "private": str(private_path.relative_to(out_dir)),
                    "private_sha256": _sha256_file(private_path),
                    "public": str(public_path.relative_to(out_dir)),
                    "public_sha256": _sha256_file(public_path),
                    "rival_findings": findings,
                }
            )

        witness = make_input(271828, 0)
        witness_outputs = {
            str(distance): execute(
                distance, witness, f"witness-distance-{distance}"
            )
            for distance in ALLOWED_SHIFT_DISTANCES
        }
        if len({_grid_sha256(value) for value in witness_outputs.values()}) != 2:
            raise AssertionError(
                "counterfactual witness does not distinguish settings"
            )

        executor_rows = {
            str(distance): {
                "bridge_pid": executor.bridge_pid,
                "call_count": executor.call_count,
            }
            for distance, executor in executors.items()
        }

        manifest = {
            "schema": "arc-parametric-shift-distance-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "status": "proposed",
            "parameter_spec": PARAMETER_SPEC,
            "programs": program_rows,
            "canonical_checks": canonical_checks,
            "episodes": episode_rows,
            "counterfactual": {
                "input": witness,
                "outputs": witness_outputs,
                "outputs_differ": True,
            },
            "racket_executors": executor_rows,
            "execution_receipts": receipts,
            "source_hashes": {
                "prototype.py": _sha256_file(Path(__file__)),
                "selected_generator.py": generator_sha256,
                str(_AUTHORITY_REL): _sha256_file(root / _AUTHORITY_REL),
            },
            "command": {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]},
            "limitations": [
                "Prototype only; production generator and RULE_HASH remain canonical.",
                "Evidence covers two bounded distances and retained seeds, not all inputs.",
                "Public challenges hide the rule setting and query output by construction.",
            ],
        }
        _write_json(out_dir / "manifest.json", manifest)
        return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_racket_evidence(args.out_dir)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "canonical_checks": len(manifest["canonical_checks"]),
                "episodes": len(manifest["episodes"]),
                "racket_calls": len(manifest["execution_receipts"]),
                "out": str(args.out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
