#!/usr/bin/env python3
"""Proposed, unapproved episode-fixed convex-hull output policies.

Run through the packet's review.py run wrapper; Racket is the label authority.
No selected generator or production runtime interface is changed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "3e0aef964b9e"
SETTINGS = (("move", "donor"), ("move", "target"), ("copy", "donor"), ("copy", "target"))
DEFAULT = SETTINGS[0]
ROOT = find_root(__file__)
_CANONICAL_CACHE = None


def sha256(body):
    return hashlib.sha256(body).hexdigest()


def selected_generator():
    return load_selected_generator(TASK_ID, root=ROOT)


def canonical_rule():
    # Cache parsing, not authority: read and hash current ledger bytes on each
    # call, so even a same-size, timestamp-preserving edit cannot return stale
    # code. Keep only the digest and selected program, not a copied data tree.
    global _CANONICAL_CACHE
    body = canonical_path(ROOT).read_bytes()
    digest = sha256(body)
    if _CANONICAL_CACHE is not None and _CANONICAL_CACHE[0] == digest:
        return _CANONICAL_CACHE[1]
    programs = []
    for line in body.splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise ValueError("expected one exact canonical program across selected task variants")
    _CANONICAL_CACHE = (digest, programs[0])
    return programs[0]


def materialize_rule(donor_policy="move", fill_policy="donor"):
    """Retain canonical selection verbatim; alter only the final output policy."""
    if (donor_policy, fill_policy) not in SETTINGS:
        raise ValueError("allowed policies: donor_policy=move|copy, fill_policy=donor|target")
    source = canonical_rule()
    clear = "(cleared (paint-cells g (find-color g donor) bg))"
    fill = "(paint-cells cleared missing donor)"
    if source.count(clear) != 1 or source.count(fill) != 1:
        raise ValueError("canonical output tail changed; re-review prototype substitutions")
    if donor_policy == "copy":
        source = source.replace(clear, "(cleared g)")
    if fill_policy == "target":
        source = source.replace(fill, "(paint-cells cleared missing (obj-color (fst cand)))")
    return source


def execute(bridge, program, grid):
    """Apply the selected self-contained lambda through the supported bridge."""
    grid = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    body = strip_rule_wrapper(program)
    if not body.startswith("(lambda (g)"):
        raise ValueError("prototype supports only the selected self-contained lambda contract")
    return normalize_grid(bridge.eval_text(f"({body} {literal})"))


def _integer(value, name, *, nonnegative=False):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not bool")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")


def choose_setting(seed):
    """Choose the rule once from a stable domain-separated hash of episode seed."""
    _integer(seed, "seed")
    digest = hashlib.sha256(f"{TASK_ID}:output-policies-v1:{seed}".encode()).digest()
    return SETTINGS[int.from_bytes(digest[:8], "big") % len(SETTINGS)]


def source_identity():
    _, generator_path, generator_hash = selected_generator()
    paths = {
        "prototype": Path(__file__),
        "test": Path(__file__).parents[2] / "tests/test_parametric.py",
        "readme": Path(__file__).with_name("README.md"),
        "reviewer_support": ROOT / "shared/runtime/reviewer_support.py",
        "bridge": ROOT / "shared/runtime/arc_repl/racket_bridge.py",
        "rule_wrapper": ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
        "prelude": ROOT / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
        "generator_base": ROOT / "shared/runtime/puzzle_generators/base.py",
        "grid_helpers": ROOT / "shared/runtime/puzzle_generators/helpers/grid.py",
        "canonical_ledger": canonical_path(ROOT),
    }
    result = {"generator_path": str(generator_path.relative_to(ROOT)), "generator_sha256": generator_hash,
              "canonical_program_sha256": sha256(canonical_rule().encode())}
    for name, path in paths.items():
        result[name + "_path"] = str(path.relative_to(ROOT))
        result[name + "_sha256"] = sha256(path.read_bytes())
    return result


def build_episode(seed, episode_index=0, *, setting=None, difficulty=None, bridge=None):
    """Return public challenge and private replay/answer evidence for one rule.

    Sampling never depends on the output policies. Three consecutive scheduled
    demonstrations precede one query; each rival must be refuted by demos alone.
    The optional setting override permits a finite exhaustive four-setting census.
    """
    _integer(seed, "seed")
    _integer(episode_index, "episode_index", nonnegative=True)
    chosen = choose_setting(seed) if setting is None else tuple(setting)
    if chosen not in SETTINGS:
        raise ValueError("unsupported parameter setting")
    if bridge is None:
        with RacketBridge(timeout=20) as owned_bridge:
            result = build_episode(seed, episode_index, setting=chosen, difficulty=difficulty, bridge=owned_bridge)
        result["private"]["parameter_selection"] = "deterministic_seed" if setting is None else "explicit_census_setting"
        return result
    gen, source, digest = selected_generator()
    indices = list(range(episode_index * 4, episode_index * 4 + 4))
    grids = [gen.generate(seed, index, difficulty=difficulty) for index in indices]
    programs = {setting: materialize_rule(*setting) for setting in SETTINGS}
    outputs = {setting: [execute(bridge, program, grid) for grid in grids]
               for setting, program in programs.items()}
    for grid, output in zip(grids, outputs[DEFAULT]):
        if gen.self_check(grid):
            raise ValueError("selected generator returned an unlawful scene")
        if output != gen.rule_mirror(grid):
            raise ValueError("canonical Racket/Python mismatch; prototype cannot certify source")
    checks = []
    for rival in SETTINGS:
        if rival == chosen:
            continue
        witnesses = [i for i in range(3) if outputs[rival][i] != outputs[chosen][i]]
        if not witnesses:
            raise ValueError(f"unidentifiable demonstrations against {rival!r}")
        checks.append({"rival_parameters": dict(zip(("donor_policy", "fill_policy"), rival)),
                       "refuted_by_demo_indices": witnesses,
                       "rival_query_differs": outputs[rival][3] != outputs[chosen][3]})
    public = {"train": [{"input": grid, "output": answer}
                         for grid, answer in zip(grids[:3], outputs[chosen][:3])],
              "test": [{"input": grids[3]}]}
    private = {"status": "proposed_unapproved_prototype", "seed": seed,
               "episode_index": episode_index, "difficulty": difficulty, "sample_indices": indices,
               "parameters": dict(zip(("donor_policy", "fill_policy"), chosen)),
               "parameter_selection": "deterministic_seed" if setting is None else "explicit_census_setting",
               "generator_path": str(source.relative_to(ROOT)), "generator_sha256": digest,
               "rule_sha256": sha256(programs[chosen].encode()),
               "query_outputs": [outputs[chosen][3]], "rival_checks": checks}
    return {"public": deepcopy(public), "private": private}


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def write_evidence(out, *, seed=73, episodes_per_setting=1, difficulty=None):
    """Write bounded materialized rules, complete episodes, and difference witness."""
    _integer(seed, "seed")
    _integer(episodes_per_setting, "episodes_per_setting", nonnegative=True)
    if not 1 <= episodes_per_setting <= 8:
        raise ValueError("episodes_per_setting must be 1..8 for this bounded prototype")
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"use a fresh evidence directory: {out}")
    source = source_identity()
    rules = []
    episodes = []
    with RacketBridge(timeout=20) as bridge:
        for setting in SETTINGS:
            program = materialize_rule(*setting)
            relative = Path("private/rules") / ("_".join(setting) + ".rkt")
            path = out / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(program, encoding="utf-8")
            rules.append({"parameters": dict(zip(("donor_policy", "fill_policy"), setting)),
                          "path": relative.as_posix(), "sha256": sha256(program.encode())})
            for offset in range(episodes_per_setting):
                number = len(episodes)
                # Cover the finite policy domain through the native seed-based
                # builder, rather than silently overriding its hidden rule.
                candidates = range(seed + offset * 1024, seed + (offset + 1) * 1024)
                episode_seed = next((candidate for candidate in candidates if choose_setting(candidate) == setting), None)
                if episode_seed is None:
                    raise ValueError(f"no seed selects {setting!r} in the declared 1024-seed search window")
                episode = build_episode(episode_seed, offset, difficulty=difficulty, bridge=bridge)
                public_path = f"public/episode-{number:03d}.json"
                private_path = f"private/episode-{number:03d}.json"
                _write_json(out / public_path, episode["public"])
                _write_json(out / private_path, episode["private"])
                episodes.append({"public_path": public_path, "private_path": private_path,
                                 "public_sha256": sha256((out / public_path).read_bytes()),
                                 "private_sha256": sha256((out / private_path).read_bytes())})
        gen, _, _ = selected_generator()
        grid = gen.generate(seed, 0, difficulty=difficulty)
        witness = {"seed": seed, "sample_index": 0, "difficulty": difficulty, "input": grid,
                   "settings": [{"parameters": dict(zip(("donor_policy", "fill_policy"), setting)),
                                 "output": execute(bridge, materialize_rule(*setting), grid)} for setting in SETTINGS]}
    distinct = len({json.dumps(row["output"]) for row in witness["settings"]})
    if distinct != 4:
        raise ValueError("the same lawful input must distinguish all four settings")
    if source_identity() != source:
        raise RuntimeError("source changed during evidence collection; rerun after source freeze")
    _write_json(out / "private/same-input-witness.json", witness)
    manifest = {"status": "proposed_unapproved_prototype", "task_id": TASK_ID,
                "source": source, "seed": seed, "episodes_per_setting": episodes_per_setting,
                "policy_seed_search_window": 1024,
                "rules": rules, "episodes": episodes, "same_input_witness": "private/same-input-witness.json",
                "limits": "Finite four-policy evidence; not production approval or universal program identifiability."}
    _write_json(out / "private/manifest.json", manifest)
    return {"episode_count": len(episodes), "same_input_distinct_outputs": distinct,
            "manifest": str(out / "private/manifest.json"), "source": source}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=73)
    parser.add_argument("--episodes-per-setting", type=int, default=1)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    args = parser.parse_args()
    print(json.dumps(write_evidence(args.out, seed=args.seed, episodes_per_setting=args.episodes_per_setting,
                                    difficulty=args.difficulty), sort_keys=True))


if __name__ == "__main__":
    main()
