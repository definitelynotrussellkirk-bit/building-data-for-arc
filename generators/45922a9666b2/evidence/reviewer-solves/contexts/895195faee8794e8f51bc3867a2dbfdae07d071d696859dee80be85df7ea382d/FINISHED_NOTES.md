# Fresh final-source visible-example solve

Earlier rule exposure: **yes**. I reviewed this task's rule and generator during
shared repair work before this solve phase. This is an exposed postrepair solve,
not an independent blind discovery. During this phase I inspected only official
public preparation/challenge data and my own experiments. I did not reopen
generator/reference source, private labels, earlier solve notes, prototype code
or audit sources. This is authored agent prose, not a captured token-level trace.

The clean episode is bound to final generator SHA-256
`901b35aa8aaf523990096af8ecfae1e4dac10f9fdfa84b21557c7179e8b52fac`
and instance
`571df09044b43d5825cf5e001c976e493e13c8e77a2375c3028d68eb6243c882`.
Three training pairs have dimensions 13x13, 13x14 and 12x13. Two query inputs
have dimensions 13x15 and 13x13; their outputs remain unknown.

Visible outputs preserve gray 5 and add red 2 in routes from bottom-row red
sources. A route prefers moving upward. When gray blocks the cell above, it
steps right if in bounds and nongray, then prefers up again. It stops at the
top or when neither move is possible. I wrote this coordinate-independent
solver directly: record initial bottom-row sources, consult immutable input
obstacles, and paint a fresh output copy. Each move decreases row or increases
column, so execution terminates. No profile lookup or deliberate negative is
included. I will compare all visible outputs and execute both query inputs.

Preparation required preserving mixed prior-source artifacts, verifying archive
hashes, and explicitly removing the old solve directory before reprepare. The
new preparation generated a new instance on the correct final source. An
overstrict old-instance assertion halted the first reset runner before any
check; the parent accepted the new instance. Earlier real checks, preparation
and finish errors are preserved in separate checks directories. They are not
invented wrong-rule attempts and are not counted as clean-episode attempts.

## Result

The single clean-episode official attempt completed with **3/3 visible examples
passing**. Both query inputs executed. Private query correctness stays
**unknown**. No solution revision was needed; I stopped after matching every
provided output and completing execution.
