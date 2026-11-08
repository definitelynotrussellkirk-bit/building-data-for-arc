#!/usr/bin/env python3
"""Source-bound parametric episodes for the aligned two-panel occupancy rule.

This is a proposed authoring prototype only.  It leaves the canonical
``a178821cc6bf`` generator and every approval decision unchanged.
"""
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

# Bind imports and data to this source tree, never cwd or a predecessor.
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
TASK_ID = "a178821cc6bf"
DEFAULT_MARKED_STATE = "both_zero"
PROGRAMS = {
    "both_zero": """(rule! (lambda (g)
         (let ((h (rows g))
               (w 4))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (and (zero? (at g r c)) (zero? (at g r (+ c 4)))) 4 0))))))""",
    "both_nonzero": """(rule! (lambda (g)
         (let ((h (rows g))
               (w 4))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (and (not (zero? (at g r c)))
                                    (not (zero? (at g r (+ c 4)))))
                               4
                               0))))))""",
}
RULE_WRAPPER = "(define (rule! f) f)"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
DEMO_HEIGHTS = (3, 4, 6, 9, 13, 18)
QUERY_HEIGHTS = (8, 15, 23, 30)
LIMITATIONS = [
    "Proposed prototype only; canonical generator and approval are unchanged.",
    "Only the marked aligned occupancy state is varied.",
    "The source rule fixes two adjacent four-column panels, so lawful stress is 30x8 rather than 30x30.",
    "Episodes contain 2..6 demonstrations and exactly four private queries.",
    "Identifiability is checked only against the two declared settings.",
    "Evidence is finite and source-bound, not proof over every seed.",
]


def open_bridge():
    """Open the provided Racket runtime and install the narrow rule! wrapper."""
    bridge = RacketBridge()
    try:
        bridge.eval_text(RULE_WRAPPER)
    except BaseException:
        bridge.shutdown()
        raise
    return bridge


def execute(bridge, marked_state, grids):
    """Execute one exact declared Racket rule for all supplied grids."""
    if marked_state not in PROGRAMS:
        raise ValueError(f"marked_state must be one of {tuple(PROGRAMS)}")
    bridge.eval_text(f"(define prototype-rule {PROGRAMS[marked_state]})")
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


def occupancy_counts(grid):
    """Count aligned zero/nonzero states in a source-shaped 4+4 panel grid."""
    grid = normalize_grid(grid)
    if any(len(row) != 8 for row in grid):
        raise ValueError("aligned-state inputs must have exactly eight columns")
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    for row in grid:
        for col in range(4):
            key = ("1" if row[col] != 0 else "0") + ("1" if row[col + 4] != 0 else "0")
            counts[key] += 1
    return counts


def _state_sequence(size, rng):
    """Cover every state, then bias toward content-rich cells for real stress."""
    if size < 4:
        raise ValueError("state canvas is too small")
    states = ["00", "10", "01", "11"]
    while len(states) < min(size, 16):
        states.extend(("00", "10", "01", "11"))
    dense_cycle = ("11", "11", "10", "01")
    while len(states) < size:
        states.append(dense_cycle[(len(states) - 16) % len(dense_cycle)])
    states = states[:size]
    rng.shuffle(states)
    return states


def _panel_grid(seed, role, index, height):
    """Draw a deterministic, setting-neutral pair of four-column panels."""
    rng = random.Random(f"{TASK_ID}|{seed}|{role}|{index}|{height}")
    palette = [value for value in range(1, 10) if value != 4]
    left_palette = rng.sample(palette, 3)
    right_palette = rng.sample(palette, 3)
    # Alternate same/different object colors so color equality cannot substitute
    # for the intended zero/nonzero relation.
    if index % 2 == 0:
        right_palette[0] = left_palette[0]
    states = _state_sequence(height * 4, rng)
    grid = [[0] * 8 for _ in range(height)]
    for flat_index, state in enumerate(states):
        row, col = divmod(flat_index, 4)
        if state[0] == "1":
            grid[row][col] = left_palette[(row * 3 + col + index) % len(left_palette)]
        if state[1] == "1":
            grid[row][col + 4] = right_palette[(row + col * 2 + index) % len(right_palette)]
    return grid


def _sample_grids(seed, n_train, n_test):
    _validate_request(seed, n_train, n_test)
    grids = [
        _panel_grid(seed, "demo", index, DEMO_HEIGHTS[index])
        for index in range(n_train)
    ]
    grids.extend(
        _panel_grid(seed, "query", index, QUERY_HEIGHTS[index])
        for index in range(n_test)
    )
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in grids}
    if len(fingerprints) != len(grids):
        raise ValueError("sampler produced duplicate visible inputs")
    return grids


def python_transform(grid, marked_state):
    """Compute a claim locally; qualification replays every label in Racket."""
    grid = normalize_grid(grid)
    if any(len(row) != 8 for row in grid):
        raise ValueError("aligned-state inputs must have exactly eight columns")
    if marked_state not in PROGRAMS:
        raise ValueError(f"marked_state must be one of {tuple(PROGRAMS)}")
    output = []
    for row in grid:
        values = []
        for col in range(4):
            left_nonzero = row[col] != 0
            right_nonzero = row[col + 4] != 0
            marked = (
                (not left_nonzero and not right_nonzero)
                if marked_state == "both_zero"
                else (left_nonzero and right_nonzero)
            )
            values.append(4 if marked else 0)
        output.append(values)
    return output


def build_claimed_episode(*, seed, marked_state, n_train, n_test=QUERY_COUNT):
    """Build deterministic Python claims for an independent worker to replay."""
    _validate_request(seed, n_train, n_test)
    if marked_state not in PROGRAMS:
        raise ValueError(f"marked_state must be one of {tuple(PROGRAMS)}")
    grids = _sample_grids(seed, n_train, n_test)
    pairs = [
        {"input": grid, "output": python_transform(grid, marked_state)}
        for grid in grids
    ]
    return {"train": pairs[:n_train], "test": pairs[n_train:]}


def assess_episode(bridge, episode):
    """Execute every declared rival on the full episode; infer only from demos."""
    pairs = episode["train"] + episode["test"]
    split = len(episode["train"])
    rivals = {}
    for marked_state in PROGRAMS:
        outputs = execute(bridge, marked_state, [pair["input"] for pair in pairs])
        matches = [actual == pair["output"] for actual, pair in zip(outputs, pairs)]
        rivals[marked_state] = {
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


def build_episode(bridge, *, seed, marked_state=None, n_train=3, n_test=QUERY_COUNT):
    """Choose one hidden setting once, then execute all labels in Racket."""
    _validate_request(seed, n_train, n_test)
    selected = random.Random(f"{TASK_ID}|{seed}|setting").choice(tuple(PROGRAMS))
    if marked_state is not None:
        if marked_state not in PROGRAMS:
            raise ValueError(f"marked_state must be one of {tuple(PROGRAMS)}")
        selected = marked_state
    grids = _sample_grids(seed, n_train, n_test)
    outputs = execute(bridge, selected, grids)
    pairs = [{"input": grid, "output": output} for grid, output in zip(grids, outputs)]
    program = PROGRAMS[selected]
    episode = {
        "seed": seed,
        "marked_state": selected,
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
    """Project exact visible bytes, excluding settings, programs, and query labels."""
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
    """Reveal one query turn without count hints, future inputs, or answers."""
    test = episode.get("test")
    if type(test) is not list or type(query_index) is not int or not 0 <= query_index < len(test):
        raise ValueError("query_index must name one stored query")
    if query_index == 0:
        return public_challenge(episode, query_indices=[0])
    return deepcopy({"test": [{"input": test[query_index]["input"]}]})


def verify_episode(episode, bridge):
    """Freshly replay all labels and the demonstration-only rival certificate."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    _validate_request(
        episode.get("seed"),
        len(train) if type(train) is list else None,
        len(test) if type(test) is list else None,
    )
    marked_state = episode.get("marked_state")
    if marked_state not in PROGRAMS:
        raise ValueError("stored marked_state is outside the declared family")
    program = PROGRAMS[marked_state]
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
    outputs = execute(bridge, marked_state, [pair["input"] for pair in pairs])
    if outputs != [pair["output"] for pair in pairs]:
        raise ValueError("stored labels differ from fresh Racket execution")
    fresh = assess_episode(bridge, episode)
    if fresh.get("demo_survivors") != [marked_state]:
        raise ValueError("demonstrations do not uniquely identify the selected setting")
    if episode.get("rival_check") != fresh:
        raise ValueError("stored rival certificate differs from fresh demo-only replay")
    return True


def source_hashes():
    """Hash the exact local sources and runtime support used by this prototype."""
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
    """Atomically write exact public files and private replay evidence."""
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
    witness = [[0, 1, 0, 2, 0, 0, 3, 4]]
    witness_outputs = {
        key: execute(bridge, key, [witness])[0]
        for key in PROGRAMS
    }
    report = {
        "schema": f"{TASK_ID}-aligned-state-parametric-v1",
        "status": "proposed prototype; not production approval",
        "training_admitted": False,
        "episode_count": len(planned),
        "public_ids": [row[0] for row in planned],
        "demonstration_counts": [len(row[2]["train"]) for row in planned],
        "query_counts": [len(row[2]["test"]) for row in planned],
        "label_count": sum(len(row[2][split]) for row in planned for split in ("train", "test")),
        "settings_exercised": sorted({row[2]["marked_state"] for row in planned}),
        "parameter": {
            "name": "marked_state",
            "allowed": list(PROGRAMS),
            "original_default": DEFAULT_MARKED_STATE,
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
            "distinct": witness_outputs["both_zero"] != witness_outputs["both_nonzero"],
        },
        "limitations": LIMITATIONS,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".aligned-state-parametric-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        private_rows = []
        for public_id, raw, episode in planned:
            (stage / "public" / f"{public_id}.json").write_bytes(raw)
            private_rows.append(dict(deepcopy(episode), public_id=public_id))
        (stage / "private" / "episodes.json").write_text(
            json.dumps(private_rows, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (stage / "private" / "verification.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        stage.rename(out)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return report


def verify_batch(path, bridge):
    """Replay a written batch and bind every file to exact visible bytes."""
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
        "settings_exercised": sorted({row["marked_state"] for row in rows}),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise ValueError(f"verification report field {key} differs from replay")
    if report.get("schema") != f"{TASK_ID}-aligned-state-parametric-v1":
        raise ValueError("verification report schema mismatch")
    if report.get("training_admitted") is not False:
        raise ValueError("prototype report must not claim training admission")
    return {"verified_episodes": len(rows), "public_ids": ids}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--marked-state", choices=tuple(PROGRAMS), default=None)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=QUERY_COUNT)
    args = parser.parse_args(argv)
    out = args.out.resolve()
    with open_bridge() as bridge:
        episodes = [
            build_episode(
                bridge,
                seed=seed,
                marked_state=args.marked_state,
                n_train=args.demos,
                n_test=args.queries,
            )
            for seed in args.seeds
        ]
        report = write_batch(episodes, out, bridge)
        verified = verify_batch(out, bridge)
    print(json.dumps({
        "out": str(out),
        "episodes": report["episode_count"],
        "settings": report["settings_exercised"],
        "public_ids": verified["public_ids"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
