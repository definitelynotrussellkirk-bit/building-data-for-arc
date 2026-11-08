#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
TASKS = ('8fbc7756d37f', '56cfec365918')

def load(task):
    path = REPO / 'generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location(f'audit_{task}', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod

for task in TASKS:
    mod = load(task)
    grids = []
    rows = []
    for seed in range(8):
        for sample_index in range(4):
            grid = mod.generate(seed, sample_index, difficulty='medium')
            findings = mod.self_check(grid)
            rows.append({'seed': seed, 'sample_index': sample_index, 'validator_findings': findings})
            grids.append(grid)
    out = ROOT / 'checks' / 'audit' / task
    (out / 'generated_inputs.json').write_text(json.dumps(grids, indent=2) + '\n')
    (out / 'generated_index.json').write_text(json.dumps(rows, indent=2) + '\n')
