from typing import List, Callable
import src.general_util as gu
import unittest

class TestExtractIntervals(unittest.TestCase):
    def test_basic_intervals(self):
        data = [1, 2, "start", 3, 4, "end", 5, "start", 6, "end", 7]
        is_start = lambda x: x == "start"
        is_end = lambda x: x == "end"
        intervals = gu.extract_intervals(data, is_start, is_end)
        self.assertEqual(len(intervals), 2)
        self.assertEqual(intervals[0].items, ["start", 3, 4, "end"])
        self.assertEqual(intervals[0].start, 2)
        self.assertEqual(intervals[0].end, 5)
        self.assertEqual(intervals[1].items, ["start", 6, "end"])
        self.assertEqual(intervals[1].start, 7)
        self.assertEqual(intervals[1].end, 9)
    
    def test_no_intervals(self):
        data = [1, 2, 3, 4, 5]
        is_start = lambda x: x == "start"
        is_end = lambda x: x == "end"
        intervals = gu.extract_intervals(data, is_start, is_end)
        self.assertEqual(len(intervals), 0)
    
    def test_unclosed_start(self):
        data = ["start", 1, 2, 3, 4]
        is_start = lambda x: x == "start"
        is_end = lambda x: x == "end"
        intervals = gu.extract_intervals(data, is_start, is_end)
        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0].items, ["start", 1, 2, 3, 4])
        self.assertEqual(intervals[0].start, 0)
        self.assertEqual(intervals[0].end, 5)
    
    def test_multiple_nested_intervals(self):
        data = ["start", 1, "start", 2, "end", 3, "end"]
        is_start = lambda x: x == "start"
        is_end = lambda x: x == "end"
        intervals = gu.extract_intervals(data, is_start, is_end)
        self.assertEqual(len(intervals), 2)
        self.assertEqual(intervals[0].items, ["start", 1])
        self.assertEqual(intervals[0].start, 0)
        self.assertEqual(intervals[0].end, 2)
        self.assertEqual(intervals[1].items, ["start", 2, "end"])
        self.assertEqual(intervals[1].start, 2)
        self.assertEqual(intervals[1].end, 4)
    
if __name__ == "__main__":
    unittest.main()
