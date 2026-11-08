#!/usr/bin/env python3
"""Task-local target selection prototype; all labels are executed in Racket.

The default is the exact current canonical program. Alternate programs change
only selection of row-major matching slots and the corresponding painting call.
Run through the packet wrapper to supply the local reviewer_support and Racket.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs, canonical_path, find_root, load_selected_generator,
    normalize_grid,
)


TASK_ID = "4f065093e631"
VERSION = "0.1.0"
POLICIES = ("first", "last", "all")
DEFAULT_POLICY = "first"
SCHEMA = "arc-parametric-target-policy-evidence-v1"
_SELECTOR = "(target (fst slots))"
_BORDER = "(border-cells (first target) (second target) (third target) (fourth target))"
_PAINT = f"(paint-cells g {_BORDER} color)"
_FRAME_DIMENSIONS = ((4, 5), (5, 4), (5, 6), (7, 4))
_GRID_DIMENSIONS = ((18, 21), (21, 18), (21, 21), (30, 30))


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")


def grid_sha256(grid):
    """Exact integer-grid hash used by the independent evidence verifier."""
    return _sha256(_json_bytes(normalize_grid(grid)))


def _root(root):
    return Path(root).resolve() if root is not None else find_root(__file__)


def _policy(target_policy):
    if target_policy not in POLICIES:
        raise ValueError("target_policy must be 'first', 'last', or 'all'")
    return target_policy


def _integer(value, name, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in {lower}..{upper}")
    return value


def _rng(seed, label):
    _integer(seed, "seed", 0, 2**63 - 1)
    material = f"{TASK_ID}:{VERSION}:{seed}:{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def canonical_record(*, root=None):
    """Read this exact task only; refuse ambiguous canonical program variants."""
    rows = []
    with canonical_path(_root(root)).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    if not rows:
        raise KeyError(TASK_ID)
    programs = {row["program_solution"] for row in rows}
    if len(programs) != 1:
        raise ValueError("Canonical variants disagree on the program")
    return rows[0]


def materialize_program(target_policy=DEFAULT_POLICY, *, root=None):
    """Return exact materialized Racket, preserving the default bytes/order."""
    _policy(target_policy)
    canonical = canonical_record(root=root)["program_solution"]
    if target_policy == "first":
        return canonical
    if canonical.count(_SELECTOR) != 1 or canonical.count(_PAINT) != 1:
        raise ValueError("Canonical selector/painting fragments changed; review materialization")
    if target_policy == "last":
        return canonical.replace(_SELECTOR, "(target (last slots))", 1)
    return canonical.replace(_SELECTOR, "(targets slots)", 1).replace(
        _PAINT,
        f"(paint-cells g (flatmap (lambda (target) {_BORDER}) targets) color)",
        1,
    )


def _border_cells(box):
    top, left, bottom, right = box
    return [(r, c) for r in range(top, bottom + 1)
            for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)]


def _place_box(rng, tile, frame_height, frame_width):
    top, left, bottom, right = tile
    if bottom - top + 1 < frame_height or right - left + 1 < frame_width:
        raise ValueError("Requested canvas cannot fit the prescribed scene tiles")
    r0 = rng.randint(top, bottom - frame_height + 1)
    c0 = rng.randint(left, right - frame_width + 1)
    return [r0, c0, r0 + frame_height - 1, c0 + frame_width - 1]


def sample_scene(seed, pair_index, *, height=None, width=None, root=None):
    """Construct one distinguishing input without rejection or fallback loops.

    Indices 0..2 are varied small demonstrations. Index 3 is a larger-frame,
    four-target query, 30x30 by default. Exact size overrides must fit the same
    two-row tile layout; impossible sizes fail before construction.
    """
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(pair_index, "pair_index", 0, 3)
    default_height, default_width = _GRID_DIMENSIONS[pair_index]
    height = default_height if height is None else _integer(height, "height", 12, 30)
    width = default_width if width is None else _integer(width, "width", 12, 30)
    rng = _rng(seed, f"scene:{pair_index}")
    frame_height, frame_width = (
        ((8, 7) if seed % 2 else (7, 8)) if pair_index == 3
        else _FRAME_DIMENSIONS[(seed + pair_index) % len(_FRAME_DIMENSIONS)]
    )
    tile_cols = 3 if pair_index == 3 else 2
    if height // 2 < frame_height or width // tile_cols < frame_width:
        raise ValueError("Requested canvas cannot fit the prescribed scene tiles")
    tiles = [[r * height // 2, c * width // tile_cols,
              (r + 1) * height // 2 - 1, (c + 1) * width // tile_cols - 1]
             for r in range(2) for c in range(tile_cols)]
    rng.shuffle(tiles)
    boxes = [_place_box(rng, tile, frame_height, frame_width) for tile in tiles[:-1]]
    source = boxes[0]
    targets = sorted(boxes[1:])
    smaller_frame = _place_box(rng, tiles[-1], 3, 3)
    frame_color, noise_a, noise_b, smaller_color = rng.sample(range(1, 10), 4)
    phase_r, phase_c = rng.randrange(2), rng.randrange(2)
    grid = [[0 if r % 2 == phase_r and c % 2 == phase_c and rng.random() < 0.7
             else rng.choice((noise_a, noise_b))
             for c in range(width)] for r in range(height)]
    # Every designated blank is sealed by a nonzero border. Background zeroes
    # are isolated, so they cannot form another >=2x2 matching interior.
    for box in boxes:
        r0, c0, r1, c1 = box
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                grid[r][c] = 0
        border = _border_cells(box)
        for r, c in border:
            grid[r][c] = frame_color if box == source else rng.choice((noise_a, noise_b))
        if box != source:
            grid[border[0][0]][border[0][1]] = noise_a
            grid[border[-1][0]][border[-1][1]] = noise_b
    for r, c in _border_cells(smaller_frame):
        grid[r][c] = smaller_color
    grid[smaller_frame[0] + 1][smaller_frame[1] + 1] = 0
    scene = {
        "pair_index": pair_index, "height": height, "width": width,
        "frame_height": frame_height, "frame_width": frame_width,
        "source": source, "targets": targets, "frame_color": frame_color,
        "noise_colors": [noise_a, noise_b], "smaller_frame": smaller_frame,
        "smaller_color": smaller_color, "construction_attempts": 1,
    }
    # These existing geometry helpers validate inputs only. They never label an
    # example: Runtime executes every saved output through the Racket bridge.
    generator, _source, _digest = load_selected_generator(TASK_ID, root=_root(root))
    frames = generator._find_frames(grid)
    best = max(frames, key=lambda frame: frame[-1])
    if list(best[1:5]) != source or sum(frame[-1] == best[-1] for frame in frames) != 1:
        raise ValueError("Constructed scene did not retain its unique largest source")
    slots = generator._zero_slots(grid, frame_height, frame_width)
    if set(slots) != {tuple(box) for box in boxes}:
        raise ValueError("Constructed scene contains unintended matching zero interiors")
    return {"input": grid, "scene": scene}


class Runtime:
    """Execute the exact materialized lambda with the included public bridge."""

    def __init__(self, *, root=None, timeout=120):
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or not 0 < timeout <= 120:
            raise ValueError("timeout must be finite and in (0,120] seconds")
        self.root = _root(root)
        self.timeout = timeout
        self.programs = {policy: materialize_program(policy, root=self.root) for policy in POLICIES}
        self.calls = []
        self.bridge = None
        self.identity = None

    def __enter__(self):
        self.bridge = RacketBridge(timeout=self.timeout)
        self.identity = self.bridge.runtime_identity
        self.identity["version"] = self.bridge.eval_text("(version)")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.bridge is not None:
            self.bridge.close()
        return False

    def execute(self, target_policy, grid):
        _policy(target_policy)
        grid = normalize_grid(grid)
        if len(grid) > 30 or len(grid[0]) > 30:
            raise ValueError("ARC grids must not exceed30x30")
        if self.bridge is None:
            raise RuntimeError("Use Runtime as a context manager")
        program = self.programs[target_policy]
        prefix = "(rule! "
        if not program.startswith(prefix) or not program.endswith(")"):
            raise ValueError("Expected this task's single rule! wrapper")
        body = program[len(prefix):-1]
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        record = {"id": f"racket-call-{len(self.calls) + 1:03d}",
                  "target_policy": target_policy,
                  "program_sha256": _sha256(program.encode("utf-8")),
                  "input_sha256": grid_sha256(grid),
                  "height": len(grid), "width": len(grid[0])}
        self.calls.append(record)
        started = time.perf_counter()
        try:
            output = normalize_grid(self.bridge.eval_text(f"({body} {literal})"))
            if (len(output), len(output[0])) != (len(grid), len(grid[0])):
                raise ValueError("Racket changed the canvas dimensions unexpectedly")
            record.update(status="passed", output_sha256=grid_sha256(output))
            return output
        except Exception as error:
            record.update(status="error", error_type=type(error).__name__, error=str(error), input=grid)
            raise
        finally:
            record["elapsed_seconds"] = round(time.perf_counter() - started, 6)


def _holdout(matches, query_index):
    demonstrations = [index for index in range(len(matches)) if index != query_index]
    demo_match = all(matches[index] for index in demonstrations)
    status = ("rejected_by_demonstrations" if not demo_match else
              "survived_all" if matches[query_index] else "ambiguous")
    return {"query_index": query_index, "demonstration_indices": demonstrations,
            "demonstrations_match": demo_match, "query_matches": matches[query_index],
            "status": status}


def _rival_evidence(pairs, predictions):
    result = {}
    for policy in POLICIES:
        matches = [prediction == pair["output"] for prediction, pair in zip(predictions[policy], pairs)]
        result[policy] = {
            "pair_matches": matches,
            "predictions": deepcopy(predictions[policy]),
            "production": _holdout(matches, 3),
            "rotations": [_holdout(matches, query_index) for query_index in range(4)],
        }
    return result


def _source_hashes(root):
    _generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    files = [Path(__file__).resolve(), generator_path,
             root / "shared/runtime/reviewer_support.py",
             root / "shared/runtime/arc_repl/racket_bridge.py"]
    readme = Path(__file__).with_name("README.md")
    if readme.is_file():
        files.append(readme)
    # A relocated runtime selects generator_path and keeps a different helper
    # layout. Only files in that explicitly selected tree are content-bound.
    result = {str(path.relative_to(root)): _sha256(path.read_bytes())
              for path in files if path.is_file() and path.is_relative_to(root)}
    result[str(generator_path.relative_to(root))] = generator_sha
    return result


class EvidenceBuildError(RuntimeError):
    """A bounded failed execution carrying source-bound partial evidence."""

    def __init__(self, report, cause):
        super().__init__(str(cause))
        self.report = report


def build_evidence(seed=1729, *, root=None, timeout=120):
    """Execute one shared four-scene lesson under each bounded policy setting.

    Each episode has one fixed hidden policy, three demonstrations and one query.
    The same inputs across settings supply directly comparable witnesses. The
    private report retains every rival prediction, canonical anchor and runtime
    call; the public projection is produced separately by write_bundle.
    """
    root = _root(root)
    _integer(seed, "seed", 0, 2**63 - 1)
    runtime = Runtime(root=root, timeout=timeout)
    canonical = canonical_record(root=root)["program_solution"]
    report = {
        "schema": SCHEMA, "visibility": "private-authoring-evidence",
        "task_id": TASK_ID, "source_task": "ARC training:890034e9",
        "prototype_version": VERSION, "status": "running",
        "parameter_name": "target_policy", "parameter_values": list(POLICIES),
        "default_setting": DEFAULT_POLICY, "seed": seed,
        "source_hashes": _source_hashes(root),
        "canonical_program_sha256": _sha256(canonical.encode("utf-8")),
        "canonical_normalized_sha256": _sha256(" ".join(canonical.split()).encode("utf-8")),
        "programs": {policy: {"text": program, "sha256": _sha256(program.encode("utf-8"))}
                     for policy, program in runtime.programs.items()},
        "episodes": [], "canonical_checks": {"pair_count": 0, "pairs": [], "all_passed": False},
        "execution": {"engine": "arc_repl.racket_bridge.RacketBridge",
                      "argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                      "timeout_seconds": timeout, "calls": runtime.calls},
        "failures": [],
        "limitations": [
            "Task-local proposed prototype; it does not change production generation or approval.",
            "Finite evidence covers one four-pair scene set per recorded seed and only the three declared parameter rivals.",
            "Row-major first/last are directional; query rotations here mean single-pair holdouts, not spatial grid rotations.",
            "Constructive scenes use disjoint sealed slots, five colors, a smaller rarer-colored frame, multiple targets and varied sizes. Production retains four calibrated 21x21 profiles and one target; even sample indices use four colors, while odd indices add a fifth-color smaller frame. A separate low/interior/high source-color rank cycle gives production a combined period of six.",
            "No claim of universal identifiability, solver mastery, or training admission is made.",
        ],
    }
    predictions = {policy: [] for policy in POLICIES}
    scenes = [sample_scene(seed, index, root=root) for index in range(4)]
    try:
        with runtime:
            report["execution"]["runtime_identity"] = runtime.identity
            for policy in POLICIES:
                for sample in scenes:
                    predictions[policy].append(runtime.execute(policy, sample["input"]))
            for episode_index, policy in enumerate(POLICIES, 1):
                pairs = []
                for index, sample in enumerate(scenes):
                    output = predictions[policy][index]
                    pairs.append({"id": f"pair-{index + 1:03d}",
                                  "role": "train" if index < 3 else "test",
                                  "input": deepcopy(sample["input"]), "output": deepcopy(output),
                                  "input_sha256": grid_sha256(sample["input"]),
                                  "output_sha256": grid_sha256(output),
                                  "scene": deepcopy(sample["scene"])})
                report["episodes"].append({
                    "id": f"episode-{episode_index:03d}", "seed": seed,
                    "parameters": {"target_policy": policy},
                    "parameter_binding": "explicit once per episode; shared scene seed enables controlled comparison",
                    "program_sha256": report["programs"][policy]["sha256"],
                    "pairs": pairs, "rivals": _rival_evidence(pairs, predictions),
                })
            checks = report["canonical_checks"]
            for pair in canonical_pairs(TASK_ID, root=root):
                actual = runtime.execute("first", pair["input"])
                checks["pairs"].append({
                    "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                    "input": pair["input"], "expected_output": pair["output"],
                    "executed_output": actual, "matches": actual == pair["output"],
                })
            checks["pair_count"] = len(checks["pairs"])
            checks["all_passed"] = all(pair["matches"] for pair in checks["pairs"])
        if not report["canonical_checks"]["all_passed"]:
            report["failures"].append({"stage": "canonical_checks", "error": "Canonical output mismatch"})
        for episode in report["episodes"]:
            policy = episode["parameters"]["target_policy"]
            for rival_policy, rival in episode["rivals"].items():
                if rival_policy != policy and any(rotation["status"] != "rejected_by_demonstrations" for rotation in rival["rotations"]):
                    report["failures"].append({"stage": "identifiability", "episode_id": episode["id"],
                                               "rival": rival_policy, "rotations": rival["rotations"]})
        report["status"] = "failed" if report["failures"] else "passed"
        return report
    except Exception as error:
        report["status"] = "failed"
        report["failures"].append({"stage": "execution", "error_type": type(error).__name__, "error": str(error)})
        report["partial_scenes"] = scenes
        report["partial_predictions"] = predictions
        raise EvidenceBuildError(report, error) from error


def generate_episode(seed, target_policy=DEFAULT_POLICY, *, root=None, timeout=120):
    """Return one complete episode; None samples its fixed policy once by seed.

    This convenience function performs the same full bounded rival/canonical
    checks as build_evidence. For multiple settings, call build_evidence once.
    """
    chosen = _rng(seed, "episode-policy").choice(POLICIES) if target_policy is None else _policy(target_policy)
    report = build_evidence(seed, root=root, timeout=timeout)
    if report["status"] != "passed":
        raise EvidenceBuildError(report, RuntimeError("Episode did not pass finite evidence checks"))
    return next(episode for episode in report["episodes"] if episode["parameters"]["target_policy"] == chosen)


def public_challenge(episode):
    """Only demonstrations and query inputs; no IDs, seeds, rules or answers."""
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["pairs"] if pair["role"] == "train"],
            "test": [{"input": deepcopy(pair["input"])}
                     for pair in episode["pairs"] if pair["role"] == "test"]}


def write_bundle(evidence, out_dir):
    """Write a new bundle from build_evidence, retaining failures privately.

    A failed report gets no public challenges. Existing destinations are never
    overwritten. The evidence.json at the bundle root is PRIVATE authoring data;
    only public/ is a model-visible challenge collection.
    """
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=False)
    report = deepcopy(evidence)
    rules_dir = out_dir / "private/rules"
    rules_dir.mkdir(parents=True)
    for policy, program in report["programs"].items():
        (rules_dir / f"{policy}.rkt").write_text(program["text"], encoding="utf-8")
        program["path"] = f"private/rules/{policy}.rkt"
    report["public_challenges"] = []
    if report["status"] == "passed":
        public_dir = out_dir / "public"
        public_dir.mkdir()
        publication_order = list(report["episodes"])
        _rng(report["seed"], "public-file-order").shuffle(publication_order)
        for index, episode in enumerate(publication_order, 1):
            relative = f"public/challenge-{index:03d}.json"
            body = _json_bytes(public_challenge(episode)) + b"\n"
            (out_dir / relative).write_bytes(body)
            report["public_challenges"].append({"path": relative, "sha256": _sha256(body),
                                                  "episode_id": episode["id"]})
    manifest = out_dir / "evidence.json"
    manifest.write_bytes(_json_bytes(report) + b"\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--out", type=Path, required=True, help="New evidence bundle directory")
    parser.add_argument("--timeout", type=float, default=120, help="Per Racket call, maximum120 seconds")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out already exists; choose a new destination")
    try:
        evidence = build_evidence(seed=args.seed, timeout=args.timeout)
    except EvidenceBuildError as error:
        evidence = error.report
    path = write_bundle(evidence, args.out)
    print(json.dumps({"status": evidence["status"], "manifest": str(path),
                      "episodes": len(evidence["episodes"]),
                      "racket_calls": len(evidence["execution"]["calls"]),
                      "failures": evidence["failures"]}, sort_keys=True))
    return 0 if evidence["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
