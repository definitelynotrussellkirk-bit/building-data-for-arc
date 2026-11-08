# Working notes: 06789067e67f

## Current reviewer decision

The base generator and a complete native parametric family are reviewer-ready on
the returned bytes. The exact canonical program remains the default. Owner source
review, native qualification/acceptance after integration, training admission,
and training activation are still pending and are not claimed here.

## Base repair

The imported generator advertised `single_component` although `self_check`
required 2–4 components, silently accepted unknown controls, accepted Boolean
integer overrides, and made parts of the documented size range unreachable
through its difficulty draws. Version `3.0.0` removes the contradictory texture,
validates every request strictly, supports exact `10..18 × 12..22` endpoints and
2–4 components, and uses bounded complete placement so the smallest lawful
four-component boards remain realizable. The canonical sort/pack rule and rule
hash `82b12cea1db8` are unchanged.

## Parametric family

`output_colors=original` is byte-for-byte canonical: crop nonzero 4-connected
components, sort by `(holes desc, area desc, color asc)`, and pack top-aligned
with one blank column. `output_colors=rank` first creates that packed
intermediate and then recolors its left-to-right components `1..4`. Inputs are
matched across settings, 2–6 demonstrations are supported, exactly four private
queries are retained, and query four is a substantive boundary-touching 30×30
scene. `skip_pack.rkt` applies the rank stage directly to the source layout for
the protected causal counterfactual.

## Adversarial findings and repairs

Three genuine two-demo teaching failures were reproduced and fixed:

1. At seed 286, random colors accidentally made pure ascending-color sorting
   agree with the full lexicographic order. Teaching colors are now chosen
   constructively so the shortcut must disagree.
2. Two geometrically identical equal-area rings made the ascending versus
   descending color tie invisible after rank recoloring. One ring was replaced
   by a different one-hole/equal-area shape so the tie direction remains visible.
3. A stable holes-only Racket sort used source scan order to recover the missing
   area/color tie-breaks. Tied teaching components now share a row and are placed
   in deliberately reversed horizontal order, breaking that positional cue.

The reusable `semantic_sweep.py` and `adversarial_probe.py` tools retain these
attacks plus wrong keys, wrong packing gaps/alignment, filled bounding boxes,
fixed/source order, rank bypasses, partial intermediates, malformed contracts,
and private/future-query mutations.

## Final bounded evidence

- 48 focused tests passed on final source.
- 400 minimum-two-demo episodes (200 seeds × two settings) rejected all 30
  semantic rivals; zero survivors and zero ambiguities.
- Protected Racket executed 669 candidate evaluations: 24 programs for the
  canonical setting and 31 for the rank setting, with 53 wrong-program
  counterexamples retained and no wrong survivor.
- Native authoring preflight passed 2 settings, 4 jobs, 24 parametric pairs,
  5 base canonical pairs, and 32 protected-Racket evaluations at 2 demos.
- The protected skip-A witness replayed with a changed final output.
- Public projection verified 16 one-query views; first-turn checking passed 24
  private-field invariance mutations and 4 visible positive controls.

These are finite falsification results over the declared grammar and candidate
banks, not a universal uniqueness or algorithmic-depth proof. The next action is
owner integration followed by fresh native qualification, witness replay, and
acceptance on the exact integrated source.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/06789067e67f/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
