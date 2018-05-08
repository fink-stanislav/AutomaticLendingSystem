
import unittest

from als.util import custom_config

class TestCustomConfig(unittest.TestCase):


    def test_get_parameter(self):
        actual = custom_config.get_temp()
        expected = 'test'
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()