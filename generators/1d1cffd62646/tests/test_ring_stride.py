"""Behavioral checks for the separate proposed ring-stride family."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import tempfile
import unittest
from unittest.mock import patch

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = Path(__file__).resolve().parents[1]


def marked_grid():
    grid = [[0] * 17 for _ in range(13)]
    for r, c in [(4, 6), (6, 8), (8, 10)]:
        grid[r][c] = 3
    return grid


class RingStrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = TASK / "workspace/parametric/prototype.py"
        assert path.exists(), "The runnable ring-stride prototype has not been implemented"
        spec = importlib.util.spec_from_file_location("ring_stride_test", path)
        cls.proto = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.proto)
        from arc_repl.racket_bridge import RacketBridge
        cls.bridge = RacketBridge(timeout=10)
        cls.bridge.__enter__()
        cls.addClassCleanup(cls.bridge.__exit__, None, None, None)

    def test_stride_changes_outer_rings_and_preserves_markers(self):
        proto, bridge = self.proto, self.bridge
        grid = marked_grid()
        one = proto.transform(grid, ring_stride=1)
        two = proto.transform(grid, ring_stride=2)
        assert one[6][12] == 3 and two[6][12] == 0
        assert one[6][14] == two[6][14] == 3
        assert all(two[r][c] == 3 for r, c in [(4, 6), (6, 8), (8, 10)])
        assert grid == marked_grid()
        for setting, expected in [(1, one), (2, two)]:
            assert proto.racket_label(bridge, proto.materialize_program(setting), grid) == expected


    def test_default_is_exact_canonical_source_and_matches_all_original_pairs(self):
        proto, bridge = self.proto, self.bridge
        with canonical_path(find_root(__file__)).open() as handle:
            rows = [json.loads(line) for line in handle]
        row = next(r for r in rows if r.get("task_id") == proto.TASK_ID and r.get("source") == "training")
        assert proto.materialize_program(1) == row["program_solution"]
        for pair in row["train"] + row["test"]:
            assert proto.transform(pair["input"], ring_stride=1) == pair["output"]
            assert proto.racket_label(bridge, proto.materialize_program(1), pair["input"]) == pair["output"]


    def test_parameter_rejects_values_outside_exact_integer_contract(self):
        for bad in [0, 3, True, 1.0, "1", None]:
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                self.proto.materialize_program(bad)


    def test_count_and_seed_boundaries_fail_before_sampling(self):
        for kwargs in [{"n_demo": 1}, {"n_demo": 9}, {"n_demo": True}, {"n_demo": 2.0},
                       {"n_query": 0}, {"n_query": 9}, {"n_query": "4"}, {"seed": -1}]:
            request = {"seed": 17, "n_demo": 2, "n_query": 4}
            request.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.proto.generate_episode(**request)


    def test_matched_inputs_independent_counts_and_demo_only_certificates(self):
        proto, bridge = self.proto, self.bridge
        episodes = [proto.generate_episode(17, ring_stride=s, n_demo=2, n_query=4, bridge=bridge)
                    for s in (1, 2)]
        inputs = [[pair["input"] for role in ("train", "test") for pair in e[role]] for e in episodes]
        assert inputs[0] == inputs[1]
        assert len({json.dumps(g) for g in inputs[0]}) == 6
        assert (30, 30) in [(len(p["input"]), len(p["input"][0])) for p in episodes[0]["test"]]
        assert episodes[0]["train"][0]["output"] != episodes[1]["train"][0]["output"]
        for stride, episode in zip((1, 2), episodes):
            certificate = proto.lesson_certificate(episode)
            assert certificate["identifiable"] is True
            assert certificate["survivors"] == [f"stride-{stride}"]
            changed = copy.deepcopy(episode)
            changed["parameters"] = {"ring_stride": 99}
            for pair in changed["test"]:
                pair["output"] = [[9]]
            assert proto.lesson_certificate(changed) == certificate
            assert proto.verify_episode(episode, bridge=bridge)["pairs"] == 6
        eight = proto.generate_episode(4, n_demo=8, n_query=1, bridge=bridge)
        assert len(eight["train"]) == 8 and len(eight["test"]) == 1


    def test_underidentified_lesson_has_a_concrete_disagreeing_query(self):
        proto = self.proto
        tiny = [[0] * 5 for _ in range(5)]
        for r, c in [(0, 0), (2, 2), (4, 4)]:
            tiny[r][c] = 3
        lesson = {"train": [{"input": tiny, "output": proto.transform(tiny, ring_stride=1)}],
                  "test": [{"input": marked_grid()}]}
        certificate = proto.lesson_certificate(lesson)
        assert {"stride-1", "stride-2"} <= set(certificate["survivors"])
        assert certificate["identifiable"] is False


    def test_writer_uses_exact_public_bytes_and_rejects_duplicates_and_tampering(self):
        proto, bridge = self.proto, self.bridge
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        tmp_path = Path(temp.name)
        episode = proto.generate_episode(23, bridge=bridge)
        output = tmp_path / "first"
        proto.write_batch([episode], output)
        assert proto.verify_batch(output, bridge=bridge)["racket_parameter_replays"] == 12
        public = list((output / "public").glob("*.json"))
        assert len(public) == 1
        payload = public[0].read_bytes()
        assert payload == public_challenge_bytes(episode)
        assert public[0].stem == hashlib.sha256(payload).hexdigest()
        visible = json.loads(payload)
        assert set(visible) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in visible["test"])
        changed = copy.deepcopy(episode)
        changed["seed"] += 1
        changed["private_note"] = "This must never change the public filename or bytes"
        proto.write_batch([changed], tmp_path / "second")
        assert (tmp_path / "second/public" / public[0].name).read_bytes() == payload
        with self.assertRaisesRegex(ValueError, "duplicate"):
            proto.write_batch([episode, changed], tmp_path / "duplicates")
        assert not (tmp_path / "duplicates").exists()
        with self.assertRaises((ValueError, FileExistsError)):
            proto.write_batch([episode], output)
        tampered = copy.deepcopy(episode)
        tampered["test"][0]["output"][0][0] = 9
        with self.assertRaises(ValueError):
            proto.verify_episode(tampered, bridge=bridge)
        tampered = copy.deepcopy(episode)
        tampered["train"][0]["input"][0][0] = False
        with self.assertRaises(ValueError):
            proto.write_batch([tampered], tmp_path / "boolean")


    def test_sampler_exhaustion_returns_no_partial_episode(self):
        with patch.object(self.proto, "_draw_input", side_effect=lambda *a, **k: marked_grid()):
            with self.assertRaisesRegex(RuntimeError, "exhaust"):
                self.proto.sample_inputs(7, n_demo=2, n_query=4)

    def test_unserializable_private_metadata_does_not_create_a_destination(self):
        episode = self.proto.generate_episode(29, bridge=self.bridge)
        episode["private_note"] = Path("author-note.txt")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "must-not-exist"
            with self.assertRaises((TypeError, ValueError)):
                self.proto.write_batch([episode], output)
            assert not output.exists(), "Serialization failure left a partially written batch"

    def test_adapter_has_exact_contract_and_reuses_identifiable_matched_inputs(self):
        path = TASK / "workspace/parametric/adapter.py"
        assert path.exists(), "The promotion adapter has not been implemented"
        spec = importlib.util.spec_from_file_location("ring_stride_adapter_test", path)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        episodes = []
        for stride in (1, 2):
            settings = {"ring_stride": stride}
            episode = adapter.generate(41, settings, 2, 4)
            assert episode["program_solution"] == adapter.program(settings)
            assert episode["program_solution"] == self.proto.materialize_program(stride)
            assert self.proto.lesson_certificate(episode)["survivors"] == [f"stride-{stride}"]
            for pair in episode["train"] + episode["test"]:
                assert self.proto.racket_label(self.bridge, adapter.program(settings), pair["input"]) == pair["output"]
            episodes.append(episode)
        assert [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] == [
            p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]
        for settings in ({}, {"ring_stride": 1, "extra": 4}, {"ring_stride": True}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                adapter.program(settings)
        contract = json.loads((path.parent / "promotion.json").read_text())
        assert contract["parameters"] == {"ring_stride": [1, 2]}
        assert contract["default"] == {"ring_stride": 1}
        assert contract["limits"] == {"demos": [2, 8], "queries": [1, 8]}

if __name__ == "__main__":
    unittest.main()
