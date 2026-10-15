"""Linux/Termux regression tests for scoped Aetherion shutdown."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

STOP = Path(__file__).resolve().parents[1] / 'runtime/ai/stop.sh'


class AetherionStopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.ai = self.root / 'runtime' / 'ai'
        self.ai.mkdir(parents=True)
        (self.ai / 'models').mkdir()
        (self.ai / 'models' / 'aetherion.gguf').write_text('test model')
        self.pidfile = self.ai / 'aetherion.pid'
        self.server = self.home / 'Aetherion/llama.cpp/build/bin/llama-server'
        self.server.parent.mkdir(parents=True)
        self.stop = self.ai / 'stop.sh'
        self.stop.write_bytes(STOP.read_bytes())
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.pkill_log = self.root / 'pkill-called'
        pkill = self.bin / 'pkill'
        pkill.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$PKILL_LOG"\n')
        pkill.chmod(0o755)
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home), PKILL_LOG=str(self.pkill_log), PATH=f'{self.bin}:' + self.env['PATH'])
        self.children = []
        self.addCleanup(self.cleanup_children)

    def cleanup_children(self):
        for proc in self.children:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)

    def launch(self, name, model=None):
        # exec -a gives a real live process the exact argv[0] used by start.sh.
        # No llama.cpp or model weights are needed for this ownership test.
        proc = subprocess.Popen(['bash', '-c',
            'exec -a "$1" python3 -c "import time; time.sleep(30)" -m "$2"',
            '_', str(name), str(model or self.ai / 'models/aetherion.gguf')],
            env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.children.append(proc)
        for _ in range(50):
            if Path(f'/proc/{proc.pid}/cmdline').read_bytes().startswith(str(name).encode() + b'\0'):
                break
            time.sleep(.02)
        return proc

    def run_stop(self):
        return subprocess.run(['bash', str(self.stop)], env=self.env,
                              capture_output=True, text=True, timeout=6)

    def test_no_pid_does_not_kill_other_servers(self):
        other = self.launch('/tmp/another-project/llama-server')
        result = self.run_stop()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(other.poll(), 'unrelated server was killed')
        self.assertFalse(self.pkill_log.exists(), 'global pkill was invoked')
        self.assertIn('not running', result.stdout)

    def test_owned_server_is_terminated(self):
        owned = self.launch(self.server)
        self.pidfile.write_text(f'{owned.pid}\n')
        result = self.run_stop()
        self.assertEqual(result.returncode, 0, result.stderr)
        owned.wait(timeout=3)
        self.assertFalse(self.pidfile.exists())
        self.assertFalse(self.pkill_log.exists(), 'global pkill was invoked')

    def test_reused_pid_or_foreign_process_is_refused(self):
        foreign = self.launch('/tmp/another-project/llama-server')
        self.pidfile.write_text(f'{foreign.pid}\n')
        result = self.run_stop()
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(foreign.poll())
        self.assertTrue(self.pidfile.exists(), 'preserve PID file for diagnosis')
        self.assertFalse(self.pkill_log.exists(), 'global pkill was invoked')

    def test_matching_executable_with_wrong_model_is_refused(self):
        foreign = self.launch(self.server, self.root / 'other.gguf')
        self.pidfile.write_text(f'{foreign.pid}\n')
        result = self.run_stop()
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(foreign.poll())
        self.assertFalse(self.pkill_log.exists(), 'global pkill was invoked')

    def test_invalid_pid_is_refused_without_signal(self):
        self.pidfile.write_text('not-a-pid\n')
        result = self.run_stop()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.pidfile.exists())
        self.assertFalse(self.pkill_log.exists(), 'global pkill was invoked')

    def test_stale_pid_is_cleaned_without_global_signal(self):
        self.pidfile.write_text('999999999\n')
        result = self.run_stop()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.pidfile.exists())
        self.assertFalse(self.pkill_log.exists(), 'global pkill was invoked')

    def test_optimizer_preserves_scoped_stop_script(self):
        optimizer = STOP.with_name('optimize_aetherion.sh').read_text()
        self.assertNotIn('pkill llama-server', optimizer)
        self.assertNotIn('cat > "$AI_HOME/stop.sh"', optimizer)
        self.assertIn('"$AI_HOME/stop.sh"', optimizer)


if __name__ == '__main__':
    unittest.main()
