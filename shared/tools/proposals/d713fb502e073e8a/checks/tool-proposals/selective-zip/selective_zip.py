"""Preflight and selectively extract a ZIP archive without dependencies."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import unicodedata
from collections import defaultdict
from pathlib import Path
import zipfile
from zipfile import ZipFile

DEFAULT_MAX_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_MEMBERS = 20_000
DEFAULT_RESERVE_BYTES = 64 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024


class SafetyError(Exception):
    """A rejected selection or destination; nothing should be extracted."""


def matches(name, selector):
    return name == selector or (selector.endswith("/") and name.startswith(selector))


def select_members(infos, includes, excludes):
    for selector in includes:
        if not selector or not any(matches(info.filename, selector) for info in infos):
            raise SafetyError(f"Include selector matched no archive members: {selector!r}")
    selected = [
        info for info in infos
        if (not includes or any(matches(info.filename, s) for s in includes))
        and not any(matches(info.filename, s) for s in excludes)
    ]
    if not selected:
        raise SafetyError("Selection contains no archive members.")
    return selected


def member_parts(info):
    name = info.filename
    if info.orig_filename != name or not name or name.startswith("/") or "\\" in name:
        raise SafetyError(f"Unsafe archive path: {info.orig_filename!r}")
    parts = (name[:-1] if info.is_dir() else name).split("/")
    if len(parts) > 128 or len(name.encode("utf-8")) > 4096:
        raise SafetyError(f"Archive path exceeds depth or length limit: {name!r}")
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT") for number in "123456789¹²³")
    for part in parts:
        if (
            part in ("", ".", "..")
            or len(part.encode("utf-8")) > 255
            or part.endswith((" ", "."))
            or any(ord(char) < 32 or ord(char) == 127 or char in ':<>"|?*' for char in part)
            or part.split(".", 1)[0].upper() in reserved
        ):
            raise SafetyError(f"Unsafe or nonportable archive path: {name!r}")
    kind = stat.S_IFMT(info.external_attr >> 16)
    allowed = (0, stat.S_IFDIR) if info.is_dir() else (0, stat.S_IFREG)
    if kind not in allowed:
        raise SafetyError(f"Symlink, special, or inconsistent member type: {name!r}")
    if info.flag_bits & (1 | 32 | 64):
        raise SafetyError(f"Encrypted or compressed-patch members are not supported: {name!r}")
    supported = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED, zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA}
    if hasattr(zipfile, "ZIP_ZSTANDARD"):
        supported.add(zipfile.ZIP_ZSTANDARD)
    if info.compress_type not in supported:
        raise SafetyError(f"Unsupported compression method {info.compress_type}: {name!r}")
    if info.is_dir() and info.file_size:
        raise SafetyError(f"Directory member unexpectedly contains data: {name!r}")
    return tuple(parts)


def validate_members(selected):
    # Include implicit parent directories, so aliases and file/parent conflicts
    # are rejected even when the ZIP has no explicit directory entries.
    nodes = {}
    for info in selected:
        parts = member_parts(info)
        for length in range(1, len(parts) + 1):
            original = parts[:length]
            key = tuple(unicodedata.normalize("NFC", part).casefold() for part in original)
            explicit = length == len(parts)
            kind = "directory" if not explicit or info.is_dir() else "file"
            previous = nodes.get(key)
            if previous:
                old_original, old_kind, old_explicit = previous
                if original != old_original or kind != old_kind or (explicit and old_explicit):
                    raise SafetyError(f"Duplicate, alias, or file/directory collision: {info.filename!r}")
                explicit = explicit or old_explicit
            nodes[key] = (original, kind, explicit)
    return {"/".join(parts) for parts, kind, _ in nodes.values() if kind == "directory"}


def validate_destination(destination):
    destination = Path(os.path.abspath(destination))
    if os.path.lexists(destination):
        raise SafetyError(f"Destination already exists; choose a new directory: {destination}")
    for ancestor in reversed(destination.parents):
        if ancestor.is_symlink():
            raise SafetyError(f"Destination parent is a symbolic link: {ancestor}")
        if not ancestor.is_dir():
            raise SafetyError(f"Destination parent is missing or is not a directory: {ancestor}")
    return destination


def nonnegative_integer(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must be nonnegative")
    return number


def positive_integer(value):
    number = nonnegative_integer(value)
    if number == 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return number


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("list", "preflight", "extract"):
        sub = commands.add_parser(command)
        sub.add_argument("archive", type=Path)
        if command != "list":
            sub.add_argument("destination", type=Path, help="new directory; its parent must already exist")
            sub.add_argument("--max-bytes", type=nonnegative_integer, default=DEFAULT_MAX_BYTES,
                             help=f"uncompressed byte budget (default {DEFAULT_MAX_BYTES})")
            sub.add_argument("--max-members", type=nonnegative_integer, default=DEFAULT_MAX_MEMBERS,
                             help=f"selected ZIP entry budget (default {DEFAULT_MAX_MEMBERS})")
            sub.add_argument("--reserve-bytes", type=nonnegative_integer, default=DEFAULT_RESERVE_BYTES,
                             help=f"disk bytes to leave free (default {DEFAULT_RESERVE_BYTES})")
            sub.add_argument("--reserve-inodes", type=nonnegative_integer, default=128,
                             help="filesystem inodes to leave free when measurable (default 128)")
        else:
            sub.add_argument("--depth", type=positive_integer, default=3, help="group path depth (default 3)")
            sub.add_argument("--members", action="store_true", help="also list every selected member")
        sub.add_argument("--include", action="append", default=[], metavar="PATH",
                         help="literal member; a trailing / selects a subtree; repeatable")
        sub.add_argument("--exclude", action="append", default=[], metavar="PATH",
                         help="literal member or subtree to omit; repeatable")
        sub.add_argument("--all", action="store_true", help="explicitly select all entries before exclusions")
        sub.add_argument("--json", action="store_true", help="emit a machine-readable report")
    return parser


def summarize(infos, selected):
    total_bytes = sum(info.file_size for info in infos)
    selected_bytes = sum(info.file_size for info in selected)
    return {
        "total_members": len(infos),
        "total_uncompressed_bytes": total_bytes,
        "selected_members": len(selected),
        "selected_files": sum(not info.is_dir() for info in selected),
        "selected_uncompressed_bytes": selected_bytes,
        "selected_compressed_bytes": sum(info.compress_size for info in selected),
        "omitted_members": len(infos) - len(selected),
        "omitted_uncompressed_bytes": total_bytes - selected_bytes,
    }


def list_groups(selected, depth):
    groups = defaultdict(lambda: {"members": 0, "uncompressed_bytes": 0, "compressed_bytes": 0})
    for info in selected:
        path = "/".join(info.filename.rstrip("/").split("/")[:depth])
        group = groups[path]
        group["members"] += 1
        group["uncompressed_bytes"] += info.file_size
        group["compressed_bytes"] += info.compress_size
    return [dict(path=path, **data) for path, data in sorted(
        groups.items(), key=lambda item: (-item[1]["uncompressed_bytes"], item[0])
    )]


def check_budgets(args, report):
    if report["selected_uncompressed_bytes"] > args.max_bytes:
        report["errors"].append(
            f"Selected bytes {report['selected_uncompressed_bytes']} exceed --max-bytes {args.max_bytes}."
        )
    if report["selected_members"] > args.max_members:
        report["errors"].append(
            f"Selected members {report['selected_members']} exceed --max-members {args.max_members}."
        )
    report.update(max_bytes=args.max_bytes, max_members=args.max_members)


def check_storage(selected, directories, destination, args, report):
    block_size, free_inodes = 4096, None
    if hasattr(os, "statvfs"):
        fs = os.statvfs(destination.parent)
        block_size = fs.f_frsize or fs.f_bsize or block_size
        if fs.f_files > 0:
            free_inodes = fs.f_favail
    free_disk = shutil.disk_usage(destination.parent).free
    allocation = sum(
        ((info.file_size + block_size - 1) // block_size) * block_size
        for info in selected if not info.is_dir()
    ) + (len(directories) + 1) * block_size
    inode_count = report["selected_files"] + len(directories) + 1
    report.update(
        allocation_block_bytes=block_size, estimated_disk_bytes=allocation,
        estimated_inodes=inode_count, free_disk_bytes=free_disk, free_inodes=free_inodes,
        reserve_bytes=args.reserve_bytes, reserve_inodes=args.reserve_inodes,
    )
    if allocation + args.reserve_bytes > free_disk:
        report["errors"].append(
            f"Insufficient disk space: estimated {allocation} + reserve {args.reserve_bytes} "
            f"> available {free_disk} bytes."
        )
    if free_inodes is not None and inode_count + args.reserve_inodes > free_inodes:
        report["errors"].append(
            f"Insufficient inodes: estimated {inode_count} + reserve {args.reserve_inodes} "
            f"> available {free_inodes}."
        )


def extract_members(archive, selected, directories, destination, max_bytes):
    # Exclusive creation prevents overwriting an existing destination even if
    # another process creates it after preflight. The parent must be trusted.
    destination.mkdir(mode=0o700)
    records, total_written = [], 0
    try:
        for relative in sorted(directories, key=lambda path: (path.count("/"), path)):
            (destination / relative).mkdir(mode=0o700)
        for info in selected:
            if info.is_dir():
                continue
            target = destination / info.filename
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(target, flags, 0o600)
            written, digest = 0, hashlib.sha256()
            with os.fdopen(descriptor, "wb") as output, archive.open(info, "r") as source:
                while True:
                    chunk = source.read(CHUNK_BYTES)
                    if not chunk:
                        break
                    written += len(chunk)
                    total_written += len(chunk)
                    if written > info.file_size or total_written > max_bytes:
                        raise SafetyError(f"Stream exceeded its declared size or byte budget: {info.filename!r}")
                    output.write(chunk)
                    digest.update(chunk)
            if written != info.file_size:
                raise SafetyError(f"Uncompressed size mismatch: {info.filename!r}")
            # Preserve only the owner's execute permission, not archive ownership,
            # timestamps, setuid bits, or group/world permissions.
            if (info.external_attr >> 16) & 0o100:
                target.chmod(0o700)
            records.append({"path": info.filename, "bytes": written, "sha256": digest.hexdigest()})
    except BaseException as exc:
        try:
            shutil.rmtree(destination)
        except OSError as cleanup_error:
            raise SafetyError(
                f"{exc}; cleanup failed, partial directory remains at {destination}: {cleanup_error}"
            ) from exc
        raise
    return records


def print_report(report, as_json):
    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return
    print(f"{report['command']}: {'OK' if report['ok'] else 'REJECTED'}")
    if "selected_members" in report:
        print(f"Selected: {report['selected_members']:,} entries, "
              f"{report['selected_uncompressed_bytes']:,} uncompressed bytes")
        print(f"Omitted: {report['omitted_members']:,} entries, "
              f"{report['omitted_uncompressed_bytes']:,} uncompressed bytes")
    for group in report.get("groups", []):
        print(f"{group['members']:>8,} {group['uncompressed_bytes']:>15,}  "
              f"{json.dumps(group['path'], ensure_ascii=True)}")
    for member in report.get("members", []):
        print(f"{member['uncompressed_bytes']:>15,}  {json.dumps(member['path'], ensure_ascii=True)}")
    if "estimated_disk_bytes" in report:
        print(f"Disk estimate: {report['estimated_disk_bytes']:,} bytes; "
              f"free: {report['free_disk_bytes']:,}; reserve: {report['reserve_bytes']:,}")
        print(f"Inode estimate: {report['estimated_inodes']:,}; free: {report['free_inodes']}")
    if "extracted_files" in report:
        print(f"Extracted and SHA-256 hashed: {report['extracted_files']:,} files")
    for warning in report["warnings"]:
        print(f"Note: {warning}")
    for error in report["errors"]:
        print(f"Error: {error}")


def main(argv=None):
    args = build_parser().parse_args(argv)
    report = {
        "command": args.command, "archive": str(args.archive), "errors": [], "warnings": [],
        "selection": {"include": args.include, "exclude": args.exclude},
        "paths_validated": False, "selected_contents_verified": False,
    }
    try:
        if args.all and args.include:
            raise SafetyError("Use either --all or --include, not both.")
        if args.command == "extract" and not args.all and not args.include:
            raise SafetyError("Extraction requires an explicit --include selection or --all.")
        with ZipFile(args.archive) as archive:
            infos = archive.infolist()
            selected = select_members(infos, args.include, args.exclude)
            report.update(summarize(infos, selected))
            if report["omitted_members"]:
                report["warnings"].append("Sparse selection: this is not a complete copy of the archive.")
            for selector in args.exclude:
                if not any(matches(info.filename, selector) for info in infos):
                    report["warnings"].append(f"Exclude selector matched no archive members: {selector!r}")
            if args.command == "list":
                report["groups"] = list_groups(selected, args.depth)
                if args.members:
                    report["members"] = [
                        {"path": info.filename, "uncompressed_bytes": info.file_size,
                         "compressed_bytes": info.compress_size, "directory": info.is_dir()}
                        for info in selected
                    ]
            else:
                check_budgets(args, report)
                directories = validate_members(selected)
                report["paths_validated"] = True
                destination = validate_destination(args.destination)
                report["destination"] = str(destination)
                check_storage(selected, directories, destination, args, report)
                report["warnings"].append(
                    "Storage is an estimate; quotas, filesystem metadata, and concurrent writes can still cause failure."
                )
                if args.command == "extract" and not report["errors"]:
                    records = extract_members(archive, selected, directories, destination, args.max_bytes)
                    report.update(files=records, extracted_files=len(records), selected_contents_verified=True)
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    report["ok"] = not report["errors"]
    print_report(report, args.json)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
