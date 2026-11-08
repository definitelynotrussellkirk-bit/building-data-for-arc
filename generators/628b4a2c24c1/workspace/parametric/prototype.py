"""Native parametric family for row seeds and color-8 corridor walls.

The canonical setting is byte-identical to the selected ARC authority.  The
alternate first measures the nearest open corridor on both sides of each seed,
then chooses the wider corridor (right on ties) before painting.  Python labels
are authoring claims; native qualification replays them through protected Racket.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
TASK_ID = "628b4a2c24c1"
POLICIES = ("rightward", "widest_corridor")
SETTINGS = tuple({"sweep_policy": value} for value in POLICIES)
DEFAULT = {"sweep_policy": "rightward"}
CANONICAL_PROGRAM = (HERE / "canonical.rkt").read_text(encoding="utf-8")
CANONICAL_SHA256 = hashlib.sha256(CANONICAL_PROGRAM.encode()).hexdigest()
_LIMIT = 2**63 - 1
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _integer(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _settings(settings: object) -> str:
    if (type(settings) is not dict or set(settings) != {"sweep_policy"}
            or type(settings["sweep_policy"]) is not str
            or settings["sweep_policy"] not in POLICIES):
        raise ValueError(
            "settings must be exactly {'sweep_policy': "
            "'rightward'|'widest_corridor'}"
        )
    return settings["sweep_policy"]


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangular integer array")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact ARC colors 0..9")
    return deepcopy(grid)


def _program_template(*, direction: str, right_stop: str = "nearest") -> str:
    if right_stop == "nearest":
        right_expr = "(if (empty? right-walls) (cols g) (first right-walls))"
    elif right_stop == "edge":
        right_expr = "(cols g)"
    elif right_stop == "required":
        right_expr = "(if (empty? right-walls) (+ c 1) (first right-walls))"
    elif right_stop == "farthest":
        right_expr = "(if (empty? right-walls) (cols g) (last right-walls))"
    else:  # pragma: no cover - internal construction guard
        raise ValueError(right_stop)

    direction_expr = {
        "widest": "(>= right-gap left-gap)",
        "nearest": "(<= right-gap left-gap)",
        "widest_tie_left": "(> right-gap left-gap)",
        "edge_distance": "(>= (- (cols g) c 1) c)",
        "right": "(= 1 1)",
        "left": "(= 1 0)",
    }[direction]
    return f"""(rule!
  (for*/fold ((out g))
    ((r (in-range (rows g)))
     (c (in-range (cols g))))
    (let ((v (at g r c)))
      (if (member? v (list 0 8))
          out
          (let* ((left-walls
                  (filter (lambda (wc) (and (< wc c) (= (at g r wc) 8)))
                          (range (cols g))))
                 (right-walls
                  (filter (lambda (wc) (and (> wc c) (= (at g r wc) 8)))
                          (range (cols g))))
                 (left-stop (if (empty? left-walls) -1 (last left-walls)))
                 (right-stop {right_expr})
                 (left-gap (- c left-stop 1))
                 (right-gap (- right-stop c 1))
                 (go-right {direction_expr})
                 (start (if go-right c (+ left-stop 1)))
                 (stop (if go-right right-stop (+ c 1))))
            (for/fold ((acc out)) ((x (in-range start stop)))
              (if (= (at acc r x) 0)
                  (set-cell acc r x v)
                  acc)))))))"""


WIDEST_PROGRAM = _program_template(direction="widest")


def program(settings: object) -> str:
    policy = _settings(settings)
    return CANONICAL_PROGRAM if policy == "rightward" else WIDEST_PROGRAM


def _row_geometry(grid: list[list[int]], row: int, col: int) -> dict:
    width = len(grid[0])
    walls = [index for index, value in enumerate(grid[row]) if value == 8]
    left = [index for index in walls if index < col]
    right = [index for index in walls if index > col]
    left_stop = left[-1] if left else -1
    right_stop = right[0] if right else width
    left_gap = col - left_stop - 1
    right_gap = right_stop - col - 1
    return {
        "left_stop": left_stop,
        "right_stop": right_stop,
        "left_gap": left_gap,
        "right_gap": right_gap,
        "direction": "right" if right_gap >= left_gap else "left",
        "right_walls": right,
    }


def dependency_intermediate(grid: object) -> dict:
    source = _grid(grid)
    rows = []
    for r, row in enumerate(source):
        for c, color in enumerate(row):
            if color in (0, 8):
                continue
            geometry = _row_geometry(source, r, c)
            rows.append({"row": r, "seed_col": c, "seed_color": color, **geometry})
    return {"height": len(source), "width": len(source[0]), "seed_rows": rows}


def _solve_mode(grid: object, mode: str) -> list[list[int]]:
    source = _grid(grid)
    output = deepcopy(source)
    width = len(source[0])
    for r, row in enumerate(source):
        for c, color in enumerate(row):
            if color in (0, 8):
                continue
            geometry = _row_geometry(source, r, c)
            left_stop = geometry["left_stop"]
            right_stop = geometry["right_stop"]
            left_gap = geometry["left_gap"]
            right_gap = geometry["right_gap"]

            if mode == "rightward":
                go_right = True
            elif mode == "widest_corridor":
                go_right = right_gap >= left_gap
            elif mode == "wall_required_right":
                go_right = True
                if not geometry["right_walls"]:
                    right_stop = c + 1
            elif mode == "right_to_edge":
                go_right = True
                right_stop = width
            elif mode == "always_left":
                go_right = False
            elif mode == "nearest_corridor":
                go_right = right_gap <= left_gap
            elif mode == "widest_tie_left":
                go_right = right_gap > left_gap
            elif mode == "edge_distance_only":
                go_right = (width - c - 1) >= c
            elif mode == "farthest_right_wall":
                go_right = True
                right_stop = geometry["right_walls"][-1] if geometry["right_walls"] else width
            else:  # pragma: no cover - internal construction guard
                raise ValueError(f"unknown solve mode {mode!r}")

            start, stop = (c, right_stop) if go_right else (left_stop + 1, c + 1)
            for x in range(start, stop):
                if output[r][x] == 0:
                    output[r][x] = color
    return output


def solve(grid: object, settings: object) -> list[list[int]]:
    return _solve_mode(grid, _settings(settings))


def rival_programs(settings: object) -> dict[str, str]:
    policy = _settings(settings)
    other = "widest_corridor" if policy == "rightward" else "rightward"
    return {
        "other_setting": program({"sweep_policy": other}),
        "wall_required_right": _program_template(direction="right", right_stop="required"),
        "right_to_edge": _program_template(direction="right", right_stop="edge"),
        "always_left": _program_template(direction="left"),
        "nearest_corridor": _program_template(direction="nearest"),
        "widest_tie_left": _program_template(direction="widest_tie_left"),
        "edge_distance_only": _program_template(direction="edge_distance"),
        "farthest_right_wall": _program_template(direction="right", right_stop="farthest"),
    }


def rival_outputs(grid: object, settings: object) -> dict[str, list[list[int]]]:
    policy = _settings(settings)
    other = "widest_corridor" if policy == "rightward" else "rightward"
    return {
        "other_setting": _solve_mode(grid, other),
        "wall_required_right": _solve_mode(grid, "wall_required_right"),
        "right_to_edge": _solve_mode(grid, "right_to_edge"),
        "always_left": _solve_mode(grid, "always_left"),
        "nearest_corridor": _solve_mode(grid, "nearest_corridor"),
        "widest_tie_left": _solve_mode(grid, "widest_tie_left"),
        "edge_distance_only": _solve_mode(grid, "edge_distance_only"),
        "farthest_right_wall": _solve_mode(grid, "farthest_right_wall"),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:row-corridor-input-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _teaching_grid(seed: int, index: int) -> list[list[int]]:
    height, width = ((9, 16), (10, 18))[index]
    rng = _rng(seed, "demo", index)
    color = _COLORS[(seed + index * 3) % len(_COLORS)]
    grid = [[0] * width for _ in range(height)]
    rows = list(range(1, 7))
    if index == 1:
        rows = [0, 2, 3, 5, 7, 9]
    # A: no right wall; both intended rules must sweep to the edge.
    specs = [
        (None, 3, ()),
        (1, width - 4, (width - 2,)),
        (1, 3, (width - 4,)),
        (1, width // 2, (width - 1,)),
        (None, 4, (6, width - 3)),
        (0, width // 3, (width // 3 + 4, width - 1)),
    ]
    if index == 1:
        specs = [
            (None, 2, ()),
            (2, width - 5, (width - 2,)),
            (1, 4, (width - 3,)),
            (2, width // 2, (width - 3,)),
            (None, 5, (7, width - 2)),
            (0, 6, (11, width - 1)),
        ]
    # Keep branch types fixed while varying row order and a few harmless walls.
    if seed % 2:
        rows[1:5] = reversed(rows[1:5])
    for row, (left, seed_col, right_walls) in zip(rows, specs):
        grid[row][seed_col] = color
        if left is not None:
            grid[row][left] = 8
        for wall in right_walls:
            grid[row][wall] = 8
    # Inactive wall-only rows add visual content and edge contacts.
    inactive = [r for r in range(height) if r not in rows]
    for offset, row in enumerate(inactive):
        grid[row][(offset * 5 + rng.randrange(width)) % width] = 8
    return grid


def _scheduled_shape(split: str, index: int) -> tuple[int, int]:
    if split == "demo":
        schedule = ((9, 16), (10, 18), (12, 20), (15, 24), (18, 26), (20, 28))
    elif split == "query":
        schedule = ((9, 14), (16, 22), (24, 30), (30, 30))
    else:  # pragma: no cover
        raise ValueError(split)
    return schedule[index]


def _spread_rows(height: int, count: int) -> list[int]:
    if count == 1:
        return [height // 2]
    rows = [round(i * (height - 1) / (count - 1)) for i in range(count)]
    if len(set(rows)) != len(rows):  # defensive for very small grids
        rows = list(range(count))
    return rows


def _general_grid(seed: int, split: str, index: int) -> list[list[int]]:
    height, width = _scheduled_shape(split, index)
    rng = _rng(seed, split, index)
    color = _COLORS[rng.randrange(len(_COLORS))]
    active_count = min(10, max(4, height // 3))
    rows = _spread_rows(height, active_count)
    grid = [[0] * width for _ in range(height)]

    for ordinal, row in enumerate(rows):
        kind = ordinal % 6
        if kind == 0:  # no right wall and a long right corridor
            seed_col = max(1, width // 5)
            left = None
            rights: tuple[int, ...] = ()
        elif kind == 1:  # much wider left corridor
            left = 1
            seed_col = width - 4
            rights = (width - 2,)
        elif kind == 2:  # much wider right corridor; nearest-rival trap
            left = 1
            seed_col = 3
            rights = (width - 2,)
        elif kind == 3:  # exact tie, right is the specified tie-break
            left = 1
            seed_col = width // 2
            right = min(width - 1, seed_col + (seed_col - left))
            rights = (right,)
        elif kind == 4:  # nearby and far right walls; actual widest is left
            left = None
            seed_col = max(3, width // 4)
            near = min(width - 3, seed_col + 2)
            far = width - 1
            rights = (near, far) if near < far else (far,)
        else:  # wall-aware direction differs from edge-only direction
            left = 0
            seed_col = min(width - 4, max(4, width // 3))
            near = min(width - 2, seed_col + 3)
            rights = (near, width - 1) if near < width - 1 else (near,)

        grid[row][seed_col] = color
        if left is not None and left != seed_col:
            grid[row][left] = 8
        for wall in rights:
            if wall != seed_col:
                grid[row][wall] = 8

    inactive = [row for row in range(height) if row not in set(rows)]
    for ordinal, row in enumerate(inactive):
        if ordinal % 2 == 0 or split == "query":
            col = (ordinal * 7 + rng.randrange(width)) % width
            grid[row][col] = 8
    return grid


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, _LIMIT)
    if split == "demo":
        _integer("demo index", index, 0, 5)
        return _teaching_grid(seed, index) if index < 2 else _general_grid(seed, split, index)
    if split == "query":
        _integer("query index", index, 0, 3)
        return _general_grid(seed, split, index)
    raise ValueError("split must be 'demo' or 'query'")


def teaching_check(episode: object) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _settings(settings)
    train = episode.get("train")
    if type(train) is not list or not train:
        raise ValueError("episode needs at least one demonstration")
    rivals = {name: None for name in rival_programs(settings)}
    for index, pair in enumerate(train):
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations need input/output grids")
        expected = solve(pair["input"], settings)
        if _grid(pair["output"]) != expected:
            raise ValueError("demonstration label differs from selected rule")
        outputs = rival_outputs(pair["input"], settings)
        for name, value in outputs.items():
            if rivals[name] is None and value != expected:
                rivals[name] = index
    surviving = sorted(name for name, index in rivals.items() if index is None)
    return {
        "status": "identified" if not surviving else "ambiguous",
        "surviving_rivals": surviving,
        "refuted_by": {name: index for name, index in rivals.items() if index is not None},
        "demonstrations": len(train),
        "limits": "Finite named rivals fitted to demonstrations only; not universal uniqueness.",
    }


def generate(seed: int, settings: object, demos: int, queries: int) -> dict:
    _integer("seed", seed, 0, _LIMIT)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _settings(settings)
    train = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": solve(grid, settings)})
    test = []
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": solve(grid, settings)})
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "train": train,
        "test": test,
        "program_solution": program(settings),
    }
    fingerprints = [json.dumps(pair["input"], separators=(",", ":"))
                    for pair in train + test]
    if len(fingerprints) != len(set(fingerprints)):
        raise RuntimeError("constructed episode contains duplicate inputs")
    certificate = teaching_check(episode)
    if certificate["surviving_rivals"]:
        raise RuntimeError("constructed demonstrations leave declared rivals alive")
    return episode


def analyze(grid: object) -> dict:
    source = _grid(grid)
    intermediate = dependency_intermediate(source)
    rows = intermediate["seed_rows"]
    return {
        "height": len(source),
        "width": len(source[0]),
        "active_rows": len({row["row"] for row in rows}),
        "seed_cells": len(rows),
        "wall_cells": sum(value == 8 for row in source for value in row),
        "widest_directions": [row["direction"] for row in rows],
        "wall_free_right_rows": sum(row["right_stop"] == len(source[0]) for row in rows),
        "foreground_cells": sum(value != 0 for row in source for value in row),
    }


def public_challenge(episode: object, query_index: int = 0) -> dict:
    if type(episode) is not dict or type(episode.get("train")) is not list \
            or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    selected = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(selected))


def export_batch(output_dir: Path | str, *, count: int, seed: int, settings: object,
                 demos: int = 3, queries: int = 4, seed_step: int = 1) -> dict:
    _integer("count", count, 1, 1000)
    _integer("seed", seed, 0, _LIMIT)
    _integer("seed_step", seed_step, 0, _LIMIT)
    if seed + (count - 1) * seed_step > _LIMIT:
        raise ValueError("last seed exceeds 2**63-1")
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _settings(settings)
    output = Path(output_dir)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)

    pending = []
    identities = set()
    for index in range(count):
        episode = generate(seed + index * seed_step, settings, demos, queries)
        visible = public_challenge(episode, 0)
        identity = public_challenge_id(visible)
        if identity in identities:
            raise ValueError("duplicate visible public challenge")
        identities.add(identity)
        visible_bytes = public_challenge_bytes(visible)
        private = {"public_id": identity, "episode": episode,
                   "training_admitted": False}
        private_bytes = (json.dumps(private, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False) + "\n").encode()
        pending.append((identity, visible_bytes, private_bytes))

    output.mkdir(parents=True, exist_ok=False)
    public_dir = output / "public"
    private_dir = output / "private"
    public_dir.mkdir()
    private_dir.mkdir()
    for identity, visible_bytes, private_bytes in sorted(pending):
        (public_dir / f"{identity}.json").write_bytes(visible_bytes)
        (private_dir / f"{identity}.json").write_bytes(private_bytes)
    return {"count": count, "public_dir": str(public_dir), "private_dir": str(private_dir),
            "queries_stored_privately": queries, "public_queries": 1,
            "training_admitted": False}
