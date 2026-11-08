# Command and sequential collision-aware L routing

This is a proposed native family. The selected production generator and its
unresolved count/command teaching audit retain their original source binding.
Native owner qualification and exact-source acceptance remain separate steps.

## Rule

`{"routing_mode":"command"}` returns the exact selected canonical Racket
program. Read the command at `(0,0)`; process nonzero colors in first row-major
appearance order, using marker locations in the original input. Connect colors
appearing exactly twice. Command 1 uses a horizontal then vertical L; command 2
uses a vertical then horizontal L. Later paths overwrite earlier cells.

`{"routing_mode":"avoid_painted"}` processes the same original pairs in the
same order. For each pair, form both distinct-cell L paths and count foreign
nonzero cells on each path in the **current accumulated canvas**. Choose the
lower-cost path; ties obey the original corner command. Paint that route before
evaluating the next pair. Earlier painted paths therefore supply state that
later routing decisions consume. Reading the original canvas instead is a
different rule, demonstrated by protected counterfactual evidence.

Colors occurring once or at least three times are not routed. Their original
cells remain unless a chosen path overwrites them. Original endpoints and the
command are read from the original input even if earlier painting covers them.
Including or excluding the two own endpoint cells contributes the same cost to
both candidate paths. Maximizing empty cells is equivalent to minimizing
occupied cells because both L paths have equal distinct-cell length; these are
not counted as separate rival mechanisms.

## API and grammar

`program(settings)` gives full `(rule! ...)` text. `generate(seed, settings,
demos=3, queries=4)` returns private complete `train`, `test`, and
`program_solution`. `mirror` is a Python claim implementation; `analyze` exposes
the route costs, chosen paths and intermediate canvases for diagnosis.

Seeds are exact integers in `0..2**63-1`; demonstrations are independently
`2..6` and queries `1..4`. Bool/float coercions and unknown settings are rejected.
Semantic inputs are rectangular exact-integer ARC grids, each dimension `1..30`,
with a unique command color 1 or 2 at `(0,0)`. Other color multiplicities are
unrestricted. The sampler constructs richer scenes from `7×9` through `30×30`.
No rotation or reflection equivariance is claimed: row-major endpoints and
processing order are part of the rule.

The two core demonstrations cover the declared independent rival bank under
both settings. They are selected from at most 512 deterministic constructed
candidates; failure is explicit rather than a silently short episode. Selection
reads demonstration inputs and labels only. Command, count profile and primary
template orientation vary independently. Additional demonstrations and queries
use separate local RNG streams; returned arrays are fresh. Input sampling is
matched across settings, and smaller count requests are stable prefixes.

Four shuffled query profiles are `7×9`, `15×19`, `24×28`, and `30×30`. Reserved
opposite-corner endpoints force full-span route geometry; the two largest
profiles have at least two original markers per quadrant. Large examples use
the whole coordinate range, including boundaries, intersecting routes,
aligned pairs and nonpair distractors. This is a sparse-marker path task;
stress is measured by route spans and painted content rather than dense input
textures.

## Reproduce

From the packet's outer folder, with its ready interpreter:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest generators/d476983a3d6c/tests -q
WORK/.venv/bin/python review.py run python3 generators/d476983a3d6c/workspace/parametric/audit.py --seeds 0,1,2,7,8,17,31,97,255 --demos 2,3,4,5,6 --out ../checks/d476983a3d6c/semantic-audit-replay.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify d476983a3d6c --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/d476983a3d6c/qualification --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/d476983a3d6c/qualification/qualification.json --out ../checks/d476983a3d6c/preview
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/d476983a3d6c/preview
```

Qualification destinations must be new. The native source inventory must be
current before qualification; the return includes it and exact command receipts.
Give a consumer only one selected `preview/public/<hash>.json` at a time. Keep
future queries, source programs, settings, seeds and answers controller-side.
`checks/projection_edges.py` exercises the existing exporter against private
mutations and verifies rejection of injected answers or extra public files.

`rivals.py` implements an independent oracle and executable Python/Racket
alternatives. `audit.py` checks bounded lesson coverage, actual protected labels,
canonical identity, fresh/count-prefix behavior and substantive large scenes.
Finite rival and seed checks establish only their recorded scope; they do not
prove universal inference, all-seed sampling success or measured training gains.

The independent minimum-demo review exposed seven further teaching predicates
and a seed-8 search-bound failure. Those exact predicates now join the demo
cover. Seed 8 requires candidate 335, beyond the previous 256-candidate cap; the
new bounded cap preserves two demonstrations and all earlier successful
candidate prefixes. The return retains the original failures and final replay.
