from typing import List, Callable
import src.general_util as gu
import unittest

class TestExtractIntervals(unittest.TestCase):
    def test_basic_intervals(self):
        data = [1, 2, "start", 3, 4, "end", 5, "start", 6, "end", 7]
        is_start = lambda x: x == "start"
        is_end = lambda x: x == "end"
        expected = [["start", 3, 4, "end"], ["start", 6, "end"]]
        self.assertEqual(gu.extract_intervals(data, is_start, is_end), expected)
    
    def test_no_intervals(self):
        data = [1, 2, 3, 4, 5]
        is_start = lambda x: x == "start"
        is_end = lambda x: x == "end"
        expected = []
        self.assertEqual(gu.extract_intervals(data, is_start, is_end), expected)
    
    def test_unclosed_start(self):
        data = ["start", 1, 2, 3, 4]
        is_start = lambda x: x == "start"
        is_end = lambda x: x == "end"
        expected = [["start", 1, 2, 3, 4]]
        self.assertEqual(gu.extract_intervals(data, is_start, is_end), expected)
    
    def test_multiple_nested_intervals(self):
        data = ["start", 1, "start", 2, "end", 3, "end"]
        is_start = lambda x: x == "start"
        is_end = lambda x: x == "end"
        expected = [["start", 1,],[ "start", 2, "end"]]
        self.assertEqual(gu.extract_intervals(data, is_start, is_end), expected)
    
if __name__ == "__main__":
    unittest.main()
