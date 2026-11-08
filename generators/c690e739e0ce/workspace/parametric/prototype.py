"""Row-reflection parametric family for c690e739e0ce.

The exact canonical setting reflects every row left-to-right.  The nearby
setting first derives the unique globally least-frequent color, then reflects
exactly the complete rows containing that color.  Settings are fixed for an
entire episode and all settings share identical sampled inputs.

This is an authoring artifact.  Protected Racket is the retained label authority
for evidence and qualification; the Python transform is an independent mirror.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "c690e739e0ce"
DEFAULT = {"reflection_scope": "all_rows"}
PARAMETERS = {"reflection_scope": ["all_rows", "minority_rows"]}
SETTINGS = [{"reflection_scope": value} for value in PARAMETERS["reflection_scope"]]

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = "(rule! flip-lr)"

_MINORITY_ROWS = """(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (colors (grid-colors g -1))
         (selector
           (first
             (sort-by colors
               (lambda (color) (length (find-color g color)))))))
    (build-grid h w (r c)
      (if (any? (lambda (cc) (= (at g r cc) selector)) (range 0 w))
          (at g r (- (- w 1) c))
          (at g r c))))))"""

_SECOND_RAREST_ROWS = """(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (colors (grid-colors g -1))
         (ordered
           (sort-by colors
             (lambda (color) (length (find-color g color)))))
         (selector (second ordered)))
    (build-grid h w (r c)
      (if (any? (lambda (cc) (= (at g r cc) selector)) (range 0 w))
          (at g r (- (- w 1) c))
          (at g r c))))))"""

_DEMO_SIZES = ((10, 12), (14, 16), (9, 11), (10, 12), (12, 14), (14, 16))
_QUERY_SIZES = ((8, 11), (13, 17), (22, 26), (30, 30))


def _integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"reflection_scope"}:
        raise ValueError("settings must name exactly reflection_scope")
    value = settings["reflection_scope"]
    if type(value) is not str or value not in PARAMETERS["reflection_scope"]:
        raise ValueError("reflection_scope must be 'all_rows' or 'minority_rows'")
    return {"reflection_scope": value}


def _grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 3 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 3 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must use literal lists with 3..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC colors 0..9")
    return grid


def program(settings: object) -> str:
    chosen = _settings(settings)
    return _CANONICAL if chosen == DEFAULT else _MINORITY_ROWS


def digest(value: object) -> str:
    if isinstance(value, bytes):
        body = value
    else:
        body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    body = f"{TASK_ID}|minority-row-v1|{seed}|{domain}|{index}".encode()
    return random.Random(int(hashlib.sha256(body).hexdigest(), 16))


def _color_counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row)


def _ordered_colors(grid: list[list[int]]) -> list[int]:
    counts = _color_counts(grid)
    return sorted(counts, key=lambda color: (counts[color], color))


def _minority_color(grid: list[list[int]]) -> int:
    counts = _color_counts(grid)
    smallest = min(counts.values())
    candidates = sorted(color for color, count in counts.items() if count == smallest)
    if len(candidates) != 1:
        raise ValueError(f"family input needs one unique minority color, got {candidates}")
    return candidates[0]


def input_profile(grid: list[list[int]]) -> dict[str, Any]:
    _grid(grid)
    counts = _color_counts(grid)
    if not 4 <= len(counts) <= 6:
        raise ValueError(f"family input must use 4..6 colors, got {len(counts)}")
    selector = _minority_color(grid)
    selected = tuple(r for r, row in enumerate(grid) if selector in row)
    unselected = tuple(r for r in range(len(grid)) if r not in selected)
    asymmetric = tuple(r for r, row in enumerate(grid) if row != row[::-1])
    if len(selected) < 2 or len(unselected) < 2:
        raise ValueError("family input needs at least two selected and two unselected rows")
    if len(asymmetric) != len(grid):
        raise ValueError("every row must be asymmetric so reflection scope is visible")
    ordered = _ordered_colors(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette": tuple(sorted(counts)),
        "counts": {str(color): counts[color] for color in sorted(counts)},
        "minority_color": selector,
        "minority_count": counts[selector],
        "second_rarest_color": ordered[1],
        "second_rarest_count": counts[ordered[1]],
        "selected_rows": selected,
        "unselected_rows": unselected,
        "asymmetric_row_count": len(asymmetric),
        "top_left_color": grid[0][0],
    }


def _reflect_rows_for_color(grid: list[list[int]], selector: int) -> list[list[int]]:
    return [row[::-1] if selector in row else row[:] for row in grid]


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    """Independent Python mirror; protected Racket remains label authority."""
    _grid(grid)
    chosen = _settings(settings)
    if chosen["reflection_scope"] == "all_rows":
        return [row[::-1] for row in grid]
    selector = _minority_color(grid)
    return _reflect_rows_for_color(grid, selector)


def _selected_rows(h: int, seed: int, domain: str, index: int) -> tuple[int, ...]:
    """Sample a visible row mask while pinning the two-demo teaching scale.

    Demo zero is intentionally small (two selected rows); demo one has nine.
    That crossed scale rejects finite "first/last N selected rows" shortcuts
    without coupling later queries to the teaching examples.
    """
    rng = _rng(seed, f"{domain}:selected", index)
    if domain == "demo" and index == 0:
        count = 2
        required = {0}
        pool = list(range(h))
    elif domain == "demo" and index == 1:
        count = 9
        required = {h - 1}
        pool = list(range(1, h))  # top-left coincidence exists only in demo zero
    else:
        count = min(max(2, h // 3), h - 2)
        required = {0 if index % 2 == 0 else h - 1}
        pool = list(range(h))

    if not len(required) <= count <= len(pool):
        raise AssertionError("invalid selected-row teaching schedule")
    remaining = [row for row in pool if row not in required]
    for _ in range(256):
        chosen = set(required)
        chosen.update(rng.sample(remaining, count - len(chosen)))
        both_parities = {row % 2 for row in chosen} == {0, 1}
        both_halves = (
            any(row < h // 2 for row in chosen)
            and any(row >= h // 2 for row in chosen)
        )
        if both_parities and both_halves:
            return tuple(sorted(chosen))
    raise AssertionError("could not sample a crossed selected-row mask")


def _palette(seed: int, domain: str, index: int, h: int) -> tuple[list[int], int]:
    rng = _rng(seed, "palette-order")
    colors = list(range(10))
    rng.shuffle(colors)
    if h >= 20:
        size = 6
    elif index < 2:
        size = 5
    else:
        size = 4 + (index % 2)
    palette = colors[:size]
    selector = palette[index % size]
    return palette, selector


def _marker_counts(domain: str, index: int, selected_count: int) -> list[int]:
    if domain == "demo" and index == 0:
        if selected_count != 2:
            raise AssertionError("first teaching demo must have two selected rows")
        return [1, 2]
    # Nine rows with 1/2/3 markers give the second teaching demo 18 selector
    # cells.  Other scenes reuse the same mixed per-row counts.
    return [1 + (ordinal % 3) for ordinal in range(selected_count)]


def _make_asymmetric(row: list[int], rare: set[int]) -> None:
    """Break a palindrome in-place without changing any color frequency."""
    if row != row[::-1]:
        return
    width = len(row)
    for c in range(width):
        for d in range(c + 1, width):
            if row[c] == row[d]:
                continue
            if row[c] in rare or row[d] in rare:
                continue
            row[c], row[d] = row[d], row[c]
            if row != row[::-1]:
                return
            row[c], row[d] = row[d], row[c]
    # A row with only one dense color still has a selector/decoy marker. Move
    # that marker rather than changing its count.
    for c, value in enumerate(row):
        if value not in rare:
            continue
        for d, other in enumerate(row):
            if other in rare or c == d:
                continue
            row[c], row[d] = row[d], row[c]
            if row != row[::-1]:
                return
            row[c], row[d] = row[d], row[c]
    raise AssertionError("failed to construct an asymmetric row")


def _make_scene(seed: int, domain: str, index: int, size: tuple[int, int]) -> list[list[int]]:
    h, w = size
    rng = _rng(seed, f"{domain}:cells", index)
    palette, selector = _palette(seed, domain, index, h)
    decoy = next(color for color in palette if color != selector)
    dense_colors = [color for color in palette if color not in {selector, decoy}]
    if len(dense_colors) < 2:
        raise AssertionError("family needs at least two dense colors")

    selected = _selected_rows(h, seed, domain, index)
    selected_set = set(selected)
    unselected = [row for row in range(h) if row not in selected_set]
    if len(unselected) < 2:
        raise AssertionError("family needs a guard row and a decoy row")
    guard_row = unselected[0]
    available_decoy_rows = unselected[1:]

    selector_counts = _marker_counts(domain, index, len(selected))
    selector_total = sum(selector_counts)
    decoy_total = selector_total + 1
    if decoy_total > len(available_decoy_rows) * w:
        raise AssertionError("decoy schedule does not fit")

    # Allocate the decoy over unselected rows, keeping one pure-dense guard row.
    decoy_counts = [0] * len(available_decoy_rows)
    for ordinal in range(decoy_total):
        decoy_counts[ordinal % len(decoy_counts)] += 1
    decoy_rows = {
        row for row, count in zip(available_decoy_rows, decoy_counts) if count
    }
    rare_rows = list(selected) + sorted(decoy_rows)

    # Every dense color is omitted from at least one marked row.  Thus no fixed
    # dense color can masquerade as either "all rows" or the selector mask.
    omitted_by_row: dict[int, int] = {}
    for ordinal, color in enumerate(dense_colors):
        omitted_by_row[rare_rows[ordinal % len(rare_rows)]] = color

    grid: list[list[int]] = []
    for r in range(h):
        omitted = omitted_by_row.get(r)
        available = [color for color in dense_colors if color != omitted]
        row = [
            available[(c + c // 3 + 5 * r + index) % len(available)]
            for c in range(w)
        ]
        grid.append(row)

    split = (w + 1) // 2
    left_interior = list(range(1, split))
    right_interior = list(range(split, w - 1))
    for ordinal, (r, marker_count) in enumerate(zip(selected, selector_counts)):
        if domain == "demo" and index == 0 and r == 0:
            positions = [0]
        else:
            side = left_interior if ordinal % 2 == 0 else right_interior
            if marker_count > len(side):
                raise AssertionError("selector marker schedule does not fit")
            positions = rng.sample(side, marker_count)
        for c in positions:
            grid[r][c] = selector

    for row_index, marker_count in zip(available_decoy_rows, decoy_counts):
        if not marker_count:
            continue
        positions = rng.sample(list(range(w)), marker_count)
        for c in positions:
            grid[row_index][c] = decoy

    for row in grid:
        _make_asymmetric(row, {selector, decoy})

    profile = input_profile(grid)
    counts = _color_counts(grid)
    if profile["selected_rows"] != selected:
        raise AssertionError("selector leaked outside the intended rows")
    if counts[selector] != selector_total:
        raise AssertionError("selector count changed during construction")
    if profile["second_rarest_color"] != decoy or counts[decoy] != decoy_total:
        raise AssertionError("controlled second-rarest decoy was not preserved")
    if any(counts[color] <= decoy_total for color in dense_colors):
        raise AssertionError("dense colors must remain more frequent than the decoy")
    if any(selector in grid[row] or decoy in grid[row] for row in [guard_row]):
        raise AssertionError("pure-dense threshold guard row was contaminated")
    return grid


def _scene(seed: int, domain: str, index: int) -> list[list[int]]:
    if domain == "demo":
        if not 0 <= index < len(_DEMO_SIZES):
            raise ValueError("demo index outside supported schedule")
        size = _DEMO_SIZES[index]
    elif domain == "query":
        if not 0 <= index < len(_QUERY_SIZES):
            raise ValueError("query index outside supported schedule")
        size = _QUERY_SIZES[index]
    else:
        raise ValueError("domain must be demo or query")
    return _make_scene(seed, domain, index, size)


def _mask_transform(grid: list[list[int]], rows: set[int]) -> list[list[int]]:
    return [row[::-1] if r in rows else row[:] for r, row in enumerate(grid)]


def _rows_with_color(grid: list[list[int]], color: int) -> set[int]:
    return {r for r, row in enumerate(grid) if color in row}


def _apply_named(name: str, grid: list[list[int]]) -> list[list[int]]:
    profile = input_profile(grid)
    h = len(grid)
    counts = _color_counts(grid)
    ordered = _ordered_colors(grid)
    selector = profile["minority_color"]
    selected = set(profile["selected_rows"])
    if name == "identity":
        return [row[:] for row in grid]
    if name == "vertical_reflection":
        return [row[:] for row in grid[::-1]]
    if name == "odd_rows":
        return _mask_transform(grid, {r for r in range(h) if r % 2 == 1})
    if name == "even_rows":
        return _mask_transform(grid, {r for r in range(h) if r % 2 == 0})
    if name == "top_half":
        return _mask_transform(grid, set(range(h // 2)))
    if name == "bottom_half":
        return _mask_transform(grid, set(range(h // 2, h)))
    if name == "top_left_color_rows":
        return _mask_transform(grid, _rows_with_color(grid, grid[0][0]))
    if name == "lowest_numeric_color_rows":
        return _mask_transform(grid, _rows_with_color(grid, min(counts)))
    if name == "most_frequent_rows":
        color = max(counts, key=lambda value: (counts[value], -value))
        return _mask_transform(grid, _rows_with_color(grid, color))
    if name == "second_rarest_rows":
        return _mask_transform(grid, _rows_with_color(grid, ordered[1]))
    if name == "first_selected_row_only":
        return _mask_transform(grid, {min(selected)})
    if name == "minority_cells_only":
        out = [row[:] for row in grid]
        w = len(grid[0])
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == selector:
                    out[r][c] = row[c]
                    out[r][w - 1 - c] = selector
        return out
    if name == "selected_rows_vertical":
        # Wrong operation after the correct intermediate: selected rows are
        # replaced by their vertically mirrored source rows instead of reversed.
        return [grid[h - 1 - r][:] if r in selected else row[:] for r, row in enumerate(grid)]
    raise KeyError(name)


EXTRA_RIVALS = (
    "identity",
    "vertical_reflection",
    "odd_rows",
    "even_rows",
    "top_half",
    "bottom_half",
    "top_left_color_rows",
    "lowest_numeric_color_rows",
    "most_frequent_rows",
    "second_rarest_rows",
    "first_selected_row_only",
    "minority_cells_only",
    "selected_rows_vertical",
)


def certify(
    episode: dict[str, Any],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match fixed episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    if len({digest(pair.get("input")) for pair in pairs}) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")
    profiles = []
    for pair in pairs:
        _grid(pair.get("input"))
        _grid(pair.get("output"))
        profiles.append(input_profile(pair["input"]))

    def apply(setting: dict[str, str], grid: list[list[int]]) -> list[list[int]]:
        if execute is None:
            return transform(grid, setting)
        return execute(program(setting), grid)

    chosen_predictions = [apply(chosen, pair["input"]) for pair in pairs]
    for index, (prediction, pair) in enumerate(zip(chosen_predictions, pairs)):
        if prediction != pair["output"]:
            raise ValueError(f"pair {index} label disagrees with fixed setting")

    records = []
    for setting in SETTINGS:
        disagree = [
            i
            for i, pair in enumerate(train)
            if apply(setting, pair["input"]) != pair["output"]
        ]
        records.append({"settings": setting, "disagreeing_demo_indices": disagree})
    survivors = [dict(row["settings"]) for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected scope: {survivors}")

    extra: dict[str, list[int]] = {}
    for name in EXTRA_RIVALS:
        disagree = [
            i
            for i, pair in enumerate(train)
            if _apply_named(name, pair["input"]) != pair["output"]
        ]
        if not disagree:
            raise ValueError(f"extra rival {name!r} survives every demonstration")
        extra[name] = disagree

    query_records = []
    for pair in test:
        query_records.append(
            {
                "input_sha256": digest(pair["input"]),
                "output_sha256": digest(pair["output"]),
                "survivors": survivors,
                "unanimous": True,
            }
        )
    return {
        "scope": "two reflection scopes plus thirteen finite shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": records,
        "extra_refutations": extra,
        "demo_profiles": profiles[: len(train)],
        "query_profiles": profiles[len(train) :],
        "queries": query_records,
    }


def generate(
    seed: int,
    settings: object = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(_rng(seed, "settings").choice(SETTINGS) if settings is None else settings)
    train = []
    for index in range(demos):
        grid = _scene(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(4):
        grid = _scene(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, chosen)})
    episode = {
        "schema": "c690e739-minority-row-parametric-proposal-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    _integer(index, 0, 3, "query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must retain four controller-side queries")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


def sequential_views(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [public_turn(episode, index) for index in range(4)]


class RacketRunner:
    """One live protected bridge for bounded evidence; never a Python fallback."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(max_calls_before_restart=256)
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()


def causal_witness(
    grid: list[list[int]],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    profile = input_profile(grid)
    apply = execute or (lambda source, value: (
        transform(value, {"reflection_scope": "minority_rows"})
        if source == _MINORITY_ROWS
        else _reflect_rows_for_color(value, profile["second_rarest_color"])
    ))
    correct = apply(_MINORITY_ROWS, grid)
    wrong = apply(_SECOND_RAREST_ROWS, grid)
    if correct == wrong:
        raise ValueError("counterfactual selector did not change the final output")
    changed_rows = [r for r, (a, b) in enumerate(zip(correct, wrong)) if a != b]
    return {
        "schema": "c690e739-sequential-witness-v1",
        "step_a": "derive the unique globally least-frequent color and its row mask",
        "intermediate": {
            "minority_color": profile["minority_color"],
            "selected_rows": list(profile["selected_rows"]),
        },
        "step_b": "reverse each complete row selected by that mask",
        "counterfactual": {
            "change": "replace the least-frequent color with the second-rarest color",
            "second_rarest_color": profile["second_rarest_color"],
            "changed_rows": changed_rows,
        },
        "input": copy.deepcopy(grid),
        "input_sha256": digest(grid),
        "correct_program": _MINORITY_ROWS,
        "counterfactual_program": _SECOND_RAREST_ROWS,
        "correct_output": copy.deepcopy(correct),
        "counterfactual_output": copy.deepcopy(wrong),
        "correct_output_sha256": digest(correct),
        "counterfactual_output_sha256": digest(wrong),
        "racket_checked": execute is not None,
    }


def source_hashes() -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE.parents[1] / "generator.py",
        REPO / "shared/data/canonical/puzzles.jsonl",
        REPO / "shared/runtime/reviewer_support.py",
    ]
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
        if path.exists()
    }


def write_batch(
    episodes: list[dict[str, Any]],
    destination: Path,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write only first-turn public challenges; all four queries remain private."""
    destination = Path(destination)
    rows = [
        (
            public_challenge_id(public_turn(episode, 0)),
            public_challenge_bytes(public_turn(episode, 0)),
            episode,
        )
        for episode in episodes
    ]
    rows.sort(key=lambda row: row[0])
    if not rows or len({identifier for identifier, _, _ in rows}) != len(rows):
        raise ValueError("batch must be nonempty with distinct first-turn challenges")
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    public = destination / "public"
    public.mkdir()
    for identifier, body, _ in rows:
        (public / f"{identifier}.json").write_bytes(body)
    (destination / "public.jsonl").write_bytes(b"".join(body for _, body, _ in rows))
    private = {
        "schema": "c690e739-minority-row-evidence-v1",
        "status": "prototype_proposed",
        "source_sha256": source_hashes(),
        "metadata": metadata or {},
        "episodes": [
            dict(
                episode,
                public_id=identifier,
                turn_ids=[public_challenge_id(public_turn(episode, i)) for i in range(4)],
            )
            for identifier, _, episode in rows
        ],
    }
    (destination / "private.json").write_text(
        json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n"
    )
    files = [destination / "public.jsonl", destination / "private.json"] + sorted(public.iterdir())
    manifest = {
        "schema": "c690e739-minority-row-export-v1",
        "public_projection": "first query only; later turns controller-private",
        "writer_executes_racket": False,
        "public_ids": [identifier for identifier, _, _ in rows],
        "files": {
            str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument(
        "--reflection-scope",
        choices=PARAMETERS["reflection_scope"],
        default="all_rows",
    )
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [{"reflection_scope": args.reflection_scope}]
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        witness_grid = _scene((args.seeds or [0])[0], "query", 3)
        witness = causal_witness(witness_grid, execute)
        metadata = {
            "payload_argv": sys.argv,
            "runtime_identity": execute.identity,
            "finite_scope": "two settings plus thirteen named shortcuts",
            "causal_witness": witness,
            "qualification": "not_run",
            "acceptance": "not_requested",
            "training_admitted": False,
        }
        manifest = write_batch(episodes, args.out, metadata=metadata)
    print(
        json.dumps(
            {
                "status": "prototype_proposed",
                "episodes": len(episodes),
                "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                "public_ids": manifest["public_ids"],
                "causal_witness": witness,
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
