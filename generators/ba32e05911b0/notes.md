# Working notes: ba32e05911b0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/ba32e05911b0/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current parametric direction family

`workspace/parametric/` proposes right (byte-exact canonical) and left (reflect
input/output around the same program), with matched input draws across settings.
Two constructive lessons cover multiple markers, repeated rolls, blocked stops,
edge stops and top exits; ordinary lessons use three demonstrations, with 2–6
supported independently of the four hidden queries. Queries include a 14×14
minimum and a 30×30 six-roll, dense-distractor stress scene.

Causal state is the first reached ledge's exit column, which selects the next
ledge/termination. `verify.py` retains a protected-Racket wrong-column witness
and one-query public views. Distractor placement protects read gaps/check strips
as well as painted cells: merely protecting changed cells can turn a blocked
ledge into an edge stop. Eleven finite shortcut families are rejected by visible
demos; no claim of universal identifiability or training benefit.

Canonical generator/rule and unresolved inherited lesson audits remain unchanged.
The new-family teaching repair does not clear the canonical seed-10 ambiguity.
The original test suite is portable now; archival source comparisons normalize
whitespace only, while the selected default-program test remains byte-exact.
Owner must integrate, qualify and accept exact source before native use.

Final self-review repair: the first demo now witnesses six rolls on 28×30,
refuting caps 1–5 before the 30×30 query. The initially passing seven-rival
check missed a two-roll cap; its failing depth test and Racket-backed before/after
case are retained. Demo count remains two at the minimum.

## Current within-setting sampler diversity

The same two accepted right/left programs now use a seed-selected mixture of the original six-roll curriculum and the independent multi-marker/four-roll curriculum. Branch choice is independent of direction and requested counts. Both original sampler modules and rule bytes are preserved; a thin wrapper supplies 1–4 query prefixes. This broadens each setting without claiming additional rule settings. See `evidence/owner-sampler-reconciliation/current.json` and current native acceptance. Existing production teaching findings remain unresolved; no training activation is implied.
