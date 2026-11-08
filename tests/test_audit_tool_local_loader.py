"""Audit tools load their shipped sibling without another tree or error masking."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=['packet', 'staged'])
def relocated(tmp_path, request):
    root = tmp_path/request.param
    folder = root/('shared/tools' if request.param == 'packet' else 'scripts')
    folder.mkdir(parents=True)
    for name in ['generator_defect_lint.py','rule_smoke.py','generator_module_loader.py']:
        shutil.copy2(ROOT/'shared/tools'/name,folder/name)
    runtime = root/'runtime'
    shutil.copytree(ROOT/'shared/runtime/puzzle_generators',runtime/'puzzle_generators',
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    return root,folder,runtime,request.param


def invoke(args, root, runtime, foreign=None):
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(str(p) for p in [runtime, *([foreign] if foreign else []), root])
    return subprocess.run([sys.executable,*args],cwd=root,text=True,capture_output=True,env=env,timeout=10)


@pytest.mark.parametrize('tool',['generator_defect_lint','rule_smoke'])
def test_relocated_cli_help_starts_in_both_layouts(relocated,tool):
    root,folder,runtime,_ = relocated
    result = invoke([str(folder/(tool+'.py')),'--help'],root,runtime)
    assert result.returncode == 0,result.stderr
    assert '--help' in result.stdout


def foreign_loader(root):
    foreign=root/'foreign';(foreign/'scripts').mkdir(parents=True)
    (foreign/'scripts/__init__.py').write_text('')
    for p in [foreign/'scripts/generator_module_loader.py',foreign/'generator_module_loader.py']:
        p.write_text('raise RuntimeError("BORROWED FOREIGN LOADER")\n')
    return foreign


@pytest.mark.parametrize('tool',['generator_defect_lint','rule_smoke'])
def test_exact_sibling_loader_handles_dataclasses_even_with_foreign_namespace(relocated,tool):
    root,folder,runtime,layout = relocated
    foreign = foreign_loader(root)
    candidate = root/'candidate.py'
    candidate.write_text('from dataclasses import dataclass\n@dataclass\nclass Example:\n    value: int\n')
    if layout == 'staged':
        # Import the real staged namespace even with a foreign cached loader.
        setup = (f'import sys,types; sys.path.insert(0,{str(root)!r}); '
                 'fake=types.ModuleType("scripts.generator_module_loader"); '
                 'fake.load_module_from_path=lambda *a: (_ for _ in ()).throw(RuntimeError("CACHED FOREIGN LOADER")); '
                 'sys.modules["scripts.generator_module_loader"]=fake; '
                 f'import scripts.{tool} as tool; fn=tool.load_module_from_path; ')
        (folder/'__init__.py').write_text('')
    else:
        setup=f'import runpy; fn=runpy.run_path({str(folder/(tool+".py"))!r})["load_module_from_path"]; '
    code=setup+f'm=fn("local_candidate",{str(candidate)!r}); assert m.Example(7).value==7; print(m.__file__)'
    result=invoke(['-c',code],root,runtime,foreign)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()==str(candidate)


@pytest.mark.parametrize('tool',['generator_defect_lint','rule_smoke'])
@pytest.mark.parametrize('failure',['missing_file','transitive_dependency'])
def test_broken_local_loader_fails_without_falling_back(relocated,tool,failure):
    root,folder,runtime,_=relocated
    foreign=foreign_loader(root)
    local=folder/'generator_module_loader.py'
    if failure=='missing_file':local.unlink()
    else:local.write_text('import missing_audit_loader_dependency_54\n')
    result=invoke([str(folder/(tool+'.py')),'--help'],root,runtime,foreign)
    assert result.returncode!=0
    assert 'BORROWED FOREIGN LOADER' not in result.stderr
    assert ('generator_module_loader.py' if failure=='missing_file' else 'missing_audit_loader_dependency_54') in result.stderr


@pytest.mark.parametrize('unstable',[False,True])
def test_hashseed_subprocess_uses_same_local_loader_and_keeps_detector(relocated,unstable):
    root,folder,runtime,_=relocated
    foreign=foreign_loader(root)
    candidate=root/'hash_candidate.py'
    candidate.write_text('import os\ndef generate(*args, **kwargs):\n    return [[' +
                         ('int(os.environ["PYTHONHASHSEED"])' if unstable else '7') + ']]\n')
    code=(f'import runpy,json; tool=runpy.run_path({str(folder/"generator_defect_lint.py")!r}); '
          f'print(json.dumps(tool["probe_hashseed"]({str(candidate)!r})))')
    result=invoke(['-c',code],root,runtime,foreign)
    assert result.returncode==0,result.stderr
    findings=json.loads(result.stdout)
    assert not any('subprocess' in s or 'failed' in s for s in findings),findings
    assert bool(findings) is unstable,findings
