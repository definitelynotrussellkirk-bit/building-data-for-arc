# Feedback to Codex

F1: Make native qualification and evidence-manifest refresh atomic. Qualification currently requires a current source inventory before execution, while its most useful receipts exist only afterward, forcing a guarded two-pass manifest replacement; add a `parametric qualify --refresh-manifest` mode that snapshots source first and appends receipt hashes without rebinding executable source.
