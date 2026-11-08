"""Proposed fixed-per-episode stamp rotation; labels always come from Racket.

Run through the packet's review.py run wrapper. This module never replaces the
selected canonical generator/rule or changes an approval record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper

TASK_ID = "28423cdf02cc"
PARAMETER_VALUES = (0, 1, 2, 3)
CANONICAL_RULE_HASH = "63b41fa0b187"
_LOOKUP = "(nth (nth pat pr) pc)"
_ROTATED_LOOKUPS = (
    _LOOKUP,
    "(nth (nth pat (- 2 pc)) pr)",
    "(nth (nth pat (- 2 pr)) (- 2 pc))",
    "(nth (nth pat pc) (- 2 pr))",
)


def _sha(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _integer(name, value, *, minimum=None, maximum=None):
    if type(value) is not int:
        raise TypeError(f"{name} must be a Python int, not {type(value).__name__}")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return value


def _root(root):
    return Path(root).resolve() if root is not None else find_root(__file__)


def _canonical_program(root):
    programs = []
    with canonical_path(root).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("Expected exactly one selected canonical program")
    program = programs[0]
    if _sha(" ".join(program.split()))[:12] != CANONICAL_RULE_HASH:
        raise ValueError("Canonical rule changed; review this prototype before reuse")
    if program.count(_LOOKUP) != 1:
        raise ValueError("Expected exactly one canonical template lookup")
    return program


def materialize_rule(quarter_turns, *, root=None):
    """Return exact Racket source; zero turns preserves canonical source bytes."""
    _integer("quarter_turns", quarter_turns, minimum=0, maximum=3)
    program = _canonical_program(_root(root))
    return program.replace(_LOOKUP, _ROTATED_LOOKUPS[quarter_turns], 1)


def label_settings(grids, *, root=None, bridge=None):
    """Execute all four rule settings on the same inputs using the real bridge."""
    root = _root(root)
    if bridge is None:
        with RacketBridge() as runtime:
            return label_settings(grids, root=root, bridge=runtime)
    canonical = _canonical_program(root)
    outputs = {}
    for turns in PARAMETER_VALUES:
        program = canonical.replace(_LOOKUP, _ROTATED_LOOKUPS[turns], 1)
        # This hash-pinned authority is already a native Racket lambda with
        # explicit h/w bindings and full for/list syntax. Only peel rule!;
        # general shorthand conversion depends on the legacy scripts layout.
        bridge.eval_text(f"(define __stamp_rotation_rule {strip_rule_wrapper(program)})")
        labels = []
        for grid in grids:
            bridge.define_grid("__stamp_rotation_input", grid)
            labels.append(bridge.eval_text("(__stamp_rotation_rule __stamp_rotation_input)"))
        outputs[turns] = labels
    return outputs


def assess_settings(selected, outputs_by_setting):
    """Reusable finite-setting checker for one three-demo, one-query episode.

    Reports each possible query holdout separately. An answer-equivalent rival
    is distinguished from an identified parameter and from a query ambiguity.
    It consumes already executed labels; it does not pretend to discover rivals.
    """
    if selected not in outputs_by_setting or len(outputs_by_setting) < 2:
        raise ValueError("Need a selected setting and at least one declared rival")
    if any(len(outputs) != 4 for outputs in outputs_by_setting.values()):
        raise ValueError("Each setting must supply exactly four labelled pairs")
    chosen = outputs_by_setting[selected]
    rotations = []
    for query_index in range(4):
        demo_indices = [index for index in range(4) if index != query_index]
        rivals, ambiguous, equivalent, survivors = [], [], [], []
        for setting, outputs in outputs_by_setting.items():
            if setting == selected:
                continue
            refuted_by = [i for i in demo_indices if outputs[i] != chosen[i]]
            changes_query = outputs[query_index] != chosen[query_index]
            if not refuted_by:
                survivors.append(setting)
                (ambiguous if changes_query else equivalent).append(setting)
            rivals.append({"setting": setting, "refuted_by_demo_indices": refuted_by,
                           "changes_query": changes_query})
        rotations.append({"query_index": query_index, "demo_indices": demo_indices,
                          "parameter_identified": not survivors,
                          "ambiguous_settings": ambiguous,
                          "equivalent_settings": equivalent, "rivals": rivals})
    return {"scope": "declared_parameter_settings_only", "selected_setting": selected,
            "production": rotations[3], "rotations": rotations}


def generate_episode(seed, *, quarter_turns=None, difficulty="medium", start_index=0,
                     root=None, bridge=None):
    """Build one fixed-rule episode, keeping inputs independent of the setting."""
    _integer("seed", seed, minimum=0)
    _integer("start_index", start_index, minimum=0)
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    if quarter_turns is None:
        quarter_turns = int(_sha(f"stamp-rotation-v1:{seed}")[:16], 16) % 4
        selection = "sha256(stamp-rotation-v1:seed), first 16 hex digits modulo 4"
    else:
        _integer("quarter_turns", quarter_turns, minimum=0, maximum=3)
        selection = "explicit episode setting"
    root = _root(root)
    generator, _, generator_hash = load_selected_generator(TASK_ID, root=root)
    indices = list(range(start_index, start_index + 4))
    grids = [generator.generate(seed, index, difficulty=difficulty) for index in indices]
    for grid in grids:
        errors = generator.self_check(grid)
        if errors:
            raise ValueError("Canonical input grammar rejected episode: " + "; ".join(errors))
    labels = label_settings(grids, root=root, bridge=bridge)
    setting_check = assess_settings(quarter_turns, labels)
    if not all(row["parameter_identified"] for row in setting_check["rotations"]):
        raise ValueError("Episode does not identify its setting under every query rotation")
    program = materialize_rule(quarter_turns, root=root)
    public = {"train": [{"input": grid, "output": output}
                        for grid, output in zip(grids[:3], labels[quarter_turns][:3])],
              "test": [{"input": grids[3]}]}
    private = {
        "schema": "arcpuzzles-stamp-rotation-episode-v1", "status": "prototype",
        "task_id": TASK_ID, "training_admitted": False,
        "parameters": {"quarter_turns": quarter_turns}, "parameter_selection": selection,
        "seed": seed, "difficulty": difficulty, "sample_indices": indices,
        "generator_sha256": generator_hash, "prototype_sha256": _sha(Path(__file__).read_bytes()),
        "canonical_program_sha256": _sha(materialize_rule(0, root=root)),
        "program": program, "program_sha256": _sha(program),
        "input_sha256": [_sha(_canonical_json(grid)) for grid in grids],
        "test_outputs": labels[quarter_turns][3:], "setting_check": setting_check,
    }
    return {"public": public, "private": private}


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def build_evidence(out, *, seeds=(0, 17), bands=("easy", "medium", "hard"), turns="all",
                   root=None):
    """Materialize a bounded, reproducible suite and separated public challenges."""
    out, root = Path(out), _root(root)
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite evidence directory: {out}")
    settings = PARAMETER_VALUES if turns == "all" else (None if turns == "auto" else int(turns),)
    for setting in settings:
        if setting is not None:
            _integer("quarter_turns", setting, minimum=0, maximum=3)
    for seed in seeds:
        _integer("seed", seed, minimum=0)
    if not seeds or not bands or any(band not in ("easy", "medium", "hard") for band in bands):
        raise ValueError("At least one seed and valid difficulty band are required")
    out.mkdir(parents=True)
    _, source, generator_hash = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root)
    report = {"schema": "arcpuzzles-stamp-rotation-evidence-v1", "status": "running",
              "task_id": TASK_ID, "prototype_status": "proposed", "training_admitted": False,
              "generator_sha256": generator_hash, "prototype_sha256": _sha(Path(__file__).read_bytes()),
              "parameters": {"quarter_turns": {"allowed": list(PARAMETER_VALUES), "default": 0,
                                                 "meaning": "clockwise quarter turns of each copied stamp"}},
              "seeds": list(seeds), "bands": list(bands), "settings_requested": turns,
              "command_argv": sys.argv, "episodes": [], "rules": {},
              "limits": ["Finite declared settings and saved inputs, not universal rule identification.",
                         "Canonical input constraints remain: full asymmetric 3x3 template and nonoverlapping stamps.",
                         "Prototype is separate from production generation and has no training admission."]}
    try:
        with RacketBridge() as bridge:
            report["runtime_identity"] = bridge.runtime_identity
            expected = [pair["output"] for pair in canonical]
            observed = label_settings([pair["input"] for pair in canonical], root=root, bridge=bridge)[0]
            if observed != expected:
                raise AssertionError("Zero-turn Racket labels failed canonical parity")
            report["canonical_default_pairs_passed"] = len(canonical)
            for setting in PARAMETER_VALUES:
                program = materialize_rule(setting, root=root)
                path = out / "rules" / f"quarter_turns_{setting}.rkt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(program)
                report["rules"][str(setting)] = {"path": str(path.relative_to(out)),
                                                "sha256": _sha(program)}
            first_witness = None
            for band in bands:
                for seed in seeds:
                    for setting in settings:
                        # Exercise different schedule starts without letting the
                        # parameter influence input construction.
                        start = seed % 5
                        episode = generate_episode(seed, quarter_turns=setting, difficulty=band,
                                                   start_index=start, root=root, bridge=bridge)
                        number = len(report["episodes"])
                        public_path = out / "public" / f"episode_{number:03d}.json"
                        private_path = out / "private" / f"episode_{number:03d}.json"
                        _write_json(public_path, episode["public"])
                        _write_json(private_path, episode["private"])
                        report["episodes"].append({"episode_index": number, "seed": seed, "band": band,
                                                   "quarter_turns": episode["private"]["parameters"]["quarter_turns"],
                                                   "public": str(public_path.relative_to(out)),
                                                   "private": str(private_path.relative_to(out)),
                                                   "public_sha256": _sha(public_path.read_bytes()),
                                                   "private_sha256": _sha(private_path.read_bytes()),
                                                   "production_identified": True, "identified_query_rotations": 4})
                        if first_witness is None:
                            grid = episode["public"]["train"][0]["input"]
                            labels = label_settings([grid], root=root, bridge=bridge)
                            if len({_canonical_json(labels[t][0]) for t in PARAMETER_VALUES}) != 4:
                                raise AssertionError("First witness does not distinguish all settings")
                            first_witness = {"input": grid, "input_sha256": _sha(_canonical_json(grid)),
                                             "outputs_by_quarter_turns": {str(t): labels[t][0] for t in PARAMETER_VALUES},
                                             "generator_sha256": generator_hash,
                                             "self_check_errors": [], "labels_from": "executed Racket programs",
                                             "rule_sha256": {str(t): report["rules"][str(t)]["sha256"] for t in PARAMETER_VALUES}}
                            _write_json(out / "parameter-witness.json", first_witness)
                        _write_json(out / "report.json", report)
            report.update(status="passed", episode_count=len(report["episodes"]),
                          labelled_pairs=4*len(report["episodes"]),
                          production_identified=len(report["episodes"]),
                          query_rotations_identified=4*len(report["episodes"]))
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
        _write_json(out / "report.json", report)
        raise
    _write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"),
                        default=["easy", "medium", "hard"])
    parser.add_argument("--turns", choices=("all", "auto", "0", "1", "2", "3"), default="all")
    args = parser.parse_args(argv)
    report = build_evidence(args.out, seeds=args.seeds, bands=args.bands, turns=args.turns)
    print(json.dumps({key: report[key] for key in ("status", "episode_count", "labelled_pairs",
                                                   "production_identified", "query_rotations_identified")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
