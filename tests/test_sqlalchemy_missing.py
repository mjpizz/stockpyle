import os
import sys
from unittest import TestCase
import stockpyle._sqlalchemy


class SqlAlchemyMissingTestCase(TestCase):
    
    def setUp(self):
        # make sure that SQLAlchemy is not in the path
        self.__original_path = sys.path
        sys.path = [os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))]
    
    def tearDown(self):
        # restore the original sys path
        import sys
        sys.path = self.__original_path
    
    def test_session_extension_throws_exception(self):
        from stockpyle._sqlalchemy import StockpyleSessionExtension
        self.assertRaises(StandardError, lambda: StockpyleSessionExtension())
