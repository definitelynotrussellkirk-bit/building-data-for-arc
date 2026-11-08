# Edge-rotation parametric prototype

**Status: proposed authoring evidence only.** The canonical generator, selected
Racket authority, approval state, training admission, and mixture weights are
unchanged.

## Rule family

The cue's full bounding-box edges are ordered clockwise as top, right, bottom,
left. `edge_shift` is fixed for the whole episode and moves every detected cue
edge clockwise by 0, 1, 2, or 3 frame sides. The cue is erased in every setting.
The canonical all-four-edges branch still fills the complete frame interior,
so it remains invariant under rotation. `edge_shift=0` returns the selected
canonical Racket program byte-for-byte.

The sampler supports 2–6 demonstrations and 1–4 queries independently. Inputs
are setting-neutral at a fixed seed. Demonstration and query streams are domain
separated, so changing the demonstration count cannot change query prefixes.
The retained four-query schedule uses 14×17, 18×22, 24×27, and exact 30×30
inputs. The 30×30 case contains an 18×20 frame and 7×9 boundary-contact cue;
size is not added as inert padding.

A certificate fits all four concrete Racket programs to demonstrations first,
requires the selected setting alone to survive, and then checks query labels
against that selected program. This is finite-family evidence, not uniqueness
against unrestricted programs.

## Reproduce focused tests and retained evidence

From the packet directory containing `review.py`:

```bash
python3 review.py run python3 -m pytest \
  generators/c130e51c4310/tests/test_parametric_edge_rotation.py -q

python3 review.py run python3 \
  generators/c130e51c4310/workspace/parametric/edge_rotation.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/c130-edge-rotation-replay
```

Choose a fresh output path for every replay; existing output roots are refused.
The CLI requires the protected bundled Racket backend. For each retained episode
it executes all four programs on every demonstration, requires one
survivor, and executes the selected program on all queries before serialization.
Existing output roots and duplicate public challenges are refused.

`public/<sha256>.json` and `public.jsonl` contain only demonstration pairs and
query inputs, serialized by `reviewer_support.public_challenge_bytes`. Public
IDs hash exactly those bytes. `private.json` contains settings, seeds, query
answers, programs, certificates, runtime identity, and source hashes.
`manifest.json` binds serialized file hashes; the writer itself does not execute
Racket. Sequential model projections reveal one query at a time and contain no
seed, setting, program, query answer, future input, index, or total-count hint.

The thin `adapter.py` loads this module by exact adjacent path. `promotion.json`
declares the bounded contract for a future independent qualification worker.
No qualification or acceptance is claimed here.
