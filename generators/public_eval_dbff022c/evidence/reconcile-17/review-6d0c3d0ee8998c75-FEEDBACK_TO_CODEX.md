# F1: Biggest avoidable friction: strict Racket form validation runs too late

Run `strict_programs` over every retained `.rkt` source in the task-local focused suite and as the adapter's first smoke check. Protected execution can otherwise conceal a trailing extra form until the final authoring preflight, forcing evidence regeneration after semantics already look green.

# F2: Biggest avoidable friction: copied-runtime tests lack one portable data/runtime root helper

Expose a public helper that resolves the staged `shared/data/raw` and `shared/runtime` roots without requiring the canonical-ledger layout. Both assigned homes needed equivalent custom search code because the copied task-test runtime intentionally omits the full repository root expected by `reviewer_support.find_root`.
