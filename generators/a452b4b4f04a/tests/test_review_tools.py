"""Lightweight regression checks for the reusable review/audit helpers."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'workspace'))
import review_probe
import audit_targets
from probe_support import independent_output, pairs


@pytest.mark.parametrize('pair',pairs())
def test_independent_probe_matches_canonical_and_is_pure(pair):
    original=deepcopy(pair['input'])
    assert review_probe.geometry(pair['input']) == pair['output']
    assert pair['input'] == original


def test_row_distractor_rival_is_deliberately_distinct_from_column_zero():
    grid=[[2,0,0],[0,0,9],[0,0,0]]
    original=deepcopy(grid)
    assert audit_targets.first_nonzero_rival(grid) == [[2,2,2],[9,9,9],[0,0,0]]
    assert grid == original


def test_canvas_table_rival_keeps_wrong_location_after_translation():
    grid=[[0]*9 for _ in range(8)]
    for r in range(1,6):grid[r][1]=grid[r][5]=8
    for c in range(1,6):grid[1][c]=grid[5][c]=8
    grid[2][2]=3
    original=deepcopy(grid)
    wrong=audit_targets.frame_table_rival(grid,{(8,9):(1,2,5,5)})
    assert wrong[3][2] == 0  # should be filled in translated frame
    assert wrong[3][5] == 3  # overwrites translated right frame
    assert grid == original


def test_probe_digest_is_key_order_independent_and_content_sensitive():
    assert review_probe.digest({'a':1,'b':2}) == review_probe.digest({'b':2,'a':1})
    assert review_probe.digest([[0]]) != review_probe.digest([[1]])
