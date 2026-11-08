#!/usr/bin/env python3
"""Inspect, plan, materialize, and verify ARCpuzzles packets with bounded storage.

This helper never imports packet code, draws assignments, modifies the manifest,
or bypasses the official review/return validators. Python 3.10+, stdlib only.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

CHUNK = 1024 * 1024
MANIFEST_LIMIT = 64 * 1024 * 1024
SCHEMA = "arcpuzzles-full-packet-v2"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def safe_name(name):
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name or "\0" in name
            or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
            or not PurePosixPath(name).parts or str(PurePosixPath(name)) != name.rstrip("/")):
        raise ValueError(f"Unsafe archive path: {name!r}")
    return name.rstrip("/")


def no_symlinks(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Symlink path or ancestor: {part}")


def digest_stream(stream, sink=None):
    digest, count = hashlib.sha256(), 0
    while block := stream.read(CHUNK):
        digest.update(block)
        count += len(block)
        if sink is not None:
            sink.write(block)
    return digest.hexdigest(), count


def digest_file(path):
    with path.open("rb") as stream:
        return digest_stream(stream)[0]


def emit(value, stream=sys.stdout):
    print(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False), file=stream)


class Packet:
    """Validated headers and unchanged original manifest; bodies remain lazy."""

    def __init__(self, archive, source):
        self.archive, self.source = archive, Path(source).resolve()
        self.files, seen = {}, set()
        for info in archive.infolist():
            safe_name(info.orig_filename)
            key = safe_name(info.filename)
            if key in seen:
                raise ValueError(f"Duplicate archive member: {info.filename}")
            seen.add(key)
            kind = stat.S_IFMT(info.external_attr >> 16)
            if (kind not in {0, stat.S_IFREG, stat.S_IFDIR} or info.flag_bits & 1
                    or (info.is_dir() and kind == stat.S_IFREG)
                    or (not info.is_dir() and kind == stat.S_IFDIR)):
                raise ValueError(f"Unsafe archive member type: {info.filename}")
            if not info.is_dir():
                self.files[info.filename] = info
        for name in self.files:
            if any(str(parent) in self.files for parent in PurePosixPath(name).parents):
                raise ValueError(f"Archive file/directory collision: {name}")
        self.prefix = "WORK/" if "WORK/PACKET-MANIFEST.json" in self.files else ""
        self.manifest_name = self.prefix + "PACKET-MANIFEST.json"
        if self.manifest_name not in self.files:
            raise ValueError("Missing PACKET-MANIFEST.json")
        if self.files[self.manifest_name].file_size > MANIFEST_LIMIT:
            raise ValueError("Manifest exceeds 64 MiB safety limit")
        raw = archive.read(self.manifest_name)
        manifest = json.loads(raw, object_pairs_hook=unique_object)
        if manifest.get("schema") != SCHEMA or canonical(manifest) != raw:
            raise ValueError("Packet manifest is not canonical or has an unsupported schema")
        self.packet_id = hashlib.sha256(raw).hexdigest()
        if not isinstance(manifest.get("files"), dict):
            raise ValueError("Manifest files must be a hash mapping")
        self.expected = {}
        for name, digest in manifest["files"].items():
            safe_name(name)
            self.add_expected(self.prefix + name, digest)
        entries = manifest.get("layout", {}).get("entry_files", {})
        if self.prefix and (manifest.get("layout", {}).get("workspace") != "WORK"
                            or set(entries) != {"START-HERE.md", "review.py"}):
            raise ValueError("Invalid workspace entry-file layout")
        for name, digest in entries.items():
            self.add_expected(name, digest)
        self.add_expected(self.manifest_name, self.packet_id)
        missing = sorted(set(self.expected) - self.files.keys())
        extra = sorted(self.files.keys() - self.expected.keys())
        if missing or extra:
            raise ValueError(f"Archive inventory differs from manifest: missing={missing[:20]!r} "
                             f"({len(missing)} total), unexpected={extra[:20]!r} ({len(extra)} total)")
        self.automatic = {self.manifest_name, *entries}

    def add_expected(self, name, digest):
        if safe_name(name) != name:
            raise ValueError(f"Manifest file path is a directory name: {name}")
        if name in self.expected or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Invalid or duplicate manifest hash entry: {name}")
        self.expected[name] = digest

    def inspect(self):
        return {"schema": "arcpuzzles-packet-inspection-v1", "packet_id": self.packet_id,
                "source_zip": str(self.source), "manifest_path": self.manifest_name,
                "manifest_schema": SCHEMA, "archive_file_count": len(self.files),
                "expanded_bytes": sum(i.file_size for i in self.files.values()),
                "compressed_member_bytes": sum(i.compress_size for i in self.files.values()),
                "top_level_file_counts": dict(sorted(collections.Counter(n.split("/")[0] for n in self.files).items())),
                "archive_inventory_matches_manifest": True, "body_hashes_verified": 0,
                "body_integrity": "not_verified; use verify for explicit selected or all-member checks"}

    def select(self, args):
        members = list(args.member)
        if args.members_file:
            members.extend(line for line in Path(args.members_file).read_text(encoding="utf-8").splitlines()
                           if line and not line.startswith("#"))
        if args.all and (members or args.prefix):
            raise ValueError("--all cannot be combined with member or prefix selection")
        if not (args.all or members or args.prefix):
            raise ValueError("Explicit selection required: --member, --prefix, --members-file, or --all")
        selected = set(self.files) if args.all else set(self.automatic)
        missing = []
        for name in members:
            safe_name(name)
            if name not in self.files:
                missing.append(name)
            else:
                selected.add(name)
        for prefix in args.prefix:
            prefix = safe_name(prefix) + "/"
            matched = {name for name in self.files if name.startswith(prefix)}
            if not matched:
                missing.append(prefix)
            selected.update(matched)
        if missing:
            raise ValueError(f"Selection has missing exact members or empty prefixes: {missing!r}")
        return sorted(selected)

    def scope(self, selected):
        return {"packet_id": self.packet_id, "source_zip": str(self.source),
                "archive_file_count": len(self.files), "selected_file_count": len(selected),
                "selected_expanded_bytes": sum(self.files[n].file_size for n in selected),
                "omitted_file_count": len(self.files) - len(selected),
                "scope": "all_packet_members" if len(selected) == len(self.files) else "selected_members",
                "automatically_preserved_members": sorted(self.automatic)}

    def plan(self, selected, args):
        result = self.scope(selected)
        if args.max_files < 1 or args.max_bytes < 1:
            raise ValueError("Extraction budgets must be positive integers")
        if len(selected) > args.max_files or result["selected_expanded_bytes"] > args.max_bytes:
            raise ValueError(f"Selection exceeds extraction budget: {len(selected)} files / "
                             f"{result['selected_expanded_bytes']} bytes; limits "
                             f"{args.max_files} files / {args.max_bytes} bytes")
        aliases = {}
        for name in selected:
            folded = name.casefold()
            if folded in aliases:
                raise ValueError(f"Selected paths have a case alias: {aliases[folded]!r}, {name!r}")
            aliases[folded] = name
        result.update(schema="arcpuzzles-packet-plan-v1", body_hashes_verified=0,
                      budgets={"max_files": args.max_files, "max_bytes": args.max_bytes},
                      selected_files=[{"path": n, "bytes": self.files[n].file_size,
                                       "sha256": self.expected[n]} for n in selected])
        return result

    def read_verified(self, name, sink=None):
        with self.archive.open(self.files[name]) as stream:
            digest, size = digest_stream(stream, sink)
        if size != self.files[name].file_size or digest != self.expected[name]:
            raise ValueError(f"SHA-256 or size mismatch: {name}")
        return digest, size


def materialize(packet, selected, args):
    receipt = packet.plan(selected, args)
    out = Path(os.path.abspath(args.out))
    no_symlinks(out)
    if out.exists():
        raise ValueError(f"Destination must be new: {out}")
    if not out.parent.is_dir():
        raise ValueError(f"Destination parent must already exist: {out.parent}")
    receipt.update(schema="arcpuzzles-packet-materialization-v1", status="running",
                   source_zip_sha256=digest_file(packet.source), verified_file_count=0,
                   checkout=str(out / "checkout"), receipt_path=str(out / "receipt.json"),
                   full_original_packet_extracted=False,
                   verification="selected original bytes only; no review/task checks executed")
    out.mkdir()

    def save():
        pending = out / ".receipt.tmp"
        with pending.open("w", encoding="utf-8") as stream:
            json.dump(receipt, stream, sort_keys=True, indent=2, ensure_ascii=False)
            stream.write("\n")
        pending.replace(out / "receipt.json")

    save()
    try:
        for name in selected:
            target = out / "checkout" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            no_symlinks(target)
            with target.open("xb") as stream:
                packet.read_verified(name, stream)
            receipt["verified_file_count"] += 1
        receipt.update(status="complete", body_hashes_verified=len(selected),
                       full_original_packet_extracted=len(selected) == len(packet.files))
        save()
        return receipt, 0
    except Exception as error:
        receipt.update(status="failed", error=f"{type(error).__name__}: {error}",
                       body_hashes_verified=receipt["verified_file_count"])
        try:
            save()
        except OSError as save_error:
            receipt["receipt_write_error"] = str(save_error)
        return receipt, 1


def verify(packet, selected, args):
    result = packet.scope(selected)
    checkout = Path(os.path.abspath(args.checkout)) if args.checkout else None
    if checkout:
        no_symlinks(checkout)
        if not checkout.is_dir():
            raise ValueError(f"Missing checkout directory: {checkout}")
    if args.failure_limit < 1:
        raise ValueError("--failure-limit must be positive")
    failures, failure_count, checked = [], 0, 0
    for name in selected:
        try:
            if checkout:
                path = checkout / name
                no_symlinks(path)
                if not path.is_file():
                    raise ValueError("Missing or nonregular file")
                if path.stat().st_size != packet.files[name].file_size or digest_file(path) != packet.expected[name]:
                    raise ValueError("SHA-256 or size mismatch")
            else:
                packet.read_verified(name)
            checked += 1
        except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
            failure_count += 1
            if len(failures) < args.failure_limit:
                failures.append({"path": name, "error": f"{type(error).__name__}: {error}"})
    result.update(schema="arcpuzzles-packet-verification-v1", status="failed" if failure_count else "passed",
                  verification_source="checkout" if checkout else "archive",
                  checkout=str(checkout) if checkout else None,
                  verified_file_count=checked, body_hashes_verified=checked,
                  failure_count=failure_count, failures=failures,
                  unlisted_failure_count=failure_count - len(failures),
                  extra_checkout_files_checked=False, tests_run=False)
    return result, int(bool(failure_count))


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    subs = root.add_subparsers(dest="command", required=True)
    for command in ("inspect", "plan", "materialize", "verify"):
        sub = subs.add_parser(command)
        sub.add_argument("archive", type=Path)
        if command == "inspect":
            continue
        sub.add_argument("--member", action="append", default=[], help="Exact archive-relative filename; repeatable")
        sub.add_argument("--prefix", action="append", default=[], help="Archive-relative directory; repeatable")
        sub.add_argument("--members-file", type=Path, help="UTF-8 exact names, one per line; # begins a comment")
        sub.add_argument("--all", action="store_true", help="Explicitly select all original packet members")
        if command in {"plan", "materialize"}:
            sub.add_argument("--max-files", type=int, default=10000)
            sub.add_argument("--max-bytes", type=int, default=256 * 1024 * 1024)
        if command == "materialize":
            sub.add_argument("--out", type=Path, required=True, help="New directory; its parent must already exist")
        if command == "verify":
            sub.add_argument("--checkout", type=Path, help="Check selected local files instead of ZIP bodies")
            sub.add_argument("--failure-limit", type=int, default=100, help="Maximum detailed failures; total is always reported")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        with zipfile.ZipFile(args.archive) as archive:
            packet = Packet(archive, args.archive)
            if args.command == "inspect":
                result, code = packet.inspect(), 0
            else:
                selected = packet.select(args)
                if args.command == "plan":
                    result, code = packet.plan(selected, args), 0
                elif args.command == "materialize":
                    result, code = materialize(packet, selected, args)
                else:
                    result, code = verify(packet, selected, args)
        emit(result)
        return code
    except (OSError, ValueError, TypeError, KeyError, AttributeError, zipfile.BadZipFile, RuntimeError) as error:
        emit({"status": "error", "error": f"{type(error).__name__}: {error}"}, sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
