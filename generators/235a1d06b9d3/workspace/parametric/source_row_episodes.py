#!/usr/bin/env python3
"""Source-bound episodes varying which copied row supplies the derived mask."""
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

for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break

from reviewer_support import (  # noqa: E402
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status  # noqa: E402

ROOT = find_root(__file__)
TASK_ID = "235a1d06b9d3"
DEFAULT_SOURCE_ROW = "row0"
PROGRAMS = {
    "row0": """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg (at g 2 1)))
             (list (map (lambda (c) (at g 0 c)) (range 0 w))
                   (map (lambda (c) (at g 1 c)) (range 0 w))
                   (map (lambda (c) (if (= (at g 0 c) bg) bg 6)) (range 0 w)))))))""",
    "row1": """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg (at g 2 1)))
             (list (map (lambda (c) (at g 0 c)) (range 0 w))
                   (map (lambda (c) (at g 1 c)) (range 0 w))
                   (map (lambda (c) (if (= (at g 1 c) bg) bg 6)) (range 0 w)))))))""",
}
RULE_WRAPPER = "(define (rule! f) f)"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
DEMO_SHAPES = ((3, 5), (5, 8), (8, 11), (12, 15), (18, 20), (22, 24))
QUERY_SHAPES = ((10, 14), (16, 20), (24, 27), (30, 30))
LIMITATIONS = [
    "Proposed prototype only; canonical generator and approval are unchanged.",
    "Only the visible source row for the derived mask is varied.",
    "The background anchor remains input cell (2,1) for both settings.",
    "Episodes contain 2..6 demonstrations and exactly four private queries.",
    "Large-height inputs stress ignored context; both rules still emit exactly three rows.",
    "Identifiability is checked only against the two declared settings.",
]


def open_bridge():
    bridge = RacketBridge()
    try:
        bridge.eval_text(RULE_WRAPPER)
    except BaseException:
        bridge.shutdown()
        raise
    return bridge


def execute(bridge, source_row, grids):
    if source_row not in PROGRAMS:
        raise ValueError(f"source_row must be one of {tuple(PROGRAMS)}")
    bridge.eval_text(f"(define prototype-rule {PROGRAMS[source_row]})")
    outputs = []
    for grid in grids:
        bridge.define_grid("prototype-input", normalize_grid(grid))
        outputs.append(normalize_grid(bridge.eval_text("(prototype-rule prototype-input)")))
    return outputs


def _validate_request(seed, n_train, n_test):
    if type(seed) is not int or not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed must be an exact integer in [0, {MAX_SEED}]")
    if type(n_train) is not int or not MIN_DEMOS <= n_train <= MAX_DEMOS:
        raise ValueError(f"n_train must be an exact integer in [{MIN_DEMOS}, {MAX_DEMOS}]")
    if type(n_test) is not int or n_test != QUERY_COUNT:
        raise ValueError(f"n_test must be the exact integer {QUERY_COUNT}")


def _balanced_mask(width, phase, stride):
    mask = [((col * stride + phase) % 7) < 3 for col in range(width)]
    if sum(mask) < 2:
        mask[0] = mask[-1] = True
    if width - sum(mask) < 2:
        mask[0] = mask[-1] = False
    return mask


def _colors(rng, index):
    if index % 2 == 0:
        background = 0
    else:
        background = rng.choice([value for value in range(1, 10) if value != 6])
    relation = index % 4
    if relation == 3:
        signal = 6
        cue = rng.choice([value for value in range(10) if value not in {background, 6}])
    else:
        signal = rng.choice([value for value in range(10) if value not in {background, 6}])
        if relation == 0:
            cue = signal
        elif relation == 2:
            cue = 6
        else:
            cue = rng.choice(
                [value for value in range(10) if value not in {background, signal, 6}]
            )
    return background, signal, cue


def sample_grid(*, seed, role, index, height, width):
    """Build a deterministic source-shaped scene with distinct row masks."""
    if type(seed) is not int or type(index) is not int:
        raise ValueError("seed and index must be exact integers")
    if type(height) is not int or type(width) is not int:
        raise ValueError("height and width must be exact integers")
    if not (3 <= height <= 30 and 5 <= width <= 30):
        raise ValueError("source-row canvases must be 3..30 by 5..30")
    rng = random.Random(f"{TASK_ID}|{seed}|{role}|{index}|{height}x{width}")
    background, signal, cue = _colors(rng, index + (0 if role == "demo" else 7))
    row0_mask = _balanced_mask(width, rng.randrange(7), 2 + (index % 3))
    shift = 1 + (index % max(1, width - 1))
    row1_mask = [not row0_mask[(col + shift) % width] for col in range(width)]
    row1_mask[1] = True
    if row1_mask == row0_mask:
        row1_mask[-1] = not row1_mask[-1]
    grid = [[background for _ in range(width)] for _ in range(height)]
    grid[0] = [signal if marked else background for marked in row0_mask]
    grid[1] = [signal if marked else background for marked in row1_mask]
    grid[1][0] = cue
    for row in range(2, height):
        grid[row][0] = cue if row % 2 == 1 else background
    info = analyze_scene(grid)
    if info["errors"]:
        raise AssertionError(info["errors"])
    if info["row0_mask"] == info["row1_mask"]:
        raise AssertionError("sampler failed to distinguish source-row masks")
    if grid[1][1] == background or grid[2][1] != background:
        raise AssertionError("sampler failed to expose the protected background anchor")
    return grid


def analyze_scene(grid):
    """Recover the bounded source grammar and the two candidate masks."""
    try:
        grid = normalize_grid(grid)
    except ValueError as error:
        return {"errors": [str(error)]}
    height, width = len(grid), len(grid[0])
    errors = []
    if height < 3 or width < 5:
        errors.append("scene must be at least 3x5")
        return {"errors": errors, "height": height, "width": width}
    background = grid[2][1]
    if background == 6:
        errors.append("background must differ from marker color 6")
    row0_nonbackground = [value for value in grid[0] if value != background]
    signals = set(row0_nonbackground)
    signal = next(iter(signals)) if len(signals) == 1 else None
    if signal is None:
        errors.append("row 0 must use exactly one signal color")
    if len(row0_nonbackground) < 2 or width - len(row0_nonbackground) < 2:
        errors.append("row 0 must contain at least two signal and two background cells")
    cue = grid[1][0]
    if cue == background:
        errors.append("cue must differ from the background")
    allowed_row1 = {background}
    if signal is not None:
        allowed_row1.add(signal)
    if any(value not in allowed_row1 for value in grid[1][1:]):
        errors.append("row 1 distractors must use the row-0 signal color")
    if signal is not None and grid[1][1] != signal:
        errors.append("row 1 column 1 must be a signal distractor")
    for row in range(2, height):
        expected_left = cue if row % 2 == 1 else background
        if grid[row][0] != expected_left:
            errors.append(f"row {row} has the wrong alternating cue")
            break
        if any(value != background for value in grid[row][1:]):
            errors.append(f"row {row} has content outside the cue column")
            break
    row0_mask = [value != background for value in grid[0]]
    row1_mask = [value != background for value in grid[1]]
    if row0_mask == row1_mask:
        errors.append("candidate source-row masks must differ")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "background": background,
        "signal": signal,
        "cue": cue,
        "row0_mask": row0_mask,
        "row1_mask": row1_mask,
        "row1_decoy_count": sum(value == signal for value in grid[1][1:]) if signal is not None else 0,
    }


def _sample_grids(seed, n_train, n_test):
    _validate_request(seed, n_train, n_test)
    grids = [
        sample_grid(seed=seed, role="demo", index=index, height=height, width=width)
        for index, (height, width) in enumerate(DEMO_SHAPES[:n_train])
    ]
    grids.extend(
        sample_grid(seed=seed, role="query", index=index, height=height, width=width)
        for index, (height, width) in enumerate(QUERY_SHAPES[:n_test])
    )
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in grids}
    if len(fingerprints) != len(grids):
        raise ValueError("sampler produced duplicate visible inputs")
    return grids


def python_transform(grid, source_row):
    grid = normalize_grid(grid)
    if source_row not in PROGRAMS:
        raise ValueError(f"source_row must be one of {tuple(PROGRAMS)}")
    info = analyze_scene(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    source_index = 0 if source_row == "row0" else 1
    background = info["background"]
    return [
        list(grid[0]),
        list(grid[1]),
        [background if value == background else 6 for value in grid[source_index]],
    ]


def build_claimed_episode(*, seed, source_row, n_train, n_test=QUERY_COUNT):
    _validate_request(seed, n_train, n_test)
    if source_row not in PROGRAMS:
        raise ValueError(f"source_row must be one of {tuple(PROGRAMS)}")
    grids = _sample_grids(seed, n_train, n_test)
    pairs = [{"input": grid, "output": python_transform(grid, source_row)} for grid in grids]
    return {"train": pairs[:n_train], "test": pairs[n_train:]}


def assess_episode(bridge, episode):
    pairs = episode["train"] + episode["test"]
    split = len(episode["train"])
    rivals = {}
    for source_row in PROGRAMS:
        outputs = execute(bridge, source_row, [pair["input"] for pair in pairs])
        matches = [actual == pair["output"] for actual, pair in zip(outputs, pairs)]
        rivals[source_row] = {
            "outputs": outputs,
            "demo_matches": matches[:split],
            "query_matches": matches[split:],
            "demo_consistent": all(matches[:split]),
            "full_episode_consistent": all(matches),
        }
    survivors = [key for key, value in rivals.items() if value["demo_consistent"]]
    return {
        "rivals": rivals,
        "demo_survivors": survivors,
        "identifiable_from_demos": len(survivors) == 1,
    }


def build_episode(bridge, *, seed, source_row=None, n_train=3, n_test=QUERY_COUNT):
    _validate_request(seed, n_train, n_test)
    selected = random.Random(f"{TASK_ID}|{seed}|source-row").choice(tuple(PROGRAMS))
    if source_row is not None:
        if source_row not in PROGRAMS:
            raise ValueError(f"source_row must be one of {tuple(PROGRAMS)}")
        selected = source_row
    grids = _sample_grids(seed, n_train, n_test)
    outputs = execute(bridge, selected, grids)
    pairs = [{"input": grid, "output": output} for grid, output in zip(grids, outputs)]
    program = PROGRAMS[selected]
    episode = {
        "seed": seed,
        "source_row": selected,
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }
    episode["rival_check"] = assess_episode(bridge, episode)
    if episode["rival_check"]["demo_survivors"] != [selected]:
        raise ValueError("draw does not distinguish the selected setting from demonstrations")
    return episode


def public_challenge(episode, query_indices=None):
    train, test = episode.get("train"), episode.get("test")
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
    return json.loads(public_challenge_bytes(challenge))


def sequential_turn(episode, query_index):
    test = episode.get("test")
    if type(test) is not list or type(query_index) is not int or not 0 <= query_index < len(test):
        raise ValueError("query_index must name one stored query")
    if query_index == 0:
        return public_challenge(episode, query_indices=[0])
    return deepcopy({"test": [{"input": test[query_index]["input"]}]})


def verify_episode(episode, bridge):
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    _validate_request(
        episode.get("seed"),
        len(train) if type(train) is list else None,
        len(test) if type(test) is list else None,
    )
    source_row = episode.get("source_row")
    if source_row not in PROGRAMS:
        raise ValueError("stored source_row is outside the declared family")
    program = PROGRAMS[source_row]
    if episode.get("program") != program:
        raise ValueError("stored program differs from the selected setting")
    if episode.get("program_sha256") != hashlib.sha256(program.encode()).hexdigest():
        raise ValueError("stored program hash differs from the selected setting")
    public_challenge_bytes(public_challenge(episode))
    pairs = train + test
    seen = set()
    for pair in pairs:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("private episode must contain complete input/output pairs")
        key = json.dumps(pair["input"], separators=(",", ":"))
        if key in seen:
            raise ValueError("duplicate visible input within episode")
        seen.add(key)
        if analyze_scene(pair["input"])["errors"]:
            raise ValueError("stored input is outside the declared source-row grammar")
    outputs = execute(bridge, source_row, [pair["input"] for pair in pairs])
    if outputs != [pair["output"] for pair in pairs]:
        raise ValueError("stored labels differ from fresh Racket execution")
    fresh = assess_episode(bridge, episode)
    if fresh.get("demo_survivors") != [source_row]:
        raise ValueError("demonstrations do not uniquely identify the selected setting")
    if episode.get("rival_check") != fresh:
        raise ValueError("stored rival certificate differs from fresh demo-only replay")
    return True


def source_hashes():
    runtime = Path(sys.modules["arc_repl.racket_bridge"].__file__).resolve().parent
    paths = [
        Path(__file__).resolve(),
        runtime / "racket_bridge.py",
        runtime / "racket_prelude/arc-prelude.rkt",
        Path(sys.modules["reviewer_support"].__file__).resolve(),
    ]
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def write_batch(episodes, out, bridge):
    if type(episodes) is not list or not episodes:
        raise ValueError("batch must contain at least one episode")
    out = Path(out)
    if out.exists():
        raise ValueError("output path already exists")
    planned = []
    for episode in episodes:
        verify_episode(episode, bridge)
        public = public_challenge(episode)
        planned.append((public_challenge_id(public), public_challenge_bytes(public), episode))
    planned.sort(key=lambda row: row[0])
    if len({row[0] for row in planned}) != len(planned):
        raise ValueError("duplicate visible payload in batch")
    witness = sample_grid(seed=0, role="witness", index=0, height=8, width=11)
    witness_outputs = {key: execute(bridge, key, [witness])[0] for key in PROGRAMS}
    report = {
        "schema": f"{TASK_ID}-source-row-parametric-v1",
        "status": "proposed prototype; not production approval",
        "training_admitted": False,
        "episode_count": len(planned),
        "public_ids": [row[0] for row in planned],
        "demonstration_counts": [len(row[2]["train"]) for row in planned],
        "query_counts": [len(row[2]["test"]) for row in planned],
        "label_count": sum(len(row[2][split]) for row in planned for split in ("train", "test")),
        "settings_exercised": sorted({row[2]["source_row"] for row in planned}),
        "parameter": {
            "name": "source_row",
            "allowed": list(PROGRAMS),
            "original_default": DEFAULT_SOURCE_ROW,
            "input_constraints_depend_on_setting": False,
        },
        "programs": {
            key: {"text": value, "sha256": hashlib.sha256(value.encode()).hexdigest()}
            for key, value in PROGRAMS.items()
        },
        "source_sha256": source_hashes(),
        "racket_runtime": racket_runtime_status(),
        "witness": {
            "input": witness,
            "outputs": witness_outputs,
            "distinct": witness_outputs["row0"] != witness_outputs["row1"],
        },
        "limitations": LIMITATIONS,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".source-row-parametric-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        private_rows = []
        for public_id, raw, episode in planned:
            (stage / "public" / f"{public_id}.json").write_bytes(raw)
            private_rows.append(dict(deepcopy(episode), public_id=public_id))
        (stage / "private/episodes.json").write_text(
            json.dumps(private_rows, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        (stage / "private/verification.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        stage.rename(out)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return report


def verify_batch(path, bridge):
    path = Path(path)
    try:
        rows = json.loads((path / "private/episodes.json").read_text(encoding="utf-8"))
        report = json.loads((path / "private/verification.json").read_text(encoding="utf-8"))
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
        if (path / "public" / f"{public_id}.json").read_bytes() != public_challenge_bytes(public):
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
        "settings_exercised": sorted({row["source_row"] for row in rows}),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise ValueError(f"verification report field {key} differs from replay")
    if report.get("schema") != f"{TASK_ID}-source-row-parametric-v1":
        raise ValueError("verification report schema mismatch")
    if report.get("training_admitted") is not False:
        raise ValueError("prototype report must not claim training admission")
    return {"verified_episodes": len(rows), "public_ids": ids}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--source-row", choices=tuple(PROGRAMS), default=None)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=QUERY_COUNT)
    args = parser.parse_args(argv)
    with open_bridge() as bridge:
        episodes = [
            build_episode(
                bridge,
                seed=seed,
                source_row=args.source_row,
                n_train=args.demos,
                n_test=args.queries,
            )
            for seed in args.seeds
        ]
        report = write_batch(episodes, args.out.resolve(), bridge)
        verified = verify_batch(args.out.resolve(), bridge)
    print(json.dumps({
        "out": str(args.out.resolve()),
        "episodes": report["episode_count"],
        "settings": report["settings_exercised"],
        "public_ids": verified["public_ids"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
