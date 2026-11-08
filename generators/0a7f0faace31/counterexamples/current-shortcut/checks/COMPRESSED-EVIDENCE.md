# Restore the complete census reports

The two large JSON reports are stored losslessly as `.json.gz`. The failed
intermediate census and the successful final census are both complete.
`COMPRESSED-EVIDENCE.json` maps every original path, size, and SHA-256 to its
compressed member; byte-for-byte round trips were verified before removing
uncompressed duplicates. Original report bytes and their embedded hashes are unchanged inside gzip.
Small JSON pointer files at the original paths identify the compressed reports;
the pointers are explicitly not census results. Their hashes are also in the mapping.

After extracting the return ZIP, first unpack its ordinary evidence bundle:

```sh
tar -xzf EVIDENCE-BUNDLE.tar.gz
```

From that extracted return directory, restore and verify with Python's standard library:

```python
import gzip, hashlib, json
from pathlib import Path
root = Path('.')
manifest = json.loads((root / 'checks/COMPRESSED-EVIDENCE.json').read_text())
for item in manifest['files']:
    compressed = (root / item['compressed_path']).read_bytes()
    assert len(compressed) == item['compressed_size']
    assert hashlib.sha256(compressed).hexdigest() == item['compressed_sha256']
    raw = gzip.decompress(compressed)
    assert len(raw) == item['original_size']
    assert hashlib.sha256(raw).hexdigest() == item['original_sha256']
    target = root / item['original_path']
    if target.exists() and target.read_bytes() != raw:
        assert hashlib.sha256(target.read_bytes()).hexdigest() == item['pointer_sha256']
    target.write_bytes(raw)
```

Restoration expands the evidence beyond the return's transfer budget; this is
expected. Commands and historical reports name the original JSON paths.
`RESULTS.json` points to the packaged `.gz` files plus this mapping.
