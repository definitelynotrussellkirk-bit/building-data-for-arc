#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/14c5c68b0201/workspace/parametric/prototype.py"


def load_proto():
    spec = importlib.util.spec_from_file_location("adversarial_parametric_14c5c68b0201", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_plain_numeric_tree(value):
    if isinstance(value, dict):
        if not all(type(key) is str for key in value):
            raise AssertionError("public object contains a non-string key")
        for child in value.values():
            assert_plain_numeric_tree(child)
    elif isinstance(value, list):
        for child in value:
            assert_plain_numeric_tree(child)
    elif type(value) is int:
        if not 0 <= value <= 9:
            raise AssertionError(f"public color outside 0..9: {value}")
    else:
        raise AssertionError(f"public object contains non-grid leaf {type(value).__name__}")


def main():
    started = time.monotonic()
    proto = load_proto()
    parity_cases = 0
    distinct_cases = 0
    privacy_cases = 0
    output_hashes = set()

    with RacketBridge(max_calls_before_restart=128) as bridge:
        programs = {setting: proto.instantiate_rule(setting, root=ROOT) for setting in proto.TILING_AXES}
        for setting, program in programs.items():
            assert proto.restore_canonical(program, root=ROOT) == proto.canonical_rule(root=ROOT)

        # Boundary-size episodes (1 demo, 1 query), varied seeds, every grid run
        # through all exact Racket settings. This probes parity without relying
        # on the Python generator as a label oracle.
        for seed in range(6):
            grids = proto.generate_inputs(seed, demo_count=1, query_count=1)
            for grid in grids:
                by_setting = {
                    setting: proto.evaluate(bridge, program, grid)
                    for setting, program in programs.items()
                }
                parity_cases += len(by_setting)
                hashes = {setting: proto.grid_sha256(output) for setting, output in by_setting.items()}
                output_hashes.update(hashes.values())
                if len(set(hashes.values())) != len(proto.TILING_AXES):
                    raise AssertionError(f"axis settings collapsed for seed {seed}: {hashes}")
                distinct_cases += 1

        # Exercise public projection at the minimum legal counts for every
        # setting, then mutate all private fields and hidden query labels.
        for setting in proto.TILING_AXES:
            episode = proto.make_episode(
                bridge,
                101,
                tiling_axes=setting,
                demo_count=1,
                query_count=1,
            )
            public = proto.public_challenge(episode)
            assert_plain_numeric_tree(public)
            visible_bytes = public_challenge_bytes(public)
            visible_id = public_challenge_id(public)
            if proto.public_filename(episode) != f"challenge-{visible_id}.json":
                raise AssertionError("prototype filename disagrees with public helper")
            lowered = visible_bytes.lower()
            for forbidden in (b"tiling_axes", b"racket", b"seed", b"parameters", b"output_sha256"):
                if forbidden in lowered:
                    raise AssertionError(f"private token leaked: {forbidden!r}")

            hidden = deepcopy(episode)
            hidden["seed"] = 999999
            hidden["parameters"] = {"tiling_axes": "vertical" if setting != "vertical" else "both"}
            hidden["racket_program"] = "not visible"
            hidden["test"][0]["output"] = [[9]]
            hidden["test"][0]["output_sha256"] = "0" * 64
            if public_challenge_bytes(proto.public_challenge(hidden)) != visible_bytes:
                raise AssertionError("private mutation changed visible bytes")
            if proto.public_filename(hidden) != proto.public_filename(episode):
                raise AssertionError("private mutation changed public filename")

            changed = deepcopy(episode)
            changed["test"][0]["input"][0][0] = (changed["test"][0]["input"][0][0] + 1) % 10
            if proto.public_filename(changed) == proto.public_filename(episode):
                raise AssertionError("visible input mutation did not change public filename")
            privacy_cases += 1

    result = {
        "schema": "arcpuzzles-parametric-adversarial-probe-v1",
        "task_id": proto.TASK_ID,
        "prototype_version": proto.PROTOTYPE_VERSION,
        "status": "bounded_no_finding",
        "surfaces": ["parameter_racket_parity", "public_private_export_and_numeric_types"],
        "parity_racket_evaluations": parity_cases,
        "axis_distinguishing_inputs": distinct_cases,
        "privacy_numeric_episodes": privacy_cases,
        "distinct_output_hashes_observed": len(output_hashes),
        "seeds": list(range(6)),
        "episode_counts": {"demonstrations": 1, "queries": 1},
        "canonical_sha256": proto.CANONICAL_SHA256,
        "prototype_sha256": proto.sha256(PROTOTYPE.read_bytes()),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limits": [
            "Bounded to seeds 0..5 and declared both/horizontal/vertical settings.",
            "Does not establish production approval or exhaust every legal grid.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
