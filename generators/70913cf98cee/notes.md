# Working notes: 70913cf98cee

## Final design

- Preserve the exact canonical default as `postprocess=direct`.
- Add `postprocess=cycle_dominoes`: A applies the row-0 source→destination legend;
  the intermediate is the post-A four-connected destination-component topology;
  B cyclically recolors exact two-cell destination components.
- Generate every input independently of the hidden setting and label the same
  inputs with both programs. Materialize full banks before count slicing so
  2–6 demo and 1–4 query prefixes are stable.
- Keep the two-demo minimum by anchoring its first two scenes to seed-randomized
  3- and 4-pair profiles rather than raising demonstration cost.

## Findings and repairs

1. Initial minimum lessons could omit the last legend color, omit an orientation,
   or use only two pairs, allowing last-pair, orientation-only, or previous-color
   shortcuts. Repaired by qualifying every destination in both anchor scenes,
   covering both orientations, and requiring 3/4-pair minimum anchors.
2. A second adversarial pass found size-≤2 and eight-connected shortcuts. Added
   diagonal same-color singletons that stay separate only under exact-size,
   four-connected semantics.
3. Crossed-control stress found no visible unmapped nuisance in the 3-pair anchor.
   Added a neutral component so nuisance color can vary at a fixed intermediate.
4. The supplied base test used a checkout-specific canonical path. Replaced it
   with `reviewer_support.find_root`/`canonical_pairs`, preserving test semantics
   while allowing staged task execution.
5. Counterfactual witness authoring exposed nested Racket syntax errors; repaired
   the recipe and retained a protected replay where wrong order changes 12 cells.

## Final evidence and limits

- 15/15 staged task tests passed.
- 64-seed minimum-lesson attack: 128 episodes, 19 rivals, 2,304 fit checks,
  zero rival rules fitting all demos and disagreeing on a query.
- 256-seed sampler stress: 512 full episodes, 5,120 labels, 512 crossed controls,
  2,560 distinct inputs, and 256 substantive 30×30 scenes.
- Four native jobs produced 32 protected-Racket evaluations with one finite
  setting survivor per job.
- Sequential projection checked 16 one-query views, 24 private-field invariance
  mutations, four positive controls, and six intentional corruptions.
- These are finite checks, not a universal uniqueness or security proof.
- Next action: owner reviews exact source, reruns native qualification and fresh
  acceptance, then separately decides any training admission.
