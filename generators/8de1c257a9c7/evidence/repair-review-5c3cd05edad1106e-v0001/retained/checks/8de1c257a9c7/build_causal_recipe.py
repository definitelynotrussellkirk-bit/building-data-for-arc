"""Select two exact native-qualified inputs and author wrong-offset recipes.

The native review_witness command subsequently executes and independently
replays both complete programs. This helper makes no execution claim.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
TASK = "8de1c257a9c7"
HOME = ROOT / "generators" / TASK / "workspace/parametric"


def load_audit():
    spec = importlib.util.spec_from_file_location("stamp_causal_audit", HOME / "audit_native.py")
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    qualification = json.loads(args.qualification.read_text())
    execution = json.loads(args.qualification.with_name("execution.json").read_text())
    audit = load_audit()
    episodes = execution["episodes"]
    mirror_index = next(i for i, e in enumerate(episodes) if e["settings"]["stamp_transform"] == "mirror_horizontal")
    episode = episodes[mirror_index]
    left, right = episode["train"][:2]
    a, b = audit.facts(left["input"]), audit.facts(right["input"])
    assert all(a[key] == b[key] for key in ("h", "w", "green", "reds", "cyan_count"))
    assert left["output"] != right["output"]
    wrong_offsets = [(r, -c) for r, c in b["offsets"]]
    right_program = episode["program"]
    needle = "(map (lambda (p) (list (- (first p) gr) (- gc (second p)))) eights)"
    assert right_program.count(needle) == 1
    literal = "'(" + " ".join(f"({r} {c})" for r, c in wrong_offsets) + ")"
    wrong_program = right_program.replace(needle, literal)
    cases = [{
        "episode_index": mirror_index, "split": "train", "pair_index": 0,
        "ablation": "wrong_intermediate", "counterfactual_program": wrong_program,
        "intermediate_value": {
            "intended_green": list(a["green"]),
            "intended_offsets": [[r, -c] for r, c in a["offsets"]],
            "counterfactual_offsets": [list(p) for p in wrong_offsets],
            "counterfactual_source": "Use the other qualified demonstration's different shape while keeping this input's destinations.",
            "same_dimensions_green_reds_cyan_count": True,
            "other_qualified_pair": {"episode_index": mirror_index, "split": "train", "pair_index": 1},
            "expected_counterfactual_output": right["output"],
        },
    }]
    dense_selection = None
    for i, e in enumerate(episodes):
        if e["settings"]["stamp_transform"] != "identity":
            continue
        for j, pair in enumerate(e["test"]):
            if (len(pair["input"]), len(pair["input"][0])) != (30, 30):
                continue
            wrong = audit.rival_output("bbox_center_anchor", pair["input"], e["settings"])
            if wrong != pair["output"]:
                dense_selection = (i, j, e, pair)
                break
        if dense_selection:
            break
    assert dense_selection is not None
    i, j, e, pair = dense_selection
    f = audit.facts(pair["input"])
    r0, c0, r1, c1 = f["bbox"]
    center = ((r0 + r1) // 2, (c0 + c1) // 2)
    cases.append({
        "episode_index": i, "split": "test", "pair_index": j,
        "ablation": "wrong_intermediate",
        "counterfactual_program": audit.rival_program("bbox_center_anchor", e["settings"]),
        "intermediate_value": {
            "intended_green": list(f["green"]), "wrong_anchor": list(center),
            "intended_offsets": [list(p) for p in f["offsets"]],
            "counterfactual_offsets": [[r-center[0], c-center[1]] for r, c in f["cyans"]],
            "counterfactual": "Infer source origin from the cyan bounding-box center instead of the green anchor.",
            "red_count": len(f["reds"]), "cyan_count": f["cyan_count"],
        },
    })
    recipe = {
        "step_a": "Find the green anchor and read every cyan cell's signed row/column offset from it; apply the episode's identity or horizontal-reflection setting to that observed offset set.",
        "intermediate": "The input-derived geometric offset set, with all source cells, holes and orientation preserved; this is more information than cyan count or a bounding box.",
        "step_b": "Clear the canvas and translate that offset set to every red destination, taking the union of overlapping cyan copies.",
        "why_b_depends_on_a": "The extracted offsets determine which cells each destination paints. Two matched demonstrations keep dimensions, green/red coordinates and cyan count fixed yet require different answers. Substituting the other shape's offsets or anchoring them at the bounding-box center changes the final painted grid. This is a source-relative geometry dependency, not iterative state simulation.",
        "cases": cases,
        "qualification_sha256": hashlib.sha256(args.qualification.read_bytes()).hexdigest(),
        "authoring_helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    assert qualification["task_id"] == TASK
    with args.out.open("x") as stream:
        json.dump(recipe, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": "recipe_authored_pending_native_execution", "cases": len(cases),
                      "selections": [{k: c[k] for k in ("episode_index", "split", "pair_index")} for c in cases]}))


if __name__ == "__main__":
    main()
