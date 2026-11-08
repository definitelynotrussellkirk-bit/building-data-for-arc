"""One bounded replay of the selected authority-sync tool request."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import time
import zipfile

from arcpuzzles.authority_sync import propose_selected_sync
from arcpuzzles.catalog import Catalog
from arc_repl.racket_bridge import RacketBridge


def sha(blob):
    return hashlib.sha256(blob.encode() if isinstance(blob, str) else blob).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("choose a new output file")
    started = time.monotonic()
    task = "637229802e6f"
    base_path = "shared/data/base/solutions/training/87ab05b8__637229802e6f.json"
    asset_path = "shared/tools/proposals/160d4de77bd6dfed/checks/authority-sync-manual.json"
    with zipfile.ZipFile(args.archive) as archive:
        baseline = {p: archive.read("WORK/repo/" + p) for p in (
            "catalog/puzzles.jsonl", "catalog/authority_files.json",
            "shared/data/canonical/puzzles.jsonl", base_path)}
        witness_bytes = archive.read("WORK/repo/" + asset_path)
        generator_bytes = archive.read(f"WORK/repo/generators/{task}/generator.py")
    assert sha(witness_bytes) == "e0c4ab90b56ff7f559b0c90fe299ee9ebe46a319ef669e3c6175fc3b462ffd68"
    assert sha(generator_bytes) == "21ab150fecd7bb6f62ca9914f873a6efb87dfb7698e61711844070b36ae4f519"
    witness = json.loads(witness_bytes)
    base = json.loads(baseline[base_path])
    row = next(json.loads(line) for line in baseline["shared/data/canonical/puzzles.jsonl"].splitlines()
               if json.loads(line).get("task_id") == task)
    canonical = row["program_solution"]
    archival = base["racket_target"]["raw_code"]
    assert sha(canonical) == witness["canonical_program_solution_sha256"]
    assert sha(archival) == witness["selected_target_sha256_before"]
    assert sha(baseline[base_path]) == witness["file_sha256_after"]

    # Exercise the real tool on a disposable copy; no live authority is edited.
    with tempfile.TemporaryDirectory(prefix="authority-request-replay-") as temporary:
        root = Path(temporary)
        for name, blob in baseline.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
        catalog = Catalog(root)
        current = propose_selected_sync(catalog, task)
        assert current["status"] == "already_synchronized" and not current["applied"]
        reconstructed = json.loads(baseline[base_path])
        reconstructed["racket_target"]["target_code"] = archival
        path = root / base_path
        path.write_text(json.dumps(reconstructed, indent=2) + "\n")
        before = path.read_bytes()
        try:
            propose_selected_sync(catalog, task)
        except ValueError as error:
            refusal = str(error)
        else:
            raise AssertionError("Unexpected proposal for token-changing historical rule")
        assert "rule tokens differ" in refusal and path.read_bytes() == before

    parity = []
    with RacketBridge(startup_timeout=60, timeout=15) as bridge:
        for name, program in (("retained_old", archival), ("current_rule", canonical)):
            text = program.strip()
            assert text.startswith("(rule!") and text.endswith(")")
            bridge.eval_text(f"(define {name} {text[len('(rule!'):-1]})")
        for split in ("train", "test"):
            for index, pair in enumerate(row[split]):
                bridge.define_grid("ticket_input", pair["input"])
                old = bridge.eval_text("(retained_old ticket_input)")
                new = bridge.eval_text("(current_rule ticket_input)")
                parity.append(dict(split=split, index=index, old_matches=old == pair["output"],
                                   current_matches=new == pair["output"], old_equals_current=old == new))
    assert len(parity) == 4 and all(all(x[k] for k in ("old_matches", "current_matches", "old_equals_current")) for x in parity)
    report = dict(schema="authority-request-replay-v1", ticket_id="ticket-7299299d81b282ce",
                  status="completed", elapsed_seconds=time.monotonic()-started,
                  source_hashes={p: sha(b) for p, b in baseline.items()},
                  retained_witness_sha256=sha(witness_bytes), generator_sha256=sha(generator_bytes),
                  probe_sha256=sha(Path(__file__).read_bytes()), current_proposal=current,
                  historical_target_reconstruction="Replaced only target_code with hash-matched retained archival source; original JSON serialization not reconstructed.",
                  historical_refusal=refusal, historical_source_unchanged_by_proposal=True,
                  racket_canonical_parity=parity,
                  proposed_disposition="Keep request open for an explicit parity-reviewed semantic proposal, or narrow it to the existing token-equivalent command; the selected authority itself is already synchronized.",
                  limits="Four canonical pairs support bounded parity only. The current command correctly refuses different rule tokens and does not implement finite-parity semantic proposals.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "completed", "canonical_pairs": len(parity), "current": current["status"], "historical_refused": True}))


if __name__ == "__main__":
    main()
