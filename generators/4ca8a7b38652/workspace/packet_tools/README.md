# ARCpuzzles packet tools

These are local proposed tools for the issued packet. Python 3.10+, standard library only. The issued manifest, contracts, shared modules, and stock wrapper remain unchanged.

## Selective inspection and extraction

Run from this directory, replacing packet.zip with the original archive:

    python3 packet_zip.py inspect packet.zip
    python3 packet_zip.py plan packet.zip --prefix WORK/repo/src/arcpuzzles
    python3 packet_zip.py materialize packet.zip --prefix WORK/repo/src/arcpuzzles --out ./new-runtime
    python3 packet_zip.py verify packet.zip --prefix WORK/repo/src/arcpuzzles
    python3 packet_zip.py verify packet.zip --all > source-verification.json
    python3 packet_zip.py verify packet.zip --all --checkout ./new-runtime/checkout

The materialization destination must be new and its parent must exist. Exact --member and directory --prefix selectors are repeatable. --members-file accepts exact archive names, one per line; blank lines and lines beginning with # are ignored. Every missing member and empty prefix is an error. No selection is an error; --all must be explicit.

The original manifest and outer entry files are automatically preserved, byte for byte. Plan/materialize default to 10,000 files and 268,435,456 expanded bytes; --max-files and --max-bytes can change these budgets. Metadata, receipts, buffers, and filesystem overhead need additional space. These limits do not reserve resources.

Inspection/planning verify archive headers, canonical manifest structure, and the complete filename inventory; they explicitly report zero verified body hashes. Materialization streams and SHA-256-checks every selected body. OUT/receipt.json begins as running and becomes complete only after all selected files pass. It records the original packet ID, archive SHA-256, selected hashes/sizes, verified count, omitted count, and whether the entire original inventory was extracted. A failed/interrupted attempt can leave a partial checkout and must not be treated as complete. Existing output is never overwritten.

Verify reports missing local files as failures. The first 100 detailed failures are shown by default; failure_count and unlisted_failure_count report the complete totals. --failure-limit raises the detail limit. Selected-original-path verification does not inspect extra local files, execute task tests, or establish return/training validity.

Both tools reject unsafe archive paths/types, duplicates, symlinks, encrypted members, noncanonical manifests, and archive/manifest inventory differences. Materialization also rejects output symlink ancestors and selected case aliases. Publisher authentication requires an external trusted archive/manifest digest; an internally consistent ZIP alone does not authenticate its publisher.

Exit codes: 0 means the requested operation passed; 1 means verification or post-start materialization failed; 2 means usage, preflight, or input errors. JSON is written to stdout for results and stderr for preflight errors.

## Authentic startup and existing runtime closure

The stock review.py start generates a seed and verifies selected baseline sources before committing its pending-draw journal. Do not repeatedly run start on an incomplete checkout.

The official draw_main(packet_root, seed=seed) API accepts exactly 32 bytes. A constrained review can record one fresh seed outside assignment internals before inspecting its selection, use the unchanged official selector to identify sources, materialize those originals, and call the unchanged official API with that same seed. Preserve the seed and command record. Never reroll, fabricate a contract, or change the manifest/policy. packet_zip.py does not draw assignments.

Draw dependencies include the original entry files/manifest, review modules, runtime_files.json and authority_files.json, every selected repair task file, canonical puzzles.jsonl, mapped authority sources selected by official _base_paths, and the selected question JSON. All 53 arcpuzzles source files total only 708,279 expanded bytes in this packet and form a practical Python bootstrap. Vendor/runtime dependencies are needed for later checks, not for the draw itself.

Reuse the packet's existing review_replay._runtime_members function for post-draw runtime member lists. It already validates official runtime/authority mappings and selects the task/rule identity, source modules, catalogs, vendor runtime, and declared dependencies. These tools deliberately do not reimplement that mapping. Copying blind-source bytes does not authorize inspecting their contents before finishing the blind solve.

## Optional archive-backed packaging proposal

The stock build_full_return rejects every missing original repo file outside selected-task candidates. Runtime-only replay or full ZIP-body verification does not make the stock wrapper support sparse packaging.

package_sourcezip.py is an opt-in local proposal. Its copied builder differs from the pinned original only by an optional source_zip argument, a strict archive-backed source verifier branch, and an embedded verification receipt. The retained original module, origin.json, and review_full_return_sourcezip.patch make that change inspectable. Shared installed modules are not edited or monkeypatched.

After reviewing this proposal, an operator can run:

    python3 package_sourcezip.py /path/to/WORK --source-zip /path/to/original.zip --out /path/to/new-return.zip

Omitting --source-zip keeps the copied builder's original physical-inventory branch. With --source-zip, the verifier requires the exact original canonical manifest, validates the complete ZIP inventory, streams every original body against its manifest hash, checks every present protected original file against that same hash, rejects unsafe live paths and undeclared live repository files, and supplies only absent immutable originals from the verified archive. Selected-task candidate changes have already passed the unchanged stock baseline/scope rules. No omitted source is merely assumed unchanged.

The copied builder retains stock patch construction, artifact accounting, INTAKE derivation, evidence budgets, solve validation, and return validation. The entrypoint additionally runs the unchanged installed official validate_full_return and includes its complete result in the command's JSON output. The archive-backed verification receipt is included as checks/packet-source/archive-backed-verification.json in the return, so the resource-constrained provenance remains explicit.

This is new local functionality, not stock review.py package support. Review the diff and tests before use. A successful return validator result describes the return format and evidence bindings; it does not establish that puzzle checks passed or that generators are training-approved.

## Verification and resource limits

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s . -p 'test_*.py' -v

The synthetic tests exercise exact partial extraction, corruption, missing selections/files, traversal, symlinks, duplicates, budgets, canonical manifests, destination protection, archive-backed omissions, live drift, undeclared sources, and stock-validator compatibility. They do not read real generators or run puzzle code.

The issued ZIP has 105,426 file members and a 19,152,145-byte manifest. ZIP metadata and the parsed manifest remain resident even though file bodies are streamed; reserve hundreds of megabytes of memory. A metadata-only real-packet attempt was killed by SIGKILL while the shared 8 GiB cgroup had roughly 17 MiB headroom and recorded OOM kills. That attempt is not success evidence. See VALIDATION.json for actual executed checks; no full real-source verification or proposed real packaging is implied by synthetic passes.

Executed validation: all 28 synthetic tests passed, including the optional command's independent official-validator result. TEST-RESULTS.txt contains the full latest run. Shared integration remains pending.

Review follow-up: the optional verifier now rejects file symlinks before cache-path/suffix exclusion. The focused undeclared repo/shared/cache.pyc regression failed before the change (CACHE-SYMLINK-RED.txt) and passes in the full suite. The stock builder and its default branch were unchanged.
