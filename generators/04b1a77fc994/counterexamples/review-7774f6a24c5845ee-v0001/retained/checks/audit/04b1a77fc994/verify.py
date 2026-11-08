from pathlib import Path
import hashlib, json, re
out = Path(__file__).resolve().parent
summary = json.loads((out / "summary.json").read_text())
source = Path("generators/04b1a77fc994/generator.py")
assert hashlib.sha256(source.read_bytes()).hexdigest() == summary["generator_sha256"]
section = (out / "section.md").read_text()
assert section.startswith("## 04b1a77fc994")
for link in re.findall(r"\]\((checks/audit/04b1a77fc994/[^)]+)\)", section):
    assert (Path("..") / link).is_file(), link
commands = json.loads((out / "commands.json").read_text())
assert all(command["exit_code"] in (0, 1) for command in commands["commands"])
assert all((Path("..") / evidence).is_file() for command in commands["commands"] for evidence in command["evidence_paths"] if evidence != "checks/audit/04b1a77fc994/verify.json")
counterexample = json.loads((out / "counterexample.json").read_text())
assert all(r["self_check"] == [] for r in counterexample["records"])
assert all(r["rival_matches_racket"] for r in counterexample["records"][:4])
assert counterexample["records"][4]["mismatched_cells"] == 25
files = [p for p in out.iterdir() if p.is_file()]
assert len(files) <= 15
report = {"source_unchanged":True,"evidence_links_valid":True,"command_evidence_valid":True,"file_count_including_this_report":len(files)+(not (out/"verify.json").exists()),"bytes_before_report":sum(p.stat().st_size for p in files),"scope":"own audit directory and selected generator hash only"}
assert report["bytes_before_report"] < 2_000_000
(out / "verify.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
