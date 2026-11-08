#!/usr/bin/env python3
"""Read-only ZIP extraction capacity estimate; never extracts or deletes files."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import zipfile


def inspect_zip(archive, destination, *, reserve_bytes=0, reserve_inodes=0):
    for name, value in [('reserve_bytes', reserve_bytes), ('reserve_inodes', reserve_inodes)]:
        if type(value) is not int or value < 0:
            raise ValueError(f'{name} must be an exact nonnegative integer')
    destination = Path(destination).absolute()
    existing = destination
    missing_destination_dirs = 0
    while not existing.exists():
        if existing.is_symlink():
            raise ValueError(f'Destination path has a dangling symlink: {existing}')
        missing_destination_dirs += 1
        existing = existing.parent
    if not existing.is_dir():
        raise ValueError("Destination or its existing ancestor is not a directory")
    fs = os.statvfs(existing)
    block = fs.f_frsize or fs.f_bsize
    files, directories, members, nested = {}, set(), set(), []
    compressed_bytes = 0
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            name = info.filename[:-1] if info.is_dir() else info.filename
            if (not name or name != info.orig_filename.rstrip('/') or '\\' in name or '\0' in name
                    or PurePosixPath(name).is_absolute() or PureWindowsPath(name).drive
                    or any(p in {'', '.', '..'} for p in name.split('/'))):
                raise ValueError(f"Unsafe ZIP path: {info.orig_filename!r}")
            if name in members:
                raise ValueError(f"Duplicate ZIP path: {name}")
            members.add(name)
            kind = stat.S_IFMT(info.external_attr >> 16)
            if kind and kind != (stat.S_IFDIR if info.is_dir() else stat.S_IFREG):
                raise ValueError(f"Nonregular ZIP member: {name}")
            compressed_bytes += info.compress_size
            for parent in PurePosixPath(name).parents:
                if str(parent) != '.':
                    directories.add(str(parent))
            if info.is_dir():
                directories.add(name)
            else:
                files[name] = info.file_size
                if name.lower().endswith(('.zip', '.tar', '.tgz', '.tar.gz', '.tar.xz')):
                    nested.append({'path': name, 'compressed_container_expanded_bytes': info.file_size})
    if set(files) & directories:
        raise ValueError("ZIP file is also used as a directory")
    expanded = sum(files.values())
    file_allocation = sum(((size + block - 1) // block) * block for size in files.values())
    directory_count = len(directories) + missing_destination_dirs
    estimated_allocation = file_allocation + directory_count * block
    required_inodes = len(files) + directory_count
    free_bytes = fs.f_bavail * block
    free_inodes = fs.f_favail if fs.f_files else None
    bytes_fit = estimated_allocation + reserve_bytes <= free_bytes
    inodes_fit = None if free_inodes is None else required_inodes + reserve_inodes <= free_inodes
    return {
        'schema': 'read-only-zip-space-preflight-v1',
        'archive': str(Path(archive).absolute()), 'destination': str(destination),
        'filesystem_checked_at': str(existing),
        'archive_bytes': Path(archive).stat().st_size,
        'zip_member_count': len(members), 'regular_file_count': len(files),
        'archive_directory_count_including_implicit': len(directories),
        'missing_destination_directory_count': missing_destination_dirs,
        'estimated_new_inodes': required_inodes,
        'expanded_file_bytes': expanded, 'compressed_member_bytes': compressed_bytes,
        'allocation_block_bytes': block,
        'rounded_file_allocation_bytes': file_allocation,
        'estimated_directory_allocation_bytes': directory_count * block,
        'estimated_total_allocation_bytes': estimated_allocation,
        'available_bytes': free_bytes, 'available_inodes': free_inodes,
        'reserved_bytes': reserve_bytes, 'reserved_inodes': reserve_inodes,
        'bytes_fit_estimate': bytes_fit, 'inodes_fit': inodes_fit,
        'capacity_status': 'insufficient' if not bytes_fit or inodes_fit is False else
                           ('unknown_inode_limit' if inodes_fit is None else 'estimated_fit'),
        'nested_archives_not_expanded': nested,
        'limits': [
            'Estimates a fresh extraction; existing destination contents are not subtracted.',
            'Directory storage is estimated at one block each; filesystem metadata, journals, temporary copies and runtime expansion can require more.',
            'Nested archives are listed but never opened; their extraction needs extra bytes and inodes.',
            'Capacity is a snapshot and may change. An estimated fit is not a reservation or extraction guarantee.',
            'Only ZIP metadata is read; CRC, payload authenticity and actual write permission are not verified.'
        ]
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--reserve-bytes', type=int, default=0)
    parser.add_argument('--reserve-inodes', type=int, default=0)
    args = parser.parse_args(argv)
    if args.reserve_bytes < 0 or args.reserve_inodes < 0:
        parser.error('reserves must be nonnegative')
    try:
        result = inspect_zip(args.archive, args.destination, reserve_bytes=args.reserve_bytes,
                             reserve_inodes=args.reserve_inodes)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(2, f'space_preflight: {exc}\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result['capacity_status'] == 'insufficient' else 0


if __name__ == '__main__':
    raise SystemExit(main())
