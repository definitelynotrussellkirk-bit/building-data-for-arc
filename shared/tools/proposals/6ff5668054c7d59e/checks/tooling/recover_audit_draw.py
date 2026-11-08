"""One documented recovery from an unjournaled, uncommitted audit draw failure."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys

packet=Path(__file__).resolve().parents[3]
work=packet/"WORK"
sys.path.insert(0,str(work/"repo/src"))
from arcpuzzles.review_full_draw import audit_ids_for_seed, draw_audit, load_manifest
archive=Path(sys.argv[1])
seed_path=packet/".audit-recovery-seed"
# Persist before selecting targets; every retry reuses these exact bytes.
if not seed_path.exists():
    with seed_path.open("xb") as stream:
        stream.write(os.urandom(32))
        stream.flush()
        os.fsync(stream.fileno())
seed=seed_path.read_bytes()
assert len(seed)==32
manifest,packet_id=load_manifest(work)
blind=json.loads((work/"BLIND_ASSIGNMENT.json").read_text())["task_id"]
pool=[tid for tid in manifest["all_ids"] if tid != blind]
ids=audit_ids_for_seed(pool,seed)
spec=importlib.util.spec_from_file_location("zip_overlay",work/"checks/tooling/zip_packet_overlay.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ledger_path=packet/".hydrated-source-paths.json"
ledger=set(json.loads(ledger_path.read_text()))
# Also retain the known first target of the failed operation as supplemental.
homes=["WORK/repo/generators/"+tid+"/" for tid in ids+["b9b63ae52d91"]]
with mod.CompactReadZip(archive) as z:
    names=[name for name in z.entries if any(name.startswith(home) for home in homes)]
    ledger.update(names)
    ledger_path.write_text(json.dumps(sorted(ledger))+"\n")
    for name in names:
        path=packet/name
        if path.exists():
            assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest["files"][name[5:]],name
            continue
        data=z.read(name)
        assert hashlib.sha256(data).hexdigest()==manifest["files"][name[5:]],name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
contract=draw_audit(work,seed)
assert [row["task_id"] for row in contract["targets"]]==ids
receipt={"status":"completed_fresh_draw_after_uncommitted_failure","initial_failed_command":["python3","review.py","audit"],"initial_failure_evidence":"checks/commands/audit-draw.log","original_known_first_target":"b9b63ae52d91","original_seed_and_second_target":"unrecoverable; no assignment file was created","recovery_seed_saved_before_selection":seed.hex(),"recovery_target_ids":ids,"original_draw_function_used":True,"main_and_blind_assignments_unchanged":True,"hydrated_files":len(names),"maintainer_acknowledgment_required":True}
(work/"checks/audit-draw-recovery.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(receipt,indent=2))
