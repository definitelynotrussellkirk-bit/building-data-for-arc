import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
RULE='(rule! (for/list (x (range 0 2)) (list x)))'
EXPECTED='(lambda (g) (let* ((h (rows g)) (w (cols g))) (for/list ([x (in-list (range 0 2))]) (list x))))'


@pytest.mark.parametrize('layout',['source','staged'])
@pytest.mark.parametrize('foreign_legacy_module',[False,True])
def test_rule_wrapper_uses_only_current_layout_parser(tmp_path,layout,foreign_legacy_module):
    base=tmp_path/'independent'
    runtime=base/'shared/runtime' if layout=='source' else base/'runtime'
    parser=base/'shared/tools/comment_solutions.py' if layout=='source' else runtime/'scripts/comment_solutions.py'
    wrapper=runtime/'puzzle_generators/rule_wrap.py';wrapper.parent.mkdir(parents=True)
    parser.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'shared/runtime/puzzle_generators/rule_wrap.py',wrapper)
    shutil.copy2(ROOT/'shared/tools/comment_solutions.py',parser)
    code=''
    if foreign_legacy_module:
        code+='import sys,types; fake=types.ModuleType("scripts.comment_solutions"); fake.Atom=object; fake.List_=object; fake.parse_racket=lambda _: []; sys.modules["scripts"]=types.ModuleType("scripts"); sys.modules["scripts.comment_solutions"]=fake; '
    code+='from puzzle_generators.rule_wrap import wrap_rule; import json; print(json.dumps(wrap_rule('+repr(RULE)+')))'
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','ARCPUZZLES_HOME'}}
    env.update(PYTHONPATH=str(runtime),PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,env=env,text=True,capture_output=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)==EXPECTED


def test_missing_same_checkout_parser_does_not_borrow_scripts_from_pythonpath(tmp_path):
    runtime=tmp_path/'source/shared/runtime';p=runtime/'puzzle_generators/rule_wrap.py';p.parent.mkdir(parents=True)
    shutil.copy2(ROOT/'shared/runtime/puzzle_generators/rule_wrap.py',p)
    env={**os.environ,'PYTHONPATH':str(runtime),'PYTHONNOUSERSITE':'1'}
    result=subprocess.run([sys.executable,'-c','from puzzle_generators.rule_wrap import wrap_rule; wrap_rule("(rule! g)")'],cwd=tmp_path,env=env,text=True,capture_output=True,timeout=15)
    assert result.returncode!=0 and 'parser missing from current' in result.stderr
