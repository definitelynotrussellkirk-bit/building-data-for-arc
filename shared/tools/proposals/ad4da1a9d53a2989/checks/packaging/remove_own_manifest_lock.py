"""Recover this packet's generated manifest lock after its process has exited.

Use only in an isolated, idle reviewer packet. Refuses any issued file, symlink,
nonempty file, hard link or currently held lock. This does not modify the
packager's allowed paths or any source authority.
"""
import fcntl
import json
import os
from pathlib import Path
import stat

WORK = Path(__file__).resolve().parents[2]
RELATIVE = "repo/REVIEW/.lock"
manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text())
if RELATIVE in manifest["files"]:
    raise ValueError("Refusing to remove a file issued in this packet")
path = WORK / RELATIVE
before = path.lstat()
if not stat.S_ISREG(before.st_mode) or before.st_size != 0 or before.st_nlink != 1:
    raise ValueError("Refusing a nonempty, linked or non-regular lock file")
fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
try:
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    held = os.fstat(fd)
    current = path.lstat()
    if ((held.st_dev, held.st_ino) != (before.st_dev, before.st_ino)
            or (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino)
            or held.st_size != 0 or held.st_nlink != 1):
        raise ValueError("Lock identity changed; refusing removal")
    path.unlink()
    print(json.dumps({"removed": RELATIVE, "issued_file": False, "bytes": held.st_size,
                      "exclusive_nonblocking_lock_acquired": True,
                      "reason": "completed native manifest command leaves an empty reviewer lock"},
                     sort_keys=True))
finally:
    os.close(fd)
