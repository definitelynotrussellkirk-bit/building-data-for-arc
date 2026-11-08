"""Opt-in tie-policy proposal; never changes or selects the canonical generator.

All labels and declared rival predictions are produced by the real RacketBridge.
Python constructs inputs, observes structural constraints, and checks evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys


TASK_ID = "4512012999bb"
PARENT_ID = "training:846bdb03"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CANONICAL_SHA256 = "e3238cefdd981958e0835cc7d91d0680cd68f3d3db6321936805ae88fb3f1beb"
SELECTOR = "(> (score #t) (score #f))"
RIVALS = ("direct", "mirror", "always-direct", "always-mirror")


def sha256(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def programs_from(canonical_source):
    """Exact canonical default; one guarded local edit for each declared rival."""
    if canonical_source.count(SELECTOR) != 1:
        raise ValueError("canonical orientation selector must occur exactly once")
    return {
        "direct": canonical_source,
        "mirror": canonical_source.replace(SELECTOR, "(>= (score #t) (score #f))", 1),
        "always-direct": canonical_source.replace(SELECTOR, "#f", 1),
        "always-mirror": canonical_source.replace(SELECTOR, "#t", 1),
    }


def load_canonical(path=None):
    candidates = [Path(path)] if path else [
        REPO / "shared/data/canonical/puzzles.jsonl",
        REPO / "data/canonical/puzzles.jsonl",
    ]
    source_path = next((p.resolve() for p in candidates if p.is_file()), None)
    if source_path is None:
        raise FileNotFoundError("canonical ledger unavailable; pass --canonical to its JSON/JSONL file")
    raw = source_path.read_bytes()
    if source_path.suffix == ".jsonl":
        rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    else:
        value = json.loads(raw)
        rows = value if isinstance(value, list) else [value]
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    if not matches:
        raise ValueError(f"canonical source contains no exact task {TASK_ID}")
    sources = {row["program_solution"] for row in matches}
    if len(sources) != 1 or sha256(next(iter(sources))) != CANONICAL_SHA256:
        raise ValueError("canonical raw source changed; review the proposal before adapting it")
    row = next((r for r in matches if r.get("source") == "training"), matches[0])
    return row, source_path


def side_scores(crop, left, right):
    """Structural measurement only; this function does not produce labels."""
    width = len(crop[0])
    direct = mirrored = 0
    for row in crop:
        for col, value in enumerate(row):
            if col < width // 2:
                direct += value == left
                mirrored += value == right
            elif col >= (width + 1) // 2:
                direct += value == right
                mirrored += value == left
    return direct, mirrored


def find_candidates(grid):
    """Observe all guide/crop candidates in the canonical enumeration order."""
    height, width = len(grid), len(grid[0])
    nonzero = [(r, c) for r in range(height) for c in range(width) if grid[r][c]]
    candidates = []
    for r0 in range(height):
        for r1 in range(r0 + 2, height):
            columns = [c for c in range(width) if grid[r0][c]
                       and grid[r0][c] == grid[r1][c]
                       and all(grid[r][c] for r in range(r0, r1 + 1))]
            for left, right in itertools.combinations(columns, 2):
                cells = [(r, c) for r, c in nonzero
                         if not (r0 <= r <= r1 and c in (left, right))]
                if not cells:
                    continue
                pr0, pr1 = min(r for r, _ in cells), max(r for r, _ in cells)
                pc0, pc1 = min(c for _, c in cells), max(c for _, c in cells)
                if pr1 - pr0 + 1 == r1 - r0 - 1 and pc1 - pc0 + 1 == right - left - 1:
                    candidates.append((r0, r1, left, right, pr0, pr1, pc0, pc1))
    return candidates


def _crop(rng, height, width, left, right, accents, kind, hard):
    # Two different accents at opposite top corners guarantee visible asymmetry.
    # Reserved corners also fix the complete bbox before any side-color sampling.
    reserved = {(0, 0), (0, width - 1), (height - 1, width - 1)}
    crop = [[rng.choice((0, 0, *accents)) for _ in range(width)] for _ in range(height)]
    crop[0][0], crop[0][-1], crop[-1][-1] = accents[0], accents[1], accents[0]
    slots = [(r, c) for r in range(height) for c in range(width)
             if (r, c) not in reserved and (c < width // 2 or c >= (width + 1) // 2)]
    rng.shuffle(slots)
    total = max(4, 2 * (int(len(slots) * 0.65) // 2))
    total = min(total, 2 * (len(slots) // 2))
    if kind == "tie":
        direct_count = total // 2
    elif hard:
        direct_count = total // 2 + (1 if kind == "direct" else -1)
    else:
        majority = total - max(1, total // 5)
        direct_count = majority if kind == "direct" else total - majority
    for index, (r, c) in enumerate(slots[:total]):
        correct = left if c < width // 2 else right
        wrong = right if c < width // 2 else left
        crop[r][c] = correct if index < direct_count else wrong
    if width % 2:
        for r in range(height):
            crop[r][width // 2] = left if r % 2 == 0 else right
    return crop


def _scene(rng, split, index):
    kinds = ("tie", "direct", "mirror", "tie") if split == "test" else ("tie", "direct", "mirror")
    kind = kinds[index % len(kinds)]
    if split == "test":
        inner_h, inner_w = ((7, 7), (8, 8), (8, 9), (10, 10))[index % 4]
    else:
        inner_h, inner_w = ((3, 4), (3, 6), (4, 6), (5, 5), (4, 4))[index % 5]
    outer_h, outer_w = inner_h + 2, inner_w + 2
    marker, left, right, accent1, accent2 = rng.sample(range(1, 10), 5)
    crop = _crop(rng, inner_h, inner_w, left, right, (accent1, accent2), kind, split == "test")
    placement = ("right", "below", "above")[index % 3] if split == "test" else ("above", "below", "right")[index % 3]
    top, margin, gap = rng.randint(1, 2), rng.randint(1, 2), rng.randint(1, 2)
    if placement == "above":
        pr0, pc0 = top, margin + rng.randint(0, 2)
        r0, cL = pr0 + inner_h + gap, margin
    elif placement == "below":
        r0, cL = top, margin
        pr0, pc0 = r0 + outer_h + gap, margin + rng.randint(0, 2)
    else:
        r0, cL = top, margin
        pr0, pc0 = r0 + 1, cL + outer_w + gap
    r1, cR = r0 + outer_h - 1, cL + outer_w - 1
    height = max(r1 + 1, pr0 + inner_h) + rng.randint(1, 2)
    width = max(cR + 1, pc0 + inner_w) + rng.randint(1, 2)
    if height > 30 or width > 30:
        return None
    grid = [[0] * width for _ in range(height)]
    varied = split == "test" or index % 3 == 2
    left_wall, right_wall = [], []
    for row in range(outer_h):
        if row in (0, outer_h - 1):
            lval = rval = marker
        elif varied and row > 1 and row % 2 == 0:
            lval, rval = accent1, accent2
        else:
            lval, rval = left, right
        left_wall.append(lval)
        right_wall.append(rval)
        grid[r0 + row][cL], grid[r0 + row][cR] = lval, rval
    for r, row in enumerate(crop):
        grid[pr0 + r][pc0:pc0 + inner_w] = row
    candidate = (r0, r1, cL, cR, pr0, pr0 + inner_h - 1, pc0, pc0 + inner_w - 1)
    candidates = find_candidates(grid)
    if candidates != [candidate]:
        return None
    scores = side_scores(crop, left, right)
    if ((kind == "tie" and not scores[0] == scores[1] > 0)
            or (kind == "direct" and scores[0] <= scores[1])
            or (kind == "mirror" and scores[1] <= scores[0])):
        raise AssertionError("constructed score relation does not match its lesson")
    return {"input": grid, "meta": {
        "kind": kind, "placement": placement, "input_shape": [height, width],
        "crop_shape": [inner_h, inner_w], "crop_area": inner_h * inner_w,
        "output_shape": [outer_h, outer_w], "candidate": list(candidate),
        "candidate_count": len(candidates), "crop": crop, "scores": list(scores),
        "left_color": left, "right_color": right,
        "left_wall": left_wall, "right_wall": right_wall,
        "asymmetric": any(row != row[::-1] for row in crop),
        "odd_center_ignored": inner_w % 2 == 1,
        "variegated_walls": varied,
    }}


def sample_inputs(seed, train_count=3, test_count=4, *, stream="direct", max_attempts=64, forbidden=None):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(train_count) is not int or not 3 <= train_count <= 64:
        raise ValueError("train must be an integer in 3..64 (three branch witnesses are required)")
    if type(test_count) is not int or not 1 <= test_count <= 64:
        raise ValueError("test must be an integer in 1..64")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 256:
        raise ValueError("max_attempts must be an integer in 1..256")
    seen = set() if forbidden is None else set(forbidden)
    result = {"train": [], "test": []}
    for split, count in (("train", train_count), ("test", test_count)):
        for index in range(count):
            for attempt in range(max_attempts):
                # Every split/index is its own stream: changing --train cannot
                # silently replace the held-out query inputs, and vice versa.
                token = f"tie-policy-v1:{seed}:{stream}:{split}:{index}:{attempt}"
                scene = _scene(random.Random(int(sha256(token), 16)), split, index)
                if scene is not None and grid_key(scene["input"]) not in seen:
                    seen.add(grid_key(scene["input"]))
                    scene["meta"]["attempts"] = attempt + 1
                    result[split].append(scene)
                    break
            else:
                raise RuntimeError(f"{split}[{index}] exhausted {max_attempts} attempts for a unique valid scene")
    return result


def identify_from_demos(demos, predictions):
    """Finite version space: only demo outputs can select surviving programs."""
    if not demos or not predictions:
        raise ValueError("nonempty demonstrations and declared predictions are required")
    query_counts = {len(value["test"]) for value in predictions.values()}
    if len(query_counts) != 1 or any(len(value["train"]) != len(demos) for value in predictions.values()):
        raise ValueError("prediction matrix shape does not match the episode")
    eliminated = {name: [i for i, pair in enumerate(demos) if value["train"][i] != pair["output"]]
                  for name, value in predictions.items()}
    survivors = sorted(name for name, mismatches in eliminated.items() if not mismatches)
    if not survivors:
        raise ValueError("no declared program agrees with the demonstrations")
    queries = []
    for index in range(next(iter(query_counts))):
        groups = {}
        for name in survivors:
            key = sha256(json.dumps(predictions[name]["test"][index], separators=(",", ":")))
            groups.setdefault(key, []).append(name)
        queries.append({"query_index": index, "identifiable": len(groups) == 1,
                        "surviving_prediction_classes": groups})
    return {"scope": "only the finite declared program family; no claim about all possible rules",
            "selection_uses": "demonstration inputs and outputs only",
            "declared_programs": sorted(predictions), "survivors": survivors,
            "eliminated": {name: indices for name, indices in eliminated.items() if indices},
            "queries": queries}


def _add_runtime_path():
    runtime = REPO / "shared/runtime"
    if runtime.is_dir() and str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))


class RacketRunner:
    def __init__(self, timeout=30):
        _add_runtime_path()
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=timeout)
        self.calls = 0

    def apply(self, source, grid):
        literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        # The source, including its rule! wrapper, is not rewritten to execute.
        expression = f"((let ((rule! (lambda (f) f))) {source}) '{literal})"
        result = self.bridge.eval_text(expression)
        self.calls += 1
        if (type(result) is not list or not result or type(result[0]) is not list or not result[0]
                or len(result) > 30 or len(result[0]) > 30
                or any(type(row) is not list or len(row) != len(result[0])
                       or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in result)):
            raise RuntimeError("Racket returned a malformed grid")
        return result

    def close(self):
        self.bridge.close()


def _check_outputs(scene, outputs):
    meta = scene["meta"]
    h, w = meta["output_shape"]
    for name, output in outputs.items():
        if [len(output), len(output[0])] != [h, w]:
            raise AssertionError(f"{name}: wrong output shape")
        if [row[0] for row in output] != meta["left_wall"] or [row[-1] for row in output] != meta["right_wall"]:
            raise AssertionError(f"{name}: guide walls were not copied row by row")
        if any(output[0][1:-1]) or any(output[-1][1:-1]):
            raise AssertionError(f"{name}: nonzero horizontal frame interior")
    if outputs["always-direct"] == outputs["always-mirror"]:
        raise AssertionError("scene does not expose orientation")
    for policy in ("direct", "mirror"):
        direct_score, mirror_score = meta["scores"]
        flip = mirror_score > direct_score or (policy == "mirror" and mirror_score == direct_score)
        rival = "always-mirror" if flip else "always-direct"
        if outputs[policy] != outputs[rival]:
            raise AssertionError(f"{policy}: Racket branch disagrees with measured scores")
    crop = meta["crop"]
    if [row[1:-1] for row in outputs["always-direct"][1:-1]] != crop:
        raise AssertionError("Racket direct output failed to preserve the detached crop")
    if [row[1:-1] for row in outputs["always-mirror"][1:-1]] != [row[::-1] for row in crop]:
        raise AssertionError("Racket mirror output failed to reflect the detached crop")


def build_episode(setting, scenes, programs, runner):
    if setting not in ("direct", "mirror"):
        raise ValueError("setting must be direct or mirror")
    predictions = {name: {"train": [], "test": []} for name in RIVALS}
    for split in ("train", "test"):
        for scene in scenes[split]:
            outputs = {name: runner.apply(programs[name], scene["input"]) for name in RIVALS}
            _check_outputs(scene, outputs)
            for name, output in outputs.items():
                predictions[name][split].append(output)
    demos = [{"input": scene["input"], "output": predictions[setting]["train"][i]}
             for i, scene in enumerate(scenes["train"])]
    certificate = identify_from_demos(demos, predictions)
    if certificate["survivors"] != [setting] or not all(q["identifiable"] for q in certificate["queries"]):
        raise AssertionError("demonstrations fail to identify every query in the declared family")
    return {"setting": setting,
            "challenge": {"train": demos, "test": [{"input": s["input"]} for s in scenes["test"]]},
            "query_answers": predictions[setting]["test"], "predictions": predictions,
            "certificate": certificate,
            "scenes": {split: [s["meta"] for s in scenes[split]] for split in ("train", "test")}}


def write_batch(out, episodes, programs, provenance):
    _add_runtime_path()
    from reviewer_support import public_challenge_bytes, public_challenge_id
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"output directory already exists: {out}; choose a new --out")
    bound = []
    for episode in episodes:
        visible = public_challenge_bytes(episode["challenge"])
        public_id = public_challenge_id(episode["challenge"])
        if sha256(visible) != public_id:
            raise AssertionError("public helper byte/hash mismatch")
        bound.append((public_id, visible, episode))
    bound.sort(key=lambda item: item[0])
    if len({item[0] for item in bound}) != len(bound):
        raise ValueError("batch contains duplicate public challenges")
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/programs").mkdir(parents=True)
    for name, source in sorted(programs.items()):
        (out / "private/programs" / f"{name}.rkt").write_bytes(source.encode("utf-8"))
    records = []
    for public_id, visible, episode in bound:
        (out / "public" / f"{public_id}.json").write_bytes(visible)
        records.append({"public_id": public_id, **{k: v for k, v in episode.items() if k != "challenge"}})
    manifest = {"schema": "4512012999bb-parametric-proposal-v1", "task_id": TASK_ID,
                "parent_id": PARENT_ID, "status": "opt-in proposal; not selected generator",
                "public_ids": [item[0] for item in bound],
                "program_sha256": {name: sha256(source) for name, source in sorted(programs.items())},
                "provenance": provenance, "episodes": records}
    (out / "private/manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def generate_batch(*, seed=17, train=3, test=4, setting="direct", out, canonical=None, max_attempts=64, timeout=30):
    if Path(out).exists():
        raise FileExistsError(f"output directory already exists: {out}; choose a new --out")
    if setting not in ("all", "direct", "mirror"):
        raise ValueError("setting must be all, direct, or mirror")
    canonical_row, canonical_path = load_canonical(canonical)
    programs = programs_from(canonical_row["program_solution"])
    settings = ("direct", "mirror") if setting == "all" else (setting,)
    scenes_by_setting, seen = {}, set()
    for policy in settings:
        scenes = sample_inputs(seed, train, test, stream=policy, max_attempts=max_attempts, forbidden=seen)
        scenes_by_setting[policy] = scenes
        seen.update(grid_key(s["input"]) for split in ("train", "test") for s in scenes[split])
    runner = RacketRunner(timeout=timeout)
    try:
        canonical_pairs = list(canonical_row["train"])
        held_out = canonical_row.get("test", [])
        canonical_pairs += [held_out] if isinstance(held_out, dict) else held_out
        canonical_passed = 0
        for index, pair in enumerate(canonical_pairs):
            if "output" not in pair:
                continue
            if runner.apply(programs["direct"], pair["input"]) != pair["output"]:
                raise AssertionError(f"exact canonical program failed labeled pair {index}")
            canonical_passed += 1
        if canonical_passed != 5:
            raise AssertionError(f"expected all five labeled canonical pairs, found {canonical_passed}")
        episodes = [build_episode(policy, scenes_by_setting[policy], programs, runner) for policy in settings]
        provenance = {"seed": seed, "train": train, "test": test, "setting": setting,
                      "max_attempts_per_scene": max_attempts, "label_backend": "actual RacketBridge",
                      "canonical_pairs_passed": canonical_passed, "racket_evaluations": runner.calls,
                      "canonical_program_sha256": sha256(programs["direct"]),
                      "canonical_file_sha256": sha256(canonical_path.read_bytes()),
                      "prototype_sha256": sha256(Path(__file__).read_bytes()),
                      "selected_generator_sha256": sha256((HERE.parents[1] / "generator.py").read_bytes()),
                      "runtime_identity": runner.bridge.runtime_identity}
    finally:
        runner.close()
    return write_batch(out, episodes, programs, provenance)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--seed", type=int, default=17)
    result.add_argument("--train", type=int, default=3, help="demo count, 3..64 (independent of --test)")
    result.add_argument("--test", type=int, default=4, help="query count, 1..64 (independent of --train)")
    result.add_argument("--setting", choices=("all", "direct", "mirror"), default="direct")
    result.add_argument("--out", type=Path, required=True, help="new output directory; existing paths are refused")
    result.add_argument("--canonical", type=Path, help="explicit canonical JSON or JSONL (optional in review runtime)")
    result.add_argument("--max-attempts", type=int, default=64)
    result.add_argument("--timeout", type=float, default=30, help="seconds per Racket evaluation")
    return result


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        result = generate_batch(**vars(arguments))
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError, AssertionError) as error:
        print(f"parametric proposal failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "generated", "public_ids": result["public_ids"],
                      "canonical_pairs_passed": result["provenance"]["canonical_pairs_passed"],
                      "racket_evaluations": result["provenance"]["racket_evaluations"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
