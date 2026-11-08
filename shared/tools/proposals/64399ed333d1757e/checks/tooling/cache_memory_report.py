#!/usr/bin/env python3
"""Read-only Linux memory diagnostic; never overrides guards or allocates a packet.

The fixed 50% discount is an illustrative estimate, not promised reclaimability.
Run with Python 3.10+; stdout is JSON. No third-party dependencies or writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re


def text(path):
    try:
        return path.read_text()
    except OSError:
        return None


def integer(value):
    try:
        result = int(value)
        return result if result >= 0 else None
    except (TypeError, ValueError):
        return None


def pairs(path):
    content = text(path)
    result = {}
    for line in (content or '').splitlines():
        parts = line.split()
        if len(parts) == 2:
            value = integer(parts[1])
            if value is not None:
                result[parts[0]] = value
    return result if content is not None else None


def group_report(path):
    maximum_text = text(path / 'memory.max')
    maximum_text = maximum_text.strip() if maximum_text is not None else None
    maximum = integer(maximum_text)
    current = integer(text(path / 'memory.current'))
    stats = pairs(path / 'memory.stat') or {}
    ordinary = (max(0, stats['file'] - stats['shmem'])
                if 'file' in stats and 'shmem' in stats else None)
    slab = stats.get('slab_reclaimable')
    strict = max(0, maximum - current) if maximum is not None and current is not None else None
    potential = strict + ordinary // 2 + slab // 2 if None not in (strict, ordinary, slab) else None
    return {'path': str(path), 'limit_bytes': maximum,
            'limit_status': 'unlimited' if maximum_text == 'max' else 'finite' if maximum is not None else 'unknown',
            'current_bytes': current, 'strict_headroom_bytes': strict,
            'file_bytes': stats.get('file'), 'shmem_bytes': stats.get('shmem'),
            'ordinary_file_cache_bytes': ordinary, 'slab_reclaimable_bytes': slab,
            'discounted_potential_headroom_bytes': potential,
            'oom_counters': pairs(path / 'memory.events')}


def report(destination, *, cgroup_root=Path('/sys/fs/cgroup'), proc_root=Path('/proc')):
    cgroup_root, proc_root = Path(cgroup_root).resolve(), Path(proc_root)
    candidates = [cgroup_root]
    for line in (text(proc_root / 'self/cgroup') or '').splitlines():
        if line.startswith('0::'):
            relative = Path(line[3:].lstrip('/'))
            if '..' not in relative.parts:
                active = cgroup_root / relative
                if active.is_dir():
                    candidates = [active] + [p for p in active.parents
                                             if p == cgroup_root or cgroup_root in p.parents]
    groups = [group_report(p) for p in dict.fromkeys(candidates)]
    finite = [g for g in groups if g['limit_status'] == 'finite']
    unknown = any(g['limit_status'] == 'unknown' for g in groups)
    strict = (min(g['strict_headroom_bytes'] for g in finite)
              if finite and not unknown and all(g['strict_headroom_bytes'] is not None for g in finite) else None)
    potential = (min(g['discounted_potential_headroom_bytes'] for g in finite)
                 if finite and not unknown and all(g['discounted_potential_headroom_bytes'] is not None for g in finite) else None)
    host = None
    for line in (text(proc_root / 'meminfo') or '').splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0] == 'MemAvailable:' and parts[2] == 'kB':
            value = integer(parts[1])
            host = value * 1024 if value is not None else None
    if potential is not None and host is not None:
        potential = min(potential, host)
    destination = Path(destination).resolve()
    probe = destination
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    fs = {'requested_path': str(destination), 'probed_path': str(probe), 'filesystem': 'unknown'}
    try:
        values = os.statvfs(probe)
        fs.update(available_bytes=values.f_bavail * (values.f_frsize or values.f_bsize),
                  available_inodes=values.f_favail if values.f_files else None)
    except OSError as error:
        fs.update(available_bytes=None, available_inodes=None, error=str(error))
    matched = ''
    for line in (text(proc_root / 'self/mountinfo') or '').splitlines():
        try:
            left, right = line.split(' - ', 1)
            fields = left.split()
            point = Path(re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), fields[4]))
            if (probe == point or point in probe.parents) and len(str(point)) >= len(matched):
                matched = str(point)
                fs.update(filesystem=right.split()[0], mountpoint=matched)
        except (ValueError, IndexError):
            continue
    return {'schema': 'arc-cache-memory-diagnostic-v1',
            'created_at': datetime.now(timezone.utc).isoformat(), 'advisory_only': True,
            'strict_cgroup_headroom_bytes': strict, 'discounted_potential_headroom_bytes': potential,
            'host_mem_available_bytes': host, 'cache_discount_fraction': 0.5,
            'cgroups': groups, 'destination': fs,
            'limitations': 'Cache reclamation is not guaranteed. The 50% discount is illustrative; '
                           'concurrent use, quotas, runtime peaks and memory.high can still constrain work. '
                           'Unknown data stays unknown. OOM counters are cgroup-wide and do not identify a victim. '
                           'This diagnostic never overrides a resource guard or certifies extraction capacity.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=Path('/dev/shm'))
    parser.add_argument('--cgroup-root', type=Path, default=Path('/sys/fs/cgroup'))
    parser.add_argument('--proc-root', type=Path, default=Path('/proc'))
    args = parser.parse_args()
    print(json.dumps(report(args.destination, cgroup_root=args.cgroup_root, proc_root=args.proc_root),
                     indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
