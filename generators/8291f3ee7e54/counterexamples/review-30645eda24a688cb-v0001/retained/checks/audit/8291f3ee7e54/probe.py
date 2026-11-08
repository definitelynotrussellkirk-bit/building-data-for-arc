"""One findings-only audit witness; never changes generator or rule source."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs


TASK_ID = "8291f3ee7e54"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"


def _digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def _write(name, value):
    path = HERE / name
    encoded = json.dumps(value, indent=2) + "\n"
    if path.exists() and path.read_text() != encoded:
        raise RuntimeError(f"refusing to replace different retained evidence: {path}")
    path.write_text(encoded)


def _generator():
    spec = importlib.util.spec_from_file_location("audited_concentric_generator", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _span_color_order(layer):
    return -layer[0], layer[1]


def union_bbox_rival(grid):
    """Wrong rule: treat every cell of each color as one object."""
    colors = sorted({color for row in grid for color in row if color})
    layers = []
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color]
        height = max(r for r, c in cells) - min(r for r, c in cells) + 1
        width = max(c for r, c in cells) - min(c for r, c in cells) + 1
        layers.append((max(height, width), color))
    layers.sort(key=_span_color_order)
    size = layers[0][0]
    out = [[0] * size for _ in range(size)]
    for span, color in layers:
        offset = (size - span) // 2
        for r in range(offset, offset + span):
            for c in range(offset, offset + span):
                if r in (offset, offset + span - 1) or c in (offset, offset + span - 1):
                    out[r][c] = color
    return out


def _witness_pair():
    base = [[0] * 12 for _ in range(12)]
    # A five-span L remnant, a three-span square frame, and a singleton.
    for c in range(1, 6):
        base[1][c] = 2
    for r in range(1, 6):
        base[r][1] = 2
    for r in range(7, 10):
        for c in range(1, 4):
            if r in (7, 9) or c in (1, 3):
                base[r][c] = 3
    base[11][11] = 4
    adversarial = deepcopy(base)
    adversarial[1][7] = 2  # Isolated; the primary component is unchanged.
    return base, adversarial


def prepare():
    gen = _generator()
    base, adversarial = _witness_pair()
    before = deepcopy((base, adversarial))
    base_errors = gen.self_check(base)
    adversarial_errors = gen.self_check(adversarial)
    assert base_errors == [], base_errors
    assert len(adversarial_errors) == 1 and "outside its primary span" in adversarial_errors[0]
    assert (base, adversarial) == before
    pairs = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    fits = [union_bbox_rival(pair["input"]) == pair["output"] for pair in pairs]
    assert len(pairs) == 3 and all(fits)
    profiles = [gen._render_profile(profile, tuple(range(1, len(profile[1]) + 1)))
                for profile in gen._CANONICAL_PROFILES]
    profile_checks = [gen.self_check(grid) for grid in profiles]
    assert profile_checks == [[], [], []]
    _write("input.json", {"inputs": [base, adversarial]})
    _write("rival.json", {"name": "union_bbox_per_color", "outputs": [union_bbox_rival(base), union_bbox_rival(adversarial)]})
    _write("metadata.json", {
        "task_id": TASK_ID,
        "generator_source": str(SOURCE),
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "canonical_record": "shared/data/base/solutions/training/c658a4bd__8291f3ee7e54.json",
        "review_index_present": (SOURCE.parent / "evidence/review_index.json").exists(),
        "input_provenance": {
            "kind": "hand_authored",
            "base": "12x12 zero grid; color2 L=(row1,cols1..5)+(rows1..5,col1); color3 3x3 frame top7,left1; color4 singleton(11,11). Coordinates are zero-based.",
            "adversarial_edit": {"row": 1, "column": 7, "before": 0, "after": 2},
            "generated_input": False,
            "generated_domain_scope": "Base is self_check-accepted but is not claimed to be a sampled output. The edited input is Racket-lawful but outside the sampler's declared union-span restriction; generation cannot emit this counterexample.",
        },
        "input_sha256": [_digest(base), _digest(adversarial)],
        "self_check": {"base": base_errors, "adversarial": adversarial_errors, "input_pure": True},
        "component_spans": {"base": [5, 3, 1], "adversarial": [5, 3, 1]},
        "union_spans": {"base": [5, 3, 1], "adversarial": [7, 3, 1]},
        "canonical_fit": [{"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"], "rival_matches": fits[index]}
                          for index, pair in enumerate(pairs)],
        "linked_profile_self_check": profile_checks,
        "claim": "A union-bbox rival fits all canonical labels and is equal to the selected rule throughout this generator's support. A one-cell same-color distractor separates the rules but is rejected by self_check.",
    })
    print(json.dumps({"canonical_rival_fit": f"{sum(fits)}/{len(fits)}", "self_check": [base_errors, adversarial_errors],
                      "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest()}))


def verify():
    metadata = json.loads((HERE / "metadata.json").read_text())
    applied = json.loads((HERE / "racket.json").read_text())
    rivals = json.loads((HERE / "rival.json").read_text())["outputs"]
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == metadata["generator_sha256"]
    assert applied["generator_sha256"] == metadata["generator_sha256"]
    assert applied["rule_hash_matches_catalog"] is True
    assert applied["executed_rule_hash"] == metadata["declared_rule_hash"]
    assert len(applied["results"]) == 2
    outputs = [item["output"] for item in applied["results"]]
    assert outputs[0] == outputs[1], "isolated pixel changed the selected-rule answer"
    assert len(outputs[0]) == 5 and len(outputs[0][0]) == 5
    assert outputs[0] == rivals[0]
    assert outputs[1] != rivals[1]
    assert len(rivals[1]) == 7 and len(rivals[1][0]) == 7
    result = {
        "task_id": TASK_ID, "status": "reproduced_teaching_gap",
        "generator_sha256": applied["generator_sha256"],
        "executed_rule_hash": applied["executed_rule_hash"],
        "rule_text_sha256": applied["rule_text_sha256"],
        "actual_output_shapes": [[len(out), len(out[0])] for out in outputs],
        "rival_output_shapes": [[len(out), len(out[0])] for out in rivals],
        "selected_rule_ignores_added_singleton": True,
        "canonical_fitting_rival_is_refuted_by_adversarial_input": True,
        "actual_outputs": outputs,
        "rival_outputs": rivals,
        "self_check": metadata["self_check"],
        "scope": metadata["input_provenance"]["generated_domain_scope"],
        "not_claimed": "No wrong generated label is alleged; this is an unteachable component-selection branch under the current generated support.",
    }
    _write("finding.json", result)
    print(json.dumps({key: result[key] for key in ("status", "generator_sha256", "executed_rule_hash", "actual_output_shapes", "rival_output_shapes")}))


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["verify"]:
        verify()
    else:
        raise SystemExit("usage: probe.py prepare|verify")
