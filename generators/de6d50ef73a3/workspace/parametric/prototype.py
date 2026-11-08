"""Racket-backed top-left / marker-corner episodes; proposed, not admitted."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "de6d50ef73a3"
SCHEMA = "arcpuzzles-marker-placement-prototype-v1"
HOME = Path(__file__).resolve().parent
PLACEMENTS = ("top_left", "marker_corner")
CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
DEMO_PROFILES = (
    (7, 9, 3, 4, "top_right", 0.25),
    (9, 11, 4, 5, "bottom_left", 0.35),
    (11, 13, 5, 6, "bottom_right", 0.45),
    (13, 15, 6, 7, "top_left", 0.30),
    (16, 18, 8, 9, "top_right", 0.50),
    (20, 22, 10, 11, "bottom_left", 0.40),
)
QUERY_PROFILES = (
    (8, 10, 4, 5, "top_right", 0.30),
    (14, 16, 7, 8, "bottom_left", 0.40),
    (22, 24, 12, 13, "bottom_right", 0.45),
    (30, 30, 20, 21, "top_left", 0.38),
)


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if (type(settings) is not dict or set(settings) != {"placement"}
            or type(settings["placement"]) is not str
            or settings["placement"] not in PLACEMENTS):
        raise ValueError("settings must contain exactly placement=top_left|marker_corner")
    return {"placement": settings["placement"]}


def program(settings):
    placement = settings_value(settings)["placement"]
    filename = "canonical.rkt" if placement == "top_left" else "marker_corner.rkt"
    return (HOME / "rules" / filename).read_text(encoding="utf-8")


def strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid requires rectangular rows and exact integer colors 0..9")
    return grid


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    stack = [remaining.pop()]
    while stack:
        r, c = stack.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def marker_info(grid):
    """Validate and describe the deliberately narrow marker-corner grammar."""
    strict_grid(grid)
    height, width = len(grid), len(grid[0])
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if len(cells) < 6:
        raise ValueError("marker grammar requires a substantive nonzero object")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    crop_h, crop_w = r1 - r0 + 1, c1 - c0 + 1
    if crop_h < 3 or crop_w < 3:
        raise ValueError("marker grammar requires a crop at least 3x3")
    if not (r0 > 0 and c0 > 0 and r1 < height - 1 and c1 < width - 1):
        raise ValueError("marker grammar requires the crop fully interior to the canvas")
    if not _connected(cells):
        raise ValueError("marker grammar requires one 4-connected nonzero support")

    counts = {}
    for r, c in cells:
        value = grid[r][c]
        counts[value] = counts.get(value, 0) + 1
    if len(counts) < 3:
        raise ValueError("marker grammar requires marker plus at least two body colors")
    minimum = min(counts.values())
    least = [color for color, count in counts.items() if count == minimum]
    if minimum != 1 or len(least) != 1:
        raise ValueError("marker grammar requires one unique singleton marker color")
    marker_color = least[0]
    marker = next((r, c) for r, c in cells if grid[r][c] == marker_color)
    relative = marker[0] - r0, marker[1] - c0
    corner_by_position = {
        (0, 0): "top_left",
        (0, crop_w - 1): "top_right",
        (crop_h - 1, 0): "bottom_left",
        (crop_h - 1, crop_w - 1): "bottom_right",
    }
    if relative not in corner_by_position:
        raise ValueError("the singleton marker must occupy a tight-crop corner")
    crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    return {
        "bbox": [r0, c0, r1, c1],
        "crop": crop,
        "corner": corner_by_position[relative],
        "marker_color": marker_color,
        "marker": [marker[0], marker[1]],
        "colors": sorted(counts),
        "counts": {str(color): counts[color] for color in sorted(counts)},
    }


class RacketEngine:
    """One protected bridge reused across bounded generation and verification."""

    def __init__(self):
        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("A live protected Racket bridge is required")
        self.evaluations = 0
        self._wrapped = {}

    def apply(self, source, grid):
        strict_grid(grid)
        wrapped = self._wrapped.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        self.evaluations += 1
        return strict_grid(self.bridge.eval_text(f"({wrapped} {literal})"))

    def close(self):
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


@contextmanager
def _engine(existing):
    if existing is None:
        with RacketEngine() as created:
            yield created
    else:
        yield existing


def _rng(seed, domain, index=0, attempt=0):
    key = json.dumps([TASK_ID, SCHEMA, seed, domain, index, attempt], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def _profile_value(profile):
    if type(profile) not in (tuple, list) or len(profile) != 6:
        raise ValueError("profile must be (canvas_h,canvas_w,crop_h,crop_w,corner,density)")
    height, width, crop_h, crop_w, corner, density = profile
    integer(height, 5, 30, "canvas height")
    integer(width, 5, 30, "canvas width")
    integer(crop_h, 3, 28, "crop height")
    integer(crop_w, 3, 28, "crop width")
    if crop_h > height - 2 or crop_w > width - 2:
        raise ValueError("crop must fit with a one-cell exterior border")
    if corner not in CORNERS:
        raise ValueError("profile corner must be a named crop corner")
    if type(density) not in (int, float) or isinstance(density, bool) or not 0 <= density < 1:
        raise ValueError("density must be numeric in [0,1)")
    return height, width, crop_h, crop_w, corner, float(density)


def sample_input(seed, domain, index, profile, attempt=0):
    """Build a connected multicolor crop with a unique singleton corner marker."""
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000, "index")
    integer(attempt, 0, 31, "attempt")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    height, width, crop_h, crop_w, corner, density = _profile_value(profile)
    rng = _rng(seed, domain, index, attempt)

    perimeter = {
        (r, c)
        for r in range(crop_h)
        for c in range(crop_w)
        if r in {0, crop_h - 1} or c in {0, crop_w - 1}
    }
    interior = [(r, c) for r in range(1, crop_h - 1) for c in range(1, crop_w - 1)]
    interior_count = min(len(interior) - 1, max(0, round(density * len(interior))))
    occupied = set(perimeter)
    available = set(interior)
    for _ in range(interior_count):
        frontier = sorted(
            position for position in available
            if any(neighbor in occupied for neighbor in (
                (position[0] - 1, position[1]), (position[0] + 1, position[1]),
                (position[0], position[1] - 1), (position[0], position[1] + 1),
            ))
        )
        if not frontier:
            raise RuntimeError("connected interior growth exhausted unexpectedly")
        position = rng.choice(frontier)
        available.remove(position)
        occupied.add(position)

    marker_position = {
        "top_left": (0, 0),
        "top_right": (0, crop_w - 1),
        "bottom_left": (crop_h - 1, 0),
        "bottom_right": (crop_h - 1, crop_w - 1),
    }[corner]
    marker_color, *remaining_colors = rng.sample(range(1, 10), 4)
    body_color_count = 2 + rng.randrange(2)
    body_colors = remaining_colors[:body_color_count]
    body_positions = sorted(occupied - {marker_position})
    rng.shuffle(body_positions)
    if len(body_positions) < 2 * body_color_count:
        raise RuntimeError("profile cannot support repeated body colors")
    paint = {marker_position: marker_color}
    cursor = 0
    for color in body_colors:
        for _ in range(2):
            paint[body_positions[cursor]] = color
            cursor += 1
    for position in body_positions[cursor:]:
        paint[position] = rng.choice(body_colors)

    crop = [[0 for _ in range(crop_w)] for _ in range(crop_h)]
    for (r, c), value in paint.items():
        crop[r][c] = value
    top = rng.randint(1, height - crop_h - 1)
    left = rng.randint(1, width - crop_w - 1)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value:
                grid[top + r][left + c] = value
    marker_info(grid)
    return grid


def python_oracle(grid, settings):
    info = marker_info(grid)
    placement = settings_value(settings)["placement"]
    height, width = len(grid), len(grid[0])
    crop = info["crop"]
    crop_h, crop_w = len(crop), len(crop[0])
    if placement == "top_left":
        top, left = 0, 0
    else:
        top, left = {
            "top_left": (0, 0),
            "top_right": (0, width - crop_w),
            "bottom_left": (height - crop_h, 0),
            "bottom_right": (height - crop_h, width - crop_w),
        }[info["corner"]]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value:
                output[top + r][left + c] = value
    return output


def _fixed_corner_source(corner):
    if corner not in CORNERS:
        raise ValueError("unknown fixed corner")
    top = "0" if corner.startswith("top") else "(- (rows g) (rows pat))"
    left = "0" if corner.endswith("left") else "(- (cols g) (cols pat))"
    return f"""(rule!
      (let ((dummy 0))
        (define (nonzero-cells grid)
          (filter (lambda (p) (not (= (at grid (first p) (second p)) 0)))
                  (grid-positions grid)))
        (define (crop-nonzero grid)
          (let ((cells (nonzero-cells grid)))
            (if (empty? cells) (list (list 0))
                (let ((bb (bbox-of-cells cells)))
                  (subgrid grid (first bb) (second bb) (third bb) (fourth bb))))))
        (define (paste-nonzero grid pat top left)
          (for*/fold ((out grid)) ((r (in-range (rows pat))) (c (in-range (cols pat))))
            (let ((v (at pat r c)) (rr (+ top r)) (cc (+ left c)))
              (if (and (not (= v 0)) (in-bounds? rr cc (rows out) (cols out)))
                  (set-cell out rr cc v) out))))
        (define pat (crop-nonzero g))
        (paste-nonzero (empty-grid (rows g) (cols g) 0) pat {top} {left})))"""


@lru_cache(maxsize=1)
def rival_programs():
    return {
        "top_left": program({"placement": "top_left"}),
        "marker_corner": program({"placement": "marker_corner"}),
        "fixed_top_right": _fixed_corner_source("top_right"),
        "fixed_bottom_left": _fixed_corner_source("bottom_left"),
        "fixed_bottom_right": _fixed_corner_source("bottom_right"),
        "identity": "(rule! (let ((dummy 0)) g))",
    }


def check_teaching(train, settings, *, engine=None):
    placement = settings_value(settings)["placement"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("teaching pair requires exactly input and output")
        marker_info(pair["input"])
        strict_grid(pair["output"])
    survivors, distinctions = [], {}
    with _engine(engine) as runtime:
        for name, source in rival_programs().items():
            mismatches = [
                i for i, pair in enumerate(train)
                if runtime.apply(source, pair["input"]) != pair["output"]
            ]
            if not mismatches:
                survivors.append(name)
            else:
                distinctions[name] = {"first_demonstration": mismatches[0]}
    if survivors != [placement]:
        raise ValueError(f"demonstrations do not identify {placement}; surviving rules={survivors}")
    return {
        "fit_scope": "demonstrations_only",
        "survivors": survivors,
        "declared_rivals": list(rival_programs()),
        "distinctions": distinctions,
        "limits": "Finite named rule family only; not uniqueness over arbitrary programs.",
    }


def _runtime_record(runtime):
    return {
        key: runtime.identity[key]
        for key in ("backend", "protected", "binary_sha256", "prelude_sha256",
                    "bridge_sha256", "boot_script_sha256")
        if key in runtime.identity
    }


def _check_evidence(episode, key, expected):
    try:
        observed = json.dumps(episode.get(key), sort_keys=True, allow_nan=False)
        wanted = json.dumps(expected, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid {key} evidence") from error
    if observed != wanted:
        raise ValueError(f"{key} evidence disagrees with executed verification")


def _inputs(seed, demos, queries):
    seen = set()
    result = {"train": [], "test": []}
    for split, domain, count, profiles in (
        ("train", "demo", demos, DEMO_PROFILES),
        ("test", "query", queries, QUERY_PROFILES),
    ):
        for index in range(count):
            for attempt in range(32):
                grid = sample_input(seed, domain, index, profiles[index], attempt)
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    break
            else:
                raise ValueError("could not generate a distinct input within 32 draws")
            seen.add(key)
            result[split].append(grid)
    return result


def verify_episode(episode, *, engine=None):
    if type(episode) is not dict or episode.get("task_id") != TASK_ID or episode.get("schema") != SCHEMA:
        raise ValueError("wrong episode identity/schema")
    settings = settings_value(episode.get("settings"))
    seed = integer(episode.get("seed"), 0, 2**63 - 1, "seed")
    source = program(settings)
    if episode.get("program_solution") != source:
        raise ValueError("program_solution differs from the selected exact rule")
    _check_evidence(episode, "program_sha256", hashlib.sha256(source.encode()).hexdigest())
    _check_evidence(episode, "variant_approved", False)
    _check_evidence(episode, "training_admitted", False)
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("train/test must be lists")
    demos = integer(len(train), 2, 6, "demos")
    queries = integer(len(test), 1, 4, "queries")
    expected_inputs = _inputs(seed, demos, queries)
    seen = set()
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or set(pair) != {"input", "output"}:
                raise ValueError("private pairs need exactly input/output")
            marker_info(pair["input"])
            strict_grid(pair["output"])
            if pair["input"] != expected_inputs[split][index]:
                raise ValueError(f"{split}[{index}] input differs from deterministic sampler")
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate demonstration/query input")
            seen.add(key)
    with _engine(engine) as runtime:
        for split, pairs in (("train", train), ("test", test)):
            for index, pair in enumerate(pairs):
                executed = runtime.apply(source, pair["input"])
                if executed != pair["output"]:
                    raise ValueError(f"{split}[{index}] label does not match executed Racket")
                if python_oracle(pair["input"], settings) != pair["output"]:
                    raise ValueError(f"{split}[{index}] label disagrees with independent oracle")
        certificate = check_teaching(train, settings, engine=runtime)
        _check_evidence(episode, "racket", _runtime_record(runtime))
    certificate["queries"] = [
        {"query_index": index, "label_matches": True,
         "compatible_rules": certificate["survivors"][:]}
        for index in range(len(test))
    ]
    _check_evidence(episode, "certificate", certificate)
    return certificate


def generate(seed, settings, demos=3, queries=4, *, engine=None):
    seed = integer(seed, 0, 2**63 - 1, "seed")
    demos = integer(demos, 2, 6, "demos")
    queries = integer(queries, 1, 4, "queries")
    settings = settings_value(settings)
    source = program(settings)
    episode = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": settings,
        "program_solution": source,
        "train": [],
        "test": [],
    }
    inputs = _inputs(seed, demos, queries)
    with _engine(engine) as runtime:
        for split in ("train", "test"):
            for grid in inputs[split]:
                output = runtime.apply(source, grid)
                if output != python_oracle(grid, settings):
                    raise RuntimeError("protected Racket label disagrees with independent oracle")
                episode[split].append({"input": grid, "output": output})
        episode["certificate"] = check_teaching(episode["train"], settings, engine=runtime)
        episode["certificate"]["queries"] = [
            {"query_index": index, "label_matches": True,
             "compatible_rules": [settings["placement"]]}
            for index in range(queries)
        ]
        episode["racket"] = _runtime_record(runtime)
    episode["program_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    episode["variant_approved"] = False
    episode["training_admitted"] = False
    return episode
