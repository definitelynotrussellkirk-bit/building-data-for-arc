from copy import deepcopy
import hashlib
import json

import pytest
from shared.runtime.reviewer_support import public_challenge_bytes, public_challenge_id


def episode():
    return {'train': [{'input': [[1, 0]], 'output': [[0, 1]]}],
            'test': [{'input': [[2, 0]], 'output': [[0, 2]]}],
            'seed': 17, 'parameters': {'direction': 'left'}}


def test_exact_written_bytes_define_id_and_hide_private_fields():
    value = episode()
    expected = b'{"test":[{"input":[[2,0]]}],"train":[{"input":[[1,0]],"output":[[0,1]]}]}\n'
    assert public_challenge_bytes(value) == expected
    assert public_challenge_id(value) == hashlib.sha256(expected).hexdigest()
    changed = deepcopy(value)
    changed.update(seed=99, parameters={'direction': 'right'}, program='secret', meta=object())
    changed['test'][0]['output'] = [[9, 9]]
    assert public_challenge_bytes(changed) == expected
    assert set(json.loads(expected)) == {'train', 'test'}


@pytest.mark.parametrize('split,field', [('train', 'input'), ('train', 'output'), ('test', 'input')])
def test_each_visible_channel_changes_identity(split, field):
    value = episode()
    changed = deepcopy(value)
    changed[split][0][field][0][0] = 8
    assert public_challenge_id(changed) != public_challenge_id(value)


@pytest.mark.parametrize('grid', [[], [[]], [[True]], [[1.0]], [['1']], [[10]], [[-1]], [[1], [1, 2]], [[1] * 31]])
def test_malformed_public_grids_are_rejected(grid):
    value = episode()
    value['test'][0]['input'] = grid
    with pytest.raises(ValueError):
        public_challenge_bytes(value)


def test_batch_visible_ids_do_not_depend_on_setting_iteration_order():
    a = episode()
    b = deepcopy(a)
    b['train'][0]['output'] = [[1, 1]]
    def write_plan(items):
        keyed = [(public_challenge_id(item), public_challenge_bytes(item)) for item in items]
        if len({key for key, _ in keyed}) != len(keyed):
            raise ValueError('duplicate public payload')
        return sorted(keyed)
    assert write_plan([a, b]) == write_plan([b, a])
    with pytest.raises(ValueError, match='duplicate'):
        write_plan([a, deepcopy(a)])
