# Probe diagnostics

The first probe attempt compared the ticket's pinned rule hash
`7be9f4d727bc` with the selected `target_code` after whitespace-only
normalization. That selected source contains comments and therefore normalizes
to `7e8a56d872dc`. The archival `raw_code` and the comment-stripped selected
source both normalize to the pinned `7be9f4d727bc`; they are behaviorally the
same rule. The retained result records both source hashes and uses the pinned
archival executable text.

The next attempt used the shared `puzzle_generators.rule_wrap.wrap_rule` helper.
In this sparse review checkout, that helper imports
`scripts.comment_solutions`, but the `scripts` package is absent, causing
`ModuleNotFoundError` before Racket execution. The final bounded probe reuses
`rule_wrap.strip_line_comments` and `strip_rule_wrapper`, asserts this pinned
rule needs neither dictionary nor `for/` rewriting, and adds the one required
`(lambda (g) ...)` wrapper. The real bundled Racket runtime then executed the
witness successfully.

These were probe-tooling/provenance diagnostics, not failures of the peer rule.
