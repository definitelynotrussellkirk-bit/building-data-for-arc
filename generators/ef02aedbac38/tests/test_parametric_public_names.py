"""Public export paths must not encode private selector settings or labels."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric' / 'prototype.py'


@pytest.fixture(scope='module')
def prototype():
    spec = importlib.util.spec_from_file_location('selector_role_public_names', SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_public_identifier_hashes_visible_bytes_but_ignores_private_answers(prototype):
    episode = {
        'meta': {'selector_role': 'five', 'episode_seed': 0},
        'train': [{'input': [[5, 2]], 'output': [[2, 0]]}],
        'test': [{'input': [[2, 5]], 'output': [[0, 2]]}],
    }
    name = prototype.public_filename(episode)
    changed = deepcopy(episode)
    changed['meta'] = {'selector_role': 'companion', 'episode_seed': 99}
    changed['test'][0]['output'] = [[5, 0]]
    assert prototype.public_filename(changed) == name
    assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', name)

    changed = deepcopy(episode)
    changed['train'][0]['output'] = [[0, 5]]
    assert prototype.public_filename(changed) != name

    changed = deepcopy(episode)
    changed['train'][0]['input'] = [[2, 5]]
    assert prototype.public_filename(changed) != name


def test_real_racket_export_uses_only_opaque_public_filenames(prototype, tmp_path):
    destination = tmp_path / 'export'
    report = prototype.write_evidence(
        destination,
        demo_count=3,
        query_count=4,
    )
    assert report['episode_shape'] == {'demo_count': 3, 'query_count': 4}
    for row in report['episodes'].values():
        path = destination / row['public_path']
        assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', path.name)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == path.stem.removeprefix(
            'challenge-'
        )
        challenge = json.loads(path.read_text())
        assert set(challenge) == {'train', 'test'}
        assert len(challenge['train']) == 3
        assert len(challenge['test']) == 4
        assert all(set(pair) == {'input'} for pair in challenge['test'])
        query_inputs = [json.dumps(pair['input'], sort_keys=True) for pair in challenge['test']]
        assert len(set(query_inputs)) == 4
        private = json.loads((destination / row['private_path']).read_text())
        assert path.name == prototype.public_filename(private['episode'])
        assert private['checks']['demo_count'] == 3
        assert private['checks']['query_count'] == 4
        assert private['checks']['all_episode_inputs_distinct'] is True


@pytest.mark.parametrize(
    ('demo_count', 'query_count'),
    [(0, 4), (3, 0), (True, 4), (3, True), (9, 4), (3, 5)],
)
def test_writer_rejects_invalid_counts_before_creating_output(
    prototype,
    tmp_path,
    demo_count,
    query_count,
):
    destination = tmp_path / f'invalid-{demo_count!r}-{query_count!r}'
    with pytest.raises(ValueError, match='count'):
        prototype.write_evidence(
            destination,
            demo_count=demo_count,
            query_count=query_count,
        )
    assert not destination.exists()


def test_writer_requires_exactly_one_seed_for_each_setting(prototype, tmp_path):
    destination = tmp_path / 'duplicate-setting'
    with pytest.raises(ValueError, match='exactly once'):
        prototype.write_evidence(
            destination,
            seeds=(0, 2, 1),
            demo_count=3,
            query_count=4,
        )
    assert not destination.exists()
