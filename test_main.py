import unittest
from main import main
import io
import contextlib

class TestCLI(unittest.TestCase):
    def test_main(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main([])
        self.assertEqual(f.getvalue(), "Coderagy CLI initialized.\n")

if __name__ == "__main__":
    unittest.main()
