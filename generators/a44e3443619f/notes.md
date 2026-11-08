# Working notes: a44e3443619f

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-66dd25ed89a1c6df — exact sampler and cascade family

### D1 — Repair the base sampler at construction time

The imported generator claimed exactly two or three isolated red X patterns, but its retry placement could combine corners from separate attempts into accidental extra centres. The retained red regression shows default seed 1 producing four effective centres; the broader probe also found one and five. Rejection after generation would leave count semantics fragile, so the repair enumerates pairwise-separated layouts once per `(height, width, count)`, paints each candidate, and retains only layouts whose computed centre set exactly equals the intended set. Strict `n_quads` overrides reject booleans, floats, and values outside `{2,3}`.

### D2 — Preserve the canonical default and add a genuinely causal second pass

`completion_depth=single` returns the selected canonical program byte-for-byte. `completion_depth=cascade` first runs that exact pass, preserving its full output as the intermediate, then recolours a red cell green when all four immediate diagonal neighbours in the intermediate are blue. Inputs contain only 0/2, so skipping Stage A leaves no eligible green targets. Complete 5×5 red lattices create four first-pass centres around a second-pass target; an eight-cell near miss creates only three and must not fire.

### D3 — Make the minimum lesson rule-identifying without setting leakage

Input sampling is identical for `single` and `cascade`. The two-demo prefix includes one- and two-target scenes at the same 13×17 dimensions, plus incomplete motifs, standalone Xs, and partial Xs. It rejects skip-A, all-blue-to-green, fixed-centre, first-only, last-only, and recolour-all-red shortcuts before any query is exposed. Four distinct queries include thin-wide, thin-tall, larger mixed, and substantive 30×30 boundary-contact scenes. Demonstration counts 2–6 are prefix-stable and query count is exactly four.

### D4 — Retain an executable adversarial tool for later agents

`workspace/parametric/adversarial_audit.py` checks setting-independent inputs, minimum lessons, named shortcuts, crossed intermediate/nuisance controls, exact-count base sampling, malformed-certificate rejection, Python/Racket parity, 30×30 stress, and current source hashes. The final protected run covered 96 episodes, 736 pairs, 1,096 Racket evaluations, 576 base draws, and six negative certificate cases; a 128-seed no-Racket sweep covered 768 episodes and 5,888 pairs. These are bounded checks, not universal identifiability proof.

### D5 — Preserve the owner gate

The source-bound authoring preflight, protected-Racket causal witness, public projection, first-turn invariance, and task-local tests pass on the retained source bytes. This review does not edit approval state, grant native acceptance, or admit training data. The next useful action is owner review of the exact patch followed by fresh native qualification and acceptance.
