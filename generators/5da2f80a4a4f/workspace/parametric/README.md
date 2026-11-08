# Proposed parametric extension: key transform

This task-local **prototype** preserves the original family: find the dense key
inside the hollow colour-2 frame, transform the key, and independently replicate
rows and columns to fill the frame interior. It does not modify or replace the
production generator or canonical Racket rule.

## Parameter

`key_transform` is chosen once per episode from:

- `identity` — canonical/default behavior; enlarge the extracted key unchanged.
- `transpose` — transpose the extracted key, then enlarge it to the same frame.

The prototype uses a 14×14 frame (12×12 interior) and a dense asymmetric 2×3
key. The interior is divisible by both 2×3 and 3×2, so every input is lawful for
either setting. Three labelled demonstrations are generated before one query;
the verifier checks that only the selected setting fits the demonstrations.

## Run

From the extracted packet root:

```sh
python3 review.py run python3 \
  generators/5da2f80a4a4f/workspace/parametric/verify.py \
  --out ../checks/parametric/identity-transpose
```

The output directory must not already exist. The verifier materializes one exact
Racket source per setting, executes every retained train/test output through the
included Racket bridge, checks the canonical/default setting against the current
canonical Python mirror, retains a same-input disagreement witness, and writes
public challenge files with hidden parameters and query outputs removed.

Focused portable tests live in
`generators/5da2f80a4a4f/tests/test_generator_5da2f80a4a4f.py`.

## Scope and limitations

This is proposed authoring evidence, not production integration or approval. It
covers two fixed complete episodes plus one cross-setting witness. The 2×3 key
and 12×12 interior are deliberate compatibility constraints; arbitrary canonical
inputs need not support the transpose setting exactly.
