#!/usr/bin/env python3
"""Static, non-mutating audit helper for ARC generator packages."""
from __future__ import annotations
import argparse,ast,hashlib,json,re,subprocess,sys
from pathlib import Path

def run(cmd,cwd,timeout=900):
    try:
        p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=timeout)
        return {'command':cmd,'exit_code':p.returncode,'stdout':p.stdout[-12000:],'stderr':p.stderr[-12000:]}
    except subprocess.TimeoutExpired as e:
        return {'command':cmd,'exit_code':124,'stdout':(e.stdout or '')[-12000:] if isinstance(e.stdout,str) else '',
                'stderr':(e.stderr or '')[-12000:] if isinstance(e.stderr,str) else 'timeout'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('task_id'); ap.add_argument('--repo',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); repo=a.repo.resolve(); base=repo/'generators'/a.task_id; out=a.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    src=base/'generator.py'; text=src.read_text(); tree=ast.parse(text)
    test_files=sorted((base/'tests').glob('test_*.py')) if (base/'tests').is_dir() else []
    test_text='\n'.join(p.read_text(errors='ignore') for p in test_files)
    broad=[]; random_calls=[]; globals_mutated=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.ExceptHandler) and n.type is None: broad.append(n.lineno)
        elif isinstance(n,ast.ExceptHandler) and isinstance(n.type,ast.Name) and n.type.id in {'Exception','BaseException'}: broad.append(n.lineno)
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='random': random_calls.append(n.lineno)
        elif isinstance(n,(ast.Global,ast.Nonlocal)): globals_mutated.append(n.lineno)
    checks={
      'has_tests':bool(test_files),
      'mentions_determinism':bool(re.search(r'determin|same.seed|reproduc',test_text,re.I)),
      'mentions_query_rotation':bool(re.search(r'rotate.query|query.rotation|query_index',test_text,re.I)),
      'mentions_rival_or_shortcut':bool(re.search(r'rival|shortcut|counterexample',test_text,re.I)),
      'mentions_difficulty_or_profile':bool(re.search(r'difficulty|profile|band',test_text,re.I)),
      'bare_or_broad_except_lines':broad,
      'module_random_calls_lines':random_calls,
      'global_or_nonlocal_lines':globals_mutated,
    }
    runs=[]
    runs.append(run([sys.executable,'-m','pytest','-q',str(base/'tests')],repo,900))
    for stage in ('lint','selfcheck','rule_smoke','defect_lint'):
        runs.append(run([sys.executable,'-m','arcpuzzles','check',a.task_id,'--stage',stage,'--timeout','600','--phase','audit','--out',str(out/stage)],repo,800))
    report={
      'task_id':a.task_id,'generator_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
      'generator_lines':len(text.splitlines()),'test_files':[str(p.relative_to(repo)) for p in test_files],
      'test_count_hint':len(re.findall(r'^def test_',test_text,re.M)),'static_checks':checks,'runs':runs,
    }
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'source.sha256').write_text(report['generator_sha256']+'  '+str(src.relative_to(repo))+'\n')
    return 0
if __name__=='__main__': raise SystemExit(main())
