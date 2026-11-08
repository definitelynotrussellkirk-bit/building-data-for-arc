# Tool-request reproduction — ticket-01c915d5ead476c8

Status: completed, source-bound.

The single targeted probe authenticated the complete retained chain for
`review-597e2d03726aa4c9:v0001:F3`: request source, canonical compact request
row, proposal manifest, current `cfadc43e5098` generator and retained allocation
audit all match their pinned SHA-256 values (15/15 checks).

The retained audit is internally coherent and remains explicitly
`runtime_approved=false`. Its original deterministic sample cannot be
independently recomputed from this bounded packet: the audit population is 3,941,
while the packet contains 300 generators and only one of the three sampled IDs.

Proposed disposition: retain it as an authenticated, source-bound proposal for
the existing-tool-request consumer. Do not install a shared allocation policy or
mark the proposal runtime-approved. Require a fresh bounded A/B test before any
policy selection.

Machine-readable evidence: `result.json`. Reusable probe: `reproduce.py`.
