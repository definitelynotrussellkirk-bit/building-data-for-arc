# Final-source visible-example solve

This is a concise work log, not a captured token-level conversation. Earlier rule exposure is yes: I worked on the repair and solved an earlier source. During this final-source solve I consulted only the prepared public examples, my own Python, and visible feedback; no generator, Racket source, private query labels, or earlier reference solution was opened.

## Observation and hypothesis

All three visible pairs preserve shape and original foreground. Original zeros become 2 inside enclosed spaces and 3 in empty space connected to an edge. Examples 0 and 2 include stepped interiors. The hypothesis uses horizontal and vertical connectivity: a diagonal foreground seal still encloses a zero pocket. I flood original zeros from every edge with four neighbors, preserve nonzero values, and color reachable zeros 3 and remaining zeros 2. Varying foreground colors support treating every nonzero value alike.

## One algorithm and recording retries

A stack-based edge flood matched 3/3 visible examples on the first final-source recording. Stale files from source 2cec appeared after directory rotation, so check numbered that attempt 0002 and finish refused to overwrite old frozen notes. The mixed artifacts are retained under checks/prior-solve/source-2b777-recording-failure. The original complete earlier solve is retained under checks/prior-solve/source-2cec2f6f. The cause of stale restoration across tool calls is unresolved; it is not a solver failure.

An atomic directory rotation and preparation verified a clean directory, but a subsequent separate tool call again observed stale attempts. That second state is retained under checks/prior-solve/recording-retry-before-atomic. I then performed archive, prepare, solution writing, two actual checks, and finish within one subprocess invocation. The second check intentionally repeats the same algorithm as a recording verification; it is not a new hypothesis or an independent discovery. Every retained current attempt is bound to the same final generator and public instance. No failed hypothesis or intentional negative solve was fabricated.

## Outcome and limits

Both actual checks match all 3 visible examples and execute on both masked queries. I stop because the visible hypothesis is consistent and execution is complete. Hidden correctness remains withheld. Earlier exposure prevents calling this an independent blind discovery.
