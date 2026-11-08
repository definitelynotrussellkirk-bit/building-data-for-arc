from pathlib import Path
import hashlib, json, re, xml.etree.ElementTree as ET
WORK = Path.cwd().parent
OUT = WORK / "checks/repository-triage"
xml = ET.parse(OUT / "rerun.xml")
cases = list(xml.iter("testcase"))
assert len(cases) == 26
failed_nodes = re.findall(r"^FAILED (tests/[^\n]+)$", (OUT / "rerun.log").read_text(), re.M)
assert len(failed_nodes) == 5
failures = [{"node_id": node, "category": "archival assertion" if "archival_reference" in node else "managed-job /proc-dependent assertion" if "managed_public" in node or "actual_detached" in node else "error-message regex assertion"} for node in failed_nodes]
report = {"original":{"failed":26,"passed":673,"skipped":3,"subtests_passed":18,"log":"checks/repository-triage/original.log"},"rerun":{"selected_nodes":26,"failed":5,"passed":21,"skipped":0,"exit_code":1,"seconds":49.01,"interpreter":str(WORK / ".venv-review/bin/python"),"environment":{"PYTHONNOUSERSITE":"1"}},"remaining_failures":failures,"baseline_execution":"not performed; no claim that remaining failures are pre-existing","source_mutations":"none by this triage"}
(OUT / "summary.json").write_text(json.dumps(report,indent=2)+"\n")
manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text())["files"]
paths = ["tests/test_archival_reference.py","tests/test_check_audit_phase.py","tests/test_check_audit_preset.py","tests/test_check_jobs.py","tests/test_packet_racket_setup.py","tests/test_review_tooling_refresh.py","tests/test_task_test_prerequisites.py","src/arcpuzzles/check_jobs.py","src/arcpuzzles/runtime.py","src/arcpuzzles/datasets.py","src/arcpuzzles/catalog.py","src/arcpuzzles/review_full_packet_files/setup_racket.py","generators/defba1ab4f90/generator.py","generators/d982cffd80f8/generator.py","shared/data/canonical/puzzles.jsonl"]
identities = []
for relative in paths:
    path = WORK / "repo" / relative
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = manifest.get("repo/"+relative)
    identities.append({"path":"repo/"+relative,"current_sha256":actual,"packet_manifest_sha256":expected,"matches_uploaded_manifest":actual == expected})
assert all(row["matches_uploaded_manifest"] for row in identities)
(OUT / "source-identities.json").write_text(json.dumps({"comparison":"current file bytes versus original PACKET-MANIFEST.json hashes; not a baseline test execution","files":identities},indent=2)+"\n")
managed = []
for number in (0,2):
    for test in ("test_managed_public_audit_chec0", "test_actual_detached_failure_w0"):
        for state in Path("/tmp/pytest-of-root").glob(f"pytest-{number}/{test}/library/var/check-runs/*/state.json"):
            managed.append({"run":"original" if number == 0 else "ready-interpreter rerun","path":str(state.parent),"state":json.loads(state.read_text()),"supervisor_log":(state.parent/"supervisor.log").read_text(),"request":json.loads((state.parent/"request.json").read_text())})
assert len(managed) == 4
(OUT / "managed-evidence.json").write_text(json.dumps(managed,indent=2)+"\n")
print(json.dumps(report,indent=2))
print("All 15 relevant source/test/data files match original packet manifest hashes.")
