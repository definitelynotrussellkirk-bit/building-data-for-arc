"""Linux read/execute confinement for a trusted relocated verification harness.

Not a sandbox for untrusted code. Allow only the new cold tree and system
runtime roots, so a successful probe cannot import an owner/predecessor tree.
"""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import sys


def main(args):
    if len(args) < 4 or sys.platform != 'linux':
        raise ValueError('Need COLD_ROOT OWNER_READ_PROBE ABSOLUTE_EXECUTABLE [ARGS...] on Linux')
    root, probe = (Path(p).resolve() for p in args[:2])
    if not root.is_dir() or probe.is_relative_to(root) or not Path(args[2]).is_absolute():
        raise ValueError('The owner read probe must be outside the cold tree')
    libc = ctypes.CDLL(None, use_errno=True);libc.syscall.restype = ctypes.c_long
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 2:raise OSError(ctypes.get_errno(), 'Landlock ABI>=2 is required; isolation not verified')
    class Ruleset(ctypes.Structure):
        _fields_ = [('handled_access_fs', ctypes.c_uint64)]
    class PathRule(ctypes.Structure):
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int)]
    mask = (1 << 0) | (1 << 2) | (1 << 3) | (1 << 13)
    attr = Ruleset(mask);ruleset = libc.syscall(444, ctypes.byref(attr), ctypes.sizeof(attr), 0)
    if ruleset < 0:raise OSError(ctypes.get_errno(), 'Landlock create_ruleset')
    for path in [root, *map(Path, ['/usr', '/lib', '/lib64', '/bin', '/sbin', '/etc', '/proc', '/sys', '/dev'])]:
        if not path.exists():continue
        fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
        rule = PathRule(mask, fd);result = libc.syscall(445, ruleset, 1, ctypes.byref(rule), 0);os.close(fd)
        if result:raise OSError(ctypes.get_errno(), 'Landlock add_rule: ' + str(path))
    if libc.prctl(38, 1, 0, 0, 0):raise OSError(ctypes.get_errno(), 'Landlock no_new_privs')
    if libc.syscall(446, ruleset, 0):raise OSError(ctypes.get_errno(), 'Landlock restrict_self')
    os.close(ruleset)
    try:probe.read_bytes()
    except PermissionError:print('owner_read_denied; Landlock ABI', abi, flush=True)
    else:raise RuntimeError('Owner file was readable; isolation not verified')
    os.execv(args[2], args[2:])


if __name__ == '__main__':
    main(sys.argv[1:])
