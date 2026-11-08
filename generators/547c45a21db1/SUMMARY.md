# 547c45a21db1 — nearest endpoint along a cardinal path

Kind: `per_puzzle`. Reviewed version: **3.1.0**.

A zero-background grid contains one simple induced four-neighbor path. Its
endpoints are colors 2 and 3; internal cells are color 1. Recolor each internal
cell by the closer endpoint in path distance, using 4 for a tie. Preserve seeds
and background. The selected canonical Racket rule remains the label authority,
with normalized identity `44ec512ed7bb`.

All bands accept exact integer overrides: height 5–14, width 6–14, total active
path length 4–20, **including both seeds**. All joint combinations are supported;
unknown names, booleans, strings, floats and out-of-range values are rejected.
The bounded randomized constructor has a constructive fallback and never clips.

Default draws alternate odd contrast, even contrast and varied geometry. Five
demonstrations plus one query retain a contrast of each parity under any one
holdout of six consecutive raw draws, before materializer rejections. Exact
overrides take priority. Real accepted lessons are checked separately.

The review adds graph validators, observed axes, declared rivals, witnesses and
147 focused tests. See `notes.md` and `workspace/README.md` for scope and tools.
Approval remains derived by the catalog from code and retained evidence.
