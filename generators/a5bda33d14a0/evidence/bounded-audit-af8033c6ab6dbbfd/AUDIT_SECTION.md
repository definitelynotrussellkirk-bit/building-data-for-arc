## a5bda33d14a0

**No issue found within bounded independent checks.** Audited generator v2.0.1,
SHA-256 `8095c7fca8bafafd63c796287fe7bba7ca1a85ea39b51542b868d913630192f5`. No audited source, reference authority or approval was changed.
The canonical Racket execution reports rule hash `eb3c0d7afaf9` and executed
rule-text SHA-256 `df988c659488b6100c933d7726d54bfa38d21ad77263db4d78a18610121a6a4b`; exact native outputs, input hashes,
generator hash and command are retained in `checks/audit/a5bda33d14a0/racket.json`.

**Concrete risks checked.** I inspected exact-control feasibility at dense 4×4
boundaries, palette/count compatibility, malformed scalar handling, preservation
of sources and interior zeros, and whether the repaired schedule still teaches
the all-source perimeter against its actual declared rivals. The compact
reproducer is `checks/audit/a5bda33d14a0/probe.py`; execution records are in
`checks/audit/a5bda33d14a0/commands.json`.

The probe generated **64 cases, 38 unique input grids**: 48 default draws from
seeds 0–3, indices 0–3, and easy/medium/hard, plus 16 exact-boundary draws from
seeds 100–115, index `(seed-100) % 4`, difficulty cycling easy/medium/hard.
Boundary requests exhaust dimensions (4,4), (4,18), (18,4), (18,18), cell counts
3 and 12, and total-color counts 2 and min(9, n_cells+1). All 64 were deterministic,
passed the selected self_check, and matched every requested measured control.
Eight targeted malformed/contradictory calls were rejected, including boolean
seed/index/dimension, negative index, unsupported numeric difficulty, dimension
19, unknown axis and n_cells=3/n_distinct_colors=9; the last rejection names both
incompatible axes. Exact seed/request/observed values are in
`checks/audit/a5bda33d14a0/cases.json`, with full inputs in `inputs.json` beside it.

Supported `arcpuzzles apply --check-generator-domain` executed canonical Racket
on all 64 cases: **64/64 outputs matched an independent pixel-based global-box
perimeter implementation, zero execution errors or domain-check failures**.
The declared canonical shortcut `first_three` fits all **5/5 canonical labeled
pairs**, as checked directly; on these 64 generated cases it matches 32/64.
The other actually declared lesson competitors match row_endpoints 13/64,
filled_box 0/64, overwrite_border 0/64, and canvas_border 2/64. These are explicit
rival counts, not an estimate of model accuracy.

**Lesson policy and verdicts.** Three demonstrations plus one query are formed
from consecutive default indices 0–3; production uses the fourth pair as query.
Across seeds 0–3 and three bands, **12/12 production lessons** had no declared
rival fitting every demonstration while disagreeing on the query. Preserving
order of the other three demonstrations and holding out each of the four pairs
also passed **48/48 query rotations**, zero ambiguities. These windows reuse the
48 default case positions and do not represent 48 additional unique inputs.
`checks/audit/a5bda33d14a0/assessment.json` retains every query case and its rival
ambiguity list, exact source/rule hashes, and all denominators.

**Limits and domain.** These finite, small-seed checks do not prove absence of
other shortcuts, identifiability for undeclared rivals, behavior at all seeds or
indices, every valid override tuple, or arbitrary lesson assembly. The current
notes explicitly reserve lesson guarantees for default generation, so exact
boundary cases were checked for input/label correctness rather than being
silently promoted to an override-level teaching guarantee. No reproduced bug,
suspected shortcut needing a finding, or new domain question arose in this audit.
This is findings-only evidence; it does not approve the generator for training.
