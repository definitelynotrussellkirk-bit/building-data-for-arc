from __future__ import annotations

import ast
import hashlib
import json
import time
from pathlib import Path

TICKET_ID = "ticket-bdb9a5b6599dee2d"
REQUEST_ID = "review-bde888379ee5fdae:v0001:F1"
EXPECTED = {
    "manifest": "9d19574c370b7462983329d9f2d9e14832bbc62558bb323105073ea0ad68a401",
    "request_source": "6c85823f8430070c462f9834d4b48778ffb8e1d58021ca748e366eefbc58d642",
    "request": "329135c4e4bbf3671f1e34fd51c2ab025a67736e52b531d0e82a69444851528f",
    "generator": "b0988612ae6038bbbddb6f8f30e787984c5d9c71a1e380f88cd13ada8655e3d6",
}
SCHEDULE_TOKENS = ("LESSON_SCHEDULE_PERIOD", "schedule_census", "enumerate_schedule_period")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def function_source(path: Path, name: str) -> str:
    text = path.read_text()
    tree = ast.parse(text)
    lines = text.splitlines()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise AssertionError(f"missing function {name} in {path}")


def main() -> None:
    started = time.monotonic()
    work = Path(__file__).resolve().parents[3]
    repo = work / "repo"
    manifest_path = repo / "shared/tools/proposals/e600321e353d8d48/manifest.json"
    request_path = repo / "REVIEW/suggestions.json"
    generator_path = repo / "generators/dc155169ea57/generator.py"
    census_path = repo / "shared/tools/proposals/e600321e353d8d48/checks/schedule-census.json"

    manifest = json.loads(manifest_path.read_text())
    suggestions = json.loads(request_path.read_text())
    request = next(item for item in suggestions["items"] if item.get("request_id") == REQUEST_ID)
    census = json.loads(census_path.read_text())

    hashes = {
        "manifest": sha(manifest_path),
        "request_source": sha(request_path),
        "request": canonical_hash(request),
        "generator": sha(generator_path),
    }
    assert hashes == EXPECTED, {"expected": EXPECTED, "actual": hashes}

    verified_assets = []
    for entry in manifest.get("files", []):
        path = repo / entry["path"]
        actual = sha(path)
        assert actual == entry["sha256"], (path, entry["sha256"], actual)
        assert path.stat().st_size == entry["bytes"], (path, entry["bytes"], path.stat().st_size)
        verified_assets.append(entry["path"])

    generator_text = generator_path.read_text()
    assert "LESSON_SCHEDULE_PERIOD = 4" in generator_text
    assert "def schedule_profile" in generator_text
    assert census["declared_schedule_period"] == 4
    assert census["enumerated_schedule_period"] == 4
    assert census["errors"] == []

    runtime_path = repo / "src/arcpuzzles/runtime.py"
    datasets_path = repo / "src/arcpuzzles/datasets.py"
    semantic_path = repo / "shared/tools/generator_semantic_gate.py"
    lesson_path = repo / "shared/tools/lesson_census.py"

    check_src = function_source(runtime_path, "check")
    generate_src = function_source(runtime_path, "generate")
    generate_runtime_src = function_source(runtime_path, "generate_in_runtime")
    export_src = function_source(datasets_path, "export_dataset")
    semantic_src = semantic_path.read_text()
    lesson_src = lesson_path.read_text()

    check_support = {token: token in check_src for token in SCHEDULE_TOKENS}
    semantic_support = {token: token in semantic_src for token in SCHEDULE_TOKENS}
    lesson_support = {token: token in lesson_src for token in SCHEDULE_TOKENS}
    export_refs = {token: token in export_src for token in SCHEDULE_TOKENS}
    runtime_generate_refs = {
        token: token in (generate_src + "\n" + generate_runtime_src) for token in SCHEDULE_TOKENS
    }

    assert check_support["schedule_census"] and check_support["enumerate_schedule_period"]
    assert all(semantic_support.values())
    assert lesson_support["LESSON_SCHEDULE_PERIOD"] and lesson_support["enumerate_schedule_period"]
    assert not any(export_refs.values())
    assert not any(runtime_generate_refs.values())
    assert "generate_in_runtime" in export_src
    assert "demonstration_policy" in export_src

    result = {
        "schema": "arcpuzzles-tool-reproduction-observation-v1",
        "ticket_id": TICKET_ID,
        "type": "tool_reproduction",
        "consumer": "existing_tool_request_disposition",
        "status": "completed",
        "request_id": REQUEST_ID,
        "request_sha256": EXPECTED["request"],
        "request_source": {"path": "repo/REVIEW/suggestions.json", "sha256": hashes["request_source"]},
        "assets_manifest": {"path": "repo/shared/tools/proposals/e600321e353d8d48/manifest.json", "sha256": hashes["manifest"]},
        "generator_binding": {
            "task_id": "dc155169ea57",
            "generator_sha256": hashes["generator"],
            "rule_hash": "c0f1818b0fb2",
            "declared_schedule_period": 4,
        },
        "retained_schedule_receipt": {
            "path": "repo/shared/tools/proposals/e600321e353d8d48/checks/schedule-census.json",
            "declared_schedule_period": census["declared_schedule_period"],
            "enumerated_schedule_period": census["enumerated_schedule_period"],
            "errors": census["errors"],
            "lesson_count": len(census.get("lessons", [])),
        },
        "current_support": {
            "runtime_check": check_support,
            "generator_semantic_gate": semantic_support,
            "lesson_census": lesson_support,
        },
        "missing_export_boundary_integration": {
            "datasets_export_dataset": export_refs,
            "runtime_generate_and_generate_in_runtime": runtime_generate_refs,
            "export_uses_generate_in_runtime": True,
            "export_uses_demonstration_policy": True,
        },
        "proposed_request_disposition": "partially_implemented_keep_open",
        "disposition_reason": (
            "Current semantic-check tooling can enumerate and consume a declared schedule receipt, "
            "but the production generate/export path has no schedule-receipt argument or enforcement. "
            "Keep the request open, narrowed to wiring the existing receipt contract into final lesson export/admission."
        ),
        "verified_manifest_assets": len(verified_assets),
        "targeted_probe_count": 1,
        "targeted_probe_elapsed_seconds": time.monotonic() - started,
        "limits": [
            "Static source-bound boundary inspection plus retained receipt validation only.",
            "No shared source was modified and no new dataset export was executed.",
            "This observes implementation coverage; it does not approve a future export design."
        ],
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "disposition": result["proposed_request_disposition"],
        "verified_manifest_assets": result["verified_manifest_assets"],
        "export_schedule_refs": export_refs,
        "runtime_generate_schedule_refs": runtime_generate_refs,
        "result": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
