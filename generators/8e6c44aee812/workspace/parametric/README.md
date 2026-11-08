# Native output-scale staircase family

This task-local family retains `output_scale` values **2** and **3**. Scale 2
returns the exact canonical program; scale 3 changes only the two output-size
multipliers. The existing production generator and canonical authority remain
separate. Reviewer qualification is followed by owner acceptance of the exact
integrated source; these examples are not admitted to training.

## Rule and dependency

Read the main diagonal of the nested-L input, remove its trailing zero padding
when present, and retain all active color occurrences in order. The resulting
sequence and its length determine the continuation: output cell `(r,c)` is
`active[max(r,c) % len(active)]`. Output dimensions are the input dimensions
multiplied by the episode's fixed scale.

The input-dependent intermediate is the full active sequence and its period.
Keeping padding in that sequence or dropping later runs of a color changes both
the recovered period and subsequent bands. This is a derived sequence controlling
continuation; it is not an iterative simulation of successive grid states.

## Episode API

```python
settings = {"output_scale": 3}
program = adapter.program(settings)
episode = adapter.generate(17, settings, demos=3, queries=4)
```

Supported counts are 2–6 demonstrations and 1–4 queries independently; defaults
are three and four. Settings are fixed for the entire episode. Inputs are matched
across the two scales and drawn before count slicing, keeping prefixes stable.
The first two demonstrations provide rich color recurrences and padded/unpadded
examples. Query inputs are distinct from one another and every demonstration.
The fourth query has a 10×10 input and a 30×30 answer at scale 3. The source input
grammar stops at 10×10; scale 2 therefore has a maximum 20×20 answer. Enlarging
that canonical grammar is not part of this native integration.

The existing `program_for`, `solve`, `generate_episode`, and `public_challenge`
entry points remain available for the retained verifier. Prefer the thin native
adapter for new consumers.

## Reproduce focused verification

From the packet's outer directory, using its prepared Python/Racket environment:

```bash
python3 review.py run python3 -m pytest \
  generators/8e6c44aee812/tests/test_parametric_output_scale.py \
  generators/8e6c44aee812/tests/test_native_adapter.py \
  generators/8e6c44aee812/tests/test_native_family.py \
  generators/8e6c44aee812/tests/test_native_audit.py \
  generators/8e6c44aee812/tests/test_native_export.py -q

python3 review.py run python3 \
  generators/8e6c44aee812/workspace/parametric/audit_native.py \
  --out ../checks/8e6c44aee812/audit-replay

python3 review.py run python3 \
  generators/8e6c44aee812/workspace/parametric/make_examples.py \
  --seed 0 --demos 3 --queries 4 \
  --out ../checks/8e6c44aee812/examples-replay

python3 review.py run python3 -m arcpuzzles parametric qualify 8e6c44aee812 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8e6c44aee812/qualification-replay --summary
```

Choose fresh output directories. The native inventory must match current source
before qualification. After any source change, update the manifest using its
exact replacement hash and perform fresh qualification and causal replay.

## Public/private exports

`make_examples.py` executes both settings through the protected native worker.
It writes two controller challenges under `public/` and eight independent
single-query payloads under `turns/`. Their filenames hash the exact visible
bytes. Each actor turn exposes only the demonstrations and that query input;
there is no answer, private setting, later input, or total-query-count field.

`private/metadata.jsonl` retains answers, settings, program and source hashes,
protected evaluator identity, demonstration-only setting certificates, and the
ordered turn identifiers. The private records explicitly remain owner-pending.
The writer refuses duplicate visible payloads and existing output directories.
Native certificates cover declared settings only; the separate finite-rival
audit checks the additional shortcuts documented in its report.

## Scope of evidence

Current command receipts and exact inputs/outputs are under `checks/8e6c44aee812/`.
The native source inventory is `evidence/manifest.json`; compact current evidence
is under `evidence/current/`. Retained `evidence/reviewer-reported/` reports belong
to the older five-demo prototype and are historical, not fresh qualification.
The audit fits each alternative using visible demonstrations before comparing
its query prediction. An alternative that agrees on every query is not counted
as a harmful ambiguity. Finite tests do not establish universal identification,
measured Qwen learning benefit, acceptance, or training eligibility.
