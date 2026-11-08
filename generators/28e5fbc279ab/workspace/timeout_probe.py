"""Diagnose the unchanged shared timeout test without patching shared code."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from arcpuzzles.runtime import run_process
import arcpuzzles.runtime as runtime_module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    rows = []
    for startup_flags in ([], ['-S']):
        for budget in (0.2, 1.0):
            start = time.monotonic()
            arrivals = []
            command = [sys.executable, *startup_flags, '-c',
                       "import time; print('RUN unfinished',flush=True); time.sleep(30)"]
            result = run_process(command, Path.cwd(), timeout=budget,
                                 on_output=lambda s: arrivals.append({'after_seconds': time.monotonic()-start, 'chunk': s}))
            rows.append({'startup_flags': startup_flags, 'timeout_seconds': budget,
                         'elapsed_seconds': time.monotonic()-start, 'arrivals': arrivals,
                         'result': result})
    report = {'schema': 'shared-timeout-diagnostic-v1',
              'runtime_sha256': hashlib.sha256(Path(runtime_module.__file__).read_bytes()).hexdigest(),
              'python': sys.version, 'executable': sys.executable,
              'command': {'cwd': str(Path.cwd()), 'argv': [sys.executable, *sys.argv]},
              'cases': rows, 'shared_code_changed': False}
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
