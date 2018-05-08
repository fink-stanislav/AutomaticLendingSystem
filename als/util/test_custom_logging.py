
import unittest

import custom_logging


class TestCustomLogging(unittest.TestCase):


    def test_init_config(self):
        logger = custom_logging.get_logger('als.core')
        self.assertIsNotNone(logger)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()