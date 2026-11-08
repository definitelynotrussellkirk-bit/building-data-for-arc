# Reusable lesson probe

`probe_lessons.py` measures the selected bounding-box generator without
depending on the review packet's transient directories. It discovers the
public runtime via `reviewer_support.find_root` and reads canonical pairs
through the portable canonical-data helpers. Never use it during a
visible-only solve: it exposes reference answers.

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B generators/41851e57e1a5/workspace/probe_lessons.py \
  --generator generators/41851e57e1a5/generator.py \
  --seeds 20 --out ../checks/lessons-after.json --baseline-witnesses
```

The report binds the generator, canonical rule, and probe source by SHA-256.
It generates fifteen pairs per seed in default/easy/medium/hard modes, checks
all twelve four-pair windows and their four query hold-outs, records strict
profile acceptance, geometric features, per-rival outcomes, unique inputs,
and full first ambiguous examples. Overlapping windows are correlated; the
denominators are evaluated lessons rather than independent trials.

Labels come from an independent Python bbox oracle checked against all five
stored canonical pairs. This probe does **not** execute Racket. Use the
packet's `arcpuzzles apply`, semantic gate, and production lesson census for
actual Racket-backed evidence. The native production sampler may choose
different indices; the task probe is a complementary cyclic-window check.

Exit zero means the probe completed without execution errors or disagreement
with a declared lesson hook. It does **not** mean zero ambiguity: inspect
`counts.ambiguous_ordinary_lessons`, `counts.ambiguous_rotations`, `canonical`,
and `errors`. A generator without declarations uses fourteen fixed independent
rivals; the report records this choice. A final passing rival result only
covers those tested functions.

`--baseline-witnesses` also rescores the exact retained baseline inputs at
seeds 0, 8, and 42, indices 0..3. Their baseline source hash is embedded in
the tool. These exhibit corner-only, occupied-only, and fixed-key teaching
failures without requiring a predecessor checkout.

Focused regressions live in `../tests/test_generator_contract.py`. To replay
the same assertions against an immutable source file, set
`ARCPUZZLES_TEST_GENERATOR_PATH` to its absolute path. The tests cover actual
grid behavior and independent oracle/rival outputs, rather than asserting a
particular implementation text. The selected implementation remains
`../generator.py`; this workspace is never automatically selected.
