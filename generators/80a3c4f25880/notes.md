# Working notes: 80a3c4f25880

## Current source and separate native prototype

Production `generator.py` remains exactly `613067f8b20870a9d47257b08852db1ec5119c09d3c9390086544b117dad6a00`; canonical rule hash remains `17e5167b1aa3`. The raw canonical program SHA-256 is `de16ce33089efad238c98636fbcd7584ad9709d56de73238bc94aaeaefd90c07`. No canonical authority, production approval, or shared runtime was changed.

`workspace/parametric/adapter.py` is a native runnable extension with `line_rule=canonical|most_cells|least_cells`. The default program is byte-identical to the canonical source. Alternatives clear the corner key, crop and rotate the object, measure each rotated row's occupied-cell count, and complete the topmost row attaining the maximum or positive minimum. The rotated crop/count vector is the input-dependent intermediate consumed by row completion. Filling before rotation changes the final grid; this is retained for both alternatives in protected native causal evidence.

The prototype supports 3–6 demonstrations and 1–4 queries independently. Three demos expose all three key meanings. The first two are structured tie and cell-count-versus-span witnesses, varied by scale/reflection/color/placement; later examples use sampled connected shapes. Input draws and ordering are shared across settings, seed-local, and independent of requested counts. Four distinct queries progress from compact to large to a connected full-bounding-box 30×30 object with a matching 30×30 output. The wider prototype grammar is separate from production's linked small profiles.

## Current executed checks and handoff

- 42 focused tests passed: exact canonical source and four official pairs, hand-counted alternatives, topmost ties, wrong order, clearing a key inside the object bbox, typing/count boundaries, shared inputs, deterministic fresh results, public projection and verifier failures.
- `checks/80a3c4f25880/audit-r2/report.json`: seeds 0/17, six episodes, 42 intended labels, 122 episode/candidate comparisons all refuted on demos, 336 protected Racket evaluations and 72 cache hits. Counts include explicit alternate-setting checks and named rivals; they are not 122 distinct programs. No sampled ambiguity remained. Coverage includes keys 1/2/3, objects of 8–296 cells, and two shared full 30×30 stress inputs across three settings.
- `checks/80a3c4f25880/audit-r2/` contains 24 strict one-query public challenges, private labels/programs, and a hash/projection verifier. One-query and four-query requests have the same first-turn content when demos/seed/setting are held fixed. No future-query count, settings, answers, or final-turn hint enters a public view.
- Independent self-review found an aggregate verifier gap: a manifest-listed public file absent from the private index could escape strict validation. The new regression reproduced it; the fixed verifier enforces exact inventory/index equality and valid IDs before indexed reads. The final 42-test run and audit-r2 include that repair.
- `workspace/parametric/evidence/manifest.json` inventories the final sources and current checks. Native `checks/80a3c4f25880/qualification-r2/qualification.json` passed all three settings at seeds 0/17 with 3 demos/4 queries: six jobs and 78 protected Racket evaluations. Both nondefault wrong-order cases in `checks/80a3c4f25880/causal-r2/witness.json` were executed and replayed, with changed final answers and the current qualification binding.

Reviewer status is **ready**. The owner must qualify and accept the exact integrated source; no owner acceptance or training admission was performed. Finite settings/seeds/rivals do not establish every-seed correctness, universal identifiability, or measured training gain. The two structured teaching slots and monotone-path/random-growth sampler constrain topology diversity. Causal intermediate descriptions remain authored interpretation; protected replay verifies the final labels.

## Open production Python-mirror defect; tested candidate patch

`workspace/mirror_probe.py` preserves an authored V5-profile input accepted by current `self_check`: an 8×8 grid, key 1 at (0,0), color 6 at (0,2),(1,2),(2,0),(2,1),(2,2). Its tight bbox includes the key. Current `_analyze` crops the uncleared grid, so its test-only Python `rule_mirror` leaks the key into the rotated output. Canonical Racket correctly clears it first. This is a mirror defect, not an incorrect canonical Racket answer or a claimed sampled-query ambiguity.

`checks/80a3c4f25880/mirror/report.json` retains the input, both outputs, exact source/runtime hashes, and five protected executions (witness plus four official regressions). `mirror/proposed-mirror-fix.patch` copies the grid, clears (0,0), then crops; the probe tests the proposed module in memory and verifies all five answers. The approved production source remains untouched because native qualification requires approval on its current bytes. Applying that candidate requires owner source reapproval, a refreshed inventory and requalification before acceptance on the repaired bytes. The separate native prototype already uses the correct key-cleared crop.

Imported associated notes retain their original evidence/timestamps in `evidence/associated_notes.jsonl`. Runnable commands and public/private boundaries are in `workspace/parametric/README.md`.
