# Forward and reverse symbol traversal

This opt-in family keeps the calibrated five-symbol path puzzle. The parameter
`read_order` is fixed for an episode: `forward` visits decoded symbols from left
to right; `reverse` visits them from right to left. Reversing traversal does not
reflect symbols, swap the meaning of bends, or reverse the output image.
`forward` returns the exact selected canonical Racket source from `canonical.rkt`.
The production generator and canonical authority are unchanged.

## Teaching design

`adapter.generate(seed, settings, demos, queries)` supports **2–6 demonstrations**
and **1–4 queries**, independently. Use three demonstrations and four queries for
ordinary training. The first two demonstrations use the same instruction counts
but different orders and paths, so counts or the final endpoint do not determine
the answer. Together they expose all four upper-row bend patterns: `00`, `02`,
`20`, and `22`. The first also includes a one-column symbol with an empty top cell,
showing that width takes precedence over upper-left occupancy.

This paired selection repairs a demonstrated two-demo ambiguity in the first
draft: the diagonal `00`/`22` examples alone could admit a same-polarity
upper-right decoder or an “any upper zero means left” decoder. The retained
pre-fix witness and failing/passing regressions are under the packet's
`checks/f0f2806877da/`. The broader canonical sampler still has its earlier
top-right shortcut finding; this adapter does not clear that production audit.

The sampler uses the reviewed exhaustive encoding bank, without rejection loops.
It selects all six demonstration roles and four query roles before taking the
requested prefixes. Inputs and their order are matched across parameter settings
and independent of requested counts. Every demo/query input has a different
instruction sequence. The first two queries contain three left bends and three
right bends respectively; they exercise columns 0 and 6. All traces reach row 7.

## Sequential dependency and real size limits

Trace a prefix of the decoded instruction sequence to obtain its cursor
`(row, column)`. The next instruction is painted at that cursor, then updates it
again. An instruction's absolute output coordinates therefore require the
preceding prefix result. The native causal witness replaces the carried column
with the initial column 3 and verifies that the final output changes.

The admitted grammar is exactly **2×12 inputs → 8×7 outputs**: two straight
symbols and three bends, with four single-column separators and at least twelve
red input cells. Its row advance is fixed at seven; its lateral displacement is
at most three. A substantive 30×30 case is not lawful in this family. Adding
ignored rows, clipping extra instructions, or padding the fixed canvas would
not test a larger reasoning problem. Both edges and the complete five-step
trace are exercised instead.

## Reproduce the audit

From the outer review packet folder, using its prepared Python environment:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/f0f2806877da/workspace/parametric/audit.py \
  --out ../checks/f0f2806877da/fresh-teaching-audit
```

Choose a new destination each time. `audit.py` executes the chosen rule and
twelve explicit rivals in protected Racket, checks demonstrations before query
answers, records minimal distinguishing examples, tests count/sampling boundaries,
and writes exact visible-byte/hash-named examples. Rival execution errors fail
the audit; they never count as eliminated alternatives. The extra sampler census
is explicitly Python-only, separate from the executed Racket cases.

`public/` contains four-query masked controller records. The model should receive
only the current file from `turns/`, or `adapter.public_turn(episode, index)`, which
contains the demonstrations and one query input. The first turn is byte-identical
to a single-query episode. Future inputs, query count, settings, programs, answers,
and seeds are absent. `*.private.json` files are controller/authoring data.

## Native handoff

`promotion.json` declares the two settings and count limits. The native inventory
at `evidence/manifest.json` binds the current adapter, canonical resource, audit,
tests and task-local evidence. The reviewer return carries native qualification
and execution receipts plus a separately replayed causal witness. Qualification
is finite evidence, not universal rule uniqueness or measured learning benefit.

After integration, the owner must run fresh native qualification and acceptance
on the exact live source. This reviewer adapter is not an acceptance record and
does not admit training data. Source changes require a fresh inventory and
qualification. The task-local tests also repair portable canonical-data loading
and compare whitespace-normalized base authority text while retaining the exact
canonical program/hash checks.
