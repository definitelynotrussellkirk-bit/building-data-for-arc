"""Export names depend only on visible challenge content."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys
import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'workspace/parametric/prototype.py'
@pytest.fixture(scope='module')
def proto():
    spec = importlib.util.spec_from_file_location('count_scope_public_names', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_name_ignores_private_setting_seed_and_query_answers(proto):
    episode = {'parameters': {'mark_action': 'half_swap'}, 'seed': 17,
               'train': [{'input': [[2, 3]], 'output': [[3, 2]]}],
               'test': [{'input': [[5, 6]], 'output': [[6, 5]]}]}
    name = proto.public_filename(episode)
    changed = deepcopy(episode)
    changed['parameters'] = {'mark_action': 'reflection'}
    changed['seed'] = 99
    changed['test'][0]['output'] = [[5, 6]]
    assert proto.public_filename(changed) == name
    assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', name)
    changed['train'][0]['output'] = [[2, 3]]
    assert proto.public_filename(changed) != name

def test_real_racket_export_names(proto, tmp_path):
    destination = tmp_path / 'export'
    manifest = proto.write_evidence(destination)
    assert len(manifest['records']) == 2
    for row in manifest['records'].values():
        private = json.loads((destination / row['private_episode']).read_text())
        public = destination / row['public_challenge']
        assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', public.name)
        assert public.name == proto.public_filename(private)
        assert json.loads(public.read_text()) == proto.public_challenge(private)
        assert all(set(pair) == {'input'} for pair in json.loads(public.read_text())['test'])


def test_public_schema_contains_no_private_rule_hint(proto):
    episode = proto.make_episode(0, verify_racket=False)
    public = proto.public_challenge(episode)
    assert public["schema"] == "arcpuzzles-challenge-v1"
    assert set(public) == {"schema", "train", "test"}
    assert len(public["test"]) == 4


def test_export_records_actual_counts_racket_calls_and_exact_rule_hashes(proto, tmp_path):
    import hashlib
    destination = tmp_path / "complete"
    manifest = proto.write_evidence(destination, train_count=5, test_count=4)
    assert manifest["requested_counts"] == {"train": 5, "test": 4}
    assert manifest["label_authority"] == "protected Racket execution of each materialized rule"
    for row in manifest["records"].values():
        assert row["actual_counts"] == {"train": 5, "test": 4}
        assert row["unique_inputs"] == 9
        assert row["racket_evaluations"] == 18
        assert row["all_queries_identified_from_demonstrations"] is True
        assert row["query_labels_racket_verified"] == 4
        rule_bytes = (destination / row["rule"]).read_bytes()
        assert hashlib.sha256(rule_bytes).hexdigest() == row["rule_sha256"]
        public = json.loads((destination / row["public_challenge"]).read_text())
        assert public["schema"] == "arcpuzzles-challenge-v1"
        assert len(public["train"]) == 5
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])


def test_rule_file_hash_covers_the_exact_written_bytes(proto, tmp_path, monkeypatch):
    import hashlib
    original = proto.make_episode
    def without_runtime(*args, **kwargs):
        kwargs["verify_racket"] = False
        return original(*args, **kwargs)
    # Only skip the external reference executor; exercise the actual file writer.
    monkeypatch.setattr(proto, "make_episode", without_runtime)
    destination = tmp_path / "rule-bytes"
    manifest = proto.write_evidence(destination)
    for row in manifest["records"].values():
        written = (destination / row["rule"]).read_bytes()
        assert hashlib.sha256(written).hexdigest() == row["rule_sha256"]


def test_public_pair_fields_are_whitelisted(proto):
    clean = {
        "train": [{"input": [[1, 2]], "output": [[1, 1, 2, 2]]}],
        "test": [{"input": [[3, 4]], "output": [[3, 3, 4, 4]]}],
    }
    changed = deepcopy(clean)
    changed["train"][0]["count_scope"] = "all"
    changed["train"][0]["reference"] = "private program"
    changed["test"][0]["seed"] = 42
    assert proto.public_challenge(changed) == proto.public_challenge(clean)
    assert proto.public_filename(changed) == proto.public_filename(clean)
