# Visible-example solve notes

- Task ID: `9900de625ddd`.
- Prepared source SHA supplied with task: `bbfd833e74437d412e40717fa44316df517f66a2ac8fb1f6e7a7dfd2cec26427`.
- Exposure declaration: `earlier-exposure=yes` is conservative session-level reporting: root saw sources during repair, but I am a fresh agent given no semantic explanation. `reference-consulted=no`: I consulted no reference or source material during this solve.
- Task content read: only `solve/challenge.json`, containing three labeled examples and two unlabeled inputs. No prepare command was rerun.

## Hypothesis and visible probes

- The transformation keeps a nonzero cell exactly when every cell in its complete 3-by-3 neighborhood has the same color, replacing all other cells with zero. This is a one-step, per-color square erosion with positions and dimensions preserved.
- A Python probe evaluated three candidate rules against the visible labels. Same-color 3-by-3 neighborhoods matched all three examples with zero differing cells.
- A four-neighbor same-color rule differed by one cell in example 1 and one cell in example 3. A 3-by-3 rule requiring only nonzero neighbors differed by two cells in example 1. These were in-memory candidate probes; no rival was submitted as a solution.
- Example 3's missing corner makes diagonal agreement necessary. Example 1's mixed-color squares make color agreement necessary.

## Submitted revision

- Revision 1 implements the same-color 3-by-3 rule directly. Boundary cells cannot have a complete neighborhood and are erased. No color values, object sizes, or query-specific coordinates are hard-coded.
- Checker revision 1 completed successfully with `visible_passed=3`, `visible_total=3`, `reported_label=unknown`. Exactly one genuine solution revision and one `--intent solve` check were submitted; there were no diagnostic or teaching-negative checker attempts.
- Stopping reason: one general local rule matches all three visible labels, and the visible examples distinguish it from the tested four-neighbor and nonzero-only alternatives. No unresolved visible failure warrants another solution revision.
- Masked-query correctness is unavailable and is not inferred from execution success. The finite visible examples do not prove the rule on all unseen inputs.
