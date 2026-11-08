"""Diagnostic only: compare the unchanged process runner with/without site startup.

This never alters shared runtime code, global Python startup, or test timeouts.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/arcpuzzles/runtime.py').is_file())
sys.path.insert(0, str(ROOT / 'src'))
from arcpuzzles.runtime import run_process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-timeout-diagnostic-') as directory:
        for skip_site in (False, True):
            for timeout in (0.2, 1.0):
                for trial in range(3):
                    chunks = []
                    begun = time.monotonic()
                    def capture(text):
                        chunks.append({'elapsed_seconds': time.monotonic() - begun, 'text': text})
                    argv = [sys.executable] + (['-S'] if skip_site else []) + [
                        '-c', "import time; print('RUN unfinished',flush=True); time.sleep(30)"]
                    result = run_process(argv, Path(directory), timeout=timeout, on_output=capture)
                    rows.append({'skip_site': skip_site, 'timeout': timeout, 'trial': trial,
                                 'elapsed_seconds': time.monotonic() - begun,
                                 'chunks': chunks, **result})
    args.out.write_text(json.dumps({'diagnostic_only': True, 'rows': rows}, indent=2) + '\n')
    print(json.dumps([{'skip_site': r['skip_site'], 'timeout': r['timeout'],
                      'stdout_retained': bool(r['stdout']), 'chunks': r['chunks']} for r in rows], indent=2))
    # A diagnostic successfully records failures; it is not a semantic pass.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
