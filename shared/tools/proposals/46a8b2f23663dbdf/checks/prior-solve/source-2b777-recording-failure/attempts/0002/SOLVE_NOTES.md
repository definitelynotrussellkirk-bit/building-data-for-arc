# Final-source visible-example solve

This is a concise work log, not a captured token-level conversation. I saw the intended rule during earlier repair work and previously solved an earlier source version. This is therefore an exposed solve. During this fresh solve I opened only the newly prepared public presentation and challenge, and authored the Python solution without importing the generator, reference code, private labels, or earlier solution files.

## Observation and hypothesis

The three displayed pairs preserve shape and every original foreground cell. Their zero cells become either 2 or 3. Color 3 reaches the edge and follows connected empty passages; color 2 occupies the enclosed spaces, including the stepped interior in examples 0 and 2. The relevant connectivity is horizontal and vertical: diagonal contacts between foreground segments still seal a zero pocket.

The hypothesis is to flood the original zero cells from every edge using four neighbors, recolor those reachable cells 3, and recolor every remaining original zero cell 2. Preserve every original nonzero value. The foreground colors vary, so the algorithm treats all nonzero colors alike.

## Implementation and checks

The single authored revision uses an explicit stack and a set of edge-reachable coordinates. It never mutates the input. I will compare it with all three visible outputs and execute it on both masked queries using the supported check command. No extra failed revisions or intentional negatives have been fabricated.

## Limits

The visible examples support this hypothesis, but prior exposure prevents treating this as an independent blind discovery. Query correctness remains withheld; successful execution is not a hidden-label accuracy claim.
