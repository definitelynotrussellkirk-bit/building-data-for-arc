"""Task-local output-color prototype; never a production generator entry point.

Only inputs are constructed in Python. Every label and every parameter-rival
prediction comes from the included Racket bridge through label_worker.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "a0fcc6f3396e"
ALLOWED_OUTPUT_COLORS = (8, 3)
DEFAULT_OUTPUT_COLOR = 8
FINAL_COLOR_EXPRESSION = "(crop-cells (second odd) 8)"
HERE = Path(__file__).resolve().parent


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_sha256(value):
    return text_sha256(json.dumps(value, sort_keys=True, separators=(",", ":")))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_source(root):
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


def materialize_program(canonical, output_color=DEFAULT_OUTPUT_COLOR):
    if type(output_color) is not int or output_color not in ALLOWED_OUTPUT_COLORS:
        raise ValueError("output_color must be the literal integer 8 or 3")
    if canonical.count(FINAL_COLOR_EXPRESSION) != 1:
        raise ValueError("Canonical final recolor changed; reassess this prototype")
    # At the default setting this replacement returns exactly the canonical text.
    # The helper's unused optional default remains 8; its final explicit argument
    # is the entire parameterized transformation difference.
    return canonical.replace(FINAL_COLOR_EXPRESSION,
                             f"(crop-cells (second odd) {output_color})", 1)


def episode_inputs(seed):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")
    # Exactly one rule draw per episode, independent of subsequent input draws.
    output_color = random.Random(seed).choice(ALLOWED_OUTPUT_COLORS)
    rng = random.Random(f"{TASK_ID}:parametric-inputs-v1:{seed}")
    # Equal area with different dimensions, shared height, shared width, then a
    # query differing in both dimensions. These are a small prototype curriculum.
    shapes = (((2, 4), (4, 2)), ((3, 3), (3, 5)),
              ((4, 2), (2, 2)), ((2, 5), (3, 4)))
    inputs, construction = [], []
    for index, (common, odd) in enumerate(shapes):
        height = rng.randint(max(common[0], odd[0]) + 1,
                             max(common[0], odd[0]) + 3)
        panel_width = rng.randint(max(common[1], odd[1]) + 1,
                                  max(common[1], odd[1]) + 3)
        odd_index = (index + seed % 3) % 3
        grid = [[0] * (3 * panel_width + 2) for _ in range(height)]
        for row in grid:
            row[panel_width] = row[2 * panel_width + 1] = 9
        offsets, common_offset = [], None
        for panel in range(3):
            rectangle = odd if panel == odd_index else common
            rh, rw = rectangle
            legal_offsets = [(r, c) for r in range(height - rh + 1)
                             for c in range(panel_width - rw + 1)]
            if panel != odd_index and common_offset is not None:
                legal_offsets.remove(common_offset)
            r0, c0 = rng.choice(legal_offsets)
            if panel != odd_index:
                common_offset = (r0, c0)
            offsets.append([r0, c0])
            panel_start = panel * (panel_width + 1)
            for r in (r0, r0 + rh - 1):
                for c in (c0, c0 + rw - 1):
                    grid[r][panel_start + c] = 2
        inputs.append(grid)
        construction.append({"common_shape": list(common), "odd_shape": list(odd),
                             "odd_panel": odd_index, "panel_width": panel_width,
                             "height": height, "offsets": offsets})
    return {"seed": seed, "parameters": {"output_color": output_color},
            "inputs": inputs, "construction": construction}


def execute_labels(root, output, request):
    """Use the public runtime preparer so wrap_rule's parser imports are local."""
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    request_path = output / "private/label-request.json"
    write_json(request_path, request)
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parametric-runtime-") as temp:
        runtime = Path(temp) / "runtime"
        manifest = prepare_runtime(Catalog(root), runtime, TASK_ID)
        # The copied selected generator is provenance only; the label worker
        # never imports or executes it and does not call production generation.
        write_json(output / "private/runtime-manifest.json", manifest)
        command = [sys.executable, str(HERE / "label_worker.py"), str(request_path)]
        execution = run_process(command, runtime, timeout=120,
                                extra_env={"PYTHONPATH": str(runtime)})
        write_json(output / "private/label-execution.json",
                   {"command": command, "cwd": str(runtime),
                    "request_sha256": file_sha256(request_path), **execution})
    if execution["exit_code"] != 0 or execution["timed_out"]:
        raise RuntimeError("Racket label worker failed; see private/label-execution.json: "
                           + execution["stderr"][-2000:])
    labels = json.loads(execution["stdout"])
    write_json(output / "private/labels.json", labels)
    return labels


def write_evidence(output, *, seeds=(0, 1), root=None):
    output = Path(output).resolve()
    root = Path(root) if root is not None else find_root(__file__)
    seeds = tuple(seeds)
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("Supply at least one seed, without duplicates")
    episodes = [episode_inputs(seed) for seed in seeds]
    output.mkdir(parents=True, exist_ok=False)
    canonical = canonical_source(root)
    programs = {str(color): materialize_program(canonical, color)
                for color in ALLOWED_OUTPUT_COLORS}
    sources = [HERE / "prototype.py", HERE / "label_worker.py", HERE / "README.md",
               root / f"generators/{TASK_ID}/tests/test_parametric.py"]
    source_hashes = {str(path.relative_to(root)): file_sha256(path) for path in sources}
    canonical_data = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    cases = {f"canonical:{i}": pair["input"] for i, pair in enumerate(canonical_data)}
    cases["settings-witness"] = episode_inputs(0)["inputs"][0]
    for episode in episodes:
        for index, grid in enumerate(episode["inputs"]):
            cases[f"episode:{episode['seed']}:{index}"] = grid
    for color, program in programs.items():
        path = output / f"private/programs/output-color-{color}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program, encoding="utf-8")
    request = {"programs": programs, "inputs": cases}
    labels = execute_labels(root, output, request)
    parity_cases = []
    for index, pair in enumerate(canonical_data):
        got = labels["programs"]["8"]["outputs"][f"canonical:{index}"]
        parity_cases.append({"variant": pair["variant"], "split": pair["split"],
                             "pair_index": pair["pair_index"], "input": pair["input"],
                             "expected": pair["output"], "actual": got,
                             "passed": got == pair["output"]})
    parity = {"passed": bool(parity_cases) and all(x["passed"] for x in parity_cases),
              "labeled_pairs": len(parity_cases), "cases": parity_cases}
    write_json(output / "private/canonical-parity.json", parity)
    witness_outputs = {color: data["outputs"]["settings-witness"]
                       for color, data in labels["programs"].items()}
    witness = {"input": cases["settings-witness"],
               "input_sha256": json_sha256(cases["settings-witness"]),
               "outputs": witness_outputs,
               "outputs_differ": witness_outputs["8"] != witness_outputs["3"],
               "lawful_construction": episode_inputs(0)["construction"][0]}
    write_json(output / "private/settings-witness.json", witness)
    episode_rows = []
    for episode in episodes:
        seed, color = episode["seed"], str(episode["parameters"]["output_color"])
        chosen = labels["programs"][color]
        outputs = [chosen["outputs"][f"episode:{seed}:{i}"] for i in range(4)]
        public = {"train": [{"input": grid, "output": label}
                            for grid, label in zip(episode["inputs"][:3], outputs[:3])],
                  "test": [{"input": episode["inputs"][3]}]}
        rivals = {}
        for rival_color, rival in labels["programs"].items():
            predictions = [rival["outputs"][f"episode:{seed}:{i}"] for i in range(4)]
            train_misses = [i for i in range(3) if predictions[i] != outputs[i]]
            query_misses = [0] if predictions[3] != outputs[3] else []
            status = ("refuted_by_demonstrations" if train_misses else
                      "ambiguous_query" if query_misses else "survived_all")
            rivals[rival_color] = {"status": status,
                                   "program_sha256": rival["program_sha256"],
                                   "demonstration_mismatch_indices": train_misses,
                                   "query_disagreement_indices": query_misses,
                                   "train_predictions": predictions[:3],
                                   "test_predictions": predictions[3:]}
        public_path = f"public/episode-{seed}.json"
        private_path = f"private/episode-{seed}.json"
        private = {"seed": seed, "parameters": episode["parameters"],
                   "parameter_selection": "random.Random(seed).choice((8, 3)), once per episode",
                   "program": programs[color], "program_sha256": chosen["program_sha256"],
                   "callable": chosen["callable"], "callable_sha256": chosen["callable_sha256"],
                   "test_outputs": outputs[3:], "construction": episode["construction"],
                   "prototype_sources": source_hashes, "rivals": rivals,
                   "declared_parameter_ambiguity": any(r["status"] == "ambiguous_query"
                                                       for r in rivals.values())}
        write_json(output / public_path, public)
        private["public_sha256"] = file_sha256(output / public_path)
        write_json(output / private_path, private)
        episode_rows.append({"seed": seed, "parameters": episode["parameters"],
                             "public_path": public_path, "private_path": private_path,
                             "public_sha256": private["public_sha256"],
                             "private_sha256": file_sha256(output / private_path),
                             "declared_parameter_ambiguity": private["declared_parameter_ambiguity"]})
    supported = (parity["passed"] and witness["outputs_differ"] and
                 not any(e["declared_parameter_ambiguity"] for e in episode_rows))
    settings_covered = sorted({e["parameters"]["output_color"] for e in episode_rows})
    missing_episode_settings = sorted(set(ALLOWED_OUTPUT_COLORS) - set(settings_covered))
    status = ("prototype_failed" if not supported else
              "prototype_partial" if missing_episode_settings else "prototype_passed")
    report = {"schema": "a0fcc6f3396e-parametric-prototype-v1", "task_id": TASK_ID,
              "status": status,
              "scope": "task-local proposed output-color variant; no production approval",
              "parameter": {"name": "output_color", "allowed_values": list(ALLOWED_OUTPUT_COLORS),
                            "original_default": DEFAULT_OUTPUT_COLOR,
                            "input_constraints_depend_on_parameter": False},
              "settings_covered": settings_covered,
              "missing_episode_settings": missing_episode_settings,
              "seeds": list(seeds), "prototype_source_sha256": source_hashes,
              "prototype_source_manifest_sha256": json_sha256(source_hashes),
              "canonical_ledger_sha256": file_sha256(canonical_path(root)),
              "canonical_program_sha256": text_sha256(canonical),
              "program_sha256": {color: text_sha256(program) for color, program in programs.items()},
              "canonical_parity": {"passed": parity["passed"], "labeled_pairs": len(parity_cases),
                                   "path": "private/canonical-parity.json"},
              "settings_witness": {"outputs_differ": witness["outputs_differ"],
                                   "path": "private/settings-witness.json"},
              "episodes": episode_rows, "racket_evaluation_count": labels["evaluation_count"],
              "racket_runtime_identity": labels["runtime_identity"],
              "label_execution_path": "private/label-execution.json",
              "limits": ["Only the listed seeds and two declared color settings were exercised.",
                         "Rival checks cover output_color 8 and 3; structural rivals are not exhaustive.",
                         "Inputs come from this four-corner prototype constructor, not the repaired generator.",
                         "Each episode has three demonstrations and one query; this is not production API support.",
                         "Canonical repair acceptance does not approve the color-3 variant."],
              "invoking_python_arguments": sys.argv}
    write_json(output / "result.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New authoring evidence directory")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    args = parser.parse_args()
    report = write_evidence(args.out, seeds=args.seeds)
    print(json.dumps({"status": report["status"], "settings_covered": report["settings_covered"],
                      "missing_episode_settings": report["missing_episode_settings"],
                      "seeds": report["seeds"], "racket_evaluation_count": report["racket_evaluation_count"],
                      "result": str(args.out / "result.json")}, sort_keys=True))
    return 0 if report["status"] == "prototype_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
