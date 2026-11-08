"""Remove only an empty, unlocked runtime file absent from this packet's source.

This is a packet-local workaround for native qualification leaving REVIEW/.lock,
which the unchanged strict delta builder rejects. It changes no source checks.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--receipt", default="checks/qualification-lock-cleanup.json",
                    help="New WORK-relative receipt path under checks/")
parser.add_argument("--package", help="Optionally run the unchanged packager immediately; supply a new ZIP basename")
args = parser.parse_args()
work = Path(__file__).resolve().parents[1]
manifest = json.loads((work / "PACKET-MANIFEST.json").read_text())
relative = "repo/REVIEW/.lock"
target = work / relative
receipt_path = Path(args.receipt)
if receipt_path.is_absolute() or ".." in receipt_path.parts or receipt_path.parts[:1] != ("checks",):
    raise ValueError("Receipt must stay under WORK/checks")
out = work / receipt_path
if out.parent.resolve() != out.parent or out.is_symlink():
    raise ValueError("Receipt path must not traverse symlinks")
if args.package and (Path(args.package).name != args.package or not args.package.endswith(".zip")):
    raise ValueError("Package output must be a new ZIP basename under WORK")
if args.package and (work / args.package).exists():
    raise ValueError("Package output must be new")
if out.exists():
    raise ValueError("Cleanup receipt must be new")
if relative in manifest["files"] or target.is_symlink() or target.parent.resolve() != target.parent:
    raise ValueError("Only a newly generated non-source regular lock is eligible")
existed = target.exists()
digest = None
if existed:
    if not target.is_file():
        raise ValueError("Lock must be a regular file")
    with target.open("rb") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        opened, current = os.fstat(handle.fileno()), target.stat()
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino) or opened.st_size != 0:
            raise ValueError("Lock identity/empty-file check failed; nothing removed")
        digest = hashlib.sha256(handle.read()).hexdigest()
        target.unlink()
        fcntl.flock(handle, fcntl.LOCK_UN)
receipt = {"schema": "arcpuzzles-packet-lock-cleanup-v1", "path": relative,
           "absent_from_packet_manifest": True, "size_bytes": 0 if existed else None, "sha256": digest,
           "exclusive_nonblocking_lock_acquired": existed, "removed": existed,
           "status": "removed" if existed else "already_absent", "lock_absent_after": not target.exists(),
           "source_modified": False, "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "package_next": args.package,
           "reason": "Native parametric operation left an empty runtime lock rejected by the strict delta builder."}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt))
if args.package:
    # A lock reappeared once between separate tool calls in the observed run.
    # Staying in this process avoids that gap; the source guard stays enabled.
    os.chdir(work)
    sys.argv = ["package_return.py", "--out", args.package]
    runpy.run_path(str(work / "package_return.py"), run_name="__main__")
