#!/usr/bin/env python3
"""Write a portable generator canonical-pair regression starter, without shims."""
from pathlib import Path
import argparse
import re

TEMPLATE='''from pathlib import Path
import importlib.util
from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("reviewed_generator", Path(__file__).parents[1] / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_canonical_inputs_are_inside_generator_domain():
    assert canonical_path(ROOT).is_file()
    pairs = canonical_pairs({task_id!r}, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
'''


def write_test(task_id,destination):
    if not re.fullmatch(r'[0-9a-f]{12}',task_id):raise ValueError('expected exact12-digit task ID')
    path=Path(destination)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as handle:handle.write(TEMPLATE.format(task_id=task_id))
    return path


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task_id');parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();print(write_test(args.task_id,args.out))
