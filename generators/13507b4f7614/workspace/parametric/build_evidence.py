"""Bounded protected-Racket evidence and private/public prototype serialization.

Run through review.py run. The public directory contains only native-format
challenges; all settings, answers, programs, runtime identity and finite rival
certificates are private. This does not accept a family or admit training data.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

from arcpuzzles.catalog import local_path, sha256
from arcpuzzles.parametric_promotion import _public, _raw
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
ROOT = HERE.parents[3]
TASK_ID = "13507b4f7614"
AXES = ("none", "horizontal", "vertical")
RIVALS = ("skip_a", "wrong_order", "ignore_parity", "both_axes", "join_only",
          "height_only", "width_only", "first_bridge", "first_group")
DEPENDENCY = {
    "step_a": "Join eligible facing yellow rectangles along the episode's chosen axis.",
    "intermediate": "The joined grid and its recomputed connected-component geometry.",
    "step_b": "Reduce odd-by-odd solid yellow rectangles in the joined grid to their center crosses.",
    "why_b_depends_on_a": "Joining changes input-dependent connectivity, solidity and dimensions; those post-join properties decide which components the center-cross rule reduces.",
}


def public_projection(episode):
    """Return a fresh native challenge projection with no private fields."""
    return json.loads(_raw(_public(episode)))


def public_bytes(episode):
    """Exact native public serialization, including its terminal newline."""
    return _raw(_public(episode))


def public_id(episode):
    return hashlib.sha256(public_bytes(episode)).hexdigest()


def observation(episode, query_index):
    """A single-query view, without future inputs or episode-length hints."""
    if type(query_index) is not int or query_index < 0:
        raise ValueError("query_index must be a nonnegative exact integer")
    visible = public_projection(episode)
    if query_index >= len(visible["test"]):
        raise IndexError("query_index is outside the episode")
    visible["test"] = [visible["test"][query_index]]
    return visible


def _pairs(episode, demos, queries):
    for name, count in (("train", demos), ("test", queries)):
        if type(count) is not int or not 1 <= count <= 32:
            raise ValueError("requested count must be an exact integer in 1..32")
        pairs = episode.get(name)
        if not isinstance(pairs, list) or len(pairs) != count:
            raise ValueError(f"{name} count differs from the independent request")
        for pair in pairs:
            if not isinstance(pair, dict) or not {"input", "output"} <= pair.keys():
                raise ValueError("each pair needs an input and output")
            _grid(pair["input"])
            _grid(pair["output"])
    pairs = episode["train"] + episode["test"]
    if len({_raw(pair["input"]) for pair in pairs}) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")
    return pairs


def check_episode(episode, *, demos, queries, declared_programs, rivals, apply_program):
    """Execute labels and audit finite rivals using demonstrations alone.

    Every supplied program executes on every input, including rivals already
    rejected by a demo. A surviving rival may agree on sampled queries; this is
    reported as finite agreement, never as a universal equivalence result.
    """
    pairs = _pairs(episode, demos, queries)
    chosen = episode.get("settings", {}).get("join_axis")
    if chosen not in declared_programs:
        raise ValueError("episode setting is undeclared")
    if episode.get("program_solution") != declared_programs[chosen]:
        raise ValueError("episode program_solution differs from the declared program")

    def disagreements(program, name):
        try:
            outputs = [_grid(apply_program(program, deepcopy(pair["input"]))) for pair in pairs]
        except Exception as exc:
            raise ValueError(f"{name} failed execution: {exc}") from exc
        return {
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "demo_disagreements": [i for i, output in enumerate(outputs[:demos])
                                   if output != pairs[i]["output"]],
            "query_disagreements": [i for i, output in enumerate(outputs[demos:])
                                    if output != pairs[demos + i]["output"]],
        }

    settings_checks = {axis: disagreements(program, "setting " + axis)
                       for axis, program in declared_programs.items()}
    selected = settings_checks[chosen]
    if selected["demo_disagreements"] or selected["query_disagreements"]:
        raise ValueError("claimed labels differ from executed Racket labels")
    survivors = [axis for axis, check in settings_checks.items() if not check["demo_disagreements"]]
    if survivors != [chosen]:
        raise ValueError("demonstrations do not uniquely identify the selected declared setting")
    rival_checks = {}
    for name, program in rivals.items():
        check = disagreements(program, "rival " + name)
        if not check["demo_disagreements"] and check["query_disagreements"]:
            raise ValueError(f"rival {name} survives every demo but disagrees on queries {check['query_disagreements']}")
        check["status"] = ("rejected_by_demonstrations" if check["demo_disagreements"]
                           else "agrees_on_sampled_queries")
        rival_checks[name] = check
    return {
        "counts": {"demos": demos, "queries": queries},
        "label_count": demos + queries,
        "declared_survivors": [{"join_axis": axis} for axis in survivors],
        "declared_settings": settings_checks,
        "rivals": rival_checks,
        "limits": "Only the declared settings, named finite rivals and sampled inputs were checked; no universal uniqueness or equivalence claim.",
    }


def write_bundle(output, episodes, summary, *, witness=None):
    """Publish new evidence with exact visible-byte names and hashes last."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("at least one episode is required")
    planned = []
    for episode in episodes:
        _pairs(episode, len(episode["train"]), len(episode["test"]))
        payload = public_bytes(episode)
        planned.append((hashlib.sha256(payload).hexdigest(), payload, episode))
    if len({row[0] for row in planned}) != len(planned):
        raise ValueError("duplicate visible challenge in prototype evidence")
    planned.sort(key=lambda row: row[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prototype-evidence-", dir=output.parent) as directory:
        stage = Path(directory)
        (stage / "public").mkdir()
        (stage / "private/episodes").mkdir(parents=True)
        for identifier, payload, episode in planned:
            (stage / "public" / f"{identifier}.json").write_bytes(payload)
            (stage / "private/episodes" / f"{identifier}.json").write_bytes(_raw(episode))
        (stage / "private/summary.json").write_bytes(_raw(summary))
        if witness is not None:
            (stage / "private/sequential-witness.json").write_bytes(_raw(witness))
        manifest = {
            "task_id": TASK_ID, "status": "complete", "episodes": len(planned),
            "training_admitted": False,
            "scope": "Pre-acceptance prototype serialization; hashes and projection checks do not independently authenticate rewritten evidence or replay Racket.",
            "files": [{"path": path.relative_to(stage).as_posix(), "sha256": sha256(path)}
                      for path in sorted(stage.rglob("*")) if path.is_file()],
        }
        (stage / "manifest.json").write_bytes(_raw(manifest))
        verify_bundle(stage)
        output.mkdir(exist_ok=False)
        for name in ("public", "private", "manifest.json"):
            os.replace(stage / name, output / name)
    return verify_bundle(output)


def verify_bundle(output):
    """Verify serialized files and exact public/private projections; no replay."""
    output = Path(output)
    if output.is_symlink():
        raise ValueError("evidence directory cannot be a symlink")
    manifest = json.loads((output / "manifest.json").read_bytes())
    if manifest.get("status") != "complete" or manifest.get("task_id") != TASK_ID:
        raise ValueError("incomplete or wrong-task prototype evidence")
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*")
              if p.is_file() and p != output / "manifest.json"}
    inventory = manifest.get("files", [])
    if len(inventory) != len(actual) or {item.get("path") for item in inventory} != actual:
        raise ValueError("evidence file inventory differs")
    for item in inventory:
        path = local_path(output, item["path"])
        if path.is_symlink() or sha256(path) != item["sha256"]:
            raise ValueError("evidence file hash differs: " + item["path"])
    private = sorted((output / "private/episodes").glob("*.json"))
    public = sorted((output / "public").glob("*.json"))
    if len(private) != manifest["episodes"] or len(public) != len(private):
        raise ValueError("evidence episode counts differ")
    for hidden in private:
        episode = json.loads(hidden.read_bytes())
        _pairs(episode, len(episode["train"]), len(episode["test"]))
        payload = public_bytes(episode)
        identifier = hashlib.sha256(payload).hexdigest()
        visible = output / "public" / f"{identifier}.json"
        if hidden.name != identifier + ".json" or not visible.is_file() or visible.read_bytes() != payload:
            raise ValueError("public name or private projection differs")
    return manifest


def _adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("_rectangle_evidence_adapter", path)
    adapter = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = adapter
    spec.loader.exec_module(adapter)
    return adapter


def make_sequential_witness(episodes, qualification, adapter, apply_program, racket):
    """Build the existing source-bound witness schema from executed ablations."""
    if (qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
            or qualification.get("status") != "qualified" or qualification.get("task_id") != TASK_ID):
        raise ValueError("a native qualified report for this task is required")
    if racket.get("backend") != "racket" or racket.get("protected") is not True:
        raise ValueError("witness requires protected Racket execution")
    cases = []
    for axis in ("horizontal", "vertical"):
        settings = {"join_axis": axis}
        program = adapter.program(settings)
        key = _raw(settings).decode().strip()
        if qualification.get("programs", {}).get(key) != hashlib.sha256(program.encode()).hexdigest():
            raise ValueError("witness program differs from qualified setting program")
        counterfactual = adapter.RULES.counterfactual_program(axis, "skip_a")
        intermediate_program = adapter.RULES.counterfactual_program(axis, "join_only")
        for episode in episodes:
            if episode["settings"] != settings:
                continue
            for pair in episode["train"] + episode["test"]:
                original = _grid(pair["input"])
                output = _grid(apply_program(program, deepcopy(original)))
                alternative = _grid(apply_program(counterfactual, deepcopy(original)))
                if output == alternative:
                    continue
                intermediate = _grid(apply_program(intermediate_program, deepcopy(original)))
                if intermediate != _grid(adapter.RULES.joined_grid(deepcopy(original), axis)):
                    raise ValueError("Python intermediate differs from executed Racket join_only result")
                cases.append({
                    "input": original, "settings": settings,
                    "intermediate_value": {"joined_grid": intermediate},
                    "program": program, "output": output,
                    "counterfactual_program": counterfactual, "counterfactual_output": alternative,
                    "ablation": "skip_a",
                })
                break
            if cases and cases[-1]["settings"] == settings:
                break
        if not cases or cases[-1]["settings"] != settings:
            raise ValueError("no changed-output skip-A witness for " + axis)
    return {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": deepcopy(qualification["source_binding"]),
        **DEPENDENCY, "racket": {"backend": "racket", "protected": True},
        "cases": cases,
    }


def build_evidence(output, *, demos=3, queries=4, qualification_path=None):
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if not output.resolve().is_relative_to(TASK_HOME.resolve()):
        raise ValueError("evidence output must stay inside this task home")
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("evidence output cannot traverse symlinks")
    qualification = None
    if qualification_path is not None:
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.parametric_promotion import _ready
        qualification = json.loads(Path(qualification_path).read_bytes())
        contract, binding = _ready(Catalog(ROOT), TASK_ID)
        if qualification.get("source_binding") != binding or qualification.get("contract") != contract:
            raise ValueError("qualification differs from the current source binding")
    adapter = _adapter()
    programs = {axis: adapter.program({"join_axis": axis}) for axis in AXES}
    episodes = []
    cache = {}
    evaluations = 0
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            def execute(program, grid):
                nonlocal evaluations
                key = (program, _raw(grid))
                if key not in cache:
                    cache[key] = _grid(apply(program, deepcopy(grid)))
                    evaluations += 1
                return deepcopy(cache[key])

            for axis in AXES:
                settings = {"join_axis": axis}
                rivals = {name: adapter.RULES.counterfactual_program(axis, name) for name in RIVALS}
                for seed in (0, 17):
                    generated = adapter.generate(seed, settings, demos=demos, queries=queries)
                    episode = {**generated, "task_id": TASK_ID, "seed": seed,
                               "settings": deepcopy(settings), "program": programs[axis],
                               "program_sha256": hashlib.sha256(programs[axis].encode()).hexdigest(),
                               "training_admitted": False, "racket": identity}
                    episode["demo_only_certificate"] = check_episode(
                        episode, demos=demos, queries=queries, declared_programs=programs,
                        rivals=rivals, apply_program=execute)
                    episodes.append(episode)
            witness = (make_sequential_witness(episodes, qualification, adapter, execute, identity)
                       if qualification is not None else None)
        finally:
            bridge.close()
    summary = {
        "status": "passed", "task_id": TASK_ID, "episodes": len(episodes),
        "seeds": [0, 17], "settings": [{"join_axis": axis} for axis in AXES],
        "counts": {"demos": demos, "queries": queries}, "rivals": list(RIVALS),
        "racket": identity, "racket_evaluations": evaluations,
        "rival_outcomes": [{"seed": episode["seed"], "settings": episode["settings"],
                            "statuses": {name: check["status"] for name, check in
                                         episode["demo_only_certificate"]["rivals"].items()}}
                           for episode in episodes],
        "training_admitted": False,
        "limits": f"Finite protected execution of six sampled episodes, their declared settings and {len(RIVALS)} named rival families; no universal learning or uniqueness claim. This is prototype evidence, not acceptance.",
    }
    manifest = write_bundle(output, episodes, summary, witness=witness)
    return {"output": str(output), "episodes": manifest["episodes"],
            "racket_evaluations": evaluations, "manifest_sha256": sha256(output / "manifest.json"),
            "summary": str(output / "private/summary.json"),
            **({"witness": str(output / "private/sequential-witness.json")} if witness is not None else {})}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new task-local evidence directory")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--qualification", type=Path,
                        help="native qualification.json; add a source-bound causal witness")
    args = parser.parse_args(argv)
    result = build_evidence(args.out, demos=args.demos, queries=args.queries,
                            qualification_path=args.qualification)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
