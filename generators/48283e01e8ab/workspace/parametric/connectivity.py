#!/usr/bin/env python3
"""Unapproved, task-local episode prototype: connectivity is fixed at 4 or 8.

All labels and parameter-rival predictions come from the public Racket bridge.
The canonical program is preserved byte-for-byte at connectivity=4. This module
does not implement or register a production parametric generator interface.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import re
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid


TASK_ID = "48283e01e8ab"
VERSION = "0.1.0-prototype"
DEFAULT_CONNECTIVITY = 4
CONNECTIVITY_VALUES = (4, 8)
DIFFICULTIES = ("easy", "medium", "hard")
SCENE_PROFILES = (
    "all_classes_contact", "foreign_contact", "unknown_sizes_contact",
    "diagonal_dominoes", "diagonal_lines", "diagonal_bends",
)
DEMONSTRATIONS = 3

# The sole rule edit appends diagonal neighbors to the existing BFS queue.
_FOUR_NEIGHBORS = "(list (list (- cr 1) cc) (list (+ cr 1) cc) (list cr (- cc 1)) (list cr (+ cc 1)))"
_EIGHT_NEIGHBORS = "(list (list (- cr 1) cc) (list (+ cr 1) cc) (list cr (- cc 1)) (list cr (+ cc 1)) (list (- cr 1) (- cc 1)) (list (- cr 1) (+ cc 1)) (list (+ cr 1) (- cc 1)) (list (+ cr 1) (+ cc 1)))"

# These remain ordinary canonical-lawful component scenes. Each contains a
# diagonal contact that changes its executed labels under 8-connectivity.
_SHAPES = {
    "all_classes_contact": (
        ((1, 1), (2, 0), (2, 1), (2, 2), (3, 1)),
        ((0, 3), (1, 3)),
        ((2, 6), (2, 7), (3, 7)),
        ((5, 4), (5, 5), (6, 5), (6, 6)),
        ((6, 8), (7, 8), (8, 8)),
        ((7, 1), (7, 2), (7, 3), (8, 1), (8, 2), (8, 3)),
    ),
    "foreign_contact": (
        ((1, 1), (1, 2)),
        ((2, 3), (2, 4), (2, 5)),
        ((5, 5), (5, 6), (5, 7), (6, 6)),
    ),
    "unknown_sizes_contact": (
        ((0, 0),),
        ((1, 1), (1, 2)),
        ((3, 5), (3, 6), (3, 7), (4, 5), (4, 6), (4, 7), (5, 6)),
        ((6, 0), (6, 1), (6, 2), (6, 3), (7, 0), (7, 1), (7, 2), (7, 3)),
    ),
    "diagonal_dominoes": (
        ((1, 1), (1, 2)),
        ((2, 3), (2, 4)),
        ((5, 6), (6, 5), (6, 6), (6, 7), (7, 6)),
    ),
    "diagonal_lines": (
        ((1, 1), (1, 2), (1, 3)),
        ((2, 4), (2, 5), (2, 6)),
        ((5, 1), (5, 2), (5, 3)),
        ((6, 4), (6, 5), (6, 6)),
    ),
    "diagonal_bends": (
        ((1, 1), (1, 2), (2, 2)),
        ((3, 3), (3, 4), (4, 4)),
        ((1, 6), (1, 7), (2, 7)),
        ((6, 1), (6, 2), (7, 2)),
    ),
}


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _check_connectivity(connectivity):
    if type(connectivity) is not int or connectivity not in CONNECTIVITY_VALUES:
        raise ValueError("connectivity must be the integer 4 or 8")


def _canonical_program(root):
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"Expected exactly one canonical program for {TASK_ID}; found {len(programs)}")
    return programs.pop()


def materialize_program(connectivity=DEFAULT_CONNECTIVITY, *, root=None):
    """Return the exact canonical rule, or the single BFS adjacency extension."""
    _check_connectivity(connectivity)
    root = find_root(__file__) if root is None else Path(root)
    canonical = _canonical_program(root)
    neighbor_pattern = re.escape(_FOUR_NEIGHBORS).replace(r"\ ", r"\s+")
    matches = list(re.finditer(neighbor_pattern, canonical))
    if len(matches) != 1:
        raise ValueError("Canonical BFS neighbor expression changed; review this prototype before adapting it")
    if connectivity == DEFAULT_CONNECTIVITY:
        return canonical
    match = matches[0]
    return canonical[:match.start()] + _EIGHT_NEIGHBORS + canonical[match.end():]


class RacketLabeler:
    """Execute materialized lambda bodies through public RacketBridge methods."""

    def __init__(self, *, root=None):
        from arc_repl.racket_bridge import RacketBridge

        self.root = find_root(__file__) if root is None else Path(root).resolve()
        self.canonical_generator, self.generator_path, self.generator_sha256 = load_selected_generator(
            TASK_ID, root=self.root)
        self.programs = {value: materialize_program(value, root=self.root) for value in CONNECTIVITY_VALUES}
        self.cache = {}
        self.executed_grids = 0
        self.bridge = RacketBridge(timeout=15.0)
        try:
            for value, program in self.programs.items():
                if not program.startswith("(rule! (lambda (g)") or not program.endswith(")"):
                    raise ValueError("The prototype expects the canonical legacy (rule! (lambda (g) ...)) form")
                # rule! is an executor directive; its unchanged lambda is the
                # actual transformation executed by the reference runtime.
                expression = program[len("(rule! "):-1]
                self.bridge.eval_text(f"(define parametric-rule-{value} {expression})")
        except BaseException:
            self.bridge.shutdown()
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.bridge.shutdown()
        return False

    def apply(self, grid, connectivity=DEFAULT_CONNECTIVITY):
        _check_connectivity(connectivity)
        source = normalize_grid(grid)
        if max(len(source), len(source[0])) > 30:
            raise ValueError("Prototype rule inputs must have at most 30 rows and columns")
        key = connectivity, tuple(map(tuple, source))
        if key not in self.cache:
            self.bridge.define_grid("parametric-input", source)
            output = normalize_grid(self.bridge.eval_text(f"(parametric-rule-{connectivity} parametric-input)"))
            if (len(output), len(output[0])) != (len(source), len(source[0])):
                raise ValueError("The recoloring rule changed grid dimensions")
            if any(output[r][c] != value for r, row in enumerate(source)
                   for c, value in enumerate(row) if value != 6):
                raise ValueError("The recoloring rule changed a non-6 cell")
            self.cache[key] = output
            self.executed_grids += 1
        return copy.deepcopy(self.cache[key])


def _rng(seed, label):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    # Tagged local streams keep parameter selection independent of pair layout.
    return random.Random(int.from_bytes(hashlib.sha256(f"{TASK_ID}:{VERSION}:{seed}:{label}".encode()).digest(), "big"))


def choose_connectivity(seed):
    """Choose exactly once for an episode; the layout streams never use it."""
    return _rng(seed, "episode-parameter").choice(CONNECTIVITY_VALUES)


def make_input(seed, pair_index, *, profile, difficulty="medium"):
    """Draw a transformed lawful scene; this draw is independent of connectivity."""
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Unknown difficulty: {difficulty!r}")
    if profile not in SCENE_PROFILES:
        raise ValueError(f"Unknown prototype profile: {profile!r}")
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer")
    rng = _rng(seed, f"input:{pair_index}:{profile}:{difficulty}")
    grid = [[7] * 9 for _ in range(9)]
    for shape in _SHAPES[profile]:
        for row, col in shape:
            grid[row][col] = 6
    if profile == "foreign_contact":
        colors = rng.sample([value for value in range(10) if value not in (6, 7)], 5)
        for (row, col), color in zip(((0, 0), (0, 3), (0, 6), (8, 2), (8, 8)), colors):
            grid[row][col] = color
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*reversed(grid))]
    height, width = {"easy": (9, 9), "medium": (9, 10), "hard": (10, 10)}[difficulty]
    top, left = rng.randrange(height - 8), rng.randrange(width - 8)
    result = [[7] * width for _ in range(height)]
    for row in range(9):
        result[row + top][left:left + 9] = grid[row][:]
    return result


def generate_episode(seed, *, connectivity=None, difficulty="medium", labeler=None):
    """Return private episode data: three demos and one query under a fixed rule.

    None means choose the hidden parameter once from seed. Explicit 4 or 8 is
    useful for controlled comparison; the original/default rule setting is 4.
    """
    if labeler is None:
        with RacketLabeler() as owned:
            return generate_episode(seed, connectivity=connectivity, difficulty=difficulty, labeler=owned)
    selected = choose_connectivity(seed) if connectivity is None else connectivity
    _check_connectivity(selected)
    rng = _rng(seed, "episode-profiles")
    profiles = list(SCENE_PROFILES[:3])
    rng.shuffle(profiles)
    profiles.append(rng.choice(SCENE_PROFILES[3:]))
    pairs = []
    for index, profile in enumerate(profiles):
        grid = make_input(seed, index, profile=profile, difficulty=difficulty)
        errors = labeler.canonical_generator.self_check(grid, difficulty=difficulty)
        if errors:
            raise ValueError(f"Prototype scene {profile} is outside the current canonical domain: {errors}")
        pairs.append({"input": grid, "output": labeler.apply(grid, selected), "profile": profile,
                      "canonical_validator_errors": errors})
    return {
        "schema": "48283e01e8ab-parametric-episode-v1", "status": "unapproved_prototype",
        "seed": seed, "difficulty": difficulty, "parameters": {"connectivity": selected},
        "program": labeler.programs[selected], "production_query_index": DEMONSTRATIONS,
        "pairs": pairs,
    }


def parameter_identifiability(episode, *, labeler):
    """Check both declared parameter settings on production and every holdout."""
    selected = episode["parameters"]["connectivity"]
    _check_connectivity(selected)
    pairs = episode["pairs"]
    if len(pairs) < 2:
        raise ValueError("Parameter identification needs a demonstration and a query")
    predictions = {value: [labeler.apply(pair["input"], value) for pair in pairs]
                   for value in CONNECTIVITY_VALUES}
    if any(predictions[selected][index] != pair["output"] for index, pair in enumerate(pairs)):
        raise ValueError("Episode labels disagree with its fixed parameter's executed Racket rule")
    scores = []
    for query_index in range(len(pairs)):
        demos = [index for index in range(len(pairs)) if index != query_index]
        surviving = [value for value in CONNECTIVITY_VALUES
                     if all(predictions[value][index] == pairs[index]["output"] for index in demos)]
        rivals = []
        for value in CONNECTIVITY_VALUES:
            if value == selected:
                continue
            rivals.append({
                "connectivity": value,
                "refuting_demo_indices": [index for index in demos
                                           if predictions[value][index] != pairs[index]["output"]],
                "query_differs": predictions[value][query_index] != pairs[query_index]["output"],
                "survived": value in surviving,
            })
        answer_identifiable = not any(row["survived"] and row["query_differs"] for row in rivals)
        status = "identified" if surviving == [selected] else "answer_equivalent" if answer_identifiable else "ambiguous"
        scores.append({"query_index": query_index, "demo_indices": demos, "status": status,
                       "answer_identifiable": answer_identifiable, "surviving_settings": surviving,
                       "rivals": rivals})
    query_index = episode["production_query_index"]
    if type(query_index) is not int or not 0 <= query_index < len(pairs):
        raise ValueError("Invalid production query index")
    return {"declared_parameter_settings": list(CONNECTIVITY_VALUES), "production": scores[query_index],
            "holdouts": scores,
            "separating_pair_indices": [index for index in range(len(pairs))
                                        if predictions[4][index] != predictions[8][index]]}


def public_challenge(episode):
    """Project private data to an ARC challenge with no metadata or query label."""
    query_index = episode["production_query_index"]
    return {"train": [{"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
                      for index, pair in enumerate(episode["pairs"]) if index != query_index],
            "test": [{"input": copy.deepcopy(episode["pairs"][query_index]["input"])}]}


def _write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run_evidence(out, *, seeds, difficulties=DIFFICULTIES):
    """Retain bounded, source-bound Racket outputs and complete private/public lessons."""
    seeds, difficulties = tuple(seeds), tuple(difficulties)
    if not seeds or not difficulties:
        raise ValueError("Evidence requires nonempty seeds and difficulties")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    source_path = Path(__file__).resolve()
    prototype_sha256 = _sha256(source_path.read_bytes())
    with RacketLabeler(root=root) as labeler:
        programs = {}
        for connectivity, program in labeler.programs.items():
            path = out / f"connectivity_{connectivity}.rkt"
            path.write_text(program, encoding="utf-8")
            programs[str(connectivity)] = {
                "file": path.name, "sha256": _sha256(path.read_bytes()),
                "normalized_sha256_12": _sha256(" ".join(program.split()).encode())[:12],
            }

        canonical = []
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = labeler.apply(pair["input"], DEFAULT_CONNECTIVITY)
            canonical.append({**pair, "racket_output": actual, "exact_match": actual == pair["output"],
                              "canonical_validator_errors": labeler.canonical_generator.self_check(pair["input"])})
        _write_json(out / "canonical_equivalence.json", canonical)

        witnesses = []
        for index, profile in enumerate(SCENE_PROFILES):
            grid = make_input(seeds[0], index, profile=profile, difficulty="easy")
            outputs = {str(value): labeler.apply(grid, value) for value in CONNECTIVITY_VALUES}
            witnesses.append({"seed": seeds[0], "pair_index": index, "difficulty": "easy", "profile": profile,
                              "input": grid, "outputs": outputs,
                              "canonical_validator_errors": labeler.canonical_generator.self_check(grid),
                              "separates": outputs["4"] != outputs["8"]})
        _write_json(out / "separating_witnesses.json", witnesses)

        scores = []
        unique_inputs = set()
        with (out / "episodes_private.jsonl").open("w", encoding="utf-8") as private, \
             (out / "challenges_public.jsonl").open("w", encoding="utf-8") as public:
            for difficulty in difficulties:
                for seed in seeds:
                    for connectivity in CONNECTIVITY_VALUES:
                        episode = generate_episode(seed, connectivity=connectivity, difficulty=difficulty, labeler=labeler)
                        identification = parameter_identifiability(episode, labeler=labeler)
                        identifier = len(scores)
                        score = {"episode_index": identifier, "seed": seed, "difficulty": difficulty,
                                 "parameters": episode["parameters"], **identification}
                        scores.append(score)
                        exported = {key: value for key, value in episode.items() if key != "program"}
                        exported.update(episode_index=identifier, program=programs[str(connectivity)])
                        private.write(json.dumps(exported, sort_keys=True, separators=(",", ":")) + "\n")
                        public.write(json.dumps(public_challenge(episode), sort_keys=True, separators=(",", ":")) + "\n")
                        unique_inputs.update(_sha256(_json_bytes(pair["input"])) for pair in episode["pairs"])

        final_generator_sha256 = _sha256(labeler.generator_path.read_bytes())
        current_prototype_sha256 = _sha256(source_path.read_bytes())
        stable_sources = (final_generator_sha256 == labeler.generator_sha256
                          and current_prototype_sha256 == prototype_sha256
                          and _canonical_program(root) == labeler.programs[DEFAULT_CONNECTIVITY])
        verdict = (stable_sources and bool(canonical) and all(row["exact_match"] for row in canonical)
                   and all(not row["canonical_validator_errors"] for row in canonical + witnesses)
                   and all(row["separates"] for row in witnesses)
                   and all(score["production"]["status"] == "identified" for score in scores)
                   and all(holdout["status"] == "identified" for score in scores for holdout in score["holdouts"]))
        report = {
            "schema": "48283e01e8ab-parametric-evidence-v1", "status": "unapproved_prototype",
            "evidence_passed": verdict, "source_stable_during_run": stable_sources,
            "task_id": TASK_ID, "prototype_version": VERSION,
            "prototype_source": source_path.relative_to(root).as_posix(),
            "prototype_source_sha256": prototype_sha256,
            "generator_source": labeler.generator_path.relative_to(root).as_posix(),
            "generator_source_sha256": labeler.generator_sha256,
            "canonical_default_program_is_exact_canonical_text": labeler.programs[4] == _canonical_program(root),
            "programs": programs, "runtime": labeler.bridge.runtime_identity,
            "parameter_contract": {"name": "connectivity", "allowed": list(CONNECTIVITY_VALUES), "original_default": 4,
                                   "episode_fixed": True, "input_distribution_depends_on_parameter": False,
                                   "rivals": ["connectivity=4", "connectivity=8"]},
            "seeds": list(seeds), "difficulties": list(difficulties),
            "seeded_auto_selections": [{"seed": seed, "connectivity": choose_connectivity(seed)} for seed in seeds],
            "lesson_policy": {"demonstrations": DEMONSTRATIONS, "queries": 1,
                              "production_query_index": DEMONSTRATIONS,
                              "demo_order": "seeded permutation of three scene profiles",
                              "query_profile": "seeded choice among three other profiles",
                              "holdouts": "every one of four pairs; other three pairs are demonstrations"},
            "counts": {"canonical_occurrences": len(canonical),
                       "canonical_unique_pairs": len({_sha256(_json_bytes([row["input"], row["output"]])) for row in canonical}),
                       "canonical_exact_matches": sum(row["exact_match"] for row in canonical),
                       "lawful_separating_witnesses": sum(row["separates"] and not row["canonical_validator_errors"] for row in witnesses),
                       "episodes": len(scores), "episode_pair_occurrences": len(scores) * 4,
                       "episode_unique_inputs": len(unique_inputs),
                       "production_identified": sum(score["production"]["status"] == "identified" for score in scores),
                       "holdouts": sum(len(score["holdouts"]) for score in scores),
                       "holdouts_identified": sum(holdout["status"] == "identified" for score in scores for holdout in score["holdouts"]),
                       "executed_unique_input_setting_labels": labeler.executed_grids},
            "lesson_checks": scores,
            "limitations": [
                "Unapproved task-local prototype; canonical approval and production interfaces are unchanged.",
                "Measured coverage is limited to the listed seeds, difficulties, scene templates and declared two-value parameter rival family.",
                "The six contact templates intentionally ensure distinguishable parameters; they are not a broad sampler of all lawful grids.",
                "Parameter identifiability does not establish identifiability against arbitrary shape, color-table or template-memorization rivals.",
                "Raw rule execution accepts rectangular 1..30 ARC grids; exported episodes additionally pass the current canonical generator self_check.",
                "Default equality on every legal input follows from preserving the exact canonical lambda; empirical canonical coverage is separately counted.",
            ],
            "payload_command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        }
        _write_json(out / "report.json", report)
    inventory = {path.name: {"bytes": path.stat().st_size, "sha256": _sha256(path.read_bytes())}
                 for path in sorted(out.iterdir()) if path.is_file()}
    _write_json(out / "files.json", inventory)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory; existing directories are refused")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 17, 83])
    parser.add_argument("--difficulties", nargs="+", choices=DIFFICULTIES, default=list(DIFFICULTIES))
    args = parser.parse_args(argv)
    report = run_evidence(args.out, seeds=args.seeds, difficulties=args.difficulties)
    print(json.dumps({"status": report["status"], "evidence_passed": report["evidence_passed"],
                      "counts": report["counts"], "report": str(args.out / "report.json")}, sort_keys=True))
    return 0 if report["evidence_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
