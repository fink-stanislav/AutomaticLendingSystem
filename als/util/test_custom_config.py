
import unittest

from als.util import custom_config as cc

class TestCustomConfig(unittest.TestCase):


    def test_get_parameter(self):
        actual = cc.get_test()
        expected = 'test'
        self.assertEqual(actual, expected)

    def test_init_config(self):
        cc.init_config(config_name='als_test')
        actual = cc.get_test()
        expected = 'test'
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()