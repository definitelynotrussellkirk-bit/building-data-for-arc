"""Native, protected-Racket path lessons; episode-fixed recolor origin.

Input streams are independent of settings and query count. Canonical source and
rule text stay fixed; native sampling adds safe rays and large teaching scenes.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import load_selected_generator, public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "76b818438a96"
PARAMETER = "recolor_origin"
VALUES = ("opposite", "aligned")
DEFAULT = "opposite"
MAX_ATTEMPTS = 32
_GENERATOR = None


def load_generator():
    global _GENERATOR
    if _GENERATOR is None:
        _GENERATOR = load_selected_generator(TASK, root=ROOT)[0]
    return _GENERATOR


def _sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load_programs():
    programs = {value: (HERE / f"rule_{value}.rkt").read_text().rstrip("\n") for value in VALUES}
    needle = "(curr other-ep)"
    if programs[DEFAULT].count(needle) != 1:
        raise ValueError("canonical program must have exactly one recolor start")
    if programs["aligned"] != programs[DEFAULT].replace(needle, "(curr ep)", 1):
        raise ValueError("aligned program must be the one-binding recolor-origin variant")
    return programs


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _request(seed, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)


def choose_parameter(seed):
    _integer(seed, "seed", 0, 2**63 - 1)
    digest = hashlib.sha256(f"{TASK}|{seed}|{PARAMETER}".encode()).digest()
    return VALUES[digest[0] % len(VALUES)]


def _input_seed(seed, split, index, attempt=0):
    key = f"{TASK}|native-input-v2|{seed}|{split}|{index}|{attempt}"
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") % (2**63)


def scene_issues(grid):
    """Reject extra marker rays, including blocked rays, and intersecting plans.

    Racket scans through occupied cells; the canonical clear-corridor validator
    alone can admit an unintended endpoint. These restrictions repair native
    sampling without changing the selected canonical generator or rule.
    """
    generator = load_generator()
    try:
        scene = generator._scene_info(grid)
    except (TypeError, ValueError) as error:
        return [str(error)]
    reasons, plans = [], []
    for link in scene["links"]:
        candidates = []
        for endpoint in link["path"]["endpoints"]:
            dr, dc = generator._outward(link["path"], endpoint)
            for marker in scene["markers"]:
                rr, cc = marker["point"][0] - endpoint[0], marker["point"][1] - endpoint[1]
                if (dr and cc == 0 and rr * dr > 0) or (dc and rr == 0 and cc * dc > 0):
                    candidates.append((endpoint, marker["point"]))
        if candidates != [(link["aligned_endpoint"], link["marker"]["point"])]:
            reasons.append(f"extra or inconsistent marker ray for path {link['path']['color']}")
        if link["extension_count"] >= len(link["path"]["cells"]):
            reasons.append("saturated traversal cannot distinguish recolor origins")
        er, ec = link["aligned_endpoint"]
        dr, dc = link["direction"]
        plans.append({(er + dr * s, ec + dc * s) for s in range(1, link["distance"])})
    if plans[0] & plans[1]:
        reasons.append("extension plans intersect")
    return reasons


def _scaled_scene(seed, size, *, teaching):
    """Two three-turn paths span the canvas; 30x30 has 60+ occupied cells."""
    rng = random.Random(seed)
    box = (size - 2) // 2
    grid = [[0] * size for _ in range(size)]
    colors = rng.sample(range(1, 10), 4)
    far = box - 2 if teaching else rng.randint(max(4, box - 4), box - 2)
    distances = [rng.choice((2, 3)), far]
    rng.shuffle(distances)
    for which, distance in enumerate(distances):
        tail = rng.randint(1, min(3, box - 3))
        cells = [(0, c) for c in range(distance, box)]
        cells += [(r, box - 1) for r in range(1, box)]
        cells += [(box - 1, c) for c in range(box - 2, 0, -1)]
        cells += [(r, 1) for r in range(box - 2, box - tail - 2, -1)]
        transform = (lambda r, c: (r, c)) if which == 0 else (lambda r, c: (size - 1 - r, size - 1 - c))
        for r, c in cells:
            rr, cc = transform(r, c)
            grid[rr][cc] = colors[which * 2]
        rr, cc = transform(0, 0)
        grid[rr][cc] = colors[which * 2 + 1]
    if rng.getrandbits(1):
        grid = [row[::-1] for row in grid]
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def sample_inputs(seed, demos, queries):
    """Separate streams preserve first-turn identity for one or four queries."""
    _request(seed, demos, queries)
    generator = load_generator()
    seen, splits, receipts, rejected = set(), {"demo": [], "query": []}, [], 0
    for split, count in (("demo", demos), ("query", queries)):
        for index in range(count):
            size = (14, 30, 20, 24, 20, 24)[index] if split == "demo" else (14, 20, 24, 30)[index]
            constructive = (split == "demo" and index < 2) or size == 30
            for attempt in range(MAX_ATTEMPTS):
                draw_seed = _input_seed(seed, split, index, attempt)
                try:
                    if constructive:
                        grid = _scaled_scene(draw_seed, size, teaching=split == "demo")
                    else:
                        grid = generator.generate(draw_seed, index * 11 + attempt,
                                                  difficulty="hard", grid_h=size, grid_w=size)
                    issues = scene_issues(grid)
                    identity = json.dumps(grid, separators=(",", ":"))
                    if identity in seen:
                        issues.append("duplicate input")
                except ValueError as error:
                    issues = [str(error)]
                if issues:
                    rejected += 1
                    continue
                seen.add(identity)
                splits[split].append(grid)
                receipts.append({"split": split, "index": index, "size": size,
                                 "seed": draw_seed, "attempts": attempt + 1,
                                 "constructive": constructive})
                break
            else:
                raise RuntimeError(f"input sampling exhausted {MAX_ATTEMPTS} attempts for {split} {index}")
    return splits["demo"], splits["query"], {"rejected_candidates": rejected, "draws": receipts,
                                             "max_attempts_per_input": MAX_ATTEMPTS}


def execute_programs(grids, programs):
    """Protected Racket labels directly, without a copied runtime per episode."""
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("native labels require the protected Racket backend")
        outputs = []
        for program in programs:
            wrapped, labels = wrap_rule(program), []
            for grid in grids:
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                value = bridge.eval_text(f"({wrapped} {literal})")
                if (type(value) is not list or len(value) != len(grid)
                        or any(type(row) is not list or len(row) != len(grid[0])
                               or any(type(c) is not int or not 0 <= c <= 9 for c in row) for row in value)):
                    raise RuntimeError("Racket returned a malformed or wrong-size grid")
                labels.append(value)
            outputs.append(labels)
        keep = {"schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"}
        return outputs, {key: value for key, value in identity.items() if key in keep}
    finally:
        bridge.close()


def rival_outputs(grid, origin):
    """Finite diagnostic rivals; authoritative labels always come from Racket."""
    generator = load_generator()
    scene = generator._scene_info(grid)
    names = ("other_origin", "far_markers_only", "extend_only", "one_cell",
             "cap_3", "cap_6", "cap_10", "distance_including_marker",
             "one_too_few", "straight_segment_only", "swapped_marker")
    results = {}
    for name in names:
        output = deepcopy(grid)
        for i, link in enumerate(scene["links"]):
            if name == "far_markers_only" and link["distance"] < 4:
                continue
            er, ec = link["aligned_endpoint"]
            dr, dc = link["direction"]
            for step in range(1, link["distance"]):
                output[er + dr * step][ec + dc * step] = link["path"]["color"]
            selected_origin = ("aligned" if origin == "opposite" else "opposite") if name == "other_origin" else origin
            endpoint = link["other_endpoint"] if selected_origin == "opposite" else link["aligned_endpoint"]
            order = generator._walk_from(link["path"], endpoint)
            count, marker_color = link["extension_count"], link["marker"]["color"]
            if name == "extend_only":
                count = 0
            elif name == "one_cell":
                count = 1
            elif name.startswith("cap_"):
                count = min(count, int(name[4:]))
            elif name == "distance_including_marker":
                count += 1
            elif name == "one_too_few":
                count = max(0, count - 1)
            elif name == "straight_segment_only":
                direction = (order[1][0] - order[0][0], order[1][1] - order[0][1])
                straight = 1
                for left, right in zip(order, order[1:]):
                    if (right[0] - left[0], right[1] - left[1]) != direction:
                        break
                    straight += 1
                count = min(count, straight)
            elif name == "swapped_marker":
                other = scene["links"][1 - i]
                marker_color, count = other["marker"]["color"], other["extension_count"]
            for r, c in order[:count]:
                output[r][c] = marker_color
        results[name] = output
    return results


def teaching_check(demos, queries, origin):
    """Fit on demonstrations only; reject only survivors changing a query."""
    if not demos:
        raise ValueError("no demonstrations")
    demo_predictions = [rival_outputs(pair["input"], origin) for pair in demos]
    query_predictions = [rival_outputs(pair["input"], origin) for pair in queries]
    rows = []
    for name in demo_predictions[0]:
        distinguishing = [i for i, predictions in enumerate(demo_predictions) if predictions[name] != demos[i]["output"]]
        conflicts = [i for i, predictions in enumerate(query_predictions) if predictions[name] != queries[i]["output"]]
        rows.append({"rival": name, "fits_all_demos": not distinguishing,
                     "distinguishing_demo_indices": distinguishing, "different_query_indices": conflicts,
                     "unsafe": not distinguishing and bool(conflicts)})
    return {"scope": "11 declared rivals, finite evidence only", "rows": rows,
            "unsafe_rivals": [row["rival"] for row in rows if row["unsafe"]],
            "all_rivals_refuted_by_demos": all(not row["fits_all_demos"] for row in rows)}


def build_episode(*, seed: int, parameter: str | None = None, n_train: int = 3, n_test: int = 4) -> dict[str, Any]:
    _request(seed, n_train, n_test)
    selected = choose_parameter(seed) if parameter is None else parameter
    if type(selected) is not str or selected not in VALUES:
        raise ValueError(f"parameter must be one of {VALUES}")
    train_inputs, test_inputs, sampling = sample_inputs(seed, n_train, n_test)
    programs = load_programs()
    outputs, runtime = execute_programs(train_inputs + test_inputs, [programs[value] for value in VALUES])
    by_setting, pairs = dict(zip(VALUES, outputs)), []
    for index, grid in enumerate(train_inputs + test_inputs):
        pairs.append({"index": index, "input": grid,
                      "outputs_by_parameter": {value: by_setting[value][index] for value in VALUES},
                      "selected_output": by_setting[selected][index], "settings_disagree": outputs[0][index] != outputs[1][index]})
    train = [{"input": p["input"], "output": p["selected_output"]} for p in pairs[:n_train]]
    test = [{"input": p["input"], "output": p["selected_output"]} for p in pairs[n_train:]]
    teaching = teaching_check(train, test, selected)
    if teaching["unsafe_rivals"]:
        raise RuntimeError(f"underidentified lesson: {teaching['unsafe_rivals']}")
    other = next(value for value in VALUES if value != selected)
    rival_fits = all(p["outputs_by_parameter"][other] == p["selected_output"] for p in pairs[:n_train])
    if rival_fits:
        raise RuntimeError("demonstrations do not identify the selected parameter")
    challenge = {"train": deepcopy(train), "test": [{"input": deepcopy(p["input"])} for p in test]}
    return {"schema": "76b818438a96-parametric-episode-v2", "seed": seed,
            "parameter_name": PARAMETER, "parameter": selected, "default": DEFAULT,
            "allowed_values": list(VALUES), "n_train": n_train, "n_test": n_test,
            "program_sha256": {v: _sha256_text(programs[v]) for v in VALUES},
            "programs": programs, "racket": runtime, "pairs": pairs,
            "train": pairs[:n_train], "test": pairs[n_train:], "sampling": sampling,
            "rival_parameter": other, "rival_fits_all_demos": rival_fits,
            "all_demos_distinguish": all(p["settings_disagree"] for p in pairs[:n_train]),
            "teaching": teaching, "public_challenge": challenge,
            "limits": ["finite rival checks do not prove universal rule uniqueness",
                       "owner exact-source acceptance and training admission are separate"]}


def write_episode(episode, out_dir):
    """Hash only public bytes; keep settings/programs/answers in private/.

    The full challenge is controller-side storage. Model consumers reveal only
    demonstrations plus the current query, never the complete stored test list.
    """
    out_dir = Path(out_dir)
    challenge = episode["public_challenge"]
    body, identifier = public_challenge_bytes(challenge), public_challenge_id(challenge)
    private_body = json.dumps(episode, indent=2) + "\n"
    answers_body = json.dumps({"test": [{"output": p["selected_output"]} for p in episode["test"]]}, indent=2) + "\n"
    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "public").mkdir()
    (out_dir / "private").mkdir()
    paths = {"challenge": out_dir / "public" / f"{identifier}.json",
             "evidence": out_dir / "private/episode_evidence.json",
             "answers": out_dir / "private/answers.json", "summary": out_dir / "private/summary.json"}
    paths["challenge"].write_bytes(body)
    paths["evidence"].write_text(private_body)
    paths["answers"].write_text(answers_body)
    paths["summary"].write_text(json.dumps({"public_id": identifier, "schema": episode["schema"],
        "parameter": episode["parameter"], "n_train": len(challenge["train"]), "n_test": len(challenge["test"]),
        "racket": episode.get("racket"), "sampling": episode.get("sampling"), "teaching": episode.get("teaching")}, indent=2) + "\n")
    return {key: str(path) for key, path in paths.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--parameter", choices=VALUES)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    episode = build_episode(seed=args.seed, parameter=args.parameter, n_train=args.n_train, n_test=args.n_test)
    paths = write_episode(episode, args.out_dir)
    print(json.dumps({"parameter": episode["parameter"], "paths": paths,
                      "rejected_candidates": episode["sampling"]["rejected_candidates"],
                      "all_rivals_refuted_by_demos": episode["teaching"]["all_rivals_refuted_by_demos"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
