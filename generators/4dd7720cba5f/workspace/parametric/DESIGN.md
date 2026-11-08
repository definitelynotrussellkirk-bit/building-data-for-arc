# Destination-scope parameter design

## Intent

Add a runnable, task-local, unapproved episode-level rule variant for
`4dd7720cba5f` without changing the approved production generator or canonical
Racket authority. The prototype should turn an existing canonical-fitting
shortcut into an explicit, teachable nearby rule.

## Parameter

- Name: `destination_scope`
- Allowed values: `all_tiles`, `empty_tiles_only`
- Canonical/default: `all_tiles`
- Fixed once per episode from the deterministic episode seed.

Both settings parse zero-separated framed tiles, group tiles by frame color, and
compute the union of same-color motif offsets. `all_tiles` writes that union into
every same-color tile and is byte-for-byte the canonical rule.
`empty_tiles_only` writes the union only into same-color tiles whose interior was
empty in the input; partially occupied source tiles remain partial.

## Teaching domain

Every retained pair uses one of the production generator's three multi-source
union profiles. Each profile has two partial source tiles for one repeated color,
so the two settings disagree on the same lawful input. Three demonstrations and
four distinct queries are generated independently; all seven inputs are unique.
The demonstrations alone must leave exactly one parameter setting consistent,
and every query must change under the rival setting.

## Evidence boundary

The CLI materializes exact Racket for both settings, executes every selected and
rival prediction through the bundled protected bridge, checks Python parity, and
writes private evidence plus opaque public challenges. Public files contain only
demonstration input/output pairs and query inputs; IDs are SHA-256 hashes of the
exact visible bytes. This is a proposed prototype, not production approval or
training admission.

## Non-goals

- No edits to `generator.py`, canonical data, approval records, or shared runtime.
- No claim that two parameter values exhaust all plausible rules.
- No production parametric API or corpus-wide distribution change.

## Approaches considered

1. **Destination scope (`all_tiles` vs `empty_tiles_only`) — selected.** It keeps
   the entire canonical parsing and union computation and varies only the target
   set. Existing multi-source profiles make it directly observable.
2. **Aggregation operator (`union` vs `intersection`).** Meaningful, but it adds
   cell erasure and changes more of the output semantics than needed.
3. **First-source vs union.** Too close to an ordering shortcut and less stable
   as a coherent episode rule.
