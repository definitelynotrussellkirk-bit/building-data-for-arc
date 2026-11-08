"""Read-only current-source and saved-export inspection; no reference execution."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root


def inspect(folder, report_path):
    root = find_root(__file__)
    folder, report_path = Path(folder).resolve(), Path(report_path).resolve()
    helper_path = root.parent / "check_public_exports.py"
    spec = importlib.util.spec_from_file_location("_branch_public_check", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    serial = helper.serializer()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    raw = lambda value: (json.dumps(value, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False, allow_nan=False) + "\n").encode()
    report = json.loads(report_path.read_bytes())
    manifest = json.loads((folder / "manifest.json").read_bytes())
    context = json.loads((folder / "private/context.json").read_bytes())
    metadata = [json.loads(line) for line in (folder / "private/metadata.jsonl").read_text().splitlines()]
    consumers = {
        "actor": helper.inspect([folder / "turns"], queries=1, demos=report["demonstrations"]),
        "controller": helper.inspect([folder / "private/controllers"],
                                     queries=report["queries"], demos=report["demonstrations"]),
    }
    findings = []
    def require(ok, detail):
        if not ok:
            findings.append(detail)
    require(all(r["status"] == "passed" for r in consumers.values()), "saved consumer format differs")
    require(manifest["complete"] is True, "manifest is incomplete")
    for value in (manifest, context, report):
        require(value["native_acceptance"] == "owner_pending" and value["training_admitted"] is False,
                "scope marker falsely claims acceptance or training admission")
    require(sha(folder / "manifest.json") == report["manifest_sha256"], "manifest binding differs")
    require(sha(folder / "private/metadata.jsonl") == report["private_metadata_sha256"], "metadata binding differs")
    require(sha(folder / "private/context.json") == report["private_context_sha256"], "context binding differs")
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    require(actual == set(manifest["files"]) | {"manifest.json"}, "exported file inventory differs")
    require(all(sha(folder / name) == digest for name, digest in manifest["files"].items()), "payload hash differs")
    require(context["source_sha256"] == report["source_sha256"], "source inventories disagree")
    require(all(sha(root / name) == digest for name, digest in report["source_sha256"].items()), "current source differs")
    native = context["native_execution"]
    require(native["racket"] == report["racket"] and native["racket"]["backend"] == "racket"
            and native["racket"]["protected"] is True, "retained protected runtime identity differs")
    require(hashlib.sha256(raw(native)).hexdigest() == report["native_execution_sha256"], "native result hash differs")
    require(native["racket_evaluations"] == report["racket_evaluations"], "retained evaluation counts differ")
    require(len(metadata) == len(native["episodes"]) == report["settings_count"], "episode counts differ")
    require([row["controller_id"] for row in metadata] == report["controller_ids"] == manifest["controller_ids"],
            "sorted controller identifiers differ")
    all_turns = []
    for row in metadata:
        episode = row["episode"]
        wrapper = episode["native_wrapper"]
        require(wrapper in native["episodes"], "original native wrapper is not retained")
        require(episode["program_solution"] == wrapper["program"], "retained program differs")
        require(hashlib.sha256(wrapper["program"].encode()).hexdigest() == wrapper["program_sha256"],
                "native program hash differs")
        require(episode["native_validation"]["owner_acceptance"] == "not_performed"
                and episode["native_validation"]["training_admitted"] is False, "private acceptance scope differs")
        for split in ("train", "test"):
            labels = [{"input": p["input"], "output": p["output"]} for p in episode[split]]
            require(raw(labels) == raw(wrapper[split]), "adapter labels differ from executed native labels")
        controller = folder / "private/controllers" / (row["controller_id"] + ".json")
        require(controller.read_bytes() == serial(wrapper), "controller projection differs")
        require(len(row["turn_ids"]) == len(wrapper["test"]) == report["queries"], "ordered turn mapping count differs")
        for identifier, pair in zip(row["turn_ids"], wrapper["test"], strict=True):
            turn = folder / "turns" / (identifier + ".json")
            require(turn.read_bytes() == serial({"train": wrapper["train"], "test": [pair]}),
                    "single-query actor projection differs")
        first = folder / "turns" / (row["turn_ids"][0] + ".json")
        require(first.read_bytes() == serial({"train": episode["train"], "test": episode["test"][:1]}),
                "single-query/four-query first-turn bytes differ")
        all_turns.extend(row["turn_ids"])
    require(sorted(all_turns) == report["turn_ids"] == manifest["turn_ids"], "sorted actor identifiers differ")
    return {"schema": "arcpuzzles-native-branch-export-inspection-v1", "status": "failed" if findings else "passed",
            "findings": findings, "actor_conformance": consumers["actor"], "controller_conformance": consumers["controller"],
            "source_bindings_checked": len(report["source_sha256"]), "payload_files_checked": len(manifest["files"]),
            "private_episode_rows": len(metadata), "retained_racket_evaluations": native["racket_evaluations"],
            "example_report_sha256": sha(report_path), "manifest_sha256": sha(folder / "manifest.json"),
            "checker_sha256": sha(Path(__file__).resolve()), "consumer_helper_sha256": sha(helper_path),
            "serializer_sha256": sha(root / "shared/runtime/reviewer_support.py"),
            "reference_program_evaluations_performed": 0, "owner_acceptance": "not_performed", "training_admitted": False,
            "limits": "Static current-source, stored-label, projection and identity checks. Native execution is retained evidence; this inspection does not re-execute labels, test a turn controller, qualify or accept source."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    result = inspect(options.export, options.report)
    with options.out.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "findings": result["findings"],
                      "source_bindings_checked": result["source_bindings_checked"],
                      "actor_files": result["actor_conformance"]["files_checked"],
                      "controller_files": result["controller_conformance"]["files_checked"]}, sort_keys=True))
    raise SystemExit(bool(result["findings"]))
