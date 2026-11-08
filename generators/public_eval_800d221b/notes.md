# Public parent 800d221b — authoring plan and current decisions

Build the exact general two-stage network vote as a new Racket reference. Infer
background and the connected wiring network geometrically; remove the solid 3x3
hub to recover terminal regions. Each terminal's non-wire majority colors its
wires. The central pixel takes the majority of the terminal values counted once
per wire contact with the hub. Keep the hub's remaining eight pixels unchanged.
The complementary `aggregation=chambers` setting counts each terminal once.
The two settings must use matched inputs; 2–6 demonstrations and 1–4 query prefixes,
with a private four-query bank, randomized sequential presentation and 30x30 stress.

Implementation sequence: (1) failing original-label and hand-counted vote tests;
(2) general Python mirror plus protected Racket reference and variant;
(3) native adapter, synthetic topology sampler and count/privacy regressions;
(4) bounded finite-rival self-review, authoring preflight, source-bound causal
counterfactual and fresh replay; (5) document exact limitations and package delta.

Alternatives considered: use global raw-pixel majorities (refuted by the official
test); count chambers (refuted by train 2, retained only as the taught alternative);
count independent wire contacts (fits the four original labeled pairs in the
exploratory calculation). This is a newly authored rule, not owner authority.
Work is in a fresh extracted sandbox; no git repository or shared checkout exists.
No external registration, source approval, acceptance or training admission is made.

## Final implemented state

The canonical Racket reference reproduces all three original demonstrations and
the supplied 30x30 test answer. Background is the modal color; wire color is the
monochrome component of largest bounding-box area; its unique solid 3x3 hub is
removed to identify terminals. This geometric rule does not assume the wire is
the second most frequent color. Lower-color tie resolution is an authored
extension; all generated local and global votes are strict.

The sampler constructs three- and five-terminal networks, one to three wire
contacts per terminal, loops, diverse dimensions/pigment palettes, and D4
orientations. The 30x30 query has five terminals, seven contacts, substantial
content and contacts with all four canvas edges. Three- and five-terminal
networks are the admitted generated grammar; arbitrary overlapping wires or
multiple hubs are not claimed. The source reference handles the original
four-terminal test and its one-chamber tie by the documented lower-color rule.

A real two-demo ambiguity was reproduced before repair: choosing the lower
pigment color at the hub fit both demonstrations but changed later queries.
The retained pre-repair counterexample contains three protected-Racket labels
and exact old source hashes. Other spatial/size shortcuts also survived chance
prefixes. Version 1.0.1 constructively contrasts palette order, terminal order,
chamber area and raw pigment totals in its first two demonstrations. Ordering
is based on actual wire-connected components, not only box coordinates.

Final checks: 26 focused tests; 64-seed audit over both settings and all demo
counts 2..6 (640 nested lesson views, 5,120 pair exposures, 640 input draws),
13 finite rival rules with zero query-changing survivors; protected authoring
preflight; 20 additional max-demo labels; causal construction and a separate
live replay (24 audit executions total); 16 validated single-query public files.
Source-bound `preflight-final` and `audit-final` checks are authoritative for
this authoring return. Earlier preflight/test receipts are superseded.

The witness replaces locally recovered majorities by local minorities before
propagation/aggregation. On the retained qualified 30x30 alternate-setting
query this changes 219 cells. Full runtime identity is preserved alongside the
required witness marker. Source hashes are rechecked by the audit tool before
and after use. Finite rivals do not prove universal identifiability or learning
gain. Final review is an author self-review; no independent reviewer is available.

Reproduce from the packet outer root:
`python3 review.py run python3 -m pytest --import-mode=importlib -q generators/public_eval_800d221b/tests`
then public-creation preflight into a new directory and task-local `audit.py`
with that `--preflight`, a new `--out` and `--seeds 64`.
Owner registration, native qualification, exact-source acceptance and any
training admission remain pending. No shared authority was modified.
