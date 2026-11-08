"""Regenerate the standalone ordinary sampler; --check refuses source drift."""
from pathlib import Path
import argparse

HERE=Path(__file__).resolve().parent
FOOTER='''
RULE_TASK_ID = 'ee_d35bdbdc'
EXAMPLES_NEEDED = 2

def generate(seed=0,sample_index=0,difficulty='medium',**kwargs):
    if type(seed) is not int or not 0<=seed<2**63 or type(sample_index) is not int or sample_index<0:
        raise ValueError('nonnegative exact integer seed/index required')
    if difficulty not in ('easy','medium','hard','mixed'):
        raise ValueError('unknown difficulty')
    grid,meta=_scene(seed+sample_index//10,sample_index%10)
    return {'input':deepcopy(grid),'metadata':deepcopy(meta)}

def self_check(grid,**kwargs):
    try:
        parse(grid);predict(grid,'one_hop')
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
'''

def source():return (HERE/'engine.py').read_text()+FOOTER

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    target=HERE.parents[1]/'generator.py'
    if args.check:
        if target.read_text()!=source():raise SystemExit('ordinary generator drift')
    else:target.write_text(source())
if __name__=='__main__':main()
