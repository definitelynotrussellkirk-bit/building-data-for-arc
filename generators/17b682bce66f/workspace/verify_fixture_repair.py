"""Verify a proposed shared-test fix ONLY in an isolated scratch copy.

The assigned generator and shared repository files are never edited. Evidence
retains both the failing pristine test and the proposed fixed test. This is a
maintainer proposal, not part of the generator repair.
"""
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    packet = Path.cwd()
    repo = packet / 'repo'
    target = repo / 'tests/test_review_solve.py'
    baseline = target.read_text()
    replacement = ('def packet(library, tmp_path):\n'
                   '    # A subprocess packet must include its own importable package.\n'
                   '    from pathlib import Path\n'
                   '    import shutil\n'
                   '    source = Path(__file__).resolve().parents[1]\n'
                   '    shutil.copytree(source / "src", library / "src",\n'
                   '                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))\n')
    patched = baseline.replace('def packet(library, tmp_path):\n', replacement, 1)
    assert patched != baseline
    report = {'schema':'isolated-fixture-repair-v1',
              'original_test_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
              'shared_source_changed':False, 'runs':[]}
    with tempfile.TemporaryDirectory(prefix='fixture-import-repro-') as temp:
        root=Path(temp)
        shutil.copytree(repo/'src',root/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (root/'tests').mkdir()
        shutil.copy2(repo/'tests/conftest.py',root/'tests/conftest.py')
        test=root/'tests/test_review_solve.py'
        test.write_text(baseline)
        env=dict(os.environ, PYTHONPATH=str(root/'src'))
        for phase,text,args in [
            ('pristine',baseline,['tests/test_review_solve.py::test_duties_solve_preparation_runs_from_packet_root']),
            ('proposed_fix',patched,['tests/test_review_solve.py'])]:
            test.write_text(text)
            argv=[sys.executable,'-m','pytest','-q',*args]
            result=subprocess.run(argv,cwd=root,env=env,capture_output=True,text=True,timeout=60)
            report['runs'].append({'phase':phase,'argv':argv,'cwd':str(root),
                                   'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    assert target.read_text() == baseline
    report['proposal_diff']=''.join(difflib.unified_diff(baseline.splitlines(True),patched.splitlines(True),
                              fromfile='a/tests/test_review_solve.py',tofile='b/tests/test_review_solve.py'))
    out=packet/'checks/fixture_import_repair.json'
    with out.open('x') as f: json.dump(report,f,indent=2);f.write('\n')
    print(out)
    return int(report['runs'][0]['exit_code'] != 1 or report['runs'][1]['exit_code'] != 0)


if __name__=='__main__':
    raise SystemExit(main())
