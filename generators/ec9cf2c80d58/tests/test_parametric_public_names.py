"""Public export paths must not encode private tie-policy settings or labels."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest
from reviewer_support import public_challenge_bytes

SOURCE = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric' / 'prototype.py'


@pytest.fixture(scope='module')
def prototype():
    spec = importlib.util.spec_from_file_location('tie_policy_public_names', SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_public_identifier_hashes_exact_visible_challenge_bytes(prototype):
    # These literals are SHA-256 values of the canonical visible JSON bytes.
    # Public demonstration labels belong in the identity; metadata and hidden
    # query labels do not.
    episode = {
        'meta': {'tie_policy': 'column', 'episode_seed': 0},
        'train': [{'input': [[5, 2]], 'output': [[2, 0]]}],
        'test': [{'input': [[2, 5]], 'output': [[0, 2]]}],
    }
    assert prototype.public_filename(episode) == (
        'challenge-a40cefc9af9b436e4b32afbe9fecc518'
        'a1f2d3ed004bd7764b8d3d2371baab95.json'
    )

    private_only = deepcopy(episode)
    private_only['meta'] = {'tie_policy': 'row', 'episode_seed': 99}
    private_only['test'][0]['output'] = [[5, 0]]
    assert prototype.public_filename(private_only) == prototype.public_filename(episode)

    public_label_changed = deepcopy(episode)
    public_label_changed['train'][0]['output'] = [[0, 5]]
    assert prototype.public_filename(public_label_changed) == (
        'challenge-802d55ef03bc9c6ca5ce34f3b384f824'
        '78a21f38e6dfffb09185155198f29d57.json'
    )


def test_real_racket_export_uses_opaque_public_keys(prototype, tmp_path):
    spec = importlib.util.spec_from_file_location('tie_policy_export_names', SOURCE.with_name('build_evidence.py'))
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    destination = tmp_path / 'export'
    builder.write_evidence(destination)
    public = json.loads((destination / 'public_challenges.json').read_text())
    private = json.loads((destination / 'episodes.json').read_text())
    assert list(public) == sorted(public)
    assert set(public) == {prototype.public_filename(episode) for episode in private.values()}
    for name, challenge in public.items():
        assert re.fullmatch(r'challenge-[0-9a-f]{64}\.json', name)
        assert set(challenge) == {'train', 'test'}
        assert len(challenge['train']) == 3
        assert len(challenge['test']) == 4
        assert all(set(pair) == {'input'} for pair in challenge['test'])
        query_inputs = [json.dumps(pair['input'], separators=(',', ':'))
                        for pair in challenge['test']]
        assert len(set(query_inputs)) == 4
        public_file = destination / 'public' / name
        assert public_file.read_bytes() == public_challenge_bytes(challenge)


def test_public_registry_rejects_duplicate_visible_payloads(prototype):
    spec = importlib.util.spec_from_file_location(
        'tie_policy_export_duplicates', SOURCE.with_name('build_evidence.py')
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    register = getattr(builder, '_register_public_challenge', None)
    assert register is not None, 'evidence writer must guard duplicate public IDs'

    episode = {
        'train': [{'input': [[5, 2]], 'output': [[2, 0]]}],
        'test': [{'input': [[2, 5]], 'output': [[0, 2]]}],
    }
    public = {}
    register(public, prototype, episode)
    with pytest.raises(ValueError, match='duplicate public challenge'):
        register(public, prototype, deepcopy(episode))
