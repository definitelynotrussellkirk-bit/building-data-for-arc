# Random adversarial audits — pending full-packet draw

The two audit targets were not assigned in this recovery environment. The
original extracted workspace was lost after the file-service reset, and the
350 MB immutable upload could not be rematerialized through the 100 MB limit.
Inventing target headings or findings would break the assignment contract.

After applying the overlay to the exact packet, run once:

```bash
python3 review.py audit
```

Then add one exact `## TASK_ID` section per drawn target, keep those targets
finding-only, and retain source-bound reproduction files under
`WORK/checks/audit/TASK_ID/`. This `AUDIT.md` is therefore an explicit blocker,
not a completed audit or a claim of “No issue found.”
