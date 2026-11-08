"""Run the unmodified native packager with an explicit, hash-bound sparse read view.

First run --index and retain its index_sha256. Package later with that hash via
--index-sha256. Only initial, manifest-listed repo omissions get is_file/read_bytes
fallback. Disk bytes always win. Selected sources, canonical data and baselines
stay physical. This verifies archive + overlay; it is not a full extraction or a
general filesystem. Keep the workspace quiescent during packaging.

Usage:
  python zip_backed_package.py --archive ORIGINAL.zip --workspace OUTER --index
  python zip_backed_package.py --archive ORIGINAL.zip --workspace OUTER --out DELTA.zip --index-sha256 HASH
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

INDEX = "checks/archive-package/index.json"
CANONICAL = "repo/shared/data/canonical/puzzles.jsonl"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def physical(path, work):
    """Reject symlinks at every component, including broken links."""
    for item in (path, *path.parents):
        if item == work.parent:
            break
        if item.is_symlink():
            raise ValueError(f"Symlink in sparse workspace: {item}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Nonregular packet file: {path}")
    return path.is_file()


@contextmanager
def archive_view(archive, workspace, *, initialize=False, index_sha256=None):
    work = Path(workspace).resolve() / "WORK"
    index_path = work / INDEX
    previous = None
    if not initialize:
        if not index_sha256 or not physical(index_path, work):
            raise ValueError("Run --index first and supply its --index-sha256")
        raw = index_path.read_bytes()
        if sha(raw) != index_sha256:
            raise ValueError("Sparse inventory hash mismatch")
        previous = json.loads(raw)
    with Path(archive).open("rb") as stream:
        archive_hash = hashlib.file_digest(stream, "sha256").hexdigest()
        if previous and previous.get("archive_sha256") != archive_hash:
            raise ValueError("Issued archive identity mismatch")
        stream.seek(0)
        with zipfile.ZipFile(stream) as source:
            infos = source.infolist()
            names = [info.filename for info in infos]
            manifest_raw = source.read("WORK/PACKET-MANIFEST.json")
            manifest = json.loads(manifest_raw)
            files = manifest["files"]
            expected = {"START-HERE.md", "review.py", "WORK/PACKET-MANIFEST.json"}
            expected.update("WORK/" + name for name in files)
            if len(names) != len(set(names)) or set(names) != expected:
                raise ValueError("Unexpected or duplicate issued archive members")
            for info in infos:
                path = PurePosixPath(info.filename)
                mode = info.external_attr >> 16
                if (path.is_absolute() or ".." in path.parts or "\\" in info.filename
                        or str(path) != info.filename or info.is_dir()
                        or stat.S_IFMT(mode) not in {0, stat.S_IFREG}):
                    raise ValueError(f"Unsafe archive member: {info.filename}")
            for name, digest in manifest.get("layout", {}).get("entry_files", {}).items():
                if sha(source.read(name)) != digest:
                    raise ValueError(f"Issued entry hash mismatch: {name}")
            for name, digest in files.items():
                if sha(source.read("WORK/" + name)) != digest:
                    raise ValueError(f"Issued member hash mismatch: {name}")
            manifest_path = work / "PACKET-MANIFEST.json"
            if not physical(manifest_path, work) or manifest_path.read_bytes() != manifest_raw:
                raise ValueError("Materialized packet manifest differs from archive")
            contract_path = work / "ASSIGNMENT.json"
            if not physical(contract_path, work):
                raise ValueError("Assignment must be physical")
            contract = json.loads(contract_path.read_bytes())
            if contract.get("packet_id") != sha(encoded(manifest)):
                raise ValueError("Assignment packet ID mismatch")
            home = f"repo/generators/{contract['task_id']}/"
            required = set(contract["baseline_sha256"]) | {CANONICAL}
            required.update(name for name in files if name.startswith(home))
            for name in required:
                if name not in files or not physical(work / name, work):
                    raise ValueError(f"Selected/baseline source must be physical: {name}")
            for name, digest in contract["baseline_sha256"].items():
                frozen = work / ".review/baseline" / name
                if (files.get(name) != digest or not physical(frozen, work)
                        or sha(frozen.read_bytes()) != digest):
                    raise ValueError(f"Frozen baseline changed: {name}")
            missing = set()
            authority = {}
            for name, digest in files.items():
                present = physical(work / name, work)
                if present and name not in required and sha((work / name).read_bytes()) != digest:
                    raise ValueError(f"Changed immutable packet source: {name}")
                if not present and name.startswith("repo/"):
                    missing.add(name)
                if not name.startswith("repo/"):
                    authority[name] = digest if present else None
            for name in ("ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json", "BLIND_ASSIGNMENT.json",
                         ".review/main-draw.lock", ".review/audit-draw.lock", ".review/blind-draw.lock"):
                authority[name] = sha((work / name).read_bytes()) if physical(work / name, work) else None
            binding = {"schema": "arcpuzzles-zip-overlay-v1", "archive_sha256": archive_hash,
                       "manifest_sha256": sha(manifest_raw), "authority_sha256": authority}
            if initialize:
                inventory = {**binding, "fallback": sorted(missing)}
                index_path.parent.mkdir(parents=True, exist_ok=True)
                with index_path.open("xb") as target:
                    target.write(encoded(inventory))
                index_path.chmod(0o444)
            else:
                inventory = previous
                if any(inventory.get(key) != value for key, value in binding.items()):
                    raise ValueError("Sparse inventory authority binding mismatch")
            fallback = set(inventory["fallback"])
            eligible = {name for name in files if name.startswith("repo/")} - required
            if (inventory["fallback"] != sorted(fallback) or not fallback <= eligible
                    or not missing <= fallback):
                raise ValueError("Missing materialized source or invalid fallback inventory")

            def fallback_name(path):
                disk = Path(path)
                if not disk.is_absolute() or not disk.is_relative_to(work):
                    return None
                name = disk.relative_to(work).as_posix()
                return name if name in fallback and not physical(disk, work) else None

            class ZipPath(type(work)):
                def is_file(self):
                    return super().is_file() or fallback_name(self) is not None

                def read_bytes(self):
                    name = fallback_name(self)
                    if name is None:
                        return super().read_bytes()
                    raw = source.read("WORK/" + name)
                    if sha(raw) != files[name]:
                        raise ValueError(f"Archive changed while reading: {name}")
                    return raw

            yield ZipPath(work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path, help="outer directory containing WORK/")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--index", action="store_true", help="create the omission inventory once")
    parser.add_argument("--index-sha256")
    parser.add_argument("--bundle-evidence", action="store_true")
    args = parser.parse_args()
    if not args.index and not args.index_sha256:
        parser.error("packaging requires --index-sha256 from the initial --index result")
    with archive_view(args.archive, args.workspace, initialize=args.index,
                      index_sha256=args.index_sha256) as root:
        if args.index:
            index = Path(root) / INDEX
            result = {"index": str(index), "index_sha256": sha(index.read_bytes()),
                      "fallback_count": len(json.loads(index.read_bytes())["fallback"])}
        else:
            sys.path.insert(0, str(Path(root) / "repo/src"))
            from arcpuzzles import review_full_return as native
            expected = Path(root) / "repo/src/arcpuzzles/review_full_return.py"
            if not expected.is_file() or Path(native.__file__).resolve() != expected.resolve():
                raise ValueError("Native validator import must match the verified local source")
            result = native.build_full_return(root, args.out, bundle_evidence=args.bundle_evidence)
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
