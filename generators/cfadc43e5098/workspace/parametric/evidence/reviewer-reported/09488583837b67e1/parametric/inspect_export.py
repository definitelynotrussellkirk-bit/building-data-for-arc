#!/usr/bin/env python3
"""Independently inspect a blocker-policy export's exact bytes and receipts."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def visible_bytes(episode):
    value = {"train": [{"input": p["input"], "output": p["output"]} for p in episode["train"]],
             "test": [{"input": p["input"]} for p in episode["test"]]}
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)+"\n").encode()


def inspect(root):
    root = Path(root)
    manifest = json.loads((root/"manifest.json").read_text())
    declared = []
    for row in manifest["files"]:
        name = PurePosixPath(row["path"])
        assert not name.is_absolute() and ".." not in name.parts, row
        path = root/name
        assert path.is_file() and not path.is_symlink(), row
        raw = path.read_bytes()
        assert sha(raw) == row["sha256"] and len(raw) == row["bytes"], row
        declared.append(row["path"])
    actual = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != root/"manifest.json")
    assert len(set(declared)) == len(declared) and sorted(declared) == actual
    report = json.loads((root/"report.json").read_text())
    episodes = []
    seen = set()
    for policy, record in report["settings"].items():
        ep = record["episode"]
        raw = visible_bytes(ep)
        name = "episode-"+sha(raw)+".json"
        assert name not in seen
        seen.add(name)
        assert (root/"public"/name).read_bytes() == raw
        assert set(json.loads(raw)) == {"train", "test"}
        assert json.loads((root/"private"/name).read_text()) == ep
        assert ep["parameter"] == {"blocker_policy": policy}
        rule = (root/"private/rules"/(policy.replace("_", "-")+".rkt")).read_bytes()
        assert rule == record["racket_text"].encode()
        assert sha(rule) == record["racket_sha256"] == ep["racket_sha256"]
        pairs = ep["train"] + ep["test"]
        assert len({json.dumps(p["input"], separators=(",", ":")) for p in pairs}) == len(pairs)
        assert len(ep["train"]) == report["request"]["demo_count"]
        assert len(ep["test"]) == report["request"]["query_count"]
        analysis = record["analysis"]
        assert analysis["production"]["status"] == "no_ambiguity_found"
        assert analysis["production"]["reference_labels_valid"]
        assert analysis["production"]["surviving_settings"] == [policy]
        assert all(q["query_input_distinct"] and q["reference_label_valid"] and q["alternative_refuted_by_demonstrations"] for q in analysis["queries"])
        episodes.append({"blocker_policy": policy, "public_file": "public/"+name,
                         "public_sha256": sha(raw), "demo_count": len(ep["train"]),
                         "query_count": len(ep["test"]), "distinct_inputs": len(pairs),
                         "racket_sha256": sha(rule), "query_verdicts": [q["status"] for q in analysis["queries"]]})
    assert sorted(seen) == sorted(p.name for p in (root/"public").iterdir())
    return {"status": "pass", "verified_manifest_files": len(declared), "episodes": episodes,
            "total_labeled_pairs": sum(e["demo_count"]+e["query_count"] for e in episodes),
            "total_queries": sum(e["query_count"] for e in episodes),
            "scope": "Exact public/private bytes, content IDs, source program hashes, distinctness, and fresh generation analysis receipts; no additional Racket replay."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.export), indent=2, sort_keys=True))
