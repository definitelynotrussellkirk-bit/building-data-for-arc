# Native stamp-mask family

`adapter.py` is the native entry point. `stamp_mask=fill_cells` retains the canonical source byte-for-byte; `template_holes` reuses the previously authored exact alternate. Template discovery, greedy nearest-different-color pairing, scale inference and first-compatible D4 placement are unchanged. Only which template cells get stamped changes. Production generator and legacy prototype APIs remain untouched.

Requests accept exact-integer seeds, 2–6 demonstrations and 1–4 queries. Six demo scenes and four query scenes are generated independently of requested counts and of settings; a separate seeded permutation shuffles the entire query bank before taking its prefix. `public_turn(episode, index)` returns demonstrations and one current query input only. All stored episodes, directory listings, permutations and rule metadata are controller-private.

The two-demo minimum includes a three-pair mixed-scale scene and a second mask/orientation. This addresses the retained first-two-pairs shortcut without increasing the count. Four canonical masks, all scales 1–3, singleton/multiple pairs, both diagonal relations, and arbitrary distinct ARC palettes are retained. Ordinary scenes are 22–27 per side; a constructive 30x30 query places the largest and medium footprints at the top corners, the small pair at the bottom right and the template bottom left. It touches every boundary and all quadrants without blank padding. Its original three-pair grammar remains sparse; we do not claim dense arbitrary objects.

A: recover template and greedy pairs, then infer each pair's anchor, scale and first-compatible D4 transform. Intermediate: those per-pair placements. B: paint the setting-selected fill or hole mask under each recovered placement. The no-rotation counterfactual retains the actual anchor and scale but substitutes identity orientation only in the painting stage; its output changes. Opposite-corner ports admit more than one mathematical symmetry; the canonical rule resolves this by first-compatible D4 order, retained exactly, not asserted uniquely inferable from port colors.

Run from the packet outer directory:
```sh
python3 review.py run python3 generators/0f5fbe0de38e/workspace/parametric/audit.py --out generators/0f5fbe0de38e/workspace/parametric/evidence/current --seeds 20
python3 review.py task-tests 0f5fbe0de38e --phase after --out ../checks/0f5fbe0de38e-tests
```
The audit executes both declared settings and six nearby rivals through the protected Racket verifier, compares them with Python claims, and rejects rivals using demos only. Count sweeps reuse prefixes, so pair-instance counts are not independent-scene counts. Public challenge files contain one query and are named by their visible JSON bytes. Finite checks do not prove universal identifiability, all-seed reliability or learning benefit. Owner exact-source acceptance remains separate; no training admission.

The older `prototype.py`/`rules/` are retained as implementation/provenance dependencies. Its old materializer is not the native exporter.
