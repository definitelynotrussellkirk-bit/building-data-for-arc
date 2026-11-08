# Working notes: 00f37833e26f

## Current decision

Built a native matched-input family with `residual_policy = all | largest_component`.
`all` is the byte-exact canonical normalized source-minus-mask crop. The alternative
uses that same subtraction as Stage A, then selects the unique largest connected
residual component as Stage B.

## Review finding and repair

A 256-seed extension found seed 100 let a `first_component` shortcut fit both
mandatory demonstrations. Root cause: independent quarter-turns could place the
largest horizontal branch first in scan order twice. The first two demos now use
0° and 180° orientations (reflection still varies), keeping the largest component
interior in scan order. Seed 100 is retained as a regression. The post-fix
256-seed sweep passed 512 teaching cases and 256 separate 30×30 stress cases.

## Handoff

Reviewer-ready authoring evidence is under `checks/00f37833e26f/`; exact-source
owner qualification, acceptance, and any training admission remain pending.
Associated imported notes remain in `evidence/associated_notes.jsonl`.
