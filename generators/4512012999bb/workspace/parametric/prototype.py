"""Episode-fixed match/contrast rules for the canonical guide-and-crop task.

The canonical generator and reference are unchanged. This separate grammar
extends lawful frame heights to 30 and constructs three distinguishing demos.
Labels returned here are claims; the native worker/exporter executes Racket.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK = "4512012999bb"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parent
ALIGNMENTS = ("match", "contrast")
DEMO_LIMITS = (3, 6)
QUERY_LIMITS = (1, 4)
MAX_ATTEMPTS = 32

# Hand-constructed score witnesses. 2/7 are side colors, 4 is the marker,
# and 3 is an irrelevant accent. Each example receives fresh random colors.
DIRECT_KERNEL = (
    (7, 3, 3, 2, 2, 2),
    (0, 2, 0, 0, 7, 0),
    (3, 0, 2, 7, 7, 0),
    (7, 0, 0, 0, 7, 3),
)
TIE_KERNEL = (
    (2, 3, 7, 0, 7),
    (7, 0, 2, 2, 0),
    (0, 2, 7, 7, 0),
    (3, 7, 2, 0, 2),
)
QUERY_PROFILES = ((7, 10, 3, 3), (16, 21, 6, 9),
                  (24, 26, 22, 11), (30, 30, 28, 14))


def _adjacent(name):
    path = HOME / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "_frame_crop_" + name + "_" + hashlib.sha256(str(path).encode()).hexdigest(), path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@lru_cache(maxsize=1)
def _rivals():
    return _adjacent("rivals")


@lru_cache(maxsize=1)
def _base():
    return load_selected_generator(TASK, root=ROOT)[0]


@lru_cache(maxsize=1)
def canonical_program():
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text().splitlines())
        if row["task_id"] == TASK
    }
    if len(programs) != 1:
        raise ValueError("Expected exactly one selected canonical rule")
    return programs.pop()


def _alignment(settings):
    if (type(settings) is not dict or set(settings) != {"alignment"}
            or type(settings["alignment"]) is not str
            or settings["alignment"] not in ALIGNMENTS):
        raise ValueError("settings must name exactly alignment=match|contrast")
    return settings["alignment"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def program(settings):
    alignment = _alignment(settings)
    canonical = canonical_program()
    if alignment == "match":
        return canonical
    old = "(flip? (> (score #t) (score #f)))"
    if canonical.count(old) != 1:
        raise ValueError("The canonical orientation decision changed; review the variant")
    return canonical.replace(old, "(flip? (< (score #t) (score #f)))")


def facts(grid):
    """Recover a unique, disjoint guide/crop scene using the canonical parser."""
    errors = _base()._valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    candidates = _base()._find_candidates(grid)
    if len(candidates) != 1:
        raise ValueError("The parametric grammar needs exactly one guide/crop candidate")
    result = _base()._facts_for_candidate(grid, candidates[0])
    fr0, fc0, fr1, fc1 = result["frame_bbox"]
    pr0, pc0, pr1, pc1 = result["crop_bbox"]
    if not (pr1 < fr0 or pr0 > fr1 or pc1 < fc0 or pc0 > fc1):
        raise ValueError("The crop must be spatially separate from the guide frame")
    if result["left_color"] == result["right_color"]:
        raise ValueError("The first interior guide colors must differ")
    if result["left_wall"][0] != result["right_wall"][0]:
        raise ValueError("Both walls must share their endpoint marker")
    return result


def render(result, flipped):
    output = [[0] * result["outer_width"] for _ in range(result["outer_height"])]
    for row in range(result["outer_height"]):
        output[row][0] = result["left_wall"][row]
        output[row][-1] = result["right_wall"][row]
        if 0 < row < result["outer_height"] - 1:
            crop_row = result["crop"][row - 1]
            output[row][1:-1] = list(reversed(crop_row)) if flipped else list(crop_row)
    return output


def predict(grid, settings):
    alignment = _alignment(settings)
    result = facts(grid)
    delta = result["flip_score"] - result["direct_score"]
    return render(result, delta > 0 if alignment == "match" else delta < 0)


def _rng(seed, stream):
    # Independent streams make both settings, counts and the first query match.
    digest = hashlib.sha256(f"frame-crop-v1:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _colors(rng):
    marker, left, right, accent, extra = rng.sample(range(1, 10), 5)
    return {0: 0, 4: marker, 2: left, 7: right, 3: accent, 8: extra}


def _scene(crop, colors, canvas, frame_at, crop_at, variegated):
    height, width = canvas
    inner_h, inner_w = len(crop), len(crop[0])
    outer_h, outer_w = inner_h + 2, inner_w + 2
    fr, fc = frame_at
    pr, pc = crop_at
    if not (0 <= fr <= height - outer_h and 0 <= fc <= width - outer_w
            and 0 <= pr <= height - inner_h and 0 <= pc <= width - inner_w):
        raise ValueError("Requested frame/crop does not fit the canvas")
    grid = [[0] * width for _ in range(height)]
    for row in range(outer_h):
        if row in (0, outer_h - 1):
            left = right = colors[4]
        elif variegated and row > 1:
            left, right = colors[7], colors[2]
        else:
            left, right = colors[2], colors[7]
        grid[fr + row][fc] = left
        grid[fr + row][fc + outer_w - 1] = right
    for row, values in enumerate(crop):
        for col, value in enumerate(values):
            grid[pr + row][pc + col] = colors[value]
    return grid


def _demo(seed, kind):
    rng = _rng(seed, f"demo:{kind}")
    colors = _colors(rng)
    crop = [list(row) for row in (TIE_KERNEL if kind == 2 else DIRECT_KERNEL)]
    if kind == 1:
        crop = [[7 if v == 2 else 2 if v == 7 else v for v in row] for row in crop]
    # Reorder lower rows without changing overall, first-row or edge scores.
    tail = crop[1:]
    rng.shuffle(tail)
    crop[1:] = tail
    placement = _rng(seed, "demo-placement").choice(("above", "below", "right"))
    if placement == "above":
        frame_at, crop_at, canvas = (6, 2), (1, 3), (13, 18)
    elif placement == "below":
        frame_at, crop_at, canvas = (1, 2), (8, 3), (13, 18)
    else:
        frame_at, crop_at, canvas = (1, 1), (2, 10), (12, 18)
    grid = _scene(crop, colors, canvas, frame_at, crop_at, variegated=True)
    return grid, facts(grid), 1


def _random_crop(height, width, rng, direction):
    crop = []
    phase = rng.randrange(3)
    for row in range(height):
        values = []
        for col in range(width):
            # Dense, irregular support, with a zero at least every third row.
            # This prevents accidental guide-length runs in the crop.
            if (row + col + phase) % 3 == 2 or rng.random() < 0.10:
                values.append(0)
                continue
            preferred = 2 if col < width // 2 else 7
            if direction == "mirror":
                preferred = 7 if preferred == 2 else 2
            opposite = 7 if preferred == 2 else 2
            values.append(rng.choices((preferred, opposite, 3, 8), (6, 2, 1, 1))[0])
        crop.append(values)
    # Guarantee the exact intended bbox without adding vertical runs.
    for row in (0, height - 1):
        if not any(crop[row]):
            col = next(c for c in range(width) if (row + c + phase) % 3 != 2)
            crop[row][col] = 3
    for col in (0, width - 1):
        if not any(crop[row][col] for row in range(height)):
            row = next(r for r in range(height) if (r + col + phase) % 3 != 2)
            crop[row][col] = 8
    return crop


def _query(seed, index, stream="query"):
    height, width, inner_h, inner_w = QUERY_PROFILES[index % len(QUERY_PROFILES)]
    rng = _rng(seed, f"{stream}:{index}")
    colors = _colors(rng)
    outer_h, outer_w = inner_h + 2, inner_w + 2
    for attempt in range(1, MAX_ATTEMPTS + 1):
        crop = _random_crop(inner_h, inner_w, rng, "mirror" if index % 2 else "direct")
        frame_at = (rng.randrange(height - outer_h + 1), 0)
        crop_at = (rng.randrange(height - inner_h + 1), width - inner_w)
        grid = _scene(crop, colors, (height, width), frame_at, crop_at, variegated=True)
        try:
            result = facts(grid)
        except ValueError:
            continue
        if any(tuple(reversed(row)) != row for row in result["crop"]):
            return grid, result, attempt
    raise ValueError(f"Could not construct {stream} {index} after {MAX_ATTEMPTS} attempts")


def _pair(grid, result, alignment):
    delta = result["flip_score"] - result["direct_score"]
    return {"input": grid,
            "output": render(result, delta > 0 if alignment == "match" else delta < 0)}


def generate(seed, settings, demos=3, queries=4):
    alignment = _alignment(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, *DEMO_LIMITS, "demos")
    _integer(queries, *QUERY_LIMITS, "queries")
    kinds = [0, 1, 2]
    _rng(seed, "demo-order").shuffle(kinds)
    demo_scenes = [_demo(seed, kind) for kind in kinds]
    demo_scenes.extend(_query(seed, i, "extra-demo") for i in range(3, demos))
    query_scenes = [_query(seed, i) for i in range(queries)]
    train = [_pair(g, f, alignment) for g, f, _ in demo_scenes]
    test = [_pair(g, f, alignment) for g, f, _ in query_scenes]
    keys = [tuple(map(tuple, pair["input"])) for pair in train + test]
    if len(set(keys)) != len(keys):
        raise ValueError("The requested episode has duplicate inputs")
    rule = program(settings)
    rejected, surviving = {}, []
    for name in _rivals().programs(rule):
        failure = next((i for i, (_, result, _) in enumerate(demo_scenes)
                        if _rivals().predict(result, name, alignment) != train[i]["output"]), None)
        if failure is None:
            surviving.append(name)
        else:
            rejected[name] = failure
    if surviving:
        raise ValueError("Demonstrations do not reject shortcuts: " + ", ".join(surviving))
    relations = ["direct" if f["direct_score"] > f["flip_score"] else
                 "mirror" if f["direct_score"] < f["flip_score"] else "tie"
                 for _, f, _ in demo_scenes]
    return {
        "train": train, "test": test, "program_solution": rule,
        "settings": dict(settings), "seed": seed,
        "teaching": {"scope": "finite declared shortcuts; Python guard, independently replayed in Racket",
                     "used_query_answers": False, "surviving_shortcuts": surviving,
                     "rejected_shortcuts": rejected, "score_relations": relations},
        "sampling": {"attempts": [a for _, _, a in demo_scenes + query_scenes],
                     "attempt_limit_per_random_input": MAX_ATTEMPTS},
    }
