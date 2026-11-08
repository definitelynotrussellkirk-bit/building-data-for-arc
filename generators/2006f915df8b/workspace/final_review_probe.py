"""Small deterministic review probe; labels here are independent Python BFS."""
import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import time


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--generator', type=Path, default=Path(__file__).resolve().parents[1] / 'generator.py')
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
SOURCE = args.generator
EXPECTED_SHA = 'f574a02ff6155f62ad28562f6af217ddbc0bb8e4d41522c73e27b569eb7c7472'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA
spec = importlib.util.spec_from_file_location('final_review_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def bfs(grid):
    start, = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    goal, = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    queue = deque([start])
    distance, ways, parent = {start: 0}, {start: 1}, {}
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < len(grid) and 0 <= nc < len(grid[0])) or grid[nr][nc] == 5:
                continue
            point, depth = (nr, nc), distance[r, c] + 1
            if point not in distance:
                distance[point], ways[point], parent[point] = depth, ways[r, c], (r, c)
                queue.append(point)
            elif distance[point] == depth:
                ways[point] += ways[r, c]
    assert ways[goal] == 1
    output, point = [row[:] for row in grid], goal
    while point != start:
        r, c = point
        if output[r][c] == 0:
            output[r][c] = 8
        point = parent[point]
    return start, goal, output


begin = time.perf_counter()
stats = dict(grids=0, witnesses=0, maze_draws=0, accepted_lessons=0,
             query_rotations=0, duplicate_rejections=0, none_replays=0)
original_regression = None
for height in range(7, 13):
    for width in range(8, 15):
        for band in (None, 'easy', 'medium', 'hard'):
            for seed in (0, 6484):
                cache = {}

                def draw(index):
                    if index in cache:
                        return cache[index]
                    grid = gen.generate(seed, index, difficulty=band, grid_h=height, grid_w=width)
                    assert (len(grid), len(grid[0])) == (height, width)
                    assert gen.self_check(grid) == []
                    start, goal, answer = bfs(grid)
                    agrees = {name: rival(grid) == answer for name, rival in gen.LESSON_COMPETITORS.items()}
                    if index % 2 == 0:
                        assert (start[0] - goal[0]) % 2 or (start[1] - goal[1]) % 2
                        assert (start[0] < goal[0]) == (index % 4 == 0)
                        assert not any(agrees.values())
                        stats['witnesses'] += 1
                    else:
                        assert all(coordinate % 2 == 1 for point in (start, goal) for coordinate in point)
                        stats['maze_draws'] += 1
                    stats['grids'] += 1
                    cache[index] = (tuple(map(tuple, grid)), agrees)
                    return cache[index]

                for index in range(8):
                    draw(index)
                for first_index in range(4):
                    accepted, seen = [], set()
                    for index in range(first_index, first_index + 20):
                        key, agrees = draw(index)
                        if key in seen:
                            stats['duplicate_rejections'] += 1
                            continue
                        seen.add(key)
                        accepted.append((index, agrees))
                        if len(accepted) == 4:
                            break
                    assert len(accepted) == 4
                    assert sum(index % 2 == 0 for index, _ in accepted) >= 2
                    for query in range(4):
                        for name in gen.LESSON_COMPETITORS:
                            if all(agrees[name] for i, (_, agrees) in enumerate(accepted) if i != query):
                                assert accepted[query][1][name]
                        stats['query_rotations'] += 1
                    stats['accepted_lessons'] += 1
                    if (seed, height, width, band, first_index) == (6484, 7, 8, 'easy', 1):
                        original_regression = [index for index, _ in accepted]

for seed in (0, 6484):
    for band in (None, 'easy', 'medium', 'hard'):
        for index in range(4):
            expected = gen.generate(seed, index, difficulty=band)
            for overrides in ({'grid_h': None}, {'grid_w': None}, {'grid_h': None, 'grid_w': None}):
                assert gen.generate(seed, index, difficulty=band, **overrides) == expected
                stats['none_replays'] += 1

assert original_regression == [1, 2, 3, 4]
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA
result = {'reviewed_generator_sha256': EXPECTED_SHA, 'status': 'pass',
          'reference': 'Independent Python BFS; this probe does not execute Racket.',
          'grid_heights': '7..12', 'grid_widths': '8..14',
          'bands': [None, 'easy', 'medium', 'hard'], 'seeds': [0, 6484],
          'stats': stats, 'original_counterexample_now_accepts': original_regression,
          'elapsed_seconds': round(time.perf_counter() - begin, 6)}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
