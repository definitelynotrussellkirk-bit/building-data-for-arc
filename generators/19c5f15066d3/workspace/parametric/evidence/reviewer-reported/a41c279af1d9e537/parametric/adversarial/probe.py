from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import load_selected_generator, public_challenge_id

TASK_ID = "19c5f15066d3"
ROOT = Path.cwd().resolve()
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
OUT = ROOT.parent / "checks" / "parametric" / "adversarial" / "report.json"


def load_prototype():
    spec = importlib.util.spec_from_file_location("adversarial_proximity_prototype", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load proximity prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha_json(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def object_distance(item, info) -> int:
    values = []
    for row, col in item["cells"]:
        values.extend(abs(col - line) for line in info["vcols"])
        values.extend(abs(row - line) for line in info["hrows"])
    return min(values)


def expect_value_error(fn, label: str) -> str:
    try:
        fn()
    except ValueError as exc:
        return f"{type(exc).__name__}: {exc}"
    raise RuntimeError(f"expected ValueError for {label}")


def main() -> None:
    prototype = load_prototype()
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=ROOT)

    sampler_seeds = [0, 1, 2, 17, 2**63 - 1]
    scene_count = 0
    input_hashes = set()
    for seed in sampler_seeds:
        grids = prototype.distinguishing_inputs(seed, prototype.MAX_EPISODE_PAIRS)
        if len(grids) != prototype.MAX_EPISODE_PAIRS:
            raise RuntimeError("maximum-count sampler returned the wrong number of scenes")
        local_hashes = [sha_json(grid) for grid in grids]
        if len(set(local_hashes)) != len(local_hashes):
            raise RuntimeError(f"duplicate scene within seed {seed}")
        for grid in grids:
            errors = generator.self_check(grid)
            if errors:
                raise RuntimeError(f"sampler emitted invalid scene: {errors}")
            info = generator._analysis(grid)
            distances = sorted(object_distance(item, info) for item in info["red_objects"])
            if distances != [0, 1, 2, 4]:
                raise RuntimeError(f"distance witnesses drifted: {distances}")
            outputs = [prototype.solve(grid, proximity_radius=value) for value in prototype.ALLOWED_PROXIMITY_RADII]
            if len({sha_json(output) for output in outputs}) != 3:
                raise RuntimeError("scene does not distinguish all radius settings")
        scene_count += len(grids)
        input_hashes.update(local_hashes)

    max_seed = 2**63 - 1
    episode = prototype.make_episode(
        max_seed,
        n_train=12,
        n_test=4,
        root=ROOT,
    )
    pairs = episode["train"] + episode["test"]
    if episode["counts"] != {"demonstrations": 12, "queries": 4}:
        raise RuntimeError(f"unexpected max-count episode counts: {episode['counts']}")
    if len({pair["input_sha256"] for pair in pairs}) != 16:
        raise RuntimeError("max-count episode contains duplicate inputs")
    if episode["ambiguities"]:
        raise RuntimeError(f"max-count episode retained ambiguity: {episode['ambiguities']}")

    fresh_grid = prototype.distinguishing_inputs(max_seed, 1)[0]
    racket_checks = []
    with RacketBridge() as bridge:
        for radius in prototype.ALLOWED_PROXIMITY_RADII:
            program = prototype.materialize_rule(radius, root=ROOT)
            actual = prototype.execute_rule(program, fresh_grid, bridge=bridge)
            expected = prototype.solve(fresh_grid, proximity_radius=radius)
            row = {
                "proximity_radius": radius,
                "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                "racket_matches_python": actual == expected,
                "output_sha256": sha_json(actual),
            }
            if not row["racket_matches_python"]:
                raise RuntimeError(f"fresh Racket parity failed for radius {radius}")
            racket_checks.append(row)

    public = prototype.public_challenge(copy.deepcopy(episode))
    public_id = public_challenge_id(public)
    changed_private = copy.deepcopy(episode)
    changed_private["seed"] = 0
    changed_private["parameters"] = {"proximity_radius": 0}
    changed_private["racket_source"] = "private-only mutation"
    changed_private["test"][0]["output"] = [[9]]
    private_mutation_id = public_challenge_id(prototype.public_challenge(changed_private))
    if private_mutation_id != public_id:
        raise RuntimeError("public ID changed after private-only mutation")

    changed_visible = copy.deepcopy(public)
    old = changed_visible["test"][0]["input"][0][0]
    changed_visible["test"][0]["input"][0][0] = (old + 1) % 10
    visible_mutation_id = public_challenge_id(changed_visible)
    if visible_mutation_id == public_id:
        raise RuntimeError("public ID did not change after visible input mutation")
    if any("output" in pair for pair in public["test"]):
        raise RuntimeError("public query answers were not masked")

    bool_public = copy.deepcopy(public)
    bool_public["test"][0]["input"][0][0] = True
    bool_rejection = expect_value_error(lambda: public_challenge_id(bool_public), "boolean public cell")
    invalid_rejections = {
        "bool_seed": expect_value_error(lambda: prototype.make_episode(True, root=ROOT), "bool seed"),
        "negative_seed": expect_value_error(lambda: prototype.make_episode(-1, root=ROOT), "negative seed"),
        "seed_above_bound": expect_value_error(lambda: prototype.make_episode(2**63, root=ROOT), "seed above bound"),
        "pair_count_above_bound": expect_value_error(
            lambda: prototype.make_episode(0, n_train=13, n_test=4, root=ROOT),
            "pair count above bound",
        ),
    }

    report = {
        "schema": "arcpuzzles-proximity-adversarial-v1",
        "task_id": TASK_ID,
        "status": "bounded_no_finding",
        "source_binding": {
            "generator_path": generator_path.relative_to(ROOT).as_posix(),
            "generator_sha256": generator_sha256,
            "prototype_path": PROTOTYPE_PATH.relative_to(ROOT).as_posix(),
            "prototype_sha256": hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest(),
        },
        "surface_sampler_count_and_seed_boundaries": {
            "seeds": sampler_seeds,
            "scenes_checked": scene_count,
            "unique_inputs_across_checked_seeds": len(input_hashes),
            "per_scene_requirements": [
                "selected generator self_check accepts input",
                "red-object distances are exactly 0,1,2,4",
                "all three radius outputs are distinct",
            ],
            "max_episode_counts": episode["counts"],
            "max_episode_selected_radius": episode["parameters"]["proximity_radius"],
            "invalid_rejections": invalid_rejections,
        },
        "surface_racket_and_public_private_boundary": {
            "fresh_seed": max_seed,
            "racket_checks": racket_checks,
            "public_id": public_id,
            "private_mutation_id": private_mutation_id,
            "visible_mutation_id": visible_mutation_id,
            "private_mutation_preserves_public_id": private_mutation_id == public_id,
            "visible_mutation_changes_public_id": visible_mutation_id != public_id,
            "query_answers_masked": all("output" not in pair for pair in public["test"]),
            "boolean_cell_rejection": bool_rejection,
        },
        "stopping_reason": "five-seed maximum-count sampler check plus one fresh exact-Racket/public-boundary probe completed; no broader seed census was run",
        "limits": [
            "The sampler check covers 80 constructed scenes, not every seed.",
            "Racket parity at the adversarial boundary covers one fresh input per setting; the retained verifier separately covers all 21 retained episode pairs.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "scenes_checked": scene_count,
        "racket_settings_checked": len(racket_checks),
        "public_boundary": True,
        "report": str(OUT.relative_to(ROOT.parent)),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
