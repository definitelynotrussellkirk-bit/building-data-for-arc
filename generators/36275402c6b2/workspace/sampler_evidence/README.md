# Reviewer-authored sampler evidence

These optional files record the bounded sampler repair. They are independent of
the generator's task behavior and are not generator inputs.

## Recorded checks

- `red.log` records the initial test-driven check against the original sampler:
  seven tests passed and the 1 MB peak-allocation gate failed at 21,557,736 bytes.
  This run preceded the addition of required-side sampling and its three tests.
- `green.log` records all eleven focused tests passing against the proposed
  sampler, including the optional required-side mode.
- `benchmark.json` records an allocation probe comparing both algorithms on
  the same original maximum layout, plus a required-side probe on a 154-slot
  expanded layout. Measurements are descriptive; elapsed time is not a gate.
- `probe.py` reproduces the probe from explicit before/after source paths.
  It does not modify either source and does not add guessed runtime paths.

The tests cover every legal rank across all 128 subsets of a seven-slot universe
with gaps, touching starts, exact separation, and row transitions. They cover
both the unrestricted and required-side distributions, representative seeded
draws with full RNG-state equality, impossible eligibility without randomness,
negative and oversized counts, and generous 1 MB allocation limits.

## Reproducing the probe

Run in the prepared task runtime with `puzzle_generators` available. If using a
standalone checkout, set `PYTHONPATH` externally to that runtime's actual path.
Supply the original and repaired generator source paths explicitly:

```sh
python probe.py \
  --before-source /absolute/path/to/original/generator.py \
  --after-source /absolute/path/to/repaired/generator.py \
  --output /absolute/path/to/benchmark.json
```

The comparison freezes the original 126-slot candidate set so an accompanying
expansion of `_legend_slots` does not confound the algorithm comparison. The
additional required-side fixture includes left and right starts on crop rows
with a black gap and uses the same row-major ordering. RNG-state equality is
checked directly in addition to recording the next RNG value.

## Mechanism

A monotone scan computes the next compatible slot after each candidate. Suffix
counts use `ways[i][k] = ways[i + 1][k] + ways[next_slot[i]][k - 1]`. Optional
`ways_side` counts selections containing a crop-row witness; choosing such a
slot satisfies the side requirement, while choosing other slots preserves it.
Lexicographic unranking takes each selecting block before its skipping block.
One `randrange(total)` draws the rank and consumes the same random state as
`Random.choice` on the corresponding explicit lawful list. Both suffix tables
use O(n × k) cells and exact integer counts. There is no rejection loop.
