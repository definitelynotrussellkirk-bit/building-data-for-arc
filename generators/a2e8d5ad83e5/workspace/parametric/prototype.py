#!/usr/bin/env python3
"""Proposed minimum-area variants of a2e8d5ad83e5, labelled only by Racket.

The canonical default remains byte-identical. Input draws and teaching retries
are independent of the selected threshold. No approval or admission is granted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path, find_root, load_selected_generator,
    public_challenge_bytes, public_challenge_id,
)

TASK_ID = "a2e8d5ad83e5"
VERSION = "minimum-anchor-area-v1"
THRESHOLDS = (4, 9, 16)
CANONICAL_SHA256 = "1f5c2de6cd5bf032069cd1890ccf1b1be00cf39c278b7fa9014d7af40f9397bc"
GENERATOR_SHA256 = "f97e068992acc9e9131f4b4c9739430fee64bfab35d6b3c6eb0ac16b0a4507e6"
CANONICAL_BRANCH = "(>= (obj-size o) 4)"
MAX_ATTEMPTS = 64
DEMO_PROFILES = (
    "mixed_sizes", "large_same_color_pair", "large_same_row", "large_same_col",
    "even_size_pair", "mixed_sizes", "edge_square", "dense_noise",
)
QUERY_PROFILES = (
    "mixed_sizes", "even_size_pair", "large_same_col", "large_same_color_pair",
    "large_same_row", "mixed_sizes", "same_color_pair", "edge_square",
)


def _sha(payload):
    return hashlib.sha256(payload.encode() if isinstance(payload, str) else payload).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"minimum_anchor_area"}:
        raise ValueError("Declare exactly minimum_anchor_area=4|9|16")
    area = settings["minimum_anchor_area"]
    if type(area) is not int or area not in THRESHOLDS:
        raise ValueError("minimum_anchor_area must be an exact integer: 4, 9 or 16")
    return area


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid dimensions must be 1..30")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [row[:] for row in value]


def canonical_source():
    sources = set()
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError("Expected one exact canonical source for the selected task")
    source = sources.pop()
    if (type(source) is not str or _sha(source) != CANONICAL_SHA256
            or source.count(CANONICAL_BRANCH) != 1):
        raise ValueError("Canonical authority changed; re-review the prototype")
    return source


def materialize_rule(minimum_anchor_area=4):
    area = _settings({"minimum_anchor_area": minimum_anchor_area})
    source = canonical_source()
    if area == 4:
        return source
    return source.replace(CANONICAL_BRANCH, f"(>= (obj-size o) {area})", 1)


def execute_rule_many(source, grids, *, bridge=None):
    """Execute only a declared program; reject numeric coercions before Racket."""
    canonical = canonical_source()
    programs = {canonical.replace(CANONICAL_BRANCH, f"(>= (obj-size o) {v})", 1)
                for v in THRESHOLDS}
    if type(source) is not str or source not in programs:
        raise ValueError("Program is not a pinned threshold variant")
    inputs = [_grid(grid) for grid in grids]
    if not inputs:
        return []
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("Pinned program is not one rule expression")
    rule = source[len(prefix):-1]
    literals = ["(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in g) + ")"
                for g in inputs]
    expression = f"(map {rule} '({' '.join(literals)}))"
    if bridge is None:
        with RacketBridge() as owned:
            outputs = owned.eval_text(expression)
    else:
        outputs = bridge.eval_text(expression)
    if type(outputs) is not list or len(outputs) != len(inputs):
        raise ValueError("Racket returned the wrong number of grids")
    return [_grid(output) for output in outputs]


def execute_rule(source, grid, *, bridge=None):
    return execute_rule_many(source, [grid], bridge=bridge)[0]


def _large_pair(generator, seed, slot, profile):
    """Two qualifying 4x4 anchors, including collisions at threshold 16."""
    rng = random.Random(int(_sha(f"{VERSION}:large:{seed}:{slot}:{profile}"), 16))
    height, width = rng.randint(20, 26), rng.randint(20, 26)
    if profile == "large_same_row":
        row = rng.randint(1, height - 5)
        boxes = [(row, 1, 4), (row, width - 5, 4)]
    elif profile == "large_same_col":
        col = rng.randint(1, width - 5)
        boxes = [(1, col, 4), (height - 5, col, 4)]
    else:
        boxes = generator._random_boxes(rng, height, width, [4, 4], distinct_centers=True)
    colors = rng.sample(list(range(1, 10)), 2)
    if profile == "large_same_color_pair":
        colors[1] = colors[0]
    grid = [[0] * width for _ in range(height)]
    for (row, col, size), color in zip(boxes, colors):
        for rr in range(row, row + size):
            for cc in range(col, col + size):
                grid[rr][cc] = color
    generator._paint_noise(rng, grid, max(16, round(height * width * 0.08)))
    return grid


def _sample(generator, seed, slot, profile):
    if profile.startswith("large_"):
        grid = _large_pair(generator, seed, slot, profile)
    else:
        grid = generator.generate(seed, slot, difficulty="medium", scene_profile=profile)
    grid = _grid(grid)
    errors = generator.self_check(grid)
    if errors:
        raise ValueError(f"Sampler produced an invalid scene: {errors}")
    return grid


def source_bindings():
    home = Path(__file__).resolve().parent
    return {
        "generator_sha256": GENERATOR_SHA256,
        "canonical_program_sha256": CANONICAL_SHA256,
        "prototype_sha256": _sha(Path(__file__).read_bytes()),
        "adapter_sha256": _sha((home / "adapter.py").read_bytes()),
        "contract_sha256": _sha((home / "promotion.json").read_bytes()),
    }


def generate_episode(seed, settings=None, demos=3, queries=4, input_seed=None, bridge=None):
    """Make one identifiable episode, with independent demo and query counts.

    A joint first-demo test is the only teaching retry. It compares all three
    candidate outputs, independent of the chosen setting. Queries are never used
    to select a setting or eliminate a rival. Every retained label is Racket's.
    """
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 1, 8)
    _integer(queries, "queries", 1, 8)
    input_seed = seed if input_seed is None else _integer(input_seed, "input_seed", 0, 2**63 - 1)
    settings = {"minimum_anchor_area": THRESHOLDS[seed % 3]} if settings is None else dict(settings) if type(settings) is dict else settings
    selected = _settings(settings)
    generator, _, digest = load_selected_generator(TASK_ID, root=find_root(__file__))
    if digest != GENERATOR_SHA256:
        raise ValueError("Production sampler changed; re-review this source-bound prototype")
    if bridge is None:
        with RacketBridge() as owned:
            return generate_episode(seed, settings, demos, queries, input_seed, owned)

    programs = {area: materialize_rule(area) for area in THRESHOLDS}
    seen, inputs, attempts = set(), [], []

    def draw(profile, base, *, teaching=False):
        for attempt in range(MAX_ATTEMPTS):
            try:
                grid = _sample(generator, input_seed, base + attempt, profile)
            except RuntimeError:
                # A bounded placement rejection is not a semantic proof.
                continue
            key = _json(grid)
            if key in seen:
                continue
            if teaching:
                alternatives = [execute_rule(programs[area], grid, bridge=bridge) for area in THRESHOLDS]
                if len({_json(output) for output in alternatives}) != len(THRESHOLDS):
                    continue
            seen.add(key)
            inputs.append(grid)
            attempts.append(attempt + 1)
            return
        raise ValueError(f"No distinct identifiable {profile} draw in {MAX_ATTEMPTS} attempts; no partial episode")

    for index, profile in enumerate(DEMO_PROFILES[:demos]):
        draw(profile, index * MAX_ATTEMPTS, teaching=index == 0)
    # This table is computed exclusively from demonstration inputs.
    demo_outputs = {area: execute_rule_many(programs[area], inputs, bridge=bridge) for area in THRESHOLDS}
    chosen_demos = demo_outputs[selected]
    survivors = [area for area in THRESHOLDS if demo_outputs[area] == chosen_demos]
    if survivors != [selected]:
        raise ValueError("Demonstrations do not uniquely identify the selected threshold")
    rejected = []
    for area in THRESHOLDS:
        if area != selected:
            witness = next(i for i in range(demos) if demo_outputs[area][i] != chosen_demos[i])
            rejected.append({"settings": {"minimum_anchor_area": area}, "demo_index": witness})
    for index, profile in enumerate(QUERY_PROFILES[:queries]):
        draw(profile, 10000 + index * MAX_ATTEMPTS)
    query_outputs = execute_rule_many(programs[selected], inputs[demos:], bridge=bridge)
    pairs = [{"input": grid, "output": output}
             for grid, output in zip(inputs, chosen_demos + query_outputs)]
    runtime = bridge.runtime_identity
    return {
        "schema": "a2e8d5ad83e5-threshold-episode-v1",
        "status": "proposed_unapproved", "training_admitted": False,
        "task_id": TASK_ID, "seed": seed, "input_seed": input_seed,
        "settings": {"minimum_anchor_area": selected},
        "program_solution": programs[selected], "program_sha256": _sha(programs[selected]),
        "train": pairs[:demos], "test": pairs[demos:],
        "input_profiles": {"train": list(DEMO_PROFILES[:demos]), "test": list(QUERY_PROFILES[:queries])},
        "draw_attempts": attempts, "sources": source_bindings(),
        "racket": {key: runtime[key] for key in (
            "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
            "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"
        ) if key in runtime},
        "certificate": {
            "scope": "Three declared minimum-area settings only; no all-program claim",
            "selection_uses": "demonstrations_only",
            "survivors": [{"minimum_anchor_area": area} for area in survivors],
            "rejected": rejected,
            "queries": [{"index": i, "surviving_setting_agrees": True} for i in range(queries)],
        },
    }


def export_episodes(episodes, out):
    """Serialize a precomputed batch; validation here does not replay labels.

    All semantic generation happens above. Validate the complete batch before
    creating the destination, and write the completion manifest last.
    """
    episodes = list(episodes)
    if not episodes:
        raise ValueError("Export needs at least one episode")
    prepared = {}
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        for split in ("train", "test"):
            for pair in episode[split]:
                _grid(pair["output"])
        keys = [_json(pair["input"]) for split in ("train", "test") for pair in episode[split]]
        if len(keys) != len(set(keys)):
            raise ValueError("All demonstration and query inputs must be distinct")
        if public_id in prepared:
            raise ValueError("Duplicate visible challenge in batch")
        # Serializing private metadata now avoids publishing a partial batch on
        # non-JSON hidden values; hidden data never participates in the public ID.
        private = (_json(episode) + "\n").encode("utf-8")
        prepared[public_id] = (payload, private)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    inventory = []
    for public_id in sorted(prepared):
        payload, private = prepared[public_id]
        (out / "public" / f"{public_id}.json").write_bytes(payload)
        (out / "private" / f"{public_id}.json").write_bytes(private)
        inventory.append({"public_id": public_id, "public_sha256": _sha(payload), "private_sha256": _sha(private)})
    manifest = {"schema": "a2e8d5ad83e5-threshold-export-v1", "status": "proposed_unapproved",
                "training_admitted": False, "episodes": len(prepared), "files": inventory,
                "verification_scope": "Serialization and public projection; no label replay"}
    (out / "private" / "manifest.json").write_text(_json(manifest) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--thresholds", nargs="+", type=int, choices=THRESHOLDS, default=list(THRESHOLDS))
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("Output must be a new directory")
    if len(set(args.seeds)) != len(args.seeds) or len(set(args.thresholds)) != len(args.thresholds):
        parser.error("Seeds and thresholds must each be distinct")
    # Validation precedes runtime startup, including CLI requests.
    for seed in args.seeds:
        _integer(seed, "seed", 0, 2**63 - 1)
    _integer(args.demo_count, "demo-count", 1, 8)
    _integer(args.query_count, "query-count", 1, 8)
    with RacketBridge() as bridge:
        episodes = [generate_episode(seed, {"minimum_anchor_area": area}, args.demo_count,
                                     args.query_count, bridge=bridge)
                    for seed in args.seeds for area in args.thresholds]
    manifest = export_episodes(episodes, args.out)
    print(_json({"status": manifest["status"], "episodes": manifest["episodes"],
                 "demos": args.demo_count, "queries": args.query_count, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
