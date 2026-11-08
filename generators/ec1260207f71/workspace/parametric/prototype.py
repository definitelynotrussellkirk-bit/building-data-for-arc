"""Proposed episode-fixed row transfer; canonical production is unchanged.

The native adapter returns Python label claims. verify.py independently executes
all retained labels and declared rivals with the packet's protected Racket.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes, public_challenge_id
from puzzle_generators.rule_wrap import strip_rule_wrapper

TASK_ID = "ec1260207f71"
HERE = Path(__file__).resolve().parent
ORDERS = ("aligned", "reversed")
SHORTCUTS = ("upper_only", "lower_only", "left_only", "right_only",
             "join_only", "transfer_only", "keep_markers")
DEMO_SHAPES = ((14, 9), (20, 12), (18, 11), (26, 15), (28, 23), (30, 27))
QUERY_SHAPES = ((14, 7), (19, 17), (26, 24), (30, 30))


def _integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"transfer_order"}
            or type(settings["transfer_order"]) is not str
            or settings["transfer_order"] not in ORDERS):
        raise ValueError("settings must contain only transfer_order=aligned|reversed")
    return settings["transfer_order"]


def program(settings):
    order = _settings(settings)
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if order == "aligned":
        return canonical
    prefix, separator, suffix = canonical.partition("((seg-col (first plain-seg))")
    needle = "(offset (- r seg-start)))"
    if not separator or suffix.count(needle) != 1:
        raise ValueError("Pinned canonical plain-segment expression has changed")
    return prefix + separator + suffix.replace(needle, "(offset (- seg-len 1 (- r seg-start))))", 1)


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def features(grid):
    _grid(grid)
    height, width = len(grid), len(grid[0])
    if not 14 <= height <= 30 or not 7 <= width <= 30:
        raise ValueError("proposed input size must be 14..30 by 7..30")
    if any(v not in (0, 2, 8) for row in grid for v in row):
        raise ValueError("input uses only background 0, red bars 2 and cyan markers 8")
    if any(v == 2 and c not in (0, width - 1) for row in grid for c, v in enumerate(row)):
        raise ValueError("red bars must occupy the side edges")
    left = [r for r in range(height) if grid[r][0] == 2]
    right = [r for r in range(height) if grid[r][-1] == 2]
    length = len(left)
    if not 4 <= length <= 14 or len(right) != length:
        raise ValueError("two equal bars of length 4..14 are required")
    if any(rows != list(range(rows[0], rows[0] + length)) for rows in (left, right)):
        raise ValueError("bars must be contiguous")
    upper, lower = sorted((left[0], right[0]))
    if lower < upper + length + 2:
        raise ValueError("bar row bands need at least two blank rows between them")
    dots = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    if not 1 <= len(dots) <= length or len({r for r, c in dots}) != len(dots):
        raise ValueError("one to bar-length cyan markers on distinct rows are required")
    if any(c in (0, width - 1) for r, c in dots):
        raise ValueError("cyan markers must be strictly inside the side edges")
    dot_rows = {r for r, c in dots}
    sides = [side for side, rows in (("left", left), ("right", right)) if dot_rows <= set(rows)]
    if len(sides) != 1:
        raise ValueError("all markers must lie in exactly one red bar's row band")
    side = sides[0]
    start, plain = (left[0], right[0]) if side == "left" else (right[0], left[0])
    return {"height": height, "width": width, "length": length, "side": side,
            "band": "upper" if start < plain else "lower", "dot_start": start,
            "plain_start": plain, "dots": [(r - start, c) for r, c in dots]}


def transform(grid, settings):
    order = _settings(settings)
    f = features(grid)
    result = copy.deepcopy(grid)
    dot_edge = 0 if f["side"] == "left" else f["width"] - 1
    plain_edge = f["width"] - 1 - dot_edge
    for offset, col in f["dots"]:
        row = f["dot_start"] + offset
        lo, hi = sorted((dot_edge, col))
        for c in range(lo + 1, hi):
            result[row][c] = 8
        result[row][col] = 4
        destination = offset if order == "aligned" else f["length"] - 1 - offset
        for c in range(f["width"]):
            if c != plain_edge:
                result[f["plain_start"] + destination][c] = 8
    return result


def _rng(seed, stream):
    # No private setting or requested count enters input sampling.
    digest = hashlib.sha256(f"{TASK_ID}:row-transfer-v1:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _draw(seed, split, index):
    height, width = (DEMO_SHAPES if split == "train" else QUERY_SHAPES)[index]
    rng = _rng(seed, f"{split}:{index}")
    roles = [("left", "upper"), ("right", "lower"), ("left", "lower"), ("right", "upper")]
    role_rng = _rng(seed, "roles")
    flip_side, flip_band = role_rng.randrange(2), role_rng.randrange(2)
    side, band = roles[index % 4]
    if flip_side:
        side = "right" if side == "left" else "left"
    if flip_band:
        band = "lower" if band == "upper" else "upper"
    length = rng.randint(4, min(10, (height - 2) // 2))
    if split == "test" and index in (2, 3):
        length = (height - 2) // 2
    upper, lower = 0, height - length
    if split == "train" and index not in (0, 1):
        upper = rng.randint(0, height - 2 * length - 2)
        lower = rng.randint(upper + length + 2, height - length)
    if split == "train" and index == 0:
        offsets = [0, length - 2]  # Constructively asymmetric under reversal.
    elif split == "train" and index == 1:
        offsets = [0, 1, length - 2]
    elif split == "test" and index == 0:
        offsets = [rng.choice((0, length - 1))]
    elif split == "test" and index == 3:
        offsets = sorted(set(range(length)) - {2, length - 3})
    elif split == "train" and index == 5:
        offsets = list(range(length))  # A lawful full-density, setting-invariant pair.
    else:
        count = rng.randint(2, length)
        offsets = sorted(rng.sample(range(length), count))
    start, plain = (upper, lower) if band == "upper" else (lower, upper)
    left_start, right_start = (start, plain) if side == "left" else (plain, start)
    grid = [[0] * width for _ in range(height)]
    for offset in range(length):
        grid[left_start + offset][0] = 2
        grid[right_start + offset][-1] = 2
    for i, offset in enumerate(offsets):
        col = (1 if i == 0 else width - 2 if i == len(offsets) - 1 else rng.randint(1, width - 2))
        grid[start + offset][col] = 8
    features(grid)
    return grid


def rival_outputs(grid, settings):
    f = features(grid)
    intended = transform(grid, settings)
    answers = {order: transform(grid, {"transfer_order": order}) for order in ORDERS}
    for name, holds in (("upper_only", f["band"] == "upper"),
                        ("lower_only", f["band"] == "lower"),
                        ("left_only", f["side"] == "left"),
                        ("right_only", f["side"] == "right")):
        answers[name] = copy.deepcopy(intended if holds else grid)
    for name, start in (("join_only", f["dot_start"]), ("transfer_only", f["plain_start"])):
        answers[name] = [copy.deepcopy(intended[r] if start <= r < start + f["length"] else grid[r])
                         for r in range(f["height"])]
    answers["keep_markers"] = [[8 if grid[r][c] == 8 else v for c, v in enumerate(row)]
                               for r, row in enumerate(intended)]
    return answers


def rival_programs(settings):
    """Executable finite rivals; failed execution is never a distinguishing witness."""
    body = strip_rule_wrapper(program(settings))
    setup = """
      (define h (rows g)) (define w (cols g))
      (define left-rows (filter (lambda (r) (= (at g r 0) 2)) (range 0 h)))
      (define right-rows (filter (lambda (r) (= (at g r (- w 1)) 2)) (range 0 h)))
      (define dot-row (first (filter (lambda (r)
        (ormap (lambda (c) (= (at g r c) 8)) (range 0 w))) (range 0 h))))
      (define left-dotted (member dot-row left-rows))
      (define ds (if left-dotted (first left-rows) (first right-rows)))
      (define ps (if left-dotted (first right-rows) (first left-rows)))
      (define n (length left-rows))
    """
    predicates = {"upper_only": "(< ds ps)", "lower_only": "(> ds ps)",
                  "left_only": "left-dotted", "right_only": "(not left-dotted)"}
    result = {order: program({"transfer_order": order}) for order in ORDERS}
    for name, predicate in predicates.items():
        result[name] = f"(rule! (lambda (g) {setup} (if {predicate} ({body} g) g)))"
    for name, start in (("join_only", "ds"), ("transfer_only", "ps")):
        result[name] = f"""(rule! (lambda (g) {setup}
          (define answer ({body} g))
          (cellmap answer (r c v)
            (if (and (>= r {start}) (< r (+ {start} n))) v (at g r c)))))"""
    result["keep_markers"] = f"""(rule! (lambda (g)
        (define answer ({body} g))
        (cellmap answer (r c v) (if (= (at g r c) 8) 8 v))))"""
    return result


def teaching_certificate(train, query_inputs, settings):
    chosen = _settings(settings)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    names = [*ORDERS, *SHORTCUTS]
    rejected = {}
    for index, pair in enumerate(train):
        _grid(pair["output"])
        for name, output in rival_outputs(pair["input"], settings).items():
            if output != pair["output"]:
                rejected.setdefault(name, index)
    survivors = [name for name in names if name not in rejected]
    if chosen not in survivors:
        raise ValueError("demonstration labels contradict the selected rule")
    identifiable = []
    for grid in query_inputs:
        outputs = rival_outputs(grid, settings)
        identifiable.append(all(outputs[name] == outputs[chosen] for name in survivors))
    return {"scope": "two parameter settings and seven declared shortcuts; not all possible programs",
            "survivors": survivors, "rejected": rejected,
            "identified": survivors == [chosen], "query_identifiable": identifiable,
            "query_answers_used_for_fitting": False}


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {"task_id": TASK_ID, "seed": seed, "settings": copy.deepcopy(settings),
               "program_solution": program(settings), "reference": "proposed_parametric",
               "training_admitted": False}
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
        raise ValueError("program_solution does not match the episode setting")
    seen = set()
    for split, bounds in (("train", (2, 6)), ("test", (1, 4))):
        pairs = episode.get(split)
        if type(pairs) is not list or not bounds[0] <= len(pairs) <= bounds[1]:
            raise ValueError(f"unsupported {split} count")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair must contain input and output")
            _grid(pair["output"])
            expected = transform(pair["input"], settings)
            if pair["output"] != expected:
                raise ValueError(f"{split} label disagrees with the selected rule")
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("all inputs must be distinct")
            seen.add(key)
    certificate = teaching_certificate(episode["train"], [p["input"] for p in episode["test"]], settings)
    if not certificate["identified"] or not all(certificate["query_identifiable"]):
        raise ValueError("demonstrations do not identify the declared rule and shortcuts")
    return certificate


def visible_turn(episode, index):
    """One current query, with no ordinal, total count, future input or private ID."""
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})


def write_export(episodes, output):
    """Write a validated prototype batch; protected Racket evidence is separate.

    The public directory is a controller-side batch store. A turn consumer uses
    visible_turn, rather than exposing all four query inputs on its first turn.
    """
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    if type(episodes) is not list or not episodes:
        raise ValueError("a nonempty episode list is required")
    rows = []
    for episode in episodes:
        certificate = verify_episode(episode)
        payload = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        private = copy.deepcopy(episode)
        private.update(public_id=public_id, certificate=certificate,
                       reference="proposed_parametric", training_admitted=False)
        rows.append((public_id, payload, private))
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("duplicate visible challenge")
    rows.sort(key=lambda row: row[0])
    output.mkdir(parents=True, exist_ok=False)
    (output / "public").mkdir()
    for public_id, payload, private in rows:
        (output / "public" / (public_id + ".json")).write_bytes(payload)
    private_bytes = b"".join((json.dumps(row[2], sort_keys=True, separators=(",", ":")) + "\n").encode()
                             for row in rows)
    (output / "private.jsonl").write_bytes(private_bytes)
    manifest = {"schema": "ec1260207f71-parametric-export-v1", "status": "proposed",
                "training_admitted": False, "public_ids": [row[0] for row in rows],
                "label_basis": "Python claims; consult the separate protected-Racket verification receipt",
                "private_sha256": hashlib.sha256(private_bytes).hexdigest()}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
