"""Syntax classification and actual ambiguity policy; no task generator imports."""
import ast
import copy
import os
from pathlib import Path
import re
from typing import Any, Callable
import unittest

HERE=Path(__file__).resolve().parent
ORIGINAL=HERE.parents[1]/'repo/shared/tools/generator_semantic_gate.py'
PROPOSED=HERE/'generator_semantic_gate.proposed.py'
NAMES={'_rot90','SIMPLE_SHORTCUTS','_AUTHORITY_SHORTCUT_HEADS','_BARE_AUTHORITY_RE',
       '_EXACT_AUTHORITY_ALIASES','authoritative_simple_shortcut','check_canonical_ambiguity'}


def load(path):
    tree=ast.parse(path.read_text())
    nodes=[]
    for node in tree.body:
        name=getattr(node,'name',None)
        if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name): name=node.target.id
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name): name=node.targets[0].id
        if name in NAMES: nodes.append(node)
    namespace={'re':re,'copy':copy,'Any':Any,'Callable':Callable,'MAX_EXAMPLES':3,
               '_grids_equal':lambda a,b:a==b}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
    return namespace


class AuthorityTests(unittest.TestCase):
    def setUp(self): self.g=load(Path(os.environ.get('AUTHORITY_SOURCE',str(PROPOSED))))
    def classify(self,program):
        self.g['_canonical_program_cached']=lambda _:program
        return self.g['authoritative_simple_shortcut']('synthetic')

    def test_original_callable_ccw_is_unrecognized(self):
        old=load(ORIGINAL); old['_canonical_program_cached']=lambda _:'(rule! rotate-ccw)'
        self.assertIsNone(old['authoritative_simple_shortcut']('synthetic'))

    def test_exact_six_whitelisted_identifiers(self):
        for identifier,shortcut in self.g['_AUTHORITY_SHORTCUT_HEADS'].items():
            with self.subTest(identifier=identifier):
                self.assertEqual(self.classify('(rule! '+identifier+')'),shortcut)
        self.assertEqual(len(self.g['_AUTHORITY_SHORTCUT_HEADS']),6)

    def test_normalized_whitespace(self):
        self.assertEqual(self.classify(' \n (rule!\t rotate-ccw)  \n'),'rot270')

    def test_reject_compound_and_nonwhitelisted_programs(self):
        for program in ['(rule! identity)','(rule! custom-rotate-ccw)','(rule! (compose rotate-ccw flip-lr))',
                        '(begin (rule! rotate-ccw))','(rule! rotate-ccw) (display 1)',
                        '(rule! rotate-ccw extra)','(rule! rotate-ccw))','(rule! (lambda (x) rotate-ccw))']:
            with self.subTest(program=program): self.assertIsNone(self.classify(program))

    def test_existing_applied_and_lambda_forms_retained(self):
        for program in ['(rule! (rotate-ccw g))','(rule! (lambda (g) (rotate-ccw g)))']:
            self.assertEqual(self.classify(program),'rot270')

    def check(self,declared):
        self.classify('(rule! rotate-ccw)')
        grid=[[1,2,3],[4,5,6]]
        self.g['_canonical_pairs_cached']=lambda _:[{'input':grid,'output':[[3,6],[2,5],[1,4]]}]
        return self.g['check_canonical_ambiguity']('synthetic',declared_shortcuts=declared,
                                                 rival_claims={},witness_rivals={})

    def test_generic_ccw_authority_does_not_demand_impossible_witness(self):
        result=self.check({})
        self.assertIn('rot270',result['authority_equal'])
        self.assertNotIn({'source':'simple','shortcut':'rot270'},result['unsatisfied'])

    def test_declared_rival_remains_unsatisfied(self):
        result=self.check({'rot270':self.g['SIMPLE_SHORTCUTS']['rot270']})
        self.assertIn({'source':'declared','shortcut':'rot270'},result['unsatisfied'])
        self.assertEqual(result['declared_validation']['rot270']['status'],'fits_all_labeled_pairs')


if __name__=='__main__': unittest.main()
