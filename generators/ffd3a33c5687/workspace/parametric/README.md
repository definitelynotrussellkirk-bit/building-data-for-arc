# Parametric mirror-priority family for `ffd3a33c5687`

This native adapter preserves the selected canonical program byte-for-byte as
`conflict_policy=left_priority`.  The alternate
`conflict_policy=guide_priority` keeps the same horizontal mirror-completion
family but makes conflict priority input-dependent.

Each input has one center-marked guide row (color 8) and one off-center guide
signal (color 7).  Step A locates that row and infers `left` or `right`; Step B
uses the inferred side to choose the winning occupied color in every mirror
conflict.  Singletons are still completed to their mirror mates.  A right-side
guide therefore distinguishes the alternate from the canonical left-priority
rule without changing the input grammar between settings.

## Contract

- `program(settings)` accepts exactly `left_priority` or `guide_priority`.
- `generate(seed, settings, demos, queries)` supports 2–6 independent
  demonstrations and exactly four distinct queries.
- Inputs are deterministic and identical across settings for matched requests.
- The first two demonstrations use opposite guide sides, so either declared
  setting is identifiable from demonstration labels alone.
- The four query shapes are 8×13, 15×16, 21×29, and a substantive 30×30
  boundary case.

`audit.py` is a reusable finite teaching/privacy audit.  It challenges visible
demonstrations with fixed-side, opposite-guide, preserve-conflict,
numeric-order, singleton-majority, and first-conflict shortcut rules, checks all
four query rotations, and verifies the first-turn public projection.  Its scope
is finite and does not prove uniqueness against every imaginable program.

The native inventory and qualification remain reviewer evidence only.  The
owner must integrate the exact bytes, replay qualification and the causal
witness, and explicitly accept them before any downstream use.
