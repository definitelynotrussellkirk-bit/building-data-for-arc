from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root

TASK_ID = "dafb4f819b93"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
EVIDENCE_TREE = ROOT.parent / "checks" / "parametric" / "dafb4f819b93-rank-delta-v1"
REPORT_PATH = HERE / "dafb4f819b93-adversarial.json"

spec = importlib.util.spec_from_file_location("dafb4f819b93_parametric_adversarial", PROTOTYPE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load prototype")
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)

rejections = []
invalid_calls = [
    ("seed_bool", lambda: prototype.make_episode(True, root=ROOT)),
    ("seed_negative", lambda: prototype.make_episode(-1, root=ROOT)),
    ("train_zero", lambda: prototype.make_episode(1, n_train=0, root=ROOT)),
    ("train_bool", lambda: prototype.make_episode(1, n_train=True, root=ROOT)),
    ("test_thirteen", lambda: prototype.make_episode(1, n_test=13, root=ROOT)),
    ("delta_bool", lambda: prototype.make_episode(1, rank_delta=True, root=ROOT)),
    ("delta_two", lambda: prototype.make_episode(1, rank_delta=2, root=ROOT)),
]
for name, call in invalid_calls:
    try:
        call()
    except (TypeError, ValueError) as error:
        rejections.append({"case": name, "exception": type(error).__name__, "message": str(error)})
    else:
        raise RuntimeError(f"invalid boundary was accepted: {name}")

with RacketBridge(max_calls_before_restart=128) as bridge:
    episode = prototype.make_episode(
        41,
        rank_delta=1,
        n_train=1,
        n_test=12,
        root=ROOT,
        bridge=bridge,
    )
    analysis = prototype.analyze_episode(episode, root=ROOT, bridge=bridge)
    clean_verification = prototype.verify_tree(EVIDENCE_TREE, root=ROOT, bridge=bridge)

pairs = episode["pairs"]
input_ids = [pair["input_sha256"] for pair in pairs]
if len(pairs) != 13 or len(set(input_ids)) != 13:
    raise RuntimeError("boundary episode did not retain 13 distinct inputs")
if any(pair["rank_delta"] != 1 for pair in pairs):
    raise RuntimeError("episode parameter changed between pairs")
if not analysis["outputs_match_selected_racket"] or not analysis["python_parity"]:
    raise RuntimeError("boundary episode lost Racket/Python parity")
if len(analysis["queries"]) != 12:
    raise RuntimeError("boundary episode did not retain 12 queries")
if clean_verification.get("status") != "pass":
    raise RuntimeError("clean materialized tree failed verification")

with tempfile.TemporaryDirectory(prefix="dafb4f819b93-tamper-") as temp:
    tampered = Path(temp) / "evidence"
    shutil.copytree(EVIDENCE_TREE, tampered)
    public_path = sorted((tampered / "public").glob("challenge-*.json"))[0]
    payload = json.loads(public_path.read_text(encoding="utf-8"))
    payload["test"][0]["input"][0][0] = 9
    public_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    try:
        prototype.verify_tree(tampered, root=ROOT)
    except ValueError as error:
        tamper_rejection = {"exception": type(error).__name__, "message": str(error)}
    else:
        raise RuntimeError("verifier accepted a tampered public challenge")

report = {
    "schema": "arcpuzzles-parametric-adversarial-v1",
    "task_id": TASK_ID,
    "prototype_path": str(PROTOTYPE_PATH.relative_to(ROOT)),
    "surfaces": {
        "sampler_and_numeric_boundaries": {
            "status": "pass",
            "valid_episode": {
                "seed": episode["seed"],
                "rank_delta": episode["parameters"]["rank_delta"],
                "n_train": episode["n_train"],
                "n_test": episode["n_test"],
                "pair_count": len(pairs),
                "distinct_input_count": len(set(input_ids)),
                "outputs_match_selected_racket": analysis["outputs_match_selected_racket"],
                "python_parity": analysis["python_parity"],
                "rival_fits_single_demo": analysis["rival_fits_demonstrations"],
                "queries_refuting_rival": sum(row["rival_query_differs"] for row in analysis["queries"]),
            },
            "invalid_rejections": rejections,
        },
        "public_export_and_verifier_rejection": {
            "status": "pass",
            "clean_tree_status": clean_verification["status"],
            "tamper_rejection": tamper_rejection,
        },
    },
    "finding": None,
    "limit": (
        "This bounded pass exercised one maximum-query episode, seven invalid "
        "numeric/count cases, one clean replay, and one public-input tamper; it "
        "is not an exhaustive seed or malformed-tree census."
    ),
}
REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": TASK_ID,
    "pair_count": len(pairs),
    "distinct_input_count": len(set(input_ids)),
    "invalid_cases_rejected": len(rejections),
    "outputs_match_selected_racket": analysis["outputs_match_selected_racket"],
    "python_parity": analysis["python_parity"],
    "clean_tree_status": clean_verification["status"],
    "tamper_rejected": True,
    "finding": None,
}, indent=2, sort_keys=True))
