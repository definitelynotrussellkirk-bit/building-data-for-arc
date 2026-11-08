"""Task-local hidden landing-offset prototype; not a production entry point.

The episode parameter is drawn exactly once. Python constructs inputs only;
every demonstration label, private query label, rival prediction, and canonical
parity result is executed by the materialized Racket programs through
``label_worker.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import random
import sys
import tempfile
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "bf53d21ff9fc"
ALLOWED_LANDING_OFFSETS = (2, 3)
DEFAULT_LANDING_OFFSET = 2
LANDING_EXPRESSION = "(- (length trail) 2)"
HERE = Path(__file__).resolve().parent
EPISODE_PROFILES = ("single_active", "multi_active", "mixed_markers", "dormant_routes")


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_sha256(value) -> str:
    return text_sha256(json.dumps(value, sort_keys=True, separators=(",", ":")))


def write_json(path: Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_source(root: Path) -> str:
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.add(row.get("program_solution"))
    if len(sources) != 1 or not all(isinstance(source, str) and source for source in sources):
        raise ValueError("Expected one unambiguous canonical Racket source")
    return sources.pop()


def materialize_program(canonical: str, landing_offset: int = DEFAULT_LANDING_OFFSET) -> str:
    if type(landing_offset) is not int or landing_offset not in ALLOWED_LANDING_OFFSETS:
        raise ValueError("landing_offset must be the literal integer 2 or 3")
    if canonical.count(LANDING_EXPRESSION) != 1:
        raise ValueError("Canonical landing expression changed; reassess this prototype")
    replacement = f"(- (length trail) {landing_offset})"
    return canonical.replace(LANDING_EXPRESSION, replacement, 1)


def _load_generator(root: Path):
    try:
        return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    except ImportError:
        runtime = Path(root) / "shared/runtime"
        if str(runtime) not in sys.path:
            sys.path.insert(0, str(runtime))
        source = Path(root) / f"generators/{TASK_ID}/generator.py"
        spec = importlib.util.spec_from_file_location(f"{TASK_ID}_prototype_generator", source)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load generator source at {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def episode_inputs(seed: int, *, root: Path | None = None):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")
    root = Path(root) if root is not None else find_root(__file__)
    generator = _load_generator(root)
    landing_offset = random.Random(seed).choice(ALLOWED_LANDING_OFFSETS)
    inputs = []
    construction = []
    for index, profile in enumerate(EPISODE_PROFILES):
        digest = hashlib.sha256(
            f"{TASK_ID}:landing-offset-input-v1:{seed}:{index}".encode()
        ).hexdigest()
        input_seed = int(digest[:12], 16)
        sample_index = seed * len(EPISODE_PROFILES) + index + 1
        grid = generator.generate(
            input_seed,
            sample_index,
            difficulty="medium",
            scene_profile=profile,
        )
        analysis = generator._analysis(grid)
        minimum_length = min(analysis["facts"]["active_lengths"])
        if analysis["errors"] or minimum_length < max(ALLOWED_LANDING_OFFSETS):
            raise AssertionError(f"prototype input violates landing-offset constraints: {analysis}")
        inputs.append(grid)
        construction.append({
            "profile": profile,
            "seed": input_seed,
            "sample_index": sample_index,
            "difficulty": "medium",
            "minimum_active_route_length": minimum_length,
            "active_route_lengths": list(analysis["facts"]["active_lengths"]),
            "self_check": list(analysis["errors"]),
        })
    return {
        "seed": seed,
        "parameters": {"landing_offset": landing_offset},
        "inputs": inputs,
        "construction": construction,
    }


def execute_labels(root: Path, output: Path, request):
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    request_path = output / "private/label-request.json"
    write_json(request_path, request)
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parametric-runtime-") as temp:
        runtime = Path(temp) / "runtime"
        manifest = prepare_runtime(Catalog(root), runtime, TASK_ID)
        write_json(output / "private/runtime-manifest.json", manifest)
        command = [sys.executable, str(HERE / "label_worker.py"), str(request_path)]
        execution = run_process(
            command,
            runtime,
            timeout=120,
            extra_env={"PYTHONPATH": str(runtime)},
        )
        write_json(output / "private/label-execution.json", {
            "command": command,
            "cwd": str(runtime),
            "request_sha256": file_sha256(request_path),
            **execution,
        })
    if execution["exit_code"] != 0 or execution["timed_out"]:
        raise RuntimeError(
            "Racket label worker failed; see private/label-execution.json: "
            + execution["stderr"][-2000:]
        )
    labels = json.loads(execution["stdout"])
    write_json(output / "private/labels.json", labels)
    return labels


def write_evidence(output: Path, *, seeds=(0, 1), root: Path | None = None):
    output = Path(output).resolve()
    root = Path(root) if root is not None else find_root(__file__)
    seeds = tuple(seeds)
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("Supply at least one seed, without duplicates")
    episodes = [episode_inputs(seed, root=root) for seed in seeds]
    output.mkdir(parents=True, exist_ok=False)

    canonical = canonical_source(root)
    programs = {
        str(offset): materialize_program(canonical, offset)
        for offset in ALLOWED_LANDING_OFFSETS
    }
    sources = [
        HERE / "prototype.py",
        HERE / "label_worker.py",
        HERE / "README.md",
        root / f"generators/{TASK_ID}/tests/test_parametric_landing_offset.py",
    ]
    source_hashes = {str(path.relative_to(root)): file_sha256(path) for path in sources}

    canonical_data = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    cases = {f"canonical:{index}": pair["input"] for index, pair in enumerate(canonical_data)}
    cases["settings-witness"] = episodes[0]["inputs"][0]
    for episode in episodes:
        for index, grid in enumerate(episode["inputs"]):
            cases[f"episode:{episode['seed']}:{index}"] = grid

    for offset, program in programs.items():
        path = output / f"private/programs/landing-offset-{offset}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program, encoding="utf-8")

    labels = execute_labels(root, output, {"programs": programs, "inputs": cases})
    parity_cases = []
    for index, pair in enumerate(canonical_data):
        actual = labels["programs"][str(DEFAULT_LANDING_OFFSET)]["outputs"][f"canonical:{index}"]
        parity_cases.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input": pair["input"],
            "expected": pair["output"],
            "actual": actual,
            "passed": actual == pair["output"],
        })
    parity = {
        "passed": bool(parity_cases) and all(case["passed"] for case in parity_cases),
        "labeled_pairs": len(parity_cases),
        "cases": parity_cases,
    }
    write_json(output / "private/canonical-parity.json", parity)

    witness_outputs = {
        offset: data["outputs"]["settings-witness"]
        for offset, data in labels["programs"].items()
    }
    witness = {
        "input": cases["settings-witness"],
        "input_sha256": json_sha256(cases["settings-witness"]),
        "outputs": witness_outputs,
        "outputs_differ": witness_outputs["2"] != witness_outputs["3"],
        "construction": episodes[0]["construction"][0],
    }
    write_json(output / "private/settings-witness.json", witness)

    episode_rows = []
    for episode in episodes:
        seed = episode["seed"]
        chosen_offset = str(episode["parameters"]["landing_offset"])
        chosen = labels["programs"][chosen_offset]
        outputs = [chosen["outputs"][f"episode:{seed}:{index}"] for index in range(4)]
        public = {
            "train": [
                {"input": grid, "output": label}
                for grid, label in zip(episode["inputs"][:3], outputs[:3])
            ],
            "test": [{"input": episode["inputs"][3]}],
        }
        rivals = {}
        for rival_offset, rival in labels["programs"].items():
            predictions = [rival["outputs"][f"episode:{seed}:{index}"] for index in range(4)]
            train_misses = [index for index in range(3) if predictions[index] != outputs[index]]
            query_misses = [0] if predictions[3] != outputs[3] else []
            status = (
                "refuted_by_demonstrations" if train_misses
                else "ambiguous_query" if query_misses
                else "survived_all"
            )
            rivals[rival_offset] = {
                "status": status,
                "program_sha256": rival["program_sha256"],
                "demonstration_mismatch_indices": train_misses,
                "query_disagreement_indices": query_misses,
                "train_predictions": predictions[:3],
                "test_predictions": predictions[3:],
            }

        public_path = f"public/episode-{seed}.json"
        private_path = f"private/episode-{seed}.json"
        write_json(output / public_path, public)
        private = {
            "seed": seed,
            "parameters": episode["parameters"],
            "parameter_selection": "random.Random(seed).choice((2, 3)), once per episode",
            "program": programs[chosen_offset],
            "program_sha256": chosen["program_sha256"],
            "callable": chosen["callable"],
            "callable_sha256": chosen["callable_sha256"],
            "test_outputs": outputs[3:],
            "construction": episode["construction"],
            "prototype_sources": source_hashes,
            "rivals": rivals,
            "declared_parameter_ambiguity": any(
                row["status"] == "ambiguous_query" for row in rivals.values()
            ),
            "public_sha256": file_sha256(output / public_path),
        }
        write_json(output / private_path, private)
        episode_rows.append({
            "seed": seed,
            "parameters": episode["parameters"],
            "public_path": public_path,
            "private_path": private_path,
            "public_sha256": private["public_sha256"],
            "private_sha256": file_sha256(output / private_path),
            "declared_parameter_ambiguity": private["declared_parameter_ambiguity"],
        })

    settings_covered = sorted({row["parameters"]["landing_offset"] for row in episode_rows})
    missing_settings = sorted(set(ALLOWED_LANDING_OFFSETS) - set(settings_covered))
    supported = (
        parity["passed"]
        and witness["outputs_differ"]
        and not any(row["declared_parameter_ambiguity"] for row in episode_rows)
    )
    status = (
        "prototype_failed" if not supported
        else "prototype_partial" if missing_settings
        else "prototype_passed"
    )
    report = {
        "schema": f"{TASK_ID}-landing-offset-parametric-prototype-v1",
        "task_id": TASK_ID,
        "status": status,
        "scope": "task-local proposed landing-offset variant; no production approval",
        "parameter": {
            "name": "landing_offset",
            "allowed_values": list(ALLOWED_LANDING_OFFSETS),
            "original_default": DEFAULT_LANDING_OFFSET,
            "input_constraints_depend_on_parameter": True,
            "input_constraint": "every active route has at least three cells",
        },
        "settings_covered": settings_covered,
        "missing_episode_settings": missing_settings,
        "seeds": list(seeds),
        "prototype_source_sha256": source_hashes,
        "prototype_source_manifest_sha256": json_sha256(source_hashes),
        "canonical_ledger_sha256": file_sha256(canonical_path(root)),
        "canonical_program_sha256": text_sha256(canonical),
        "program_sha256": {offset: text_sha256(program) for offset, program in programs.items()},
        "canonical_parity": {
            "passed": parity["passed"],
            "labeled_pairs": len(parity_cases),
            "path": "private/canonical-parity.json",
        },
        "settings_witness": {
            "outputs_differ": witness["outputs_differ"],
            "path": "private/settings-witness.json",
        },
        "episodes": episode_rows,
        "racket_evaluation_count": labels["evaluation_count"],
        "racket_runtime_identity": labels["runtime_identity"],
        "label_execution_path": "private/label-execution.json",
        "limits": [
            "Only offsets 2 and 3 and the listed seeds were exercised.",
            "The parameter is fixed once per episode and is not exposed in public challenges.",
            "Rival checks cover only the declared landing offsets, not all structural alternatives.",
            "Inputs are forced calibrated generator profiles with active routes of length at least three.",
            "Canonical repair acceptance does not approve the offset-3 variant for production.",
        ],
        "invoking_python_arguments": sys.argv,
    }
    write_json(output / "result.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New authoring evidence directory")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    args = parser.parse_args()
    report = write_evidence(args.out, seeds=args.seeds)
    print(json.dumps({
        "status": report["status"],
        "settings_covered": report["settings_covered"],
        "missing_episode_settings": report["missing_episode_settings"],
        "seeds": report["seeds"],
        "racket_evaluation_count": report["racket_evaluation_count"],
        "result": str(args.out / "result.json"),
    }, sort_keys=True))
    return 0 if report["status"] == "prototype_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
