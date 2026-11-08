# Read-only ZIP extraction preflight

Run before choosing an extraction destination:

~~~sh
python3 -B space_preflight.py packet.zip --destination /path/to/planned/extraction
~~~

Optional --reserve-bytes and --reserve-inodes require nonnegative integers.
The imported API validates these too. Exit codes: 0 for estimated fit or unknown
inode limit, 1 for insufficient capacity, 2 for invalid input. Read the JSON
capacity_status to distinguish unknown inode capacity from an estimated fit.

The helper reads ZIP metadata and filesystem capacity. It counts files and
implicit parent directories, rounds file allocations to destination block size,
and estimates one block per directory. It lists nested archives without opening
them. It does not extract, delete, clean caches, change permissions or reserve
space. It rejects unsafe/ambiguous ZIP member paths and unusable destinations,
including dangling symlinks. Existing destination contents are not subtracted.

Filesystem metadata, temporary copies and nested extraction can need more space;
a passing estimate is not a guarantee or an archive authenticity check. An inode
is a filesystem record for a file or directory: many tiny files can exhaust
inodes even if their content would fit in the free bytes.

Run the six focused regressions from this directory:

~~~sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v test_space_preflight
~~~

This packet's observed evidence is in WORK/checks/environment/storage-*.json in
the review return. The standalone tool requires only the Python standard library.
