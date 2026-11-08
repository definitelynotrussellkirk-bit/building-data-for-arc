"""Unapproved, task-local episode prototype; canonical generation is untouched.

All labels and rival outputs come from the included RacketBridge. The only
executed rule parameter is beam_axes. Inputs are independent of its value.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid


TASK_ID = "0b8ba9bb3c63"
DEFAULT_AXES = "both"
ALLOWED_AXES = ("both", "horizontal", "vertical")
N_TRAIN = 3
N_PAIRS = 4
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json_sha(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _validate_seed(seed):
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("seed must be an integer in 0..2**64-1")


def _validate_axes(axes):
    if not isinstance(axes, str) or axes not in ALLOWED_AXES:
        raise ValueError("beam_axes must be both, horizontal, or vertical")


def _subseed(seed, domain, index=0):
    return int.from_bytes(hashlib.sha256(f"beam-axes-v1:{domain}:{seed}:{index}".encode()).digest(), "big")


def choose_axes(seed):
    """Choose the hidden rule once per episode, with a separate RNG domain."""
    _validate_seed(seed)
    return ALLOWED_AXES[_subseed(seed, "rule") % len(ALLOWED_AXES)]


def rule_source(beam_axes=DEFAULT_AXES):
    """The materialized source, including its original rule! wrapper."""
    _validate_axes(beam_axes)
    return (HERE / f"{beam_axes}.rkt").read_text(encoding="utf-8")


def source_hashes():
    return {path.name: _sha(path.read_bytes()) for path in [HERE / "prototype.py", *sorted(HERE.glob("*.rkt"))]}


def selected_canonical_source():
    sources = set()
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise RuntimeError("The selected task must have one canonical Racket authority")
    return sources.pop()


def apply_rule(bridge, beam_axes, grid):
    """Execute the exact materialized lambda using the included bridge.

    These three sources contain an explicit lambda with local h/w bindings,
    no shorthand, no dictionary literals and no comments. The shared wrapper
    peeler therefore suffices; no private normalizer or Python label mirror is
    used. The canonical source itself remains byte-for-byte unchanged.
    """
    _validate_axes(beam_axes)
    grid = normalize_grid(grid)
    expression = strip_rule_wrapper(rule_source(beam_axes))
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    output = normalize_grid(bridge.eval_text(f"({expression} {literal})"))
    if (len(output), len(output[0])) != (len(grid), len(grid[0])):
        raise RuntimeError("Beam rule unexpectedly changed the grid dimensions")
    return output


def make_input(seed, pair_index):
    """Construct one bounded scene without observing the episode parameter.

    The five red rectangles include one beyond a blocker, while the other
    four cross the two beam bands. Each side has a blocker that clips part of
    the band. The final pair is always 30x30; demonstrations are 23..27 per
    dimension. Random reflections/rotations preserve these constraints.
    """
    _validate_seed(seed)
    if type(pair_index) is not int or not 0 <= pair_index < N_PAIRS:
        raise ValueError("pair_index must be an integer in 0..3")
    rng = random.Random(_subseed(seed, "input", pair_index))
    h, w = (30, 30) if pair_index == N_TRAIN else (rng.randint(23, 27), rng.randint(23, 27))
    ch, cw = rng.randint(3, 5), rng.randint(3, 5)
    top, left = rng.randint(8, h - ch - 8), rng.randint(8, w - cw - 8)
    bottom, right = top + ch - 1, left + cw - 1
    grid = [[0] * w for _ in range(h)]

    def paint(r, c, rh, rw, color):
        for y in range(r, r + rh):
            for x in range(c, c + rw):
                if not (0 <= y < h and 0 <= x < w) or grid[y][x] != 0:
                    raise RuntimeError("Constructor placed overlapping/out-of-bounds rectangles")
                grid[y][x] = color

    paint(top, left, ch, cw, 8)
    blockers = ((top, left - 6), (top - 6, right - 1),
                (bottom - 1, right + 5), (bottom + 5, left))
    for r, c in blockers:
        paint(r, c, 2, 2, rng.choice((1, 3, 5, 6, 7, 9)))
    paint(top - 1, left - 3, 3, 2, 2)
    paint(top - 3, left + 1, 2, 3, 2)
    paint(bottom, right + 2, 3, 2, 2)
    paint(bottom + 2, left - 1, 2, 3, 2)
    paint(top, left - 8, 2, 1, 2)
    if rng.choice((False, True)):
        grid = [row[::-1] for row in grid]
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def _first_difference(expected, rival):
    for r, row in enumerate(expected):
        for c, value in enumerate(row):
            if value != rival[r][c]:
                return {"row": r, "column": c, "selected": value, "rival": rival[r][c]}
    return None


def _check_lesson(beam_axes, outputs, query_index):
    demo_indices = [index for index in range(N_PAIRS) if index != query_index]
    checks = []
    for rival in ALLOWED_AXES:
        if rival == beam_axes:
            continue
        witnesses = [{"pair_index": index, "cell": cell} for index in demo_indices
                     if (cell := _first_difference(outputs[beam_axes][index], outputs[rival][index])) is not None]
        checks.append({"beam_axes": rival,
                       "refuting_demo_indices": [witness["pair_index"] for witness in witnesses],
                       "witnesses": witnesses,
                       "query_differs": outputs[beam_axes][query_index] != outputs[rival][query_index]})
    return {"query_index": query_index, "demo_indices": demo_indices,
            "status": "pass" if all(row["refuting_demo_indices"] for row in checks) else "ambiguous",
            "rivals": checks}


def build_episode(seed, *, beam_axes=DEFAULT_AXES, bridge=None):
    """Return separate public/private records; never emits per-pair rule draws.

    Omitted beam_axes retains the canonical default. Passing None requests one
    deterministic draw from the finite rule family using the episode seed.
    Supplying a live bridge amortizes startup without caching labels.
    """
    _validate_seed(seed)
    if beam_axes is not None:
        _validate_axes(beam_axes)
    if bridge is None:
        with RacketBridge(timeout=20.0) as owned_bridge:
            return build_episode(seed, beam_axes=beam_axes, bridge=owned_bridge)
    selected_axes = choose_axes(seed) if beam_axes is None else beam_axes
    if rule_source() != selected_canonical_source():
        raise RuntimeError("both.rkt differs from the selected canonical authority")
    generator, _source_path, generator_sha = load_selected_generator(TASK_ID, root=ROOT)
    inputs = [make_input(seed, index) for index in range(N_PAIRS)]
    for index, grid in enumerate(inputs):
        errors = generator.self_check(grid)
        if errors:
            raise RuntimeError(f"Pair {index} rejected by the selected canonical input checker: {errors}")
    outputs = {axes: [apply_rule(bridge, axes, grid) for grid in inputs] for axes in ALLOWED_AXES}
    rotations = [_check_lesson(selected_axes, outputs, query_index) for query_index in range(N_PAIRS)]
    if any(row["status"] != "pass" for row in rotations):
        raise RuntimeError("Episode is ambiguous against a declared parameter rival")
    source = rule_source(selected_axes)
    public = {"train": [{"input": copy.deepcopy(inputs[index]), "output": copy.deepcopy(outputs[selected_axes][index])}
                        for index in range(N_TRAIN)],
              "test": [{"input": copy.deepcopy(inputs[N_TRAIN])}]}
    private = {"schema": "beam-axes-episode-prototype-v1", "task_id": TASK_ID,
               "parent": "training:6ffe8f07", "approval_status": "prototype_unapproved",
               "seed": seed, "parameters": {"beam_axes": selected_axes},
               "parameter_selection": "seeded_once" if beam_axes is None else "explicit_or_default",
               "demonstration_count": N_TRAIN, "query_pair_index": N_TRAIN,
               "selected_generator_sha256": generator_sha, "prototype_source_hashes": source_hashes(),
               "rule": {"file": f"{selected_axes}.rkt", "text": source, "sha256": _sha(source.encode()),
                        "normalized_sha256": _sha(" ".join(source.split()).encode())},
               "input_sha256": [_json_sha(grid) for grid in inputs],
               "public_sha256": _json_sha(public), "answers": copy.deepcopy(outputs[selected_axes][N_TRAIN:]),
               "all_racket_outputs": outputs,
               "identifiability": {"rivals": [axes for axes in ALLOWED_AXES if axes != selected_axes],
                                   "production": copy.deepcopy(rotations[N_TRAIN]), "rotations": rotations}}
    return {"public": public, "private": private}


def public_filename(challenge):
    """Name only visible demonstrations/query inputs, excluding private metadata."""
    visible = {"train": [{"input": p["input"], "output": p["output"]} for p in challenge["train"]],
               "test": [{"input": p["input"]} for p in challenge["test"]]}
    digest = hashlib.sha256(json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return "challenge-" + digest + ".json"


def write_evidence(out, seeds=(11, 29, 47), beam_axes="all"):
    """Retain exact episodes, finite parameter-rival proofs and runtime hashes."""
    seeds = list(seeds)
    if not seeds:
        raise ValueError("At least one seed is required")
    for seed in seeds:
        _validate_seed(seed)
    settings = ALLOWED_AXES if beam_axes == "all" else (None if beam_axes == "seeded" else beam_axes,)
    for axes in settings:
        if axes is not None:
            _validate_axes(axes)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    source_before = source_hashes()
    selected_generator, _path, generator_before = load_selected_generator(TASK_ID, root=ROOT)
    del selected_generator
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    summary = {"schema": "beam-axes-prototype-verification-v1", "status": "running",
               "approval_status": "prototype_unapproved", "task_id": TASK_ID,
               "allowed_settings": list(ALLOWED_AXES), "default_setting": DEFAULT_AXES,
               "seeds": seeds, "source_hashes": source_before, "selected_generator_sha256": generator_before,
               "demonstrations_per_episode": N_TRAIN, "queries_per_episode": 1,
               "ordering_policy": "three demonstrations then final query; all four query rotations also checked",
               "rival_scope": "exactly all other declared beam_axes settings; no universal rule-identifiability claim",
               "episodes": []}
    with RacketBridge(timeout=20.0) as bridge:
        summary["racket_runtime"] = bridge.runtime_identity
        for pair in canonical:
            if apply_rule(bridge, "both", pair["input"]) != pair["output"]:
                raise RuntimeError("Canonical default failed an official labelled pair")
        summary["canonical_default"] = {"status": "pass", "occurrences": len(canonical),
                                         "unique_inputs": len({_json_sha(pair["input"]) for pair in canonical}),
                                         "exact_source_matches_selected": rule_source() == selected_canonical_source()}
        for seed in seeds:
            for axes in settings:
                episode = build_episode(seed, beam_axes=axes, bridge=bridge)
                index = len(summary["episodes"]) + 1
                public_name, private_name = public_filename(episode["public"]), f"episode-{index:03}.private.json"
                for name, record in ((public_name, episode["public"]), (private_name, episode["private"])):
                    (out / name).write_text(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
                private = episode["private"]
                summary["episodes"].append({"seed": seed, "beam_axes": private["parameters"]["beam_axes"],
                                             "public_file": public_name, "private_file": private_name,
                                             "public_sha256": _sha((out / public_name).read_bytes()),
                                             "private_sha256": _sha((out / private_name).read_bytes()),
                                             "rule_sha256": private["rule"]["sha256"],
                                             "production": private["identifiability"]["production"]["status"],
                                             "rotation_statuses": [row["status"] for row in private["identifiability"]["rotations"]],
                                             "query_dimensions": [len(episode["public"]["test"][0]["input"]), len(episode["public"]["test"][0]["input"][0])]})
    if source_hashes() != source_before or load_selected_generator(TASK_ID, root=ROOT)[2] != generator_before:
        raise RuntimeError("Source changed during evidence construction; retained outputs are not final evidence")
    n = len(summary["episodes"])
    summary.update({"status": "pass", "counts": {"episodes": n, "episode_pairs": n * N_PAIRS,
                    "episode_rule_applications": n * N_PAIRS * len(ALLOWED_AXES),
                    "canonical_rule_applications": len(canonical), "production_lessons": n,
                    "production_rival_checks": n * 2, "query_rotations": n * N_PAIRS,
                    "rotation_rival_checks": n * N_PAIRS * 2},
                    "limitations": ["Finite constructed scene family and listed seeds only; no training or production approval.",
                                    "Identifiability is checked only against the two declared alternative axis settings.",
                                    "All inputs use one emitter, four 2x2 blockers, five red rectangles, and both-axis evidence.",
                                    "Prototype does not change generate(), approval hashes, shared APIs, or canonical authority."]})
    (out / "verification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New output directory (contains private answers)")
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 29, 47])
    parser.add_argument("--beam-axes", choices=[*ALLOWED_AXES, "seeded", "all"], default="all")
    args = parser.parse_args(argv)
    summary = write_evidence(args.out, seeds=args.seeds, beam_axes=args.beam_axes)
    print(json.dumps({"status": summary["status"], "approval_status": summary["approval_status"],
                      "counts": summary["counts"], "verification": str(args.out / "verification.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
