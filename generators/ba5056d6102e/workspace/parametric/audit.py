"""Run from the repository via review.py run python3 <this file> --out PATH."""
import argparse
import importlib.util
import json
from pathlib import Path
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seeds',type=int,default=20)
    parser.add_argument('--no-racket',action='store_true')
    args=parser.parse_args()
    if args.seeds<1: parser.error('--seeds must be positive')
    spec=importlib.util.spec_from_file_location('recovery_audit_adapter',Path(__file__).with_name('adapter.py'))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    print(json.dumps(m.audit(args.out,args.seeds,not args.no_racket),sort_keys=True,indent=2))
