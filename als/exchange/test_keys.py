
import unittest

from als.exchange.keys import get_keys


class Test(unittest.TestCase):

    def test_get_keys_default(self):
        keys = get_keys()
        self.assertTrue(keys.has_key('api_key'))
        self.assertTrue(keys.has_key('secret'))

    def test_get_keys_absent(self):
        keys = get_keys('absent')
        self.assertTrue(not keys.has_key('api_key'))
        self.assertTrue(not keys.has_key('secret'))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()