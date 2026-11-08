"""Source-bound cross-product stress test beyond the battery's default draws."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import itertools
import json
import random
import time
from pathlib import Path
from probe_distribution import SOURCE, geometry_only


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    spec = importlib.util.spec_from_file_location('stress_subject', SOURCE)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    state = random.getstate()
    checked = counterexamples = replays = 0
    start = time.perf_counter()
    digest = hashlib.sha256()
    for band, profile, h, w, seed in itertools.product(
        (None, 'easy', 'medium', 'hard'), gen.SCHEDULE_PROFILES, (7, 8, 9), (7, 8, 9), range(25)
    ):
        kw = dict(grid_h=h, grid_w=w, scene_profile=profile)
        grid = gen.generate(seed, seed % 12, difficulty=band, **kw)
        assert not gen.self_check(grid, meta={'overrides':kw}), (band, kw, seed)
        assert gen.observe_overrides(grid) == kw
        rays = [set(e['ray']) for e in gen._analyze(grid)['emitters']]
        assert all(not a & b for i,a in enumerate(rays) for b in rays[i+1:])
        if profile == 'canonical_distractor':
            assert geometry_only(grid) != gen.rule_mirror(grid)
            counterexamples += 1
        if seed == 0:
            assert grid == gen.generate(seed, seed % 12, difficulty=band, **kw)
            replays += 1
        digest.update(json.dumps(grid, separators=(',', ':')).encode())
        checked += 1
    assert random.getstate() == state
    result = {'schema':'directed-ray-stress-v1', 'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'draws':checked, 'distractor_rival_refutations':counterexamples,
              'deterministic_replays':replays, 'global_rng_unchanged':True,
              'elapsed_seconds':time.perf_counter()-start, 'corpus_sha256':digest.hexdigest(),
              'racket_checked':False, 'oracle_note':'Local invariant stress; Racket parity is separate battery/probe evidence.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
