from copy import deepcopy
import random

import pytest

from arcpuzzles.query_presentation import iter_public_turns, present_queries, query_order, verify_presentation


def test_private_shuffle_is_reproducible_unbiased_at_zero_and_rng_isolated():
    before = random.getstate()
    orders = [query_order(4, seed) for seed in range(96)]
    assert all(sorted(order) == [0, 1, 2, 3] for order in orders)
    assert {order[0] for order in orders} == {0, 1, 2, 3}
    assert len({tuple(order) for order in orders}) > 16
    assert orders == [query_order(4, seed) for seed in range(96)]
    assert random.getstate() == before


def test_actor_turn_contains_only_current_visible_bytes_and_no_mutable_source_alias():
    source = {'episode_id': 'private', 'seed': 5, 'settings': {'private': 1},
              'train': [{'input': [[0]], 'output': [[1]], 'private': 1}],
              'test': [{'input': [[i]], 'output': [[i + 1]]} for i in range(2, 6)]}
    presented = present_queries(source, seed=5, count=4)
    assert verify_presentation(presented) == source['test']
    turn = next(iter_public_turns(presented))
    assert set(turn) == {'train', 'test'}
    assert len(turn['test']) == 1 and set(turn['test'][0]) == {'input'}
    assert set(turn['train'][0]) == {'input', 'output'}
    assert turn == next(iter_public_turns(present_queries(source, seed=5, count=1)))
    turn['train'][0]['input'][0][0] = 9
    assert source['train'][0]['input'] == presented['train'][0]['input'] == [[0]]
    changed = deepcopy(presented)
    changed['test'][0]['output'] = [[9]]
    with pytest.raises(ValueError, match='paired answers'):
        verify_presentation(changed)


def test_controller_can_present_raw_native_episode_without_a_bundle_id():
    source = {'seed': 3, 'train': [{'input': [[8]], 'output': [[9]]}],
              'test': [{'input': [[i]], 'output': [[i + 1]]} for i in range(4)]}
    selected = present_queries(source, seed=3, count=1)
    assert verify_presentation(selected) == source['test']
    assert next(iter_public_turns(selected))['test'] == [{'input': selected['test'][0]['input']}]
