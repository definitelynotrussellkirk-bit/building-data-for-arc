import importlib.util
from pathlib import Path
import unittest
HOME=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('test_public_waypoint',HOME/'workspace/parametric/family.py')
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
class FamilyTests(unittest.TestCase):
    def test_default_exact(self):self.assertEqual(f.program(),(HOME/'reference.rkt').read_text())
    def test_thirty_seeds(self):
        for seed in range(30):
            gs=f.inputs(seed);self.assertEqual(len({repr(g) for g in gs}),10)
            self.assertTrue(any(len(g)==len(g[0])==30 for g in gs[6:]))
            for mode in f.SETTINGS:
                for name in f.RIVALS:
                    self.assertTrue(any(f.render(f.analyze(g),mode)!=f.render(f.analyze(g),mode,name) for g in gs[:2]),(seed,mode,name))
            self.assertTrue(all(f.render(f.analyze(g),f.SETTINGS[0])!=f.render(f.analyze(g),f.SETTINGS[1]) for g in gs))
    def test_input_grammar(self):
        motifs=set();heads=set();ends=set();colors=set();stress_slots=set()
        for seed in range(30):
            for i,g in enumerate(f.inputs(seed)):
                a=f.analyze(g);motifs.add(len(a['cells']));heads.add(a['heading']);ends.add(a['directions'][-1]);colors.add(a['bg']);self.assertLessEqual(max(len(g),len(g[0])),30)
                if i>=6 and len(g)==30:stress_slots.add(i-6)
        self.assertEqual(motifs,{3,4,6});self.assertEqual(len(heads),4);self.assertEqual(len(ends),4);self.assertEqual(len(colors),10);self.assertEqual(len(stress_slots),4)
    def test_controls(self):
        for args in ((True,None,2,4),(0,None,1,4),(0,None,2,5),(0,{'orientation':'bad'},2,4)):
            with self.assertRaises(ValueError):f.generate(*args)
