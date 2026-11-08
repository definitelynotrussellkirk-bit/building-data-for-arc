"""Small source-bound current-export replay; destination must be new."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

checks=Path(__file__).resolve().parent
work=checks.parents[1]
home=work/'repo/generators/3f26d45b9f51'
source=home/'workspace/parametric/occluded_rectangles.py'
spec=importlib.util.spec_from_file_location('occluded',source)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
parser=argparse.ArgumentParser(); parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
episodes=[m.generate_episode(seed=220,paint='outline',n_train=1,n_queries=4,max_attempts=32),
          m.generate_episode(seed=221,paint='filled',n_train=3,n_queries=4,max_attempts=32)]
manifest=m.export_batch(episodes,args.out)
verification=m.verify_export(args.out)
binary=work/'.review/racket-runtime/racket/bin/racket'
files=[source,source.with_suffix('.rkt'),home/'workspace/parametric/OCCLUDED_RECTANGLES.md',home/'tests/test_occluded_rectangles.py']
result={'status':'pass','episodes':2,'demonstrations':4,'queries':8,
        'verification':verification,'batch_manifest':str(args.out/'manifest.json'),
        'sources':{str(p.relative_to(work/'repo')):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'racket_runtime':{'binary':str(binary),'version':subprocess.check_output([str(binary),'--version'],text=True).strip(),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()},
        'unit_tests':{'tests':10,'failures':0,'errors':0,'log':'tdd-green-export-validation.log'},
        'commands':{'tests':'TMPDIR=../checks/occluded/tmp python -m unittest discover -s generators/3f26d45b9f51/tests -p test_occluded_rectangles.py -v',
                    'roundtrip':'TMPDIR=../checks/occluded/tmp python ../checks/occluded/verify_roundtrip.py --out ../checks/occluded/sample_batch_v2',
                    'verify':'TMPDIR=../checks/occluded/tmp python generators/3f26d45b9f51/workspace/parametric/occluded_rectangles.py --verify ../checks/occluded/sample_batch_v2'},
        'historical_evidence':{'result':'result-before-export-validation.json','export':'sample_batch','scope':'Earlier source only; old metadata/export schema is not claimed current.'},
        'project_suite':'Earlier attempt blocked: No module named pytest; no full-suite success claimed.'}
(checks/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
