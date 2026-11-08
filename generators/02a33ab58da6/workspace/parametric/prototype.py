"""Proposed episode-fixed turn-policy family for ``02a33ab58da6``.

The source ray and old red tail are unchanged.  The hidden rule selects whether
the tail rotates perpendicular toward or away from the canvas center.  The
sampler reserves both perpendicular arms, so every generated input is total for
both settings and input bytes never depend on the private setting.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import public_challenge_bytes

TASK_ID = "02a33ab58da6"
HERE = Path(__file__).resolve().parent
PARAMETER_NAME = "turn_policy"
POLICIES = ("toward_center", "away_from_center")
DEFAULT_SETTING = "toward_center"
SHORTCUTS = ("clockwise", "counterclockwise", "no_move")
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
FIELD, RED, GRAY, PIVOT = 7, 2, 5, 0

# Height, width, motif count.  The first N entries are count-prefix stable.
DEMO_PROFILES = ((12, 13, 2), (15, 16, 3), (18, 20, 4),
                 (22, 21, 5), (26, 27, 6), (30, 28, 7))
QUERY_PROFILES = ((14, 16, 3), (20, 22, 5), (27, 26, 7), (30, 30, 8))


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _settings(settings: object) -> str:
    if (type(settings) is not dict or set(settings) != {PARAMETER_NAME}
            or type(settings[PARAMETER_NAME]) is not str
            or settings[PARAMETER_NAME] not in POLICIES):
        raise ValueError("settings must contain only turn_policy=toward_center|away_from_center")
    return settings[PARAMETER_NAME]


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _toward(direction: tuple[int, int], pivot: tuple[int, int], height: int, width: int):
    dr, dc = direction
    row, col = pivot
    if dc != 0:
        return (1, 0) if row < height // 2 else (-1, 0)
    return (0, 1) if col < width // 2 else (0, -1)


def _clockwise(direction: tuple[int, int]):
    dr, dc = direction
    return dc, -dr


def _counterclockwise(direction: tuple[int, int]):
    dr, dc = direction
    return -dc, dr


def _sense(direction, turn):
    if turn == _clockwise(direction):
        return "clockwise"
    if turn == _counterclockwise(direction):
        return "counterclockwise"
    raise ValueError("turn must be perpendicular")


def _scan(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    moves = []
    for gr in range(height):
        for gc in range(width):
            if grid[gr][gc] != GRAY:
                continue
            candidates = []
            for dr, dc in DIRECTIONS:
                step = 1
                while 0 <= gr + dr * step < height and 0 <= gc + dc * step < width:
                    value = grid[gr + dr * step][gc + dc * step]
                    if value == RED:
                        step += 1
                        continue
                    if value != PIVOT:
                        break
                    pivot = gr + dr * step, gc + dc * step
                    tail_len = 0
                    while (0 <= pivot[0] + dr * (tail_len + 1) < height
                           and 0 <= pivot[1] + dc * (tail_len + 1) < width
                           and grid[pivot[0] + dr * (tail_len + 1)][pivot[1] + dc * (tail_len + 1)] == RED):
                        tail_len += 1
                    if tail_len:
                        turn = _toward((dr, dc), pivot, height, width)
                        candidates.append({
                            "gray": (gr, gc), "pivot": pivot, "direction": (dr, dc),
                            "bar_len": step - 1, "tail_len": tail_len,
                            "toward_turn": turn, "toward_sense": _sense((dr, dc), turn),
                        })
                    break
            if len(candidates) != 1:
                raise ValueError("each gray endpoint must define exactly one ray motif")
            moves.append(candidates[0])
    return moves


def features(grid: list[list[int]]) -> dict[str, Any]:
    data = _grid(grid)
    height, width = len(data), len(data[0])
    palette = {value for row in data for value in row}
    if palette != {FIELD, RED, GRAY, PIVOT}:
        raise ValueError("palette must be exactly {0,2,5,7}")
    moves = _scan(data)
    if not moves:
        raise ValueError("at least one motif is required")
    grays = {(r, c) for r, row in enumerate(data) for c, value in enumerate(row) if value == GRAY}
    pivots = {(r, c) for r, row in enumerate(data) for c, value in enumerate(row) if value == PIVOT}
    reds = {(r, c) for r, row in enumerate(data) for c, value in enumerate(row) if value == RED}
    if {move["gray"] for move in moves} != grays or {move["pivot"] for move in moves} != pivots:
        raise ValueError("every gray endpoint and black pivot must belong to exactly one motif")
    expected_red = set()
    for move in moves:
        gr, gc = move["gray"]
        pr, pc = move["pivot"]
        dr, dc = move["direction"]
        for step in range(1, move["bar_len"] + 1):
            expected_red.add((gr + dr * step, gc + dc * step))
        for step in range(1, move["tail_len"] + 1):
            expected_red.add((pr + dr * step, pc + dc * step))
    if reds != expected_red:
        raise ValueError("red cells must belong exactly to motif bars and old tails")
    return {"height": height, "width": width, "moves": moves}


def _turn(move: dict[str, Any], policy: str):
    if policy == "toward_center":
        return move["toward_turn"]
    if policy == "away_from_center":
        tr, tc = move["toward_turn"]
        return -tr, -tc
    if policy == "clockwise":
        return _clockwise(move["direction"])
    if policy == "counterclockwise":
        return _counterclockwise(move["direction"])
    if policy == "no_move":
        return None
    raise ValueError(policy)


def _transform_policy(grid: list[list[int]], policy: str) -> list[list[int]]:
    facts = features(grid)
    if policy == "no_move":
        return copy.deepcopy(grid)
    result = copy.deepcopy(grid)
    for move in facts["moves"]:
        pr, pc = move["pivot"]
        dr, dc = move["direction"]
        for step in range(1, move["tail_len"] + 1):
            result[pr + dr * step][pc + dc * step] = FIELD
    destinations = set()
    for move in facts["moves"]:
        pr, pc = move["pivot"]
        tr, tc = _turn(move, policy)
        for step in range(1, move["tail_len"] + 1):
            cell = pr + tr * step, pc + tc * step
            if not (0 <= cell[0] < facts["height"] and 0 <= cell[1] < facts["width"]):
                raise ValueError(f"{policy} tail leaves the grid")
            if grid[cell[0]][cell[1]] != FIELD or cell in destinations:
                raise ValueError(f"{policy} tail destination is occupied")
            destinations.add(cell)
            result[cell[0]][cell[1]] = RED
    return result


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    return _transform_policy(grid, _settings(settings))


def program(settings: dict[str, str]) -> str:
    policy = _settings(settings)
    name = "canonical.rkt" if policy == "toward_center" else "away.rkt"
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def _program_with_turn(pdr: str, pdc: str) -> str:
    source = program({PARAMETER_NAME: "toward_center"})
    old_pdr = '(pdr (if (zero? dc) 0 (if (< kr (/ h 2)) 1 -1)))'
    old_pdc = '(pdc (if (zero? dr) 0 (if (< kc (/ w 2)) 1 -1))))'
    replacement_pdr = f"(pdr {pdr})"
    replacement_pdc = f"(pdc {pdc}))"
    if source.count(old_pdr) != 1 or source.count(old_pdc) != 1:
        raise ValueError("pinned canonical turn expressions changed")
    return source.replace(old_pdr, replacement_pdr).replace(old_pdc, replacement_pdc)


def rival_programs(settings: dict[str, str]) -> dict[str, str]:
    _settings(settings)
    return {
        "toward_center": program({PARAMETER_NAME: "toward_center"}),
        "away_from_center": program({PARAMETER_NAME: "away_from_center"}),
        "clockwise": _program_with_turn("dc", "(- dr)"),
        "counterclockwise": _program_with_turn("(- dc)", "dr"),
        "no_move": "(rule! (lambda (g) g))",
    }


def _candidate(height, width, pivot, direction, bar_len, tail_len):
    pr, pc = pivot
    dr, dc = direction
    gray = pr - dr * (bar_len + 1), pc - dc * (bar_len + 1)
    bar = {(pr - dr * step, pc - dc * step) for step in range(1, bar_len + 1)}
    old_tail = {(pr + dr * step, pc + dc * step) for step in range(1, tail_len + 1)}
    cw = {(pr + _clockwise(direction)[0] * step, pc + _clockwise(direction)[1] * step)
          for step in range(1, tail_len + 1)}
    ccw = {(pr + _counterclockwise(direction)[0] * step, pc + _counterclockwise(direction)[1] * step)
           for step in range(1, tail_len + 1)}
    source = {gray, pivot} | bar | old_tail
    reserved = source | cw | ccw
    if any(not (0 <= r < height and 0 <= c < width) for r, c in reserved):
        return None
    if len(source) != 2 + bar_len + tail_len or source & (cw | ccw) or cw & ccw:
        return None
    # A one-cell cardinal guard prevents a neighboring motif from extending a
    # red bar/tail or creating a second apparent ray during parser recovery.
    guard = set(reserved)
    for r, c in tuple(reserved):
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= rr < height and 0 <= cc < width:
                guard.add((rr, cc))
    toward = _toward(direction, pivot, height, width)
    return {
        "gray": gray, "pivot": pivot, "bar": bar, "old_tail": old_tail,
        "source": source, "reserved": reserved, "guard": guard,
        "toward_sense": _sense(direction, toward),
    }


def _specs(split: str, index: int, count: int):
    # Both senses occur in every episode item.  The 30x30 item uses long arms
    # and four source-boundary anchors rather than padding a small puzzle.
    specs = []
    for i in range(count):
        sense = "clockwise" if i % 2 == 0 else "counterclockwise"
        if split == "test" and index == 3:
            # Boundary anchors use source-axis contact; perpendicular arms stay
            # in-bounds.  Eight 4+4 rays yield 80 non-field source cells.
            boundary_directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
            direction = boundary_directions[i] if i < 4 else DIRECTIONS[i % 4]
            bar_len = 4
            tail_len = 4
            touch = ("top", "bottom", "left", "right")[i] if i < 4 else None
        else:
            direction = DIRECTIONS[(i + 2 * index) % len(DIRECTIONS)]
            bar_len = 1 + (i + index) % 4
            tail_len = 2 + (2 * i + index) % 4
            touch = None
        specs.append((direction, sense, bar_len, tail_len, touch))
    return specs


def _touches(cells: set[tuple[int, int]], touch: str | None, height: int, width: int) -> bool:
    if touch is None:
        return True
    return any({"top": r == 0, "bottom": r == height - 1,
                "left": c == 0, "right": c == width - 1}[touch] for r, c in cells)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:turn-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


@lru_cache(maxsize=256)
def _draw_frozen(seed: int, split: str, index: int):
    height, width, count = (DEMO_PROFILES if split == "train" else QUERY_PROFILES)[index]
    rng = _rng(seed, split, index)
    spec_rows = _specs(split, index, count)
    candidate_sets = []
    for direction, sense, bar_len, tail_len, touch in spec_rows:
        candidates = []
        for r in range(height):
            for c in range(width):
                item = _candidate(height, width, (r, c), direction, bar_len, tail_len)
                if item is None or item["toward_sense"] != sense:
                    continue
                if not _touches(item["source"], touch, height, width):
                    continue
                candidates.append(item)
        rng.shuffle(candidates)
        candidate_sets.append(candidates)
    order = sorted(range(count), key=lambda i: len(candidate_sets[i]))
    chosen: list[dict[str, Any] | None] = [None] * count

    def place(depth: int, occupied_reserved: set[tuple[int, int]],
              occupied_source: set[tuple[int, int]],
              occupied_guard: set[tuple[int, int]]) -> bool:
        if depth == len(order):
            return True
        spec_index = order[depth]
        # Source cells may not touch another motif's reserved cross; reserved
        # output arms may be adjacent to each other, which is harmless and
        # avoids over-constraining small canvases.
        for item in candidate_sets[spec_index][:600]:
            if (item["reserved"] & occupied_reserved
                    or item["source"] & occupied_guard
                    or item["guard"] & occupied_source):
                continue
            chosen[spec_index] = item
            if place(depth + 1,
                     occupied_reserved | item["reserved"],
                     occupied_source | item["source"],
                     occupied_guard | item["guard"]):
                return True
        chosen[spec_index] = None
        return False

    if not place(0, set(), set(), set()):
        raise RuntimeError(f"could not construct collision-free {split} profile {index}")
    grid = [[FIELD] * width for _ in range(height)]
    for item in chosen:
        assert item is not None
        gr, gc = item["gray"]
        pr, pc = item["pivot"]
        grid[gr][gc] = GRAY
        grid[pr][pc] = PIVOT
        for r, c in item["bar"] | item["old_tail"]:
            grid[r][c] = RED
    facts = features(grid)
    if len(facts["moves"]) != count:
        raise AssertionError("constructed motif count changed during parsing")
    if {move["toward_sense"] for move in facts["moves"]} != {"clockwise", "counterclockwise"}:
        raise AssertionError("constructed item lacks both turn senses")
    # Prove totality for both admitted settings before caching the input.
    for policy in POLICIES:
        _transform_policy(grid, policy)
    return tuple(tuple(row) for row in grid)


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    return [list(row) for row in _draw_frozen(seed, split, index)]


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {name: _transform_policy(grid, name) for name in (*POLICIES, *SHORTCUTS)}


def teaching_certificate(train, query_inputs, settings):
    chosen = _settings(settings)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    names = (*POLICIES, *SHORTCUTS)
    rejected = {}
    for index, pair in enumerate(train):
        _grid(pair["output"])
        for name, output in rival_outputs(pair["input"]).items():
            if output != pair["output"]:
                rejected.setdefault(name, index)
    survivors = [name for name in names if name not in rejected]
    if chosen not in survivors:
        raise ValueError("demonstration labels contradict selected policy")
    identifiable = []
    for grid in query_inputs:
        outputs = rival_outputs(grid)
        identifiable.append(all(outputs[name] == outputs[chosen] for name in survivors))
    return {
        "scope": "two settings plus fixed-clockwise, fixed-counterclockwise and no-move shortcuts",
        "survivors": survivors, "rejected": rejected,
        "identified": survivors == [chosen], "query_identifiable": identifiable,
        "query_answers_used_for_fitting": False,
    }


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {
        "task_id": TASK_ID, "seed": seed, "settings": copy.deepcopy(settings),
        "program_solution": program(settings), "reference": "proposed_parametric",
        "training_admitted": False,
    }
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = _draw(seed, split, index)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    episode["certificate"] = verify_episode(episode)
    return episode


def verify_episode(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _settings(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("program_solution does not match selected policy")
    seen = set()
    for split, bounds in (("train", (2, 6)), ("test", (1, 4))):
        pairs = episode.get(split)
        if type(pairs) is not list or not bounds[0] <= len(pairs) <= bounds[1]:
            raise ValueError(f"unsupported {split} count")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair must contain input and output")
            expected = transform(pair["input"], settings)
            _grid(pair["output"])
            if pair["output"] != expected:
                raise ValueError(f"{split} label disagrees with selected policy")
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("all inputs must be distinct")
            seen.add(key)
    certificate = teaching_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], settings
    )
    if not certificate["identified"] or not all(certificate["query_identifiable"]):
        raise ValueError("demonstrations do not identify the selected policy")
    return certificate


def visible_turn(episode, index: int) -> bytes:
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})
