import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


GENERATOR = Path(__file__).parents[1] / "tools" / "generate_token.py"


class TokenGeneratorTest(unittest.TestCase):
    def test_private_fragments_match_and_existing_token_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, str(GENERATOR), "--output-dir", directory]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            root = Path(directory)
            token = (root / "bridge-token.txt").read_text().strip()
            self.assertRegex(token, r"^[A-Za-z0-9_-]{43}$")
            self.assertNotIn(token, result.stdout + result.stderr)
            options = json.loads((root / "addon-options.fragment.json").read_text())
            self.assertEqual(options["bridge_token"], token)
            self.assertEqual(
                (root / "display-secrets.fragment.yaml").read_text().strip(),
                f'spotify_bridge_token: "{token}"',
            )
            self.assertEqual((root / ".gitignore").read_text(), "*\n!.gitignore\n")
            repeat = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertNotIn(token, repeat.stdout + repeat.stderr)
            self.assertEqual((root / "bridge-token.txt").read_text().strip(), token)


if __name__ == "__main__":
    unittest.main()
