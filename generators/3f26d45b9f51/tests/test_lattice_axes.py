"""Focused tests of the proposed axes extension; canonical production is unchanged."""
from pathlib import Path
import copy
import hashlib
import importlib
import json
import sys
import tempfile
import unittest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace/parametric"))


class LatticeAxesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = importlib.import_module("lattice_axes")
        cls.racket = cls.m.RacketLabels()
        cls.episodes = [cls.m.make_episode(17, axes=mode, n_demo=2, n_query=4,
                        K=7, n_colors=3, racket=cls.racket) for mode in cls.m.MODES]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "racket"):
            cls.racket.close()

    def test_original_program_is_exact_and_all_canonical_pairs_execute(self):
        m = self.m
        self.assertEqual(m.program_for("both"), m.canonical_program())
        pairs = m.canonical_pairs(m.TASK_ID, root=m.ROOT)
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            self.assertEqual(self.racket.apply(m.program_for("both"), pair["input"]), pair["output"])

    def test_all_settings_have_distinct_queries_and_demo_only_certificates(self):
        for mode, ep in zip(self.m.MODES, self.episodes):
            self.assertEqual(ep["parameters"], {"axes": mode})
            self.assertEqual((len(ep["train"]), len(ep["test"])), (2, 4))
            inputs = [json.dumps(p["input"]) for p in ep["train"] + ep["test"]]
            self.assertEqual(len(set(inputs)), 6)
            cert = self.m.lesson_certificate(ep["train"], [p["input"] for p in ep["test"]])
            self.assertIn("axes:" + mode, cert["surviving_hypotheses"])
            self.assertEqual(cert, ep["certificate"])
            self.assertTrue(all(row["identifiable"] for row in cert["queries"]))
            for pair in ep["train"] + ep["test"]:
                self.assertEqual(pair["output"], self.m.solve_python(pair["input"], mode))
        outputs = [json.dumps(ep["test"][0]["output"]) for ep in self.episodes]
        self.assertEqual(len(set(outputs)), 3)
        self.assertEqual(self.episodes[0]["test"][0]["input"], self.episodes[1]["test"][0]["input"])

    def test_demo_and_query_counts_are_independent(self):
        ep = self.m.make_episode(23, axes="rows", n_demo=4, n_query=1,
                                 K=9, n_colors=2, racket=self.racket)
        self.assertEqual((len(ep["train"]), len(ep["test"])), (4, 1))
        self.assertTrue(all(row["identifiable"] for row in ep["certificate"]["queries"]))

    def test_invalid_counts_numeric_types_and_parameters_fail_before_sampling(self):
        for field in ("n_demo", "n_query"):
            for value in (True, False, 0, -1, "3", 2.5, 65):
                with self.subTest(field=field, value=value):
                    with self.assertRaises((ValueError, TypeError)):
                        self.m.make_episode(0, racket=self.racket, **{field:value})
        for kwargs in ({"axes":"diagonal"}, {"axes":[]}, {"K":True},
                       {"K":7.0}, {"K":10}, {"n_colors":"3"},
                       {"max_attempts":0}, {"max_attempts":True}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((ValueError, TypeError)):
                    self.m.make_episode(0, racket=self.racket, **kwargs)

    def test_distinct_sampler_exhausts_exact_budget(self):
        calls=[]
        def repeated(i):
            calls.append(i)
            return [[0]]
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.m.distinct_inputs(repeated, count=2, max_attempts=3)
        self.assertEqual(calls, [0,1,2])
        with self.assertRaises((ValueError, TypeError)):
            self.m.distinct_inputs(lambda i:[[True]], count=1, max_attempts=1)

    def test_one_demo_rejected_with_teaching_support_limit(self):
        with self.assertRaisesRegex(ValueError, "n_demo"):
            self.m.make_episode(23, axes="rows", n_demo=1, n_query=4, racket=self.racket)

    def test_boolean_hidden_label_is_rejected(self):
        ep=copy.deepcopy(self.episodes[0])
        output=ep["test"][0]["output"]
        changed=False
        for row in output:
            for j, value in enumerate(row):
                if value in (0,1):
                    row[j]=bool(value)
                    changed=True
                    break
            if changed:
                break
        self.assertTrue(changed)
        with self.assertRaisesRegex(ValueError, "integer"):
            self.m.verify_episode(ep,racket=self.racket)

    def test_duplicate_visible_payload_with_different_metadata_is_rejected_cleanly(self):
        ep=copy.deepcopy(self.episodes[0])
        ep["seed"]+=1
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"duplicate"):
                self.m.write_batch([self.episodes[0],ep],Path(tmp)/"bad",racket=self.racket)

    def test_public_ids_ignore_private_metadata_but_writer_rejects_wrong_labels(self):
        ep=copy.deepcopy(self.episodes[0])
        before=self.m.public_challenge_id(ep)
        ep["seed"]=9999
        ep["parameters"]={"axes":"columns"}
        ep["program"]="private unrelated text"
        ep["test"][0]["output"][0][0]=(ep["test"][0]["output"][0][0]+1)%10
        self.assertEqual(before,self.m.public_challenge_id(ep))
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"bad"
            with self.assertRaises((ValueError,TypeError)):
                self.m.write_batch([ep],out,racket=self.racket)
            self.assertFalse(out.exists())

    def test_episode_provenance_and_exact_metadata_types_are_verified(self):
        for field,value in (("schema","unknown"),("status","approved"),
                            ("seed",True),("seed",-1),
                            ("origin",{"task_id":"other"}),
                            ("parameters",{"axes":"both","unreviewed":1})):
            with self.subTest(field=field,value=value):
                ep=copy.deepcopy(self.episodes[0]); ep[field]=value
                with self.assertRaises(ValueError):
                    self.m.verify_episode(ep,racket=self.racket)

    def test_certificate_boolean_integer_substitutions_are_rejected(self):
        for field,value in (("query_index",False),("identifiable",1)):
            with self.subTest(field=field):
                ep=copy.deepcopy(self.episodes[0])
                ep["certificate"]["queries"][0][field]=value
                with self.assertRaisesRegex(ValueError,"certificate"):
                    self.m.verify_episode(ep,racket=self.racket)

    def test_manifest_claims_and_exact_count_types_are_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"good"
            original=self.m.write_batch([self.episodes[0]],root,racket=self.racket)
            for field,value in (("schema","unknown"),("status","approved"),
                                ("episodes",True),("query_count",999),
                                ("query_count",True),("labels_per_setting",[999]),
                                ("labels_per_setting",[6.0])):
                with self.subTest(field=field,value=value):
                    modified=copy.deepcopy(original); modified[field]=value
                    (root/"private/manifest.json").write_text(json.dumps(modified))
                    with self.assertRaises(ValueError):
                        self.m.verify_export(root,racket=self.racket)

    def test_export_roundtrip_order_tamper_and_duplicate_rejection(self):
        m=self.m
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"good"
            report=m.write_batch(list(reversed(self.episodes)),root,racket=self.racket)
            self.assertEqual(report["public_ids"],sorted(report["public_ids"]))
            self.assertEqual(m.verify_export(root,racket=self.racket)["episodes"],3)
            for ep in self.episodes:
                pid=m.public_challenge_id(ep)
                self.assertEqual((root/"public"/(pid+".json")).read_bytes(),m.public_challenge_bytes(ep))
                public=json.loads((root/"public"/(pid+".json")).read_text())
                self.assertEqual(set(public),{"train","test"})
                self.assertTrue(all(set(p)=={"input"} for p in public["test"]))
            duplicate=Path(tmp)/"duplicate"
            with self.assertRaisesRegex(ValueError,"duplicate"):
                m.write_batch([self.episodes[0],self.episodes[0]],duplicate,racket=self.racket)
            self.assertFalse(duplicate.exists())
            file=next((root/"public").glob("*.json"))
            file.write_bytes(file.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"public"):
                m.verify_export(root,racket=self.racket)


if __name__ == "__main__":
    unittest.main(verbosity=2)
