"""Verify bounded evidence integrity; no new semantic output claims."""
from pathlib import Path
import argparse
import hashlib
import json

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--evidence", type=Path,
                    default=Path(__file__).resolve().parent / "episodes-final")
EVIDENCE = parser.parse_args().evidence
manifest = json.loads((EVIDENCE / "private/manifest.json").read_text())
for name, expected in manifest["source_sha256"].items():
    source = manifest.get("source_paths", {}).get(name, name)
    assert hashlib.sha256((REPO / source).read_bytes()).hexdigest() == expected, name
for order, expected in manifest["program_sha256"].items():
    assert hashlib.sha256((EVIDENCE / "rules" / (order + ".rkt")).read_bytes()).hexdigest() == expected, order
for episode in manifest["episodes"]:
    public = json.loads((EVIDENCE / "public" / episode["file"]).read_text())
    private = json.loads((EVIDENCE / "private" / episode["file"]).read_text())
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    survivors = [name for name, check in private["rival_checks"].items()
                 if check["matches_all_demonstrations"]]
    assert survivors == [private["parameter"]["output_order"]]
print("PASS: source/rule SHA-256, challenge privacy, and one declared rule survivor per episode.")
