#!/usr/bin/env python3
"""Run an unchanged review packet on a private tmpfs; export new response ZIPs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import zipfile

MIB = 1024 * 1024


def directory(raw, *, empty=False, unmounted=False):
    path = Path(raw).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"Directory contains a symlink: {path}")
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"An existing directory is required: {path}")
    if unmounted and os.path.ismount(path):
        raise ValueError(f"Mountpoint is already mounted: {path}")
    if empty and any(path.iterdir()):
        raise ValueError(f"Mountpoint must be empty: {path}")
    return path


def digest(stream):
    checksum = hashlib.sha256()
    for block in iter(lambda: stream.read(MIB), b""):
        checksum.update(block)
    return checksum.hexdigest()


def inventory(archive):
    seen, files, directories = set(), set(), set()
    total = allocated = 0
    for item in archive.infolist():
        name = item.orig_filename
        parts = name.rstrip("/").split("/")
        if (name != item.filename or not name or name.startswith("/") or "\\" in name
                or any(p in {"", ".", ".."} for p in parts)
                or re.match(r"^[A-Za-z]:", name) or name.endswith("//")):
            raise ValueError(f"Unsafe ZIP path: {name!r}")
        key = "/".join(parts)
        if key in seen:
            raise ValueError(f"Duplicate ZIP entry: {key}")
        seen.add(key)
        kind = stat.S_IFMT(item.external_attr >> 16)
        allowed_kind = stat.S_IFDIR if item.is_dir() else stat.S_IFREG
        if kind not in {0, allowed_kind} or item.flag_bits & 1:
            raise ValueError(f"Unsafe ZIP type or encryption: {key}")
        directories.update("/".join(parts[:i]) for i in range(1, len(parts)))
        if item.is_dir():
            if item.file_size:
                raise ValueError(f"Unsafe nonempty ZIP directory: {key}")
            directories.add(key)
        else:
            files.add(key)
            total += item.file_size
            allocated += ((item.file_size + 4095) // 4096) * 4096
    if files & directories:
        raise ValueError("ZIP file/directory parent conflict")
    count = len(files) + len(directories)
    return {"files": len(files), "directories": len(directories), "payload_bytes": total,
            "required_inodes": count, "estimated_allocated_bytes": allocated,
            "tmpfs_bytes": ((max(512 * MIB, allocated * 2 + 256 * MIB) + MIB - 1) // MIB) * MIB,
            "tmpfs_inodes": max(32768, count * 2 + 4096)}, files


def preflight(packet, mountpoint, output):
    mountpoint = directory(mountpoint, empty=True, unmounted=True)
    output = directory(output)
    packet = Path(packet).absolute()
    if packet.is_symlink() or not packet.is_file():
        raise ValueError("Packet must be a regular, non-symlink ZIP file")
    packet = packet.resolve()
    for path in (packet, output, Path(__file__).resolve()):
        if path == mountpoint or mountpoint in path.parents:
            raise ValueError("Packet, helper and output must be outside the mountpoint")
    with packet.open("rb") as stream:
        sha = digest(stream)
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            plan, _ = inventory(archive)
    tools = {name: shutil.which(name) for name in ("unshare", "mount")}
    if not all(tools.values()):
        raise ValueError("Required namespace tools unavailable: unshare and mount")
    free = os.statvfs(output)
    plan.update(packet=str(packet), mountpoint=str(mountpoint), output_dir=str(output),
                archive_sha256=sha, tools=tools, output_available_bytes=free.f_bavail * free.f_frsize,
                output_available_inodes=free.f_favail,
                outer_mount_namespace=os.readlink("/proc/self/ns/mnt"),
                outer_user_namespace=os.readlink("/proc/self/ns/user"))
    return plan


def export_outputs(root, output, original_files):
    root, output = Path(root), directory(output)
    if output == root or root in output.parents:
        raise ValueError("Output directory must be outside the private mount")
    if (root / "WORK").is_symlink():
        raise ValueError("Unsafe symlink WORK output directory")
    candidates = sorted([*root.glob("review_response_*.zip"),
                         *(root / "WORK").glob("review_response_*.zip")])
    selected, names = [], set()
    for source in candidates:
        if source.relative_to(root).as_posix() in original_files:
            continue
        if source.is_symlink() or not source.is_file() or not zipfile.is_zipfile(source):
            raise ValueError(f"Unsafe or invalid response ZIP: {source}")
        target = output / source.name
        if source.name in names or target.exists() or target.is_symlink():
            raise FileExistsError(f"Response name collision; nothing overwritten: {target}")
        names.add(source.name)
        selected.append((source, target))
    free = os.statvfs(output)
    needed = sum(((source.stat().st_size + 4095) // 4096) * 4096 for source, _ in selected)
    if needed > free.f_bavail * free.f_frsize or len(selected) > free.f_favail:
        raise OSError("Output directory has insufficient free bytes or inodes")
    exported = []
    for source, target in selected:
        with source.open("rb") as reader, target.open("xb") as writer:
            expected = digest(reader)
            reader.seek(0)
            shutil.copyfileobj(reader, writer)
            writer.flush()
            os.fsync(writer.fileno())
        with target.open("rb") as reader:
            if digest(reader) != expected:
                raise OSError(f"Export verification failed; retained partial file: {target}")
        exported.append(str(target))
    if exported:
        fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return exported


def inside(plan):
    if (os.readlink("/proc/self/ns/mnt") == plan["outer_mount_namespace"]
            or os.readlink("/proc/self/ns/user") == plan["outer_user_namespace"]):
        raise ValueError("Refusing to mount outside new private user and mount namespaces")
    root = directory(plan["mountpoint"], empty=True, unmounted=True)
    directory(plan["output_dir"])
    with Path(plan["packet"]).open("rb") as stream:
        if digest(stream) != plan["archive_sha256"]:
            raise ValueError("Packet changed after preflight")
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            _, original_files = inventory(archive)
            subprocess.run([plan["tools"]["mount"], "-n", "-t", "tmpfs", "-o",
                            f"size={plan['tmpfs_bytes']},nr_inodes={plan['tmpfs_inodes']},mode=700,nosuid,nodev",
                            "packet-review", str(root)], check=True)
            for item in archive.infolist():
                target = root / item.filename
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as reader, target.open("xb") as writer:
                        shutil.copyfileobj(reader, writer)
                    target.chmod(0o644)
    temporary = tempfile.mkdtemp(prefix=".packet-tmp-", dir=root)
    env = {**os.environ, "TMPDIR": temporary, "TMP": temporary, "TEMP": temporary}
    while True:
        result = subprocess.run(plan["command"], cwd=root, env=env)
        try:
            exported = export_outputs(root, plan["output_dir"], original_files)
        except (ValueError, OSError) as error:
            if not plan["shell"]:
                raise
            print(f"Export failed: {error}\nPrivate workspace retained. Fix the output problem in this "
                  "shell; exiting retries export. Hard termination loses unsaved data.", file=sys.stderr)
            continue
        print(json.dumps({"status": "exported" if exported else "no_response_zips_generated",
                          "exported": exported, "command_exit_code": result.returncode}), flush=True)
        return result.returncode if result.returncode >= 0 else 128 - result.returncode


def main(argv=None):
    # Catch Ctrl-C in supervisors; exec resets this caught handler for the command.
    signal.signal(signal.SIGINT, lambda *_: None)
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--_inside"]:
        return inside(json.loads(argv[1]))
    command = []
    if "--" in argv:
        split = argv.index("--")
        argv, command = argv[:split], argv[split + 1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--mountpoint", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dry-run", "--preflight", action="store_true")
    parser.add_argument("--shell", action="store_true", help="Explicitly open an interactive shell")
    args = parser.parse_args(argv)
    if args.shell and command:
        raise ValueError("Choose either --shell or a command after --")
    if not args.dry_run and not (args.shell or command):
        raise ValueError("A command after -- or explicit --shell is required")
    if args.shell and not args.dry_run:
        if not sys.stdin.isatty():
            raise ValueError("--shell requires an interactive terminal")
        command = [shutil.which("bash") or "/bin/sh", "-i"]
    plan = preflight(args.packet, args.mountpoint, args.output_dir)
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    plan.update(command=command, shell=args.shell)
    return subprocess.run([plan["tools"]["unshare"], "--user", "--map-root-user", "--mount",
                           "--propagation", "private", "--fork", "--kill-child=TERM",
                           sys.executable, str(Path(__file__).resolve()), "--_inside", json.dumps(plan)]).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print(f"packet_tmpfs: {error}", file=sys.stderr)
        raise SystemExit(2)
