# Independent review findings and repairs

The first implementation passed the original packet and 32 synthetic scenarios.
A separate read-only review identified two concrete malformed-ZIP cases. Both
were reproduced before the implementation changed; `red_review_tests.txt` retains
the five failing regression scenarios.

1. **Understated expanded length.** `ZipExtFile` clips output to the declared
   length before returning it. A member containing additional bytes could therefore
   match a manifest hash and CRC for only its declared prefix. The final verifier
   reads the complete STORED or DEFLATE extent independently, with bounded output
   chunks, exact expanded-length checks, DEFLATE end/trailing-data checks, and CRC
   verification. The regressions cover both source files and the manifest itself
   in both supported compression formats.
2. **Malformed UTF-8 filename.** A filename decoding exception could escape the
   JSON error boundary. The final verifier catches it as an `invalid_zip` failure.
   A fixture with invalid filename bytes and the UTF-8 flag exercises that path.

The final suite and original-packet run are recorded in `verification_runs.json`,
bound to the exact final verifier and test source hashes. Packet source files,
assignment state, manifest bytes, and the original packet archive were untouched.
