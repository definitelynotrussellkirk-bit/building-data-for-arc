"""Run the unmodified packet builder on verified original bytes plus a real overlay.

Requires pyfakefs==5.9.3 (Python 3.12 tested). This is a storage adapter, not a
replacement validator. The input ZIP, extraction inventory, frozen baseline and
working tree are read only. Only the final, independently validated delta ZIP is
written. The explicit inventory distinguishes unextracted files from deletions.
The disposable .review/racket-runtime tree is excluded; all repo source and all
checks/solve evidence, including unexpected changes, remain visible to the builder.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib
import io
import json
import linecache
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def safe_name(name: str) -> None:
    p = PurePosixPath(name)
    if (not name or name == "." or p.is_absolute() or p.as_posix() != name or
            ".." in p.parts or "\\" in name or ":" in name or "\0" in name):
        raise ValueError(f"Unsafe packet path: {name!r}")


@dataclass(frozen=True)
class Entry:
    mode: int
    data: bytes | str | None


@dataclass
class Snapshot:
    packet: Path
    work: Path
    manifest: dict
    original: dict[str, Entry]
    overlay: dict[str, Entry]
    archive_sha256: str


def read_original(packet: Path) -> tuple[dict, dict[str, Entry], str]:
    raw_zip = packet.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        for info in infos:
            safe_name(info.orig_filename)
            if info.filename != info.orig_filename:
                raise ValueError(f"Altered raw ZIP filename: {info.orig_filename!r}")
        folded = {n.casefold() for n in names}
        if len(folded) != len(names):
            raise ValueError("Duplicate or case-colliding input ZIP members")
        for name in names:
            if any(str(p).casefold() in folded
                   for p in PurePosixPath(name).parents if str(p) != "."):
                raise ValueError(f"Input file/directory collision: {name}")
        manifest_raw = archive.read("WORK/PACKET-MANIFEST.json")
        manifest = json.loads(manifest_raw)
        if (manifest.get("schema") != "arcpuzzles-full-packet-v2" or
                canonical(manifest) != manifest_raw or
                manifest.get("layout", {}).get("workspace") != "WORK"):
            raise ValueError("Expected a canonical v2 packet with WORK layout")
        expected = {}
        for name, digest in manifest["files"].items():
            safe_name(name)
            if name == "PACKET-MANIFEST.json":
                raise ValueError("Manifest cannot declare itself")
            expected["WORK/" + name] = digest
        for name, digest in manifest["layout"]["entry_files"].items():
            safe_name(name)
            if name == "WORK" or name.startswith("WORK/") or name == "PACKET-MANIFEST.json":
                raise ValueError("Outer entry must be outside WORK and cannot declare the manifest")
            if name in expected:
                raise ValueError(f"Conflicting manifest path: {name}")
            expected[name] = digest
        expected["WORK/PACKET-MANIFEST.json"] = sha(manifest_raw)
        if set(names) != set(expected):
            raise ValueError("Input ZIP members differ from its complete manifest")
        original = {}
        for info in infos:
            mode = info.external_attr >> 16
            if (stat.S_IFMT(mode) != stat.S_IFREG or mode & 0o111 or
                    info.flag_bits & 1 or info.compress_type not in
                    {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}):
                raise ValueError(f"Unsafe input ZIP member: {info.filename}")
            raw = archive.read(info)  # Also checks decompression and CRC.
            if sha(raw) != expected[info.filename]:
                raise ValueError(f"Original member hash differs: {info.filename}")
            original[info.filename] = Entry(mode, raw)
    return manifest, original, sha(raw_zip)


def read_overlay(work: Path) -> dict[str, Entry]:
    """Read exact bytes and lstat modes without following directory symlinks."""
    result = {}

    def visit(path: Path) -> None:
        name = path.relative_to(work.parent).as_posix()
        if name == "WORK/.review/racket-runtime":
            return
        before = path.lstat()
        mode = before.st_mode
        if stat.S_ISLNK(mode):
            result[name] = Entry(mode, os.readlink(path))
        elif stat.S_ISDIR(mode):
            result[name] = Entry(mode, None)
            for child in sorted(path.iterdir()):
                visit(child)
        elif stat.S_ISREG(mode):
            result[name] = Entry(mode, path.read_bytes())
        else:
            raise ValueError(f"Unsupported working-tree file type: {name}")
        after = path.lstat()
        if (before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns) != (
                after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns):
            raise ValueError(f"Working tree changed while reading: {name}")

    if work.name != "WORK" or work.is_symlink() or not work.is_dir():
        raise ValueError("--work must name a real WORK directory")
    visit(work)
    return result


def read_snapshot(packet: Path, work: Path) -> Snapshot:
    packet, work = packet.absolute(), work.absolute()
    manifest, original, archive_hash = read_original(packet)
    overlay = read_overlay(work)
    contract = json.loads(overlay["WORK/ASSIGNMENT.json"].data)
    inventory = json.loads(overlay["WORK/extraction_inventory.json"].data)
    packet_hash = sha(original["WORK/PACKET-MANIFEST.json"].data)
    if (inventory.get("schema") != "arcpuzzles-partial-extraction-inventory-v1"
            or inventory.get("source_archive_sha256") != archive_hash
            or inventory.get("packet_sha256") != packet_hash
            or contract.get("packet_id") != packet_hash):
        raise ValueError("Inventory/assignment does not match the original packet")
    members = inventory.get("members", [])
    if (not isinstance(members, list) or len(members) != len(set(members))
            or not set(members) <= original.keys()):
        raise ValueError("Invalid extraction inventory")
    # These scopes were completely extracted before this adapter was written.
    mandatory = {n for n in original if n.startswith(
        ("WORK/repo/src/", "WORK/repo/shared/runtime/"))}
    mandatory.update("WORK/" + n for n in contract["baseline_sha256"])
    mandatory.update(manifest["layout"]["entry_files"])
    mandatory.add("WORK/PACKET-MANIFEST.json")
    if not mandatory <= set(members):
        raise ValueError("Extraction inventory omits an initially extracted scope")
    for name in members:
        if not os.path.lexists(work.parent / name):
            raise ValueError(f"Missing extracted member: {name}")
    for name, entry in original.items():
        if name.startswith("WORK/"):
            current = overlay.get(name)
        else:
            path = work.parent / name
            mode = path.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise ValueError(f"Changed immutable packet entry: {name}")
            current = Entry(mode, path.read_bytes())
            overlay[name] = current
        if current is not None and name not in members:
            raise ValueError(f"New extraction needs an inventory entry: {name}")
        if current is not None and not name.startswith("WORK/repo/"):
            if (not stat.S_ISREG(current.mode) or current.mode & 0o111
                    or current.data != entry.data):
                raise ValueError(f"Changed immutable packet entry: {name}")
    for name, digest in contract["baseline_sha256"].items():
        safe_name(name)
        frozen = overlay.get("WORK/.review/baseline/" + name)
        if (manifest["files"].get(name) != digest or frozen is None or
                not stat.S_ISREG(frozen.mode) or sha(frozen.data) != digest):
            raise ValueError(f"Frozen baseline changed or missing: {name}")
    return Snapshot(packet, work, manifest, original, overlay, archive_hash)


def official_builder(packet: Path):
    """Import authentic source from the verified ZIP, never from an edited helper."""
    source = str(packet) + "/WORK/repo/src"
    for name, module in sys.modules.copy().items():
        if name == "arcpuzzles" or name.startswith("arcpuzzles."):
            if not str(getattr(module, "__file__", "")).startswith(source + "/"):
                raise ValueError("Run in a fresh Python process; arcpuzzles is already loaded")
    sys.path.insert(0, source)
    return importlib.import_module("arcpuzzles.review_full_return")


def hydrate(snapshot: Snapshot, fs) -> None:
    for name, entry in snapshot.original.items():
        fs.create_file(str(snapshot.work.parent / name), contents=entry.data,
                       st_mode=entry.mode, apply_umask=False)
    for name, entry in sorted(snapshot.overlay.items(), key=lambda item: (item[0].count("/"), item[0])):
        path = snapshot.work.parent / name
        if os.path.lexists(path):
            if stat.S_ISDIR(entry.mode) and path.is_dir() and not path.is_symlink():
                continue
            fs.remove_object(str(path))
        if stat.S_ISDIR(entry.mode):
            fs.create_dir(str(path))
        elif stat.S_ISLNK(entry.mode):
            fs.create_symlink(str(path), entry.data)
        else:
            fs.create_file(str(path), contents=entry.data, st_mode=entry.mode, apply_umask=False)
    for name, entry in snapshot.overlay.items():
        path = snapshot.work.parent / name
        if stat.S_ISDIR(entry.mode):
            path.chmod(stat.S_IMODE(entry.mode))
    # Check roundtrip bytes, mode and symlink targets for every real overlay entry.
    for name, entry in snapshot.overlay.items():
        path = snapshot.work.parent / name
        data = (os.readlink(path) if stat.S_ISLNK(entry.mode) else
                None if stat.S_ISDIR(entry.mode) else path.read_bytes())
        if data != entry.data or path.lstat().st_mode != entry.mode:
            raise ValueError(f"In-memory overlay differs: {name}")
    # Untouched original members also survive the materialization byte-for-byte.
    for name, entry in snapshot.original.items():
        shadowed = any(str(p) in snapshot.overlay and not stat.S_ISDIR(snapshot.overlay[str(p)].mode)
                       for p in PurePosixPath(name).parents if str(p) != ".")
        if name not in snapshot.overlay and not shadowed:
            path = snapshot.work.parent / name
            if path.read_bytes() != entry.data or path.lstat().st_mode != entry.mode:
                raise ValueError(f"In-memory original differs: {name}")


def memory_return(snapshot: Snapshot, builder, *, verify_input: bool = False) -> bytes | None:
    from pyfakefs.fake_filesystem_unittest import Patcher
    # Import before filesystem substitution. Cache authentic source lines because
    # pyfakefs stack inspection otherwise recursively invokes zipimport's I/O.
    for name in ("review_solve", "review_tickets", "review_curriculum", "review_full_draw", "review_nvarc"):
        importlib.import_module("arcpuzzles." + name)
    for name, module in sys.modules.copy().items():
        if name == "arcpuzzles" or name.startswith("arcpuzzles."):
            linecache.getlines(module.__file__, module.__dict__)
    with Patcher(use_known_patches=False) as patcher:
        hydrate(snapshot, patcher.fs)
        if verify_input:
            return None
        target = Path("/__arcpuzzles_memory_return__/return.zip")
        builder.build_full_return(Path(str(snapshot.work)), target)
        return target.read_bytes()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verify-input", action="store_true", help="Verify/hydrate only; do not build a return")
    args = parser.parse_args()
    if not args.verify_input and args.out is None:
        parser.error("--out is required unless --verify-input is used")
    if args.out is not None and os.path.lexists(args.out):
        raise FileExistsError(args.out)
    snapshot = read_snapshot(args.packet, args.work)
    builder = official_builder(snapshot.packet)
    raw = memory_return(snapshot, builder, verify_input=args.verify_input)
    # Real filesystem APIs are restored before independent ZIP validation.
    result = {"original_members": len(snapshot.original), "overlay_entries": len(snapshot.overlay),
              "source_archive_sha256": snapshot.archive_sha256}
    if raw is not None:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            checked = builder.validate_full_return(archive, snapshot.manifest)
        if read_snapshot(snapshot.packet, snapshot.work) != snapshot:
            raise ValueError("Inputs changed during packaging; no output was written")
        with args.out.open("xb") as stream:
            try:
                stream.write(raw)
                stream.flush()
                with zipfile.ZipFile(args.out) as archive:
                    persisted = builder.validate_full_return(archive, snapshot.manifest)
                if persisted != checked or args.out.read_bytes() != raw:
                    raise ValueError("Saved return differs from validated bytes")
            except BaseException:
                args.out.unlink()
                raise
        result.update(zip=str(args.out.absolute()), zip_sha256=sha(raw),
                      assignment_id=checked["assignment_id"], completion_state=checked["completion_state"])
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
