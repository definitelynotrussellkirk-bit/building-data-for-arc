# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Assigned audit reproducer

`audit_probe.py` regenerates the two assigned audit witnesses, runs deterministic
300-draw domain probes, and verifies the separate public `arcpuzzles apply`
receipts. It never modifies either audit target and does not import a private
Racket runner. See its module docstring for exact commands.
