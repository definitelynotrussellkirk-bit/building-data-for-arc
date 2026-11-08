# a820c3ed3124: finite learnability counterexample

Current generator unchanged. A plausible executable wrong rule, **fill the largest gray-bounded chamber, preserving nonblack cells; break ties in reading order**, fits three generated demonstrations but changes the next query. The rival is implemented as `largest_chamber` in `room_size_probe.py`.

## Reproduction

Run from the packet root:

```sh
WORK/.venv/bin/python review.py run --receipt checks/a820c3ed3124/command.json python3 ../checks/a820c3ed3124/room_size_probe.py
```

The actual command returned exit 0. Generator version 1.1.0, seed 0, sample indices 0–3, default difficulty and no overrides. Only four grids were drawn (the first candidate succeeded); only four native reference evaluations ran. Racket reported backend `racket` and `protected: true`. All four grids pass this generator's `self_check`.

| Role | Sample index | Shape | Chamber widths, left to right | Red seed, zero based | Cells differing from reference |
|---|---:|---|---|---|---:|
| demonstration | 0 | 9 × 11 | [7, 1] | (1, 5) | 0 |
| demonstration | 1 | 7 × 10 | [3, 1, 2] | (2, 2) | 0 |
| demonstration | 2 | 9 × 13 | [6, 1, 2] | (5, 6) | 0 |
| query | 3 | 7 × 12 | [4, 5] | (2, 4) | 44 |

## Implication and scope

The visible lesson does not distinguish red-seed selection from largest-room selection. The query does: the sampler always puts red in the leftmost chamber, but here that chamber is smaller than another chamber. `witness.json` retains the exact inputs, Racket reference outputs, rival outputs and changed coordinates. `command.json` records actual launcher completion.

This is one finite counterexample, not an estimate of how often episodes are ambiguous, a claim about every generated episode, or a claim that the reference labels are wrong. The rival is Python; reference labels are native protected Racket. No battery, parametric qualification, generator repair, rule edit or acceptance was attempted. A possible repair direction is to add episode-level distinguishing demonstrations where the seed chamber is not the largest and to vary chamber position; that proposal was not implemented or tested here.

No `evidence/review_index.json` or existing task prototype was present in the task home. Current `notes.md` contains only its initial placeholder.

## Audited bytes

- Generator SHA-256: `69db8ae7dc9cde7d0d8993e95221b5f52ae7bc29ad2e2f566a33bf6c128c1e95`
- Canonical solution file SHA-256: `107ae90ef1346fe71b5af1e0ab4333b3afdc4214aba595a1357acca38533337a`
- Executed canonical `target_code` SHA-256: `867436c319a857b04518fed2c80a4018dc572ee2d668f81d37955c137f30d1d5`
- Reproducer SHA-256: `fe13e2a552e7d34e6dfe5e79254dfc0486f6163634d6b8ba0d7aa5e1f224c2ff`

Source: `repo/generators/a820c3ed3124/generator.py` and `repo/shared/data/base/solutions/banks/f4facb1306bd/M116__a820c3ed3124.json` (paths relative to WORK).
