"""Proposed connectivity family for bb75d495c809; never canonical authority.

The task still groups non-background cells and recolors each object by size
(1->3, 2->2, 3->1, >=4->0).  The episode-fixed ``connectivity`` setting chooses
4- or 8-neighbor grouping.  Identical inputs expose diagonal contacts under both
settings; retained evidence is re-executed by protected Racket before export.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "bb75d495c809"
DEFAULT = {"connectivity": 4}
PARAMETERS = {"connectivity": [4, 8]}
SETTINGS = [{"connectivity": value} for value in PARAMETERS["connectivity"]]

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = '''(rule! (lambda (g)
  (paint-objects-by g (objects g (mode g 0))
    (lambda (o) (casev (obj-size o) (hash 1 3 2 2 3 1) 0)))))'''

_EIGHT = '''(rule! (lambda (g)
  (paint-objects-by g (objects-8 g (mode g 0))
    (lambda (o) (casev (obj-size o) (hash 1 3 2 2 3 1) 0)))))'''

_DEMO_SHAPES = ((10, 11), (11, 12), (12, 14), (14, 16), (16, 18), (18, 20))
_QUERY_SHAPES = ((10, 10), (16, 18), (24, 26), (30, 30))
_WALLS = (4, 5, 6, 7, 8, 9)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIRS8 = _DIRS4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))
_SIZE_COLOR = {1: 3, 2: 2, 3: 1}


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: Any) -> dict[str, int]:
    if type(settings) is not dict or set(settings) != {"connectivity"}:
        raise ValueError("settings must name exactly connectivity")
    value = settings["connectivity"]
    if type(value) is not int or value not in PARAMETERS["connectivity"]:
        raise ValueError("connectivity must be the exact integer 4 or 8")
    return {"connectivity": value}


def _grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 2 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 2 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 2..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    if not any(cell != 0 for row in grid for cell in row):
        raise ValueError("grid needs a nonzero modal background")
    return grid


def program(settings: Any) -> str:
    chosen = _settings(settings)
    return _CANONICAL if chosen["connectivity"] == 4 else _EIGHT


def _background(grid: list[list[int]]) -> int:
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    if not counts:
        return 0
    return max(counts, key=counts.get)


def _objects(grid: list[list[int]], connectivity: int) -> list[list[tuple[int, int]]]:
    background = _background(grid)
    directions = _DIRS4 if connectivity == 4 else _DIRS8
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[list[tuple[int, int]]] = []
    for r in range(height):
        for c in range(width):
            if (r, c) in seen or grid[r][c] == background:
                continue
            color = grid[r][c]
            seen.add((r, c))
            stack = [(r, c)]
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in directions:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append(cells)
    return objects


def transform(grid: Any, settings: Any) -> list[list[int]]:
    """Python semantic mirror; retained evidence uses Racket as authority."""
    value = _grid(grid)
    connectivity = _settings(settings)["connectivity"]
    output = [list(row) for row in value]
    for cells in _objects(value, connectivity):
        color = _SIZE_COLOR.get(len(cells), 0)
        for r, c in cells:
            output[r][c] = color
    return output


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    token = _digest([TASK_ID, "connectivity-v1", seed, domain, index])
    return random.Random(int(token, 16))


def _candidate_shape(rng: random.Random, size: int) -> set[tuple[int, int]]:
    if size == 1:
        return {(0, 0)}
    if size == 2:
        return {(0, 0), (0, 1)} if rng.randrange(2) else {(0, 0), (1, 0)}
    shapes = (
        {(0, 0), (1, 0), (1, 1)},
        {(0, 1), (1, 0), (1, 1)},
        {(0, 0), (0, 1), (0, 2)},
        {(0, 0), (1, 0), (2, 0)},
    )
    return set(rng.choice(shapes))


def _place_isolated(
    zeros: set[tuple[int, int]],
    shape: set[tuple[int, int]],
    top: int,
    left: int,
    height: int,
    width: int,
) -> set[tuple[int, int]] | None:
    cells = {(top + r, left + c) for r, c in shape}
    if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
        return None
    for r, c in cells:
        for dr, dc in _DIRS8:
            neighbor = (r + dr, c + dc)
            if neighbor in zeros and neighbor not in cells:
                return None
    return cells if not (cells & zeros) else None


def _scene(seed: int, index: int, *, query_slot: int | None = None) -> list[list[int]]:
    rng = _rng(seed, "query" if query_slot is not None else "demo", index)
    if query_slot is None:
        height, width = _DEMO_SHAPES[index % len(_DEMO_SHAPES)]
    else:
        height, width = _QUERY_SHAPES[query_slot]
    wall = rng.choice(_WALLS)
    grid = [[wall] * width for _ in range(height)]

    # Two guaranteed diagonal-contact motifs:
    # A) singleton + singleton: 4-neighbor sizes 1+1, 8-neighbor size 2.
    # B) singleton + domino: 4-neighbor sizes 1+2, 8-neighbor size 3.
    zeros: set[tuple[int, int]] = {
        (1, 1), (2, 2),
        (1, width - 4), (2, width - 3), (2, width - 2),
        (height - 4, 1), (height - 3, 1), (height - 3, 2),
        (height - 2, 4), (height - 2, 5),
        (height - 3, width - 2),
    }

    # Larger scenes receive additional 8-neighbor-isolated pockets to make the
    # 24x26 and 30x30 cases real component-scanning stress rather than padding.
    target_extra = min(12, max(0, (height * width - 100) // 70))
    added = 0
    for _ in range(2000):
        if added >= target_extra:
            break
        shape = _candidate_shape(rng, rng.choice((1, 1, 2, 2, 3)))
        placed = _place_isolated(
            zeros,
            shape,
            rng.randrange(1, height - 1),
            rng.randrange(1, width - 1),
            height,
            width,
        )
        if placed is not None:
            zeros.update(placed)
            added += 1
    if added != target_extra:
        raise RuntimeError("could not place requested isolated stress pockets")

    for r, c in zeros:
        grid[r][c] = 0
    return grid


def _apply_python(source: str, grid: list[list[int]]) -> list[list[int]]:
    for setting in SETTINGS:
        if program(setting) == source:
            return transform(grid, setting)
    raise ValueError("unknown connectivity program")


def _all_singletons(grid: list[list[int]]) -> list[list[int]]:
    background = _background(grid)
    return [[cell if cell == background else 3 for cell in row] for row in grid]


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
        raise ValueError("queries must be exactly four")

    all_pairs = train + test
    inputs: set[str] = set()
    for pair in all_pairs:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each private pair must contain exactly input and output")
        grid = _grid(pair["input"])
        output = _grid(pair["output"])
        if len(output) != len(grid) or len(output[0]) != len(grid[0]):
            raise ValueError("connectivity output must preserve grid dimensions")
        key = _digest(grid)
        if key in inputs:
            raise ValueError("all demonstration and query inputs must be distinct")
        inputs.add(key)

    apply = execute or _apply_python
    records = []
    for setting in SETTINGS:
        predictions = [apply(program(setting), pair["input"]) for pair in train]
        records.append(
            {
                "settings": dict(setting),
                "disagreeing_demo_indices": [
                    index
                    for index, (prediction, pair) in enumerate(zip(predictions, train))
                    if prediction != pair["output"]
                ],
            }
        )
    survivors = [row["settings"] for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify the chosen setting: {survivors}")

    shortcut_refutations = {
        "treat_every_nonbackground_cell_as_a_singleton": any(
            _all_singletons(pair["input"]) != pair["output"] for pair in train
        ),
        "leave_pockets_unchanged": any(pair["input"] != pair["output"] for pair in train),
    }
    if not all(shortcut_refutations.values()):
        raise ValueError(f"demonstrations leave a declared shortcut alive: {shortcut_refutations}")

    for pair in all_pairs:
        if apply(program(chosen), pair["input"]) != pair["output"]:
            raise ValueError("retained label disagrees with selected rule")
    queries = [
        {
            "input_sha256": _digest(pair["input"]),
            "output_sha256": _digest(pair["output"]),
            "survivors": survivors,
            "unanimous": True,
        }
        for pair in test
    ]
    return {
        "scope": "two declared connectivity rules plus two explicit shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": records,
        "shortcut_refutations": shortcut_refutations,
        "queries": queries,
    }


def generate(
    seed: int,
    settings: dict[str, int] | None = None,
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
        grid = _scene(seed, index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for slot in range(4):
        grid = _scene(seed, 10_000 + slot, query_slot=slot)
        test.append({"input": grid, "output": transform(grid, chosen)})

    episode = {
        "schema": "bb75-connectivity-parametric-proposal-v1",
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


class RacketRunner:
    """One live protected bridge for a bounded evidence batch."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
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

    def __exit__(self, *exc: Any) -> None:
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE.parents[1] / "generator.py",
        REPO / "shared/runtime/reviewer_support.py",
        REPO / "shared/runtime/arc_repl/racket_bridge.py",
        REPO / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
        REPO / "shared/runtime/puzzle_generators/rule_wrap.py",
    ]
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
        if path.is_file()
    }


def public_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    """Model-visible one-query turn; never includes future inputs or count hints."""
    if type(query_index) is not int or not 0 <= query_index < 4:
        raise ValueError("query_index must be the exact integer 0..3")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must contain demonstrations and exactly four controller queries")
    return public_challenge_bytes({"train": train, "test": [test[query_index]]})


def write_batch(episodes: list[dict[str, Any]], destination: Path, *, metadata=None) -> dict[str, Any]:
    destination = Path(destination)
    rows = []
    for episode in episodes:
        controller_body = public_challenge_bytes(episode)
        controller_id = hashlib.sha256(controller_body).hexdigest()
        turns = []
        for query_index in range(4):
            body = public_turn_bytes(episode, query_index)
            turns.append((hashlib.sha256(body).hexdigest(), body))
        rows.append((controller_id, controller_body, turns, episode))
    rows.sort(key=lambda row: row[0])
    controller_ids = [row[0] for row in rows]
    turn_ids = [identifier for _, _, turns, _ in rows for identifier, _ in turns]
    if not rows or len(set(controller_ids)) != len(controller_ids):
        raise ValueError("batch must be nonempty with distinct controller challenges")
    if len(set(turn_ids)) != len(turn_ids):
        raise ValueError("all model-visible turns must have distinct public bytes")
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    public = destination / "public"
    controller = destination / "controller"
    public.mkdir()
    controller.mkdir()
    episode_index = []
    private_episodes = []
    for controller_id, controller_body, turns, episode in rows:
        controller_path = controller / f"{controller_id}.json"
        controller_path.write_bytes(controller_body)
        ordered_turn_ids = []
        for identifier, body in turns:
            (public / f"{identifier}.json").write_bytes(body)
            ordered_turn_ids.append(identifier)
        episode_index.append({
            "controller": str(controller_path.relative_to(destination)),
            "turn_ids": ordered_turn_ids,
        })
        private_episodes.append(dict(
            episode,
            controller_id=controller_id,
            turn_ids=ordered_turn_ids,
        ))
    private = {
        "schema": "bb75-connectivity-evidence-v1",
        "status": "prototype_proposed",
        "source_sha256": source_hashes(),
        "metadata": metadata or {},
        "episodes": private_episodes,
    }
    (destination / "private.json").write_text(
        json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n"
    )
    files = [
        destination / "private.json",
        *sorted(public.iterdir()),
        *sorted(controller.iterdir()),
    ]
    manifest = {
        "schema": "bb75-connectivity-export-v2",
        "public_ids": turn_ids,
        "episodes": episode_index,
        "public_usage": "Serve only the next public/ file selected by controller/private state.",
        "controller_usage": "controller/ holds all four future inputs; it is not a model prompt.",
        "manifest_usage": "Controller metadata only; never place manifest.json in model context.",
        "writer_executes_racket": False,
        "files": {
            str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--connectivity", type=int, choices=PARAMETERS["connectivity"], default=4)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [{"connectivity": args.connectivity}]
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        manifest = write_batch(
            episodes,
            args.out,
            metadata={
                "payload_argv": sys.argv,
                "runtime_identity": execute.identity,
                "qualification": "not_run",
                "acceptance": "not_requested",
                "training_admitted": False,
            },
        )
    print(
        json.dumps(
            {
                "status": "prototype_proposed",
                "episodes": len(episodes),
                "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                "public_ids": manifest["public_ids"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
