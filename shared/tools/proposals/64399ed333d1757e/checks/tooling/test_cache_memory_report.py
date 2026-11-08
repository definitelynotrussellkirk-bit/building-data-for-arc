"""Fixture-based tests; all temporary data stays in a task-specific tmpfs folder."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('cache_memory_report.py')


class CacheMemoryReportTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('cache_report', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.tmp = tempfile.TemporaryDirectory(prefix='cache-report-test-', dir=SCRIPT.parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cg = self.root / 'cgroup'
        self.proc = self.root / 'proc'
        self.cg.mkdir()
        (self.proc / 'self').mkdir(parents=True)
        (self.proc / 'self/cgroup').write_text('0::/\n')
        (self.proc / 'meminfo').write_text('MemAvailable: 10 kB\n')
        (self.proc / 'self/mountinfo').write_text(
            f'1 0 0:1 / {self.root} rw - tmpfs tmpfs rw\n')
        self.group(self.cg)

    def group(self, path, maximum='1000', current='900', stats=None):
        path.mkdir(parents=True, exist_ok=True)
        (path / 'memory.max').write_text(maximum)
        (path / 'memory.current').write_text(current)
        (path / 'memory.stat').write_text(stats or 'file 600\nshmem 400\nslab_reclaimable 100\n')
        (path / 'memory.events').write_text('oom 3\noom_kill 1\n')

    def report(self):
        return self.module.report(self.root, cgroup_root=self.cg, proc_root=self.proc)

    def test_shmem_excluded_and_estimate_labeled_advisory(self):
        r = self.report()
        self.assertEqual(r['strict_cgroup_headroom_bytes'], 100)
        self.assertEqual(r['discounted_potential_headroom_bytes'], 250)
        self.assertEqual(r['cgroups'][0]['ordinary_file_cache_bytes'], 200)
        self.assertEqual(r['cgroups'][0]['oom_counters'], {'oom': 3, 'oom_kill': 1})
        self.assertIn('not guaranteed', r['limitations'])
        self.assertTrue(r['advisory_only'])
        self.assertNotIn('ready', r)

    def test_missing_cache_stat_keeps_potential_unknown(self):
        (self.cg / 'memory.stat').write_text('file 600\nshmem 400\n')
        self.assertIsNone(self.report()['discounted_potential_headroom_bytes'])

    def test_unlimited_cgroup_does_not_invent_finite_capacity(self):
        (self.cg / 'memory.max').write_text('max')
        r = self.report()
        self.assertIsNone(r['strict_cgroup_headroom_bytes'])
        self.assertIsNone(r['discounted_potential_headroom_bytes'])

    def test_tighter_ancestor_is_respected(self):
        self.group(self.cg / 'child', maximum='2000', current='100')
        (self.proc / 'self/cgroup').write_text('0::/child\n')
        r = self.report()
        self.assertEqual(len(r['cgroups']), 2)
        self.assertEqual(r['strict_cgroup_headroom_bytes'], 100)
        self.assertEqual(r['discounted_potential_headroom_bytes'], 250)

    def test_host_available_caps_illustrative_estimate(self):
        (self.proc / 'meminfo').write_text('MemAvailable: 0 kB\n')
        self.assertEqual(self.report()['discounted_potential_headroom_bytes'], 0)

    def test_filesystem_reports_actual_free_space(self):
        r = self.report()
        self.assertEqual(r['destination']['filesystem'], 'tmpfs')
        self.assertGreater(r['destination']['available_bytes'], 0)
        self.assertGreater(r['destination']['available_inodes'], 0)

    def test_unknown_limit_and_negative_cache_are_not_optimistic(self):
        (self.cg / 'memory.max').unlink()
        self.assertIsNone(self.report()['discounted_potential_headroom_bytes'])
        self.group(self.cg, stats='file 100\nshmem 200\nslab_reclaimable 0\n')
        r = self.report()
        self.assertEqual(r['cgroups'][0]['ordinary_file_cache_bytes'], 0)
        self.assertEqual(r['discounted_potential_headroom_bytes'], 100)

    def test_cli_produces_json_without_writing_files(self):
        before = set(self.root.rglob('*'))
        result = subprocess.run([sys.executable, str(SCRIPT), '--destination', str(self.root),
                                 '--cgroup-root', str(self.cg), '--proc-root', str(self.proc)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['advisory_only'])
        self.assertEqual(set(self.root.rglob('*')), before)


if __name__ == '__main__':
    unittest.main()
