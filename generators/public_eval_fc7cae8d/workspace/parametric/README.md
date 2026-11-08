# Colored-frame alignment family

The source public parent is `fc7cae8d`. Its immutable provenance remains at
`../public-parent.json`; the general Racket reference is the task's root
`reference.rkt`. No supplied input or answer is a lookup key in the implementation.

## Rule

Find the single interior four-connected nonzero component. Its two reserved
colored bars occupy adjacent sides of a rectangular picture. Match each bar to
the outer canvas side with the greatest count of that color. These two side
correspondences determine one of the eight rotations/reflections. Remove the
bars and apply that transform to the complete picture, retaining zeros and colors.

| Episode parameter | Meaning |
|---|---|
| `marker_pairing=match` | Match the same marker colors; exact canonical reference. |
| `marker_pairing=swap` | Exchange the two outer marker correspondences before resolving orientation. |

There are two settings, held fixed across an episode. This changes the executed
orientation rule while preserving extraction, spatial reasoning and picture
content. `program(default)` is byte-identical to the root reference.

`native_family.py` validates the admitted grammar and computes deterministic
Python label claims. `adapter.py` loads adjacent files by exact paths; the public
authoring preflight independently re-executes those claims through protected
Racket. `generator.py` constructs only inputs and remains usable in the owner's
relocated base runtime; it never imports this workspace.

## Grammar and coverage

Grids use exact integer colors 0..9, zero background, and axes no greater than 30.
Exactly one nonzero four-connected component is separated from the boundary.
Two reserved colors form complete adjacent inner bars, with a black missing
shared corner. Their unique dominant outer sides are adjacent. Other outer-frame
colors are absent from the payload. The parser supports picture axes at least 2;
generated pictures start at 3x4. The full rectangular crop includes black notches.

The portable base sampler has one declared input override,
`max_frame_depth=1|2|3`, an exact-integer upper bound on inward frame thickness.
`difficulty="hard"` selects the 30x30 canvas with a 23x23 picture. These are
implemented base-input controls and are separate from the episode's hidden
`marker_pairing` rule. Public-source authoring remains unapproved until the
owner's registration and acceptance steps.

The sampler materializes six demonstrations and four distinct query inputs,
then independently shuffles the full query bank before any prefix is selected.
It supports 2..6 demonstrations and 1..4 query prefixes. All settings use identical
ordered inputs for a given seed. Strict seeds span 0..2**63-1; booleans and floats
are rejected. Two demonstrations carry the minimum teaching context; additional
demonstrations add diversity rather than repair an omitted distinction.

Queries cover 9x10, 17x22, 24x29 and 30x30 canvases. The largest role contains a 23x23
picture plus surrounding frame, not merely a small object in a padded canvas.
The output is the picture's original size, optionally with axes exchanged; this
grammar does not produce 30x30 outputs because the input also contains a frame.

## Evidence and owner handoff

The packet's checks under `checks/public_eval_fc7cae8d/` retain focused tests,
protected official-label execution, finite shortcut audits, maximum seed/count
labels, source-bound causal witnesses and single-query public export probes.
The native pre-registration command is:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles.review_public_creation \
  preflight public_eval_fc7cae8d --root . \
  --out ../checks/public_eval_fc7cae8d/preflight-new
```

Run from the outer packet folder. The payload runs in `WORK/repo`; choose a fresh
output after any source edit. The preflight checks all supplied original labels
including test gold, then all settings at seeds 17/43 with two demonstrations and
four queries. The separate audit also checks seed 0 and retained regression seeds.

The reusable `checks/tools/public_creation_evidence.py` builds witnesses and
authoring-only public views directly from preflight. Each visible file contains
demonstrations and one query input. Settings, programs, answers, source indices,
presentation ordering and future queries stay in controller-private files.

This is reviewer authoring evidence. Owner registration, source review, native
qualification and fresh acceptance remain required. Finite rivals and seeds do
not prove universal uniqueness or learning benefit, and training is not admitted.
