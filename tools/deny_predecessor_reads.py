#!/usr/bin/env python3
"""Run a relocated check with reads outside system/temp roots denied.

Usage: python scripts/deny_predecessor_reads.py /absolute/python -m pytest -q
Requires Linux Landlock ABI>=2. This is a verification harness, not an episode
sandbox. REFER is explicitly permitted within allowed roots so the wrapper does
not accidentally disable ordinary rename/quarantine behavior under test.
"""
import ctypes
import os
from pathlib import Path
import sys

libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
abi = libc.syscall(444, 0, 0, 1)
if abi < 2:
    raise OSError(ctypes.get_errno(), 'Landlock unavailable')
class Ruleset(ctypes.Structure):
    _fields_ = [('handled_access_fs', ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int)]
mask = (1 << 2) | (1 << 3) | (1 << 13)
# Landlock always mediates cross-directory REFER. Permit ordinary renames within
# allowed roots while retaining the same denial of reads outside these roots.
attr = Ruleset(mask)
ruleset = libc.syscall(444, ctypes.byref(attr), ctypes.sizeof(attr), 0)
if ruleset < 0:
    raise OSError(ctypes.get_errno(), 'create_ruleset')
for name in ['/usr', '/lib', '/lib64', '/bin', '/sbin', '/etc', '/proc', '/sys', '/dev', '/tmp', '/var']:
    if not Path(name).exists():
        continue
    fd = os.open(name, os.O_PATH | os.O_CLOEXEC)
    rule = PathRule(mask, fd)
    result = libc.syscall(445, ruleset, 1, ctypes.byref(rule), 0)
    os.close(fd)
    if result:
        raise OSError(ctypes.get_errno(), 'add_rule: ' + name)
if libc.prctl(38, 1, 0, 0, 0):
    raise OSError(ctypes.get_errno(), 'no_new_privs')
if libc.syscall(446, ruleset, 0):
    raise OSError(ctypes.get_errno(), 'restrict_self')
os.close(ruleset)
try:
    list(Path('/home').iterdir())
except PermissionError:
    print('Landlock ABI', abi, ': predecessor reads denied', flush=True)
else:
    raise AssertionError('/home is still readable')
if len(sys.argv) < 2:
    raise SystemExit("Provide the absolute executable followed by its arguments")
os.execv(sys.argv[1], sys.argv[1:])
