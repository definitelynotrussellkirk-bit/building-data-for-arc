"""Proposed front/back layer selection for the crossing-band ARC family.

Canonical generation, authority and approvals are unchanged. All emitted labels
are executed through the protected Racket bridge; the Python graph observer is
an independent structural check. Run with --help for a bounded four-query export.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "7b0cb3b9a618"
VERSION = "layer-selection-prototype-v1"
HERE = Path(__file__).resolve().parent
SETTINGS = ("front", "back")
PROFILES = ((3, 3, 2), (8, 12, 4), (9, 11, 4), (11, 11, 5), (11, 12, 5), (11, 13, 4))
MAX_EPISODE_ATTEMPTS = 64


def _integer(value: Any, name: str, lower: int | None = None, upper: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be a literal integer")
    if lower is not None and value < lower or upper is not None and value > upper:
        raise ValueError(f"{name} must be in {lower}..{upper}")
    return value


def _setting(target_layer: str) -> str:
    if type(target_layer) is not str or target_layer not in SETTINGS:
        raise ValueError("target_layer must be 'front' or 'back'")
    return target_layer


def program_for(target_layer: str = "front") -> str:
    """Return exact materialized rule bytes for an episode-fixed setting."""
    return (HERE / (_setting(target_layer) + ".rkt")).read_text(encoding="utf-8")


def _grid(grid: Any) -> None:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row) for row in grid):
        raise ValueError("grid must be rectangular with literal integer colors 0..9")


def visible_endpoints(grid: list[list[int]]) -> dict[str, Any]:
    """Infer crossing order from pixels, requiring unique first and last bands.

    Middle layers may be incomparable. No hidden paint order or sample metadata
    enters this observer, and malformed geometry or cyclic crossings fails closed.
    """
    _grid(grid)
    height, width = len(grid), len(grid[0])
    colors = {cell for row in grid for cell in row}
    if 0 not in colors or len(colors) < 3:
        raise ValueError("visible background and at least two band colors are required")
    colors.remove(0)
    horizontal, vertical = {}, {}
    for color in sorted(colors):
        cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == color]
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        dh, dw = rows[-1] - rows[0] + 1, cols[-1] - cols[0] + 1
        if dw > dh and rows == list(range(rows[0], rows[-1] + 1)):
            horizontal[color] = rows
        elif dh > dw and cols == list(range(cols[0], cols[-1] + 1)):
            vertical[color] = cols
        else:
            raise ValueError(f"color {color} lacks a unique contiguous band orientation")
    if not horizontal or not vertical:
        raise ValueError("both horizontal and vertical bands are required")
    row_owner, col_owner = [0] * height, [0] * width
    for bands, owners in ((horizontal, row_owner), (vertical, col_owner)):
        for color, span in bands.items():
            for position in span:
                if owners[position]:
                    raise ValueError("same-orientation bands overlap")
                owners[position] = color
    if 0 not in row_owner or 0 not in col_owner:
        raise ValueError("each orientation must retain a background line")
    edges: set[tuple[int, int]] = set()
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            h, v = row_owner[r], col_owner[c]
            if h and v:
                if cell == h:
                    edges.add((v, h))
                elif cell == v:
                    edges.add((h, v))
                else:
                    raise ValueError("crossing contains neither incident color")
            elif cell != (h or v):
                raise ValueError("band is broken or a cell lies outside the bands")
    outgoing = {color: set() for color in colors}
    incoming = {color: set() for color in colors}
    for earlier, later in edges:
        outgoing[earlier].add(later)
        incoming[later].add(earlier)
    indegree = {color: len(incoming[color]) for color in colors}
    queue = deque(color for color in colors if indegree[color] == 0)
    visited = 0
    while queue:
        color = queue.popleft()
        visited += 1
        for later in outgoing[color]:
            indegree[later] -= 1
            if indegree[later] == 0:
                queue.append(later)
    if visited != len(colors):
        raise ValueError("crossings imply a cyclic paint order")
    first = [color for color in colors if not incoming[color]]
    last = [color for color in colors if not outgoing[color]]
    if len(first) != 1 or len(last) != 1:
        raise ValueError("front and back must each have exactly one visible candidate")
    return {"front": last[0], "back": first[0], "edges": [list(e) for e in sorted(edges)],
            "horizontal": horizontal, "vertical": vertical}


def _spans(length: int, colors: list[int], rng: random.Random, thin: set[int]) -> dict[int, list[int]]:
    widths = {color: 1 for color in colors}
    extra = length - (2 if length == 3 else 3) - len(colors)
    options = list(colors)
    rng.shuffle(options)
    for color in options:
        if extra > 0 and color not in thin and rng.random() < 0.6:
            widths[color] += 1
            extra -= 1
    rng.shuffle(options)
    gaps = [0] * (len(colors) + 1)
    for _ in range(length - sum(widths.values())):
        gaps[rng.randrange(len(gaps))] += 1
    cursor, spans = gaps[0], {}
    for i, color in enumerate(options):
        spans[color] = list(range(cursor, cursor + widths[color]))
        cursor += widths[color] + gaps[i + 1]
    return spans


def sample_input(seed: int, sample_index: int) -> list[list[int]]:
    """Sample an alternating crossing chain, independently of target_layer."""
    _integer(seed, "seed")
    _integer(sample_index, "sample_index", 0)
    key = f"{VERSION}:{seed}:{sample_index}".encode()
    rng = random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))
    height, width, count = PROFILES[(sample_index // 2) % len(PROFILES)]
    order = rng.sample(range(1, 10), count)
    front_horizontal = sample_index % 2 == 0
    orientations = [front_horizontal if (count - 1 - i) % 2 == 0 else not front_horizontal
                    for i in range(count)]
    horizontal = [color for color, is_h in zip(order, orientations) if is_h]
    vertical = [color for color, is_h in zip(order, orientations) if not is_h]
    hs = _spans(height, horizontal, rng, set())
    vs = _spans(width, vertical, rng, {order[-1]} if not front_horizontal else set())
    if not front_horizontal and vs[order[-1]] == [0]:
        vs = {color: sorted(width - 1 - c for c in span) for color, span in vs.items()}
    grid = [[0] * width for _ in range(height)]
    for color, is_h in zip(order, orientations):
        if is_h:
            for row in hs[color]:
                grid[row] = [color] * width
        else:
            for col in vs[color]:
                for row in range(height):
                    grid[row][col] = color
    observed = visible_endpoints(grid)
    if observed["front"] != order[-1] or observed["back"] != order[0]:
        raise AssertionError("painted scene disagrees with its visible crossing graph")
    return grid


class RacketLabeler:
    """One protected bridge reused for labels, canonical parity and rivals."""
    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=10.0, startup_timeout=45.0)
        self.runtime_identity = self.bridge.runtime_identity
        if not self.runtime_identity.get("protected"):
            self.close()
            raise RuntimeError("protected Racket runtime handshake did not pass")

    def label(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        _grid(grid)
        if type(program) is not str or not program.strip():
            raise ValueError("a nonempty materialized Racket program is required")
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        # rule! is a lexical identity here; exact authority text stays intact.
        expression = f"((let ([rule! (lambda (candidate) candidate)]) {program}) {literal})"
        result = self.bridge.eval_text(expression)
        _grid(result)
        if len(result) != 1 or len(result[0]) != 1 or result[0][0] == 0:
            raise ValueError("layer rule must return one nonzero color")
        return result

    def close(self) -> None:
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def rival_predictions(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    """Concrete shortcut hypotheses; these are not reference label authorities."""
    width = len(grid[0])
    clean_rows = [row[0] for row in grid if row[0] and len(set(row)) == 1]
    clean_cols = [grid[0][c] for c in range(width)
                  if grid[0][c] and len({row[c] for row in grid}) == 1]
    dirty_major = [row[0] for row in grid if row[0] and row.count(row[0]) > width - 2]
    foreground = [cell for row in grid for cell in row if cell]
    counts = Counter(foreground)
    values = {
        "uniform_row_only": (clean_rows or dirty_major or [0])[0],
        "uniform_column_only": (clean_cols or [0])[0],
        "most_frequent": min(counts, key=lambda color: (-counts[color], color)),
        "least_frequent": min(counts, key=lambda color: (counts[color], color)),
        "smallest_color": min(foreground), "largest_color": max(foreground),
        "first_nonzero": foreground[0], "last_nonzero": foreground[-1],
    }
    return {name: [[value]] for name, value in values.items()}


def _key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(map(tuple, grid))


def build_episode(seed: int, *, target_layer: str = "front", demo_count: int = 3,
                  query_count: int = 4, labeler: RacketLabeler | None = None) -> dict[str, Any]:
    """Build one fixed-setting episode; fail explicitly after 64 candidate lessons.

    Both lawful settings and eight shortcuts are compared using demonstrations
    only. Queries are labeled after those demonstrations eliminate all rivals.
    """
    _integer(seed, "seed")
    _setting(target_layer)
    _integer(demo_count, "demo_count", 2, 12)
    _integer(query_count, "query_count", 1, 32)
    programs = {setting: program_for(setting) for setting in SETTINGS}
    context = RacketLabeler() if labeler is None else nullcontext(labeler)
    count = demo_count + query_count
    with context as runtime:
        for attempt in range(MAX_EPISODE_ATTEMPTS):
            # Advance through every schedule slot regardless of requested counts.
            inputs = [sample_input(seed, attempt + i) for i in range(count)]
            if len({_key(grid) for grid in inputs}) != count:
                continue
            demos = inputs[:demo_count]
            labels = {setting: [runtime.label(programs[setting], grid) for grid in demos]
                      for setting in SETTINGS}
            expected = labels[target_layer]
            settings = [setting for setting in SETTINGS if labels[setting] == expected]
            demo_rivals = [rival_predictions(grid) for grid in demos]
            rivals = [name for name in demo_rivals[0]
                      if all(row[name] == answer for row, answer in zip(demo_rivals, expected))]
            if settings != [target_layer] or rivals:
                continue
            queries = inputs[demo_count:]
            answers = [runtime.label(programs[target_layer], grid) for grid in queries]
            program = programs[target_layer]
            return {
                "schema": "arcpuzzles-layer-selection-prototype-v1", "task_id": TASK_ID,
                "prototype_version": VERSION, "status": "proposed", "training_admitted": False,
                "target_layer": target_layer, "seed": seed, "draw_attempt": attempt,
                "demo_count": demo_count, "query_count": query_count,
                "program": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "runtime_identity": runtime.runtime_identity,
                "train": [{"input": grid, "output": answer} for grid, answer in zip(demos, expected)],
                "test": [{"input": grid, "output": answer} for grid, answer in zip(queries, answers)],
                "identifiability": {
                    "basis": "demonstrations_only", "settings_checked": list(SETTINGS),
                    "rivals_checked": sorted(demo_rivals[0]), "surviving_settings": settings,
                    "surviving_rivals": rivals,
                    "queries": [{"query_index": i, "identifiable": True,
                                 "reason": "one lawful setting survives; all declared shortcuts refuted by demos"}
                                for i in range(query_count)],
                },
            }
    raise RuntimeError(f"no distinct, identifiable lesson after {MAX_EPISODE_ATTEMPTS} attempts; "
                       f"seed={seed}, target_layer={target_layer}, demos={demo_count}, queries={query_count}")


def write_batch(episodes: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    """Export exact public bytes plus private evidence; never overwrite a batch.

    This writer projects already authored records. It does not certify modified
    private labels. IDs depend only on the bytes visible to a learner.
    """
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise FileExistsError(f"choose a fresh output directory: {out_dir}")
    if not episodes:
        raise ValueError("at least one episode is required")
    prepared, seen = [], set()
    for episode in episodes:
        raw = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if public_id != hashlib.sha256(raw).hexdigest():
            raise AssertionError("public helper bytes and identifier disagree")
        if public_id in seen:
            raise ValueError(f"duplicate visible payload: {public_id}")
        seen.add(public_id)
        program = episode["program"]
        digest = hashlib.sha256(program.encode("utf-8")).hexdigest()
        if digest != episode["program_sha256"]:
            raise ValueError("private program digest does not match program text")
        private = json.dumps(episode, sort_keys=True, indent=2) + "\n"
        prepared.append((public_id, raw, private, digest, program))
    prepared.sort(key=lambda item: item[0])
    manifest = {"schema": "arcpuzzles-layer-selection-export-v1", "status": "proposed",
                "training_admitted": False, "public_identifier_status": "visible_bytes_only",
                "public_ids": [item[0] for item in prepared],
                "episodes": [{"public_id": item[0], "program_sha256": item[3]} for item in prepared]}
    # All serialization, hashes and duplicate checks finish before the first write.
    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "public").mkdir()
    (out_dir / "private/programs").mkdir(parents=True)
    for public_id, raw, private, digest, program in prepared:
        (out_dir / "public" / (public_id + ".json")).write_bytes(raw)
        (out_dir / "private" / (public_id + ".json")).write_text(private, encoding="utf-8")
        (out_dir / "private/programs" / (digest + ".rkt")).write_text(program, encoding="utf-8")
    (out_dir / "private/manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=190807)
    parser.add_argument("--target-layer", choices=(*SETTINGS, "both"), default="both")
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    settings = SETTINGS if args.target_layer == "both" else (args.target_layer,)
    with RacketLabeler() as labeler:
        episodes = [build_episode(args.seed, target_layer=setting, demo_count=args.demo_count,
                                  query_count=args.query_count, labeler=labeler) for setting in settings]
    manifest = write_batch(episodes, args.out)
    print(json.dumps({"status": "proposed", "episodes": len(episodes),
                      "demonstrations": args.demo_count, "queries_per_episode": args.query_count,
                      "public_ids": manifest["public_ids"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
