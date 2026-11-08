"""Bounded replay of the pinned abcb59bec35f generator-contract audit."""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-e5e87aace297207f"
TASK_ID = "abcb59bec35f"
RETURN_ID = "review-d398b07a4e6e2d3b:v0001"
EXPECTED_SOURCE = "d28e0eaa73dbfaafef3b528ab8c20a7c50d441040bf0567dabdf6341af72805d"
EXPECTED_INDEX = "f8643569dac06ad2587d0325d708e89d97ac6705b3cdcf6b2b1cf0384710a6f3"
EXPECTED_ASSETS = "847dda19d7360acdcf014667efaf68377b9b4aeb53c1655b7bddfcf815757e93"
EXPECTED_RECORD = "f4aa0b8bbb453c2ddc9cf1157cc6d57df3d1f02c56faf5de4755748d71aca7b5"
EXPECTED_RULE_HASH = "1b55eff07dbd"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return sha_bytes(canonical_bytes(value))


def run_variant(module, *, label: str, overrides: dict[str, Any], expected_error: str | None = None):
    base = importlib.import_module("puzzle_generators.base")
    observed = []
    base.set_ctx_observer(observed.append)
    row: dict[str, Any] = {"label": label, "overrides": overrides, "expected_error": expected_error}
    try:
        grid = module.generate(20261011, 7, difficulty="medium", **overrides)
    except BaseException as exc:
        row.update({"status": "error", "error_type": type(exc).__name__, "error_message": str(exc)})
        if observed:
            row["overrides_used"] = observed[-1].overrides_used()
            row["recorded_draws"] = observed[-1].recorded_draws()
        return row
    finally:
        base.set_ctx_observer(None)
    row.update({
        "status": "returned",
        "grid": grid,
        "grid_sha256": digest(grid),
        "distinct_colors": sorted({cell for line in grid for cell in line}),
        "self_check_errors": module.self_check(grid, difficulty="medium", meta=None),
        "overrides_used": observed[-1].overrides_used() if observed else {},
        "recorded_draws": observed[-1].recorded_draws() if observed else {},
    })
    return row


def comparable(row):
    keys = (
        "label", "overrides", "expected_error", "status", "error_type", "error_message",
        "grid_sha256", "distinct_colors", "self_check_errors", "overrides_used", "recorded_draws",
    )
    value = {key: row.get(key) for key in keys if key in row or key in ("label", "overrides", "expected_error", "status")}
    # Historical JSON stores draw tuples as arrays; compare their serialized values.
    return json.loads(json.dumps(value, sort_keys=True))


def main():
    module, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    assert source_sha == EXPECTED_SOURCE

    task_dir = ROOT / "generators" / TASK_ID
    index_path = task_dir / "evidence" / "review_index.json"
    # Counterexample folder uses review-...-v0001 rather than the return-id colon.
    retained_dir = task_dir / "counterexamples" / "review-d398b07a4e6e2d3b-v0001"
    assets_path = retained_dir / "audit_assets.json"
    assert sha_bytes(index_path.read_bytes()) == EXPECTED_INDEX
    assert sha_bytes(assets_path.read_bytes()) == EXPECTED_ASSETS

    index = json.loads(index_path.read_text())
    records = [row for row in index["audits"] if row["return_id"] == RETURN_ID]
    assert len(records) == 1
    record = records[0]
    assert sha_bytes(canonical_bytes(record)) == EXPECTED_RECORD
    assert record["source_sha256"] == EXPECTED_SOURCE
    assert record["resolution"] == "needs_triage"

    assets = json.loads(assets_path.read_text())
    assert assets["return_id"] == RETURN_ID
    assert assets["audited_generator_sha256"] == EXPECTED_SOURCE
    verified_assets = []
    for asset in assets["files"]:
        path = ROOT / asset["path"]
        actual = sha_bytes(path.read_bytes())
        assert actual == asset["sha256"], (path, actual, asset["sha256"])
        verified_assets.append({"path": asset["path"], "sha256": actual, "bytes": path.stat().st_size})

    retained_results_path = retained_dir / "retained" / "checks" / "audit" / "override-probe-results.json"
    retained_spec_path = retained_dir / "retained" / "checks" / "audit" / "override-probes.json"
    retained_results = json.loads(retained_results_path.read_text())
    retained_by_name = {row["name"]: row for row in retained_results["cases"]}

    layout = [
        run_variant(module, label="layout-checker", overrides={"cell_layout": "checker"}),
        run_variant(module, label="layout-block", overrides={"cell_layout": "block"}),
    ]
    scalar = [
        run_variant(module, label="zero", overrides={"color_count": 0}, expected_error="ValueError"),
        run_variant(module, label="four", overrides={"color_count": 4}, expected_error="ValueError"),
        run_variant(module, label="boolean", overrides={"color_count": True}, expected_error="TypeError"),
        run_variant(module, label="float", overrides={"color_count": 2.0}, expected_error="TypeError"),
        run_variant(module, label="string", overrides={"color_count": "2"}, expected_error="TypeError"),
    ]

    expected_layout = retained_by_name["abcb59bec35f-layout-axis"]["variants"]
    expected_scalar = retained_by_name["abcb59bec35f-invalid-color-count"]["variants"]
    assert [comparable(row) for row in layout] == [comparable(row) for row in expected_layout]
    assert [comparable(row) for row in scalar] == [comparable(row) for row in expected_scalar]

    layout_equal = len({row["grid_sha256"] for row in layout}) == 1
    layout_unconsumed = all(row["overrides_used"] == {} for row in layout)
    strict_scalar_defect = {
        "boolean_returned": scalar[2]["status"] == "returned" and scalar[2]["self_check_errors"] == [],
        "float_returned": scalar[3]["status"] == "returned" and scalar[3]["self_check_errors"] == [],
        "zero_rejected": scalar[0]["status"] == "error",
        "four_rejected": scalar[1]["status"] == "error",
        "string_rejected": scalar[4]["status"] == "error",
    }
    assert layout_equal and layout_unconsumed and all(strict_scalar_defect.values())

    rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert rows and len({row["program_solution"] for row in rows}) == 1
    raw_rule = rows[0]["program_solution"]
    rule_hash = sha_bytes(" ".join(raw_rule.split()).encode())[:12]
    assert rule_hash == EXPECTED_RULE_HASH

    report = {
        "schema": "arcpuzzles-ticket-audit-replay-v1",
        "ticket_id": TICKET_ID,
        "type": "audit_replay",
        "task_id": TASK_ID,
        "return_id": RETURN_ID,
        "status": "reproduced",
        "source_bound": True,
        "identity": {
            "source_sha256": source_sha,
            "audit_index_sha256": EXPECTED_INDEX,
            "assets_manifest_sha256": EXPECTED_ASSETS,
            "audit_record_sha256": EXPECTED_RECORD,
            "rule_hash": rule_hash,
            "retained_asset_count": len(verified_assets),
            "retained_spec_sha256": sha_bytes(retained_spec_path.read_bytes()),
            "retained_results_sha256": sha_bytes(retained_results_path.read_bytes()),
        },
        "layout_axis": {
            "seed": 20261011,
            "sample_index": 7,
            "difficulty": "medium",
            "outputs_equal": layout_equal,
            "grid_sha256": layout[0]["grid_sha256"],
            "overrides_used": [row["overrides_used"] for row in layout],
            "variants": [comparable(row) for row in layout],
        },
        "strict_scalar": {
            **strict_scalar_defect,
            "variants": [comparable(row) for row in scalar],
        },
        "retained_exact_match": True,
        "audit_disposition": "Bounded claim reproduced; existing needs_triage audit is not cleared or broadened.",
        "not_run": ["peer battery", "isolated lint", "unrelated retained cases"],
    }
    (HERE / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
