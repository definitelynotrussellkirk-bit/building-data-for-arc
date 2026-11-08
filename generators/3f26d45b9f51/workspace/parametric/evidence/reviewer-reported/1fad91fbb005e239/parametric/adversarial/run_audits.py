#!/usr/bin/env python3
"""Independent read-only audits for retained connection_axes evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK = SCRIPT.parents[3]
REPO = WORK / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


def load_prototype():
    path = REPO / "generators/3f26d45b9f51/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("_independent_connection_axes", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


prototype = load_prototype()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def define_rules(bridge: RacketBridge, evidence: Path) -> dict[str, str]:
    symbols = {}
    for setting in prototype.SETTINGS:
        source = (evidence / f"private/rules/rule-{setting}.rkt").read_text()
        symbol = f"__audit_{setting}"
        bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
        symbols[setting] = symbol
    return symbols


def execute(bridge: RacketBridge, symbols: dict[str, str], grid, index: int):
    name = f"__audit_grid_{index}"
    bridge.define_grid(name, grid)
    return {
        setting: bridge.eval_text(f"({symbols[setting]} {name})")
        for setting in prototype.SETTINGS
    }


def parity_audit(evidence: Path, sweep_count: int) -> dict[str, Any]:
    canonical = prototype.canonical_program(root=find_root(SCRIPT))
    default_source = (evidence / "private/rules/rule-both.rkt").read_text()
    assert default_source == canonical

    invalid_settings = [None, True, 1, 1.0, "", "diagonal", "BOTH"]
    rejected = []
    for value in invalid_settings:
        try:
            prototype.validate_setting(value)
        except (TypeError, ValueError):
            rejected.append(repr(value))
        else:
            raise AssertionError(f"invalid setting accepted: {value!r}")

    mutated = canonical.replace("same-color marker", "same-colour marker", 1)
    for setting in ("horizontal", "vertical"):
        try:
            prototype._derive_alternative_program(mutated, setting)
        except ValueError:
            pass
        else:
            raise AssertionError(f"edit-point mutation did not fail closed for {setting}")

    retained_grids = 0
    retained_outputs = 0
    sweep_grids = 0
    ordinal = 0
    with RacketBridge(timeout=20, startup_timeout=45, max_calls_before_restart=300) as bridge:
        symbols = define_rules(bridge, evidence)
        for setting in prototype.SETTINGS:
            episode = json.loads((evidence / f"private/episode-{setting}.json").read_text())
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    outputs = execute(bridge, symbols, pair["input"], ordinal)
                    ordinal += 1
                    expected_all = episode["racket_outputs_by_pair"][f"{split}:{pair_index}"]
                    assert outputs == expected_all
                    assert pair["output"] == outputs[setting]
                    for candidate, output in outputs.items():
                        assert output == prototype.apply_python(pair["input"], candidate)
                    assert len({json.dumps(value) for value in outputs.values()}) == 3
                    retained_grids += 1
                    retained_outputs += len(outputs)

        for offset in range(sweep_count):
            seed = 910000 + offset
            grid = prototype.build_input(seed, offset % 9)
            outputs = execute(bridge, symbols, grid, ordinal)
            ordinal += 1
            for setting, output in outputs.items():
                assert output == prototype.apply_python(grid, setting)
            assert len({json.dumps(value) for value in outputs.values()}) == 3
            sweep_grids += 1
        runtime = bridge.runtime_identity

    return {
        "status": "passed",
        "surface": "parameter-and-racket-parity",
        "canonical_default_exact": True,
        "invalid_settings_rejected": rejected,
        "mutated_edit_points_failed_closed": ["horizontal", "vertical"],
        "retained_grids_reexecuted": retained_grids,
        "retained_outputs_reexecuted": retained_outputs,
        "unseen_seed_grids_checked": sweep_grids,
        "all_three_settings_distinct_per_grid": True,
        "python_racket_parity": True,
        "protected_racket": runtime["protected"],
        "runtime_identity_sha256": hashlib.sha256(
            json.dumps(runtime, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def privacy_audit(evidence: Path) -> dict[str, Any]:
    report = json.loads((evidence / "report.json").read_text())
    checked = []
    forbidden = (
        b"connection_axes",
        b"racket_program",
        b"prototype_version",
        b"label_executor",
        b"horizontal",
        b"vertical",
    )
    for row in report["episodes"]:
        setting = row["setting"]
        private = json.loads((evidence / f"private/episode-{setting}.json").read_text())
        expected_bytes = public_challenge_bytes(private)
        public_path = evidence / "public" / row["public_identifier"]
        actual_bytes = public_path.read_bytes()
        assert actual_bytes == expected_bytes
        digest = hashlib.sha256(actual_bytes).hexdigest()
        assert public_path.name == f"episode-{digest}.json"
        assert all(token not in actual_bytes for token in forbidden)

        public = json.loads(actual_bytes)
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])

        private_mutation = copy.deepcopy(private)
        private_mutation["seed"] = 999999999
        private_mutation["parameter"]["value"] = "private-only-mutation"
        private_mutation["racket_program"] = "private-only-mutation"
        private_mutation["test"][0]["output"] = [[9]]
        assert public_challenge_bytes(private_mutation) == actual_bytes
        assert public_challenge_id(private_mutation) == digest

        visible_mutation = copy.deepcopy(private)
        cell = visible_mutation["train"][0]["output"][0][0]
        visible_mutation["train"][0]["output"][0][0] = (cell + 1) % 10
        assert public_challenge_bytes(visible_mutation) != actual_bytes
        assert public_challenge_id(visible_mutation) != digest

        checked.append({
            "setting_private_only": setting,
            "public_file": public_path.name,
            "public_sha256": digest,
            "private_mutations_stable": True,
            "visible_mutation_changes_id": True,
            "query_outputs_absent": True,
        })

    manifest = json.loads((evidence / "manifest.json").read_text())
    listed = manifest["files"]
    actual = {
        path.relative_to(evidence).as_posix()
        for path in evidence.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    assert set(listed) == actual
    for relative, metadata in listed.items():
        path = evidence / relative
        assert metadata["sha256"] == sha256_file(path)
        assert metadata["bytes"] == path.stat().st_size

    return {
        "status": "passed",
        "surface": "public-private-export-and-identifiers",
        "episodes_checked": checked,
        "forbidden_private_tokens_absent": [token.decode() for token in forbidden],
        "manifest_complete_and_exact": True,
        "public_bytes_rederived_from_private": True,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sweep-count", type=int, default=24)
    args = parser.parse_args(argv)
    evidence = args.evidence.resolve()
    output = args.out.resolve()
    if output.exists():
        raise FileExistsError(output)
    result = {
        "schema": "3f26d45b9f51-connection-axes-independent-audits-v1",
        "evidence": str(evidence),
        "parity": parity_audit(evidence, args.sweep_count),
        "privacy": privacy_audit(evidence),
    }
    result["status"] = (
        "passed" if result["parity"]["status"] == result["privacy"]["status"] == "passed"
        else "failed"
    )
    write_json(output, result)
    print(json.dumps({"status": result["status"], "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
