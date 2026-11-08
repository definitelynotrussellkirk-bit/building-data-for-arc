"""Native axis-policy sampler and projection over the retained exact programs.

Python outputs are claims checked independently by native protected Racket.
The historical prototypes and production generator are unchanged.
"""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import find_root, load_selected_generator, public_challenge_bytes

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
POLICIES = ("more_coherent", "less_coherent")


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _policy(settings):
    if (type(settings) is not dict or set(settings) != {"axis_policy"}
            or type(settings["axis_policy"]) is not str or settings["axis_policy"] not in POLICIES):
        raise ValueError("settings must contain exactly axis_policy=more_coherent|less_coherent")
    return settings["axis_policy"]


@lru_cache(maxsize=1)
def _retained():
    path = HERE / "axis_policy/prototype.py"
    name = "_retained_axis_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _generator():
    module, _, _ = load_selected_generator("90082143f2ec", root=ROOT)
    return module


def program(settings):
    policy = _policy(settings)
    source = _retained().program_for(policy)
    if policy == "more_coherent":
        return source
    # The native runner recognizes a lambda as callable, but treats the retained
    # outer let as a body expression. Apply that unchanged callable explicitly.
    body = strip_rule_wrapper(strip_line_comments(source))
    return f"(rule! (lambda (g) ({body} g)))"


def _validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")


def _mode(values, tie="low"):
    counts = Counter(values)
    best = max(counts.values())
    winners = [value for value in counts if counts[value] == best]
    return max(winners) if tie == "high" else winners[0] if tie == "first" else min(winners)


def observables(grid, tie="low"):
    _validate_grid(grid)
    rows = [_mode(row, tie) for row in grid]
    columns = [_mode(list(col), tie) for col in zip(*grid)]
    row_coherence = sum(v == rows[r] for r, row in enumerate(grid) for v in row)
    col_coherence = sum(v == columns[c] for row in grid for c, v in enumerate(row))
    return {"row_modes": rows, "column_modes": columns,
            "row_coherence": row_coherence, "column_coherence": col_coherence,
            "dominant_axis": "columns" if col_coherence > row_coherence else "rows"}


def _axis(facts, policy):
    columns = (facts["column_coherence"] > facts["row_coherence"] if policy == "more_coherent"
               else facts["column_coherence"] < facts["row_coherence"])
    return "columns" if columns else "rows"


def _fill(grid, facts, axis):
    return ([[facts["column_modes"][c] for c in range(len(grid[0]))] for _ in grid]
            if axis == "columns" else [[mode] * len(grid[0]) for mode in facts["row_modes"]])


def solve(grid, settings):
    """Propose labels on the sampled grammar; protected Racket is authoritative.

    The exact canonical program keeps its historical tie behavior. Its selected
    slices have strict modes in this sampler; arbitrary tied grids are outside
    this helper's canonical-parity claim. Alternate ties choose the lowest color.
    """
    policy = _policy(settings)
    facts = observables(grid)
    return _fill(grid, facts, _axis(facts, policy))


def _stream(seed, split, index):
    value = hashlib.sha256(f"native-axis-v1/{seed}/{split}/{index}".encode()).digest()
    return random.Random(int.from_bytes(value, "big")), int.from_bytes(value[:8], "big") % 2**63


def _teaching_grid(rng, transpose):
    low, middle, high = sorted(rng.sample(range(1, 10), 3))
    # Non-minimum colors at both ends make first-seen tie selection observably wrong.
    colors = [high, low, middle]
    grid = [[color for color in colors for _ in range(2)] for _ in range(6)]
    tied_row = rng.choice((2, 3))
    for r in range(6):
        if r == tied_row:
            continue
        donor = r % 3
        c = donor * 2 + r // 3
        grid[r][c] = colors[(donor + 1) % 3]
    return [list(row) for row in zip(*grid)] if transpose else grid


def _large_grid(rng, height, width, orientation):
    count = rng.choice((3, 4, 5))
    length = width if orientation == "columns" else height
    widths = _generator()._partition(length, count, rng)
    colors = rng.sample(range(1, 10), count)
    modes = [color for color, size in zip(colors, widths) for _ in range(size)]
    clean = ([[modes[c] for c in range(width)] for _ in range(height)] if orientation == "columns"
             else [[modes[r]] * width for r in range(height)])
    grid = deepcopy(clean)
    target = round(height * width * 0.18)
    capacity = (height if orientation == "columns" else width) // 3
    used = [0] * (width if orientation == "columns" else height)
    positions = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(positions)
    corners = [(0, 0), (height-1, width-1), (0, width-1), (height-1, 0)]
    positions = corners + [p for p in positions if p not in corners]
    chosen = []
    for r, c in positions:
        line = c if orientation == "columns" else r
        if used[line] < capacity:
            chosen.append((r, c))
            used[line] += 1
        if len(chosen) == target:
            break
    if len(chosen) != target:
        raise RuntimeError("bounded noise placement did not reach the requested count")
    missing = [v for v in range(1, 10) if v not in colors]
    rng.shuffle(missing)
    for index, (r, c) in enumerate(chosen):
        original = clean[r][c]
        if index < 4:
            value = rng.choice([v for v in colors if v != original])
        elif index - 4 < len(missing):
            value = missing[index - 4]
        else:
            value = rng.choice([v for v in range(1, 10) if v != original])
        grid[r][c] = value
    facts = observables(grid)
    if facts["dominant_axis"] != orientation or solve(grid, {"axis_policy": "more_coherent"}) != clean:
        raise RuntimeError("independent noise changed the intended band modes or axis")
    return grid


def sample_input(seed, split, index):
    rng, child_seed = _stream(seed, split, index)
    if split == "train":
        if index < 2:
            return _teaching_grid(rng, transpose=index == 1)
        if index < 4:
            return _generator().generate(child_seed, (4, 2)[index - 2], difficulty="medium")
        height, width = ((22, 23), (26, 27))[index - 4]
        return _large_grid(rng, height, width, "columns" if index == 4 else "rows")
    if index < 2:
        return _generator().generate(child_seed, (0, 6)[index], difficulty="hard")
    size = (24, 30)[index - 2]
    orientation = "columns" if (seed + index) % 2 else "rows"
    return _large_grid(rng, size, size, orientation)


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    _policy(settings)
    episode = {"task_id": "90082143f2ec", "seed": seed,
               "settings": deepcopy(settings), "program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = sample_input(seed, split, index)
            episode[split].append({"input": grid, "output": solve(grid, settings)})
    return episode


def visible_turn(episode, index):
    _integer(index, "query index", 0, len(episode["test"]) - 1)
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])} for p in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][index]["input"])}]}


def rival_names(settings):
    policy = _policy(settings)
    names = ["other_policy", "always_rows", "always_columns", "shape_axis", "aspect_axis",
             "global_mode", "identity", "minimum_color", "maximum_color", "first_line"]
    if policy == "less_coherent":
        names += ["highest_tie", "first_seen_tie", "restore_before_weaker"]
    return names


def rival_output(name, grid, settings):
    policy = _policy(settings)
    facts = observables(grid)
    axis = _axis(facts, policy)
    if name == "other_policy":
        return solve(grid, {"axis_policy": POLICIES[1-POLICIES.index(policy)]})
    if name in ("always_rows", "always_columns"):
        return _fill(grid, facts, name.removeprefix("always_"))
    if name in ("shape_axis", "aspect_axis"):
        strong = ("columns" if len(grid) == 13 else "rows") if name == "shape_axis" else (
            "columns" if len(grid[0]) >= len(grid) else "rows")
        selected = strong if policy == "more_coherent" else ("rows" if strong == "columns" else "columns")
        return _fill(grid, facts, selected)
    if name in ("global_mode", "minimum_color", "maximum_color"):
        flat = [v for row in grid for v in row]
        value = _mode(flat) if name == "global_mode" else min(flat) if name == "minimum_color" else max(flat)
        return [[value] * len(grid[0]) for _ in grid]
    if name == "identity":
        return deepcopy(grid)
    if name == "first_line":
        return [grid[0][:] for _ in grid] if axis == "columns" else [[row[0]] * len(row) for row in grid]
    if name in ("highest_tie", "first_seen_tie"):
        other = observables(grid, "high" if name == "highest_tie" else "first")
        return _fill(grid, other, _axis(other, policy))
    if name == "restore_before_weaker":
        return solve(solve(grid, {"axis_policy": "more_coherent"}), {"axis_policy": "less_coherent"})
    raise ValueError("unknown rival")


def teaching_report(train, settings):
    if not train:
        raise ValueError("demonstrations are required")
    rows = []
    for name in rival_names(settings):
        counterexample = next((i for i, p in enumerate(train)
                               if rival_output(name, p["input"], settings) != p["output"]), None)
        rows.append({"name": name, "counterexample_demo": counterexample})
    return {"rival_count": len(rows), "all_refuted": all(r["counterexample_demo"] is not None for r in rows),
            "rivals": rows, "scope": "finite demonstration-only alternatives"}


def write_batch(episodes, out):
    staged, seen, turn_seen = [], set(), set()
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identifier = hashlib.sha256(payload).hexdigest()
        if identifier in seen:
            raise ValueError("duplicate visible episode")
        seen.add(identifier)
        turns = []
        for index in range(len(episode["test"])):
            visible = public_challenge_bytes(visible_turn(episode, index))
            turn_id = hashlib.sha256(visible).hexdigest()
            if turn_id in turn_seen:
                raise ValueError("duplicate visible query turn")
            turn_seen.add(turn_id)
            turns.append((turn_id, visible))
        staged.append((identifier, payload, turns, episode))
    if not staged:
        raise ValueError("at least one episode is required")
    staged.sort(key=lambda row: row[0])
    target = Path(out)
    target.mkdir(parents=True, exist_ok=False)
    (target / "public").mkdir()
    (target / "turns").mkdir()
    private = []
    for identifier, payload, turns, episode in staged:
        (target / "public" / f"{identifier}.json").write_bytes(payload)
        for turn_id, payload in turns:
            (target / "turns" / f"{turn_id}.json").write_bytes(payload)
        private.append({"public_id": identifier, "turn_ids": [p[0] for p in turns], "episode": episode})
    (target / "private.json").write_text(json.dumps({"episodes": private}, sort_keys=True) + "\n")
    return {"public_ids": [p[0] for p in staged], "turn_count": sum(len(p[2]) for p in staged)}
