#!/usr/bin/env python3
"""Bounded stdlib authoring prototype; no production API or approval changes."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import tempfile

# Bind imports and data to this source tree, never to cwd or a predecessor.
for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
from reviewer_support import (
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status

ROOT = find_root(__file__)
DEFAULT_DIRECTION = "ccw"
PROGRAMS = {"ccw": "(rule! rotate-ccw)", "cw": "(rule! rotate-cw)"}
# This callable adapter supports only our declared bare-callable rule! forms.
RULE_WRAPPER = "(define (rule! f) f)"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
DEMO_SHAPES = ((3, 5), (4, 4), (5, 8), (6, 6), (7, 10), (8, 8))
QUERY_SHAPES = ((11, 15), (16, 21), (24, 29), (30, 30))
LIMITATIONS = [
    "Proposed prototype only; canonical generator and approval are unchanged.",
    "Only direction ccw/cw is varied; identity and half-turn are not declared parameters.",
    "Episodes support 2..6 demonstrations and exactly four controller-side queries.",
    "Inputs are structured 3..30 integer-color grids with four distinct corners.",
    "Identifiability is checked against the two declared rotations, not all programs.",
    "Evidence is finite and source-bound, not proof over all seeds.",
    "The rule! bridge wrapper supports only the declared bare callable forms.",
]


def open_bridge():
    """Open the provided reference runtime and install the narrow rule! wrapper."""
    bridge = RacketBridge()
    try:
        bridge.eval_text(RULE_WRAPPER)
    except BaseException:
        bridge.shutdown()
        raise
    return bridge


def execute(bridge, direction, grids):
    """Install exact declared Racket once and execute it for every supplied grid."""
    if direction not in PROGRAMS:
        raise ValueError(f"direction must be one of {tuple(PROGRAMS)}")
    bridge.eval_text(f"(define prototype-rule {PROGRAMS[direction]})")
    outputs = []
    for grid in grids:
        bridge.define_grid("prototype-input", normalize_grid(grid))
        outputs.append(normalize_grid(bridge.eval_text("(prototype-rule prototype-input)")))
    return outputs


def assess_episode(bridge, episode):
    """Execute every parameter rival on full episode; infer only from demos."""
    pairs = episode["train"] + episode["test"]
    split = len(episode["train"])
    rivals = {}
    for direction in PROGRAMS:
        outputs = execute(bridge, direction, [p["input"] for p in pairs])
        matches = [actual == pair["output"] for actual, pair in zip(outputs, pairs)]
        rivals[direction] = {
            "outputs": outputs,
            "demo_matches": matches[:split],
            "query_matches": matches[split:],
            "demo_consistent": all(matches[:split]),
            "full_episode_consistent": all(matches),
        }
    survivors = [key for key, value in rivals.items() if value["demo_consistent"]]
    return {"rivals": rivals, "demo_survivors": survivors,
            "identifiable_from_demos": len(survivors) == 1}


def _validate_request(seed, n_train, n_test):
    if type(seed) is not int or not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed must be an exact integer in [0, {MAX_SEED}]")
    if type(n_train) is not int or not MIN_DEMOS <= n_train <= MAX_DEMOS:
        raise ValueError(f"n_train must be an exact integer in [{MIN_DEMOS}, {MAX_DEMOS}]")
    if type(n_test) is not int or n_test != QUERY_COUNT:
        raise ValueError(f"n_test must be the exact integer {QUERY_COUNT}")


def _structured_grid(seed, role, index, height, width):
    """Draw a dense asymmetric field whose content spans the full canvas."""
    rng = random.Random(f"{seed}|{role}|{index}|{height}x{width}")
    palette = list(range(10))
    rng.shuffle(palette)
    row_stride = 3 + 2 * (index % 3)
    col_stride = 5 + 2 * ((index + 1) % 3)
    block_h = 2 + index % 4
    block_w = 3 + (index * 2) % 5
    phase = rng.randrange(10)
    grid = []
    for row in range(height):
        values = []
        for col in range(width):
            code = (
                row * row_stride
                + col * col_stride
                + (row // block_h) * 3
                + (col // block_w) * 7
                + phase
            ) % 10
            value = palette[code]
            # Sparse zero corridors add object boundaries without turning a
            # large query into padded empty space.
            if (row * 11 + col * 7 + index) % 17 == 0:
                value = 0
            values.append(value)
        grid.append(values)
    corners = rng.sample(range(1, 10), 4)
    grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1] = corners
    return grid


def _sample_grids(seed, n_train, n_test):
    _validate_request(seed, n_train, n_test)
    grids = [
        _structured_grid(seed, "demo", index, *DEMO_SHAPES[index])
        for index in range(n_train)
    ]
    grids.extend(
        _structured_grid(seed, "query", index, *QUERY_SHAPES[index])
        for index in range(n_test)
    )
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in grids}
    if len(fingerprints) != len(grids):
        raise ValueError("sampler produced duplicate visible inputs")
    return grids


def python_transform(grid, direction):
    """Compute a label claim locally; qualification replays it in protected Racket."""
    normalized = normalize_grid(grid)
    if direction == "ccw":
        return [list(row) for row in zip(*normalized)][::-1]
    if direction == "cw":
        return [list(row) for row in zip(*normalized[::-1])]
    raise ValueError(f"direction must be one of {tuple(PROGRAMS)}")


def build_claimed_episode(*, seed, direction, n_train, n_test=QUERY_COUNT):
    """Build deterministic Python claims for the native promotion worker to replay."""
    _validate_request(seed, n_train, n_test)
    if direction not in PROGRAMS:
        raise ValueError(f"direction must be one of {tuple(PROGRAMS)}")
    grids = _sample_grids(seed, n_train, n_test)
    pairs = [
        {"input": grid, "output": python_transform(grid, direction)}
        for grid in grids
    ]
    return {"train": pairs[:n_train], "test": pairs[n_train:]}


def build_episode(bridge, *, seed, direction=None, n_train=3, n_test=QUERY_COUNT):
    """Choose one hidden direction, then draw distinct structured examples."""
    _validate_request(seed, n_train, n_test)
    selected = random.Random(seed).choice(tuple(PROGRAMS))
    if direction is not None:
        if direction not in PROGRAMS:
            raise ValueError(f"direction must be one of {tuple(PROGRAMS)}")
        selected = direction
    grids = _sample_grids(seed, n_train, n_test)
    outputs = execute(bridge, selected, grids)
    pairs = [{"input": grid, "output": output} for grid, output in zip(grids, outputs)]
    episode = {"seed": seed, "direction": selected,
               "program": PROGRAMS[selected],
               "program_sha256": hashlib.sha256(PROGRAMS[selected].encode()).hexdigest(),
               "train": pairs[:n_train], "test": pairs[n_train:]}
    episode["rival_check"] = assess_episode(bridge, episode)
    if episode["rival_check"]["demo_survivors"] != [selected]:
        raise ValueError("draw does not distinguish the selected direction from demos")
    return episode


def public_challenge(episode, query_indices=None):
    """Project exact model-visible bytes, excluding private rule and query labels."""
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    if query_indices is None:
        indices = list(range(len(test)))
    else:
        if type(query_indices) not in (list, tuple) or not query_indices:
            raise ValueError("query_indices must be a nonempty list or tuple")
        indices = list(query_indices)
        if any(type(index) is not int or not 0 <= index < len(test) for index in indices):
            raise ValueError("query index outside the episode")
        if len(set(indices)) != len(indices):
            raise ValueError("query_indices must be distinct")
    challenge = {
        "train": [{"input": pair["input"], "output": pair["output"]} for pair in train],
        "test": [{"input": test[index]["input"]} for index in indices],
    }
    # Round-trip through the canonical helper so malformed/private fields cannot
    # accidentally influence the exported object or its identifier.
    return json.loads(public_challenge_bytes(challenge))


def sequential_turn(episode, query_index):
    """Render one model turn with no count hint, future query, or query answer."""
    test = episode.get("test")
    if type(test) is not list or type(query_index) is not int or not 0 <= query_index < len(test):
        raise ValueError("query_index must name one stored query")
    if query_index == 0:
        return public_challenge(episode, query_indices=[0])
    return deepcopy({"test": [{"input": test[query_index]["input"]}]})


def verify_episode(episode, bridge):
    """Freshly replay labels and the demonstration-only declared-setting check."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    _validate_request(episode.get("seed"), len(train) if type(train) is list else None,
                      len(test) if type(test) is list else None)
    direction = episode.get("direction")
    if direction not in PROGRAMS:
        raise ValueError("stored direction is outside the declared setting family")
    program = PROGRAMS[direction]
    if episode.get("program") != program:
        raise ValueError("stored program differs from the selected setting")
    if episode.get("program_sha256") != hashlib.sha256(program.encode()).hexdigest():
        raise ValueError("stored program hash differs from the selected setting")
    public_challenge_bytes(public_challenge(episode))
    pairs = train + test
    seen = set()
    for pair in pairs:
        key = json.dumps(pair["input"], separators=(",", ":"))
        if key in seen:
            raise ValueError("duplicate visible input within episode")
        seen.add(key)
        if "output" not in pair:
            raise ValueError("private episode is missing an executed query label")
    outputs = execute(bridge, direction, [pair["input"] for pair in pairs])
    if outputs != [pair["output"] for pair in pairs]:
        raise ValueError("stored labels differ from fresh Racket execution")
    fresh = assess_episode(bridge, episode)
    if fresh.get("demo_survivors") != [direction]:
        raise ValueError("demonstrations do not uniquely identify the selected direction")
    if episode.get("rival_check") != fresh:
        raise ValueError("stored rival certificate differs from fresh demo-only replay")
    return True


def write_batch(episodes, out, bridge):
    """Atomically publish sorted exact-public files plus private replay evidence."""
    if type(episodes) is not list or not episodes:
        raise ValueError("batch must contain at least one episode")
    out = Path(out)
    if out.exists():
        raise ValueError("output path already exists")
    planned = []
    for episode in episodes:
        verify_episode(episode, bridge)
        public = public_challenge(episode)
        raw = public_challenge_bytes(public)
        planned.append((public_challenge_id(public), raw, episode))
    planned.sort(key=lambda row: row[0])
    if len({row[0] for row in planned}) != len(planned):
        raise ValueError("duplicate visible payload in batch")

    witness = [[1, 2, 3], [4, 5, 6]]
    witness_outputs = {key: execute(bridge, key, [witness])[0] for key in PROGRAMS}
    report = {
        "schema": "864eaaac6503-parametric-rotation-prototype-v2",
        "status": "proposed prototype; not production approval",
        "training_admitted": False,
        "episode_count": len(planned),
        "public_ids": [row[0] for row in planned],
        "demonstration_counts": [len(row[2]["train"]) for row in planned],
        "query_counts": [len(row[2]["test"]) for row in planned],
        "label_count": sum(len(row[2][split]) for row in planned for split in ("train", "test")),
        "directions_exercised": sorted({row[2]["direction"] for row in planned}),
        "parameter": {"name": "direction", "allowed": list(PROGRAMS),
                      "original_default": DEFAULT_DIRECTION,
                      "input_constraints_depend_on_direction": False},
        "programs": {key: {"text": value,
                           "sha256": hashlib.sha256(value.encode()).hexdigest()}
                     for key, value in PROGRAMS.items()},
        "source_sha256": source_hashes(),
        "racket_runtime": racket_runtime_status(),
        "witness": {"input": witness, "outputs": witness_outputs,
                    "distinct": witness_outputs["ccw"] != witness_outputs["cw"]},
        "limitations": LIMITATIONS,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".rotation-parametric-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        private_rows = []
        for public_id, raw, episode in planned:
            (stage / "public" / f"{public_id}.json").write_bytes(raw)
            private_rows.append(dict(deepcopy(episode), public_id=public_id))
        (stage / "private" / "episodes.json").write_text(
            json.dumps(private_rows, sort_keys=True, indent=2) + "\n"
        )
        (stage / "private" / "verification.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n"
        )
        stage.rename(out)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return report


def verify_batch(path, bridge):
    """Replay a written batch and bind every public file to exact visible bytes."""
    path = Path(path)
    try:
        rows = json.loads((path / "private" / "episodes.json").read_text())
        report = json.loads((path / "private" / "verification.json").read_text())
    except (OSError, ValueError) as error:
        raise ValueError("missing or invalid private batch evidence") from error
    if type(rows) is not list or not rows:
        raise ValueError("private episode list must be nonempty")
    ids = []
    for row in rows:
        verify_episode(row, bridge)
        public = public_challenge(row)
        public_id = public_challenge_id(public)
        if row.get("public_id") != public_id:
            raise ValueError("private public-ID binding mismatch")
        public_path = path / "public" / f"{public_id}.json"
        if public_path.read_bytes() != public_challenge_bytes(public):
            raise ValueError("public bytes differ from their exact visible projection")
        ids.append(public_id)
    if ids != sorted(set(ids)):
        raise ValueError("batch must be sorted and visibly distinct")
    if sorted(item.name for item in (path / "public").iterdir()) != [f"{value}.json" for value in ids]:
        raise ValueError("unexpected public files")
    expected = {
        "episode_count": len(rows),
        "public_ids": ids,
        "demonstration_counts": [len(row["train"]) for row in rows],
        "query_counts": [len(row["test"]) for row in rows],
        "label_count": sum(len(row[split]) for row in rows for split in ("train", "test")),
        "directions_exercised": sorted({row["direction"] for row in rows}),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise ValueError(f"verification report field {key} differs from replay")
    if report.get("schema") != "864eaaac6503-parametric-rotation-prototype-v2":
        raise ValueError("verification report schema mismatch")
    if report.get("training_admitted") is not False:
        raise ValueError("prototype report must not claim training admission")
    return {"verified_episodes": len(rows), "public_ids": ids}


def source_hashes():
    """Hash the exact prototype and reference support files used by this run."""
    runtime = Path(sys.modules["arc_repl.racket_bridge"].__file__).resolve().parent
    files = [Path(__file__).resolve(), runtime / "racket_bridge.py",
             runtime / "racket_prelude/arc-prelude.rkt",
             Path(sys.modules["reviewer_support"].__file__).resolve()]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--direction", choices=tuple(PROGRAMS), default=None,
                        help="optional explicit setting; omitted selects once from each seed")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=QUERY_COUNT)
    args = parser.parse_args(argv)
    out = args.out.resolve()
    with open_bridge() as bridge:
        episodes = [build_episode(bridge, seed=seed, direction=args.direction,
                                  n_train=args.demos, n_test=args.queries)
                    for seed in args.seeds]
        report = write_batch(episodes, out, bridge)
        verified = verify_batch(out, bridge)
    print(json.dumps({"out": str(out), "episodes": report["episode_count"],
                      "directions": report["directions_exercised"],
                      "public_ids": verified["public_ids"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
