# Shared-tool request reproduction report

**Ticket:** `ticket-33570482635e6a19`  
**Consumer:** `existing_tool_request_disposition`  
**Status:** completed; proposed disposition `retain_open_accepted`

## Source binding

The exact accepted request `review-803b0250fdb9ec1a:v0001:F1` matches canonical
SHA-256 `efbf2e2a274ba9aa4f4d056908d6a21130321ff3a0e7a001abd74dba2ef31245`.
Its source, anchor generator, and retained asset manifest also match their pins:

- request source: `6c85823f8430070c462f9834d4b48778ffb8e1d58021ca748e366eefbc58d642`
- generator: `d222d3cf44d694716979214022e8f461ee2995df4a635c868b291e9a3a82178a`
- asset manifest: `5b438e8675224732d54480fea5de0bfda79fa9a3b6b3154965c53c2d472732fa`
- catalog rule hash: `bb6a3cb8ba31`

All four retained files match their manifest byte counts and hashes.

## Reproduced witnesses

For `67e9e17efb62`, all three demonstrations and all 12 canonical pairs fit the
left/right-position shortcut, while the retained right-anchored query differs;
the protected-Racket confirmation agrees with the intended output. For
`1a21a4a82b48`, all three demonstrations fit the size/tie-color shortcut, while
the retained query differs in two cells; its protected-Racket confirmation also
agrees with the intended output.

These establish two concrete ambiguity witnesses. They do not establish their
frequency or validate arbitrary nuisance interventions.

## Disposition

Keep the request **accepted and open**. The retained proposal manifest explicitly
says `runtime_approved=false`, and the selected `shared/tools/lesson_census.py`
does not contain the requested opt-in nuisance-axis / safe-paired-override
interface. Therefore it would be false to mark the request fulfilled or closed.

A future implementation should require task-declared lawful interventions,
canonical Racket labels on both sides, source/rule/input-hash caching, advisory
status for auto-discovered axes, and emission of a concrete surviving
rival/query pair. No shared tool, generator, admission rule, approval, or audit
disposition changed in this return.

Full source-bound checks and limitations are in `result.json`; the exact probe
command is in `command.json`.
