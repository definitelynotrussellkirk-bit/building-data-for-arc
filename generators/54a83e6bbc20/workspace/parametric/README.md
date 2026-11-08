# Jigsaw assembly-order prototype

Status: **proposed prototype 1.0.0** for original ARC training task `18447a8d`.
The production generator and its canonical Racket authority remain unchanged.

Match each cyan anchor to the colored piece that completes a 3×5 rectangle.
The hidden `assembly_order` then determines where the completed bands go:

| Setting | Completed rectangle placement |
| --- | --- |
| `top_to_bottom` (canonical default) | Preserve the cyan anchors' input order. |
| `bottom_to_top` (proposed) | Reverse that order, preserving each piece's orientation. |

Even integer seeds choose the default; odd seeds choose the proposed setting.
This choice is made once for the entire episode. Every demonstration and query
uses that same complete Racket program. The alternative changes only the band
origin from `(r0 (obj-r1 left))` to `(r0 (- h 1 (obj-r2 left)))`; first-placement
search, modal-width selection, shape matching, colors, and piece geometry stay
in the rule. The default source is byte-for-byte canonical, hash `82f172ba82d3`.

## Generate episodes with four queries

From the outer packet directory, run with a fresh private output path and public
directory:

```bash
python3 review.py run python3 \
  generators/54a83e6bbc20/workspace/parametric/prototype.py \
  --n-train 3 --n-test 4 \
  --out ../checks/jigsaw-new/private.json \
  --write-public ../checks/jigsaw-new/public
```

The default command produces one episode for seed 18 and one for seed 19, so
both settings have three demonstrations and four distinct queries. Repeat
`--seed INTEGER` to choose explicit episodes. Python callers can use:

```python
episode = build_episode(root=repo_root, seed=19, n_train=5, n_test=2)
```

`n_train` accepts exact integers in **3..32**, independently of `n_test` in
**1..32**. Fewer than three demonstrations are unsupported: the retained
three-example curriculum includes an equal-area anchor and a row-critical
anchor. Default episodes use four-piece, 17×11 scenes from the unchanged hard
distribution. Inputs are distinct across both splits. Sampling is deterministic
and bounded to 32 attempts per requested pair; exhausted support raises instead
of cloning inputs or returning an incomplete episode. Changing query count
preserves the demonstrations and the existing query prefix.

Every accepted pair is labelled by executing Racket. The Python transform is
an assertion mirror and never replaces failed reference execution. The command
also retains exact programs in `racket/`; conflicting existing files are refused.

## Evidence about what the demonstrations teach

`analyze_rivals` filters 19 declared programs using only demonstration inputs and
outputs. These include both correct order settings; input-row, sorted-color,
area-only, and each omitted-row matcher under **both** output orders; whole-grid
reflections; and candidate-order alternatives. It then checks every query against
the surviving predictions. An episode with a query-changing survivor fails
explicitly. The private evidence names each survivor and the first demonstration
rejecting each other program.

Reversing bands is different from reflecting the whole grid: the latter also
reverses rows inside each jigsaw piece. Retained asymmetric examples distinguish
these behaviors. Applying both output orders to wrong matchers prevents their
rejection solely because they used the wrong order.

`verify_semantics.py` is a reusable, bounded check of the actual programs:

```bash
python3 review.py run python3 \
  generators/54a83e6bbc20/workspace/parametric/verify_semantics.py \
  --out ../checks/jigsaw-new/semantics.json
```

It executes both settings on all four canonical labeled fixtures, six generated
examples across the 2/3/4-piece boundaries, and two lawful counterfactuals. It
reconstructs the expected answers independently from row cuts and candidate
colors. Swapping only two cyan anchors must change the answer in both settings;
swapping only candidate positions must preserve the answer. These checks show
that anchor order and shape matching still affect the result.

Ordering completed rectangles by candidate order was rejected as the proposed
parameter: on this grammar it allows filling cyan around each colored suffix
without consulting the cyan anchors. That simpler behavior remains a named rival.

## Public examples and private authoring data

Only `examples/public/` is a shareable challenge directory. Its two filenames are
full SHA-256 hashes of the exact visible bytes, with `.json` suffixes. Both bytes
and IDs come from the shared `public_challenge_bytes` / `public_challenge_id`
helpers. Files contain demonstration inputs/outputs and query inputs. Seeds,
parameters, source programs, sample indices, and query answers are excluded from
both their content and their names.

`write_public_challenges` sorts files by content ID, rejects duplicate visible
episodes, preflights collisions, and refuses overwrites. The CLI rejects a
private evidence path inside the public directory. The evidence directory is
private authoring material: it includes query labels and parameter mappings.

## Run the focused tests

The tests require `pytest`; all execution uses the packet's local Python
dependencies and offline Racket runtime after `python3 review.py setup`.

```bash
python3 review.py run python3 -m pytest -q \
  generators/54a83e6bbc20/tests/test_parametric_assembly_order.py
```

Current source hashes and retained check results are in `evidence/manifest.json`.
The checks cover exact authority preservation, actual labels, independent counts,
global distinctness, explicit exhaustion, fixed episode semantics, finite-rival
teaching, and public export behavior.

## Limits

This is a fixed three-row, width-five prefix/suffix jigsaw family, not arbitrary
polyomino assembly. Size checks cover 9×11, 13×11, and 17×11; default prototype
episodes use 17×11. The producer's width-mode safety restriction is retained.
The 19-program check is finite evidence, not universal identifiability or measured
learning improvement. No production parametric API, variant approval, or training
admission is created by this prototype. Existing canonical approval does not
approve the alternate rule.
