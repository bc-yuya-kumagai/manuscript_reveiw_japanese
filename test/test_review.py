import unittest
# src配下のreview.pyをimportする
from src.review import can_construct_from_index_lists


class TestCanConstructFromIndexLists(unittest.TestCase):
    def test_empty_index_lists(self):
        self.assertTrue(can_construct_from_index_lists([]))

    def test_single_character_match(self):
        self.assertTrue(can_construct_from_index_lists(["a"]))  

    def test_single_character_no_match(self):
        self.assertFalse(can_construct_from_index_lists(["xx"]))

    def test_multiple_characters_match(self):
        self.assertTrue(can_construct_from_index_lists(["a", "b"]))

    def test_multiple_characters_no_match(self):
        self.assertFalse(can_construct_from_index_lists(["1","a","b","x"]))

    def test_complex_case(self):
        self.assertTrue(can_construct_from_index_lists(["1","a","b","あ","い","う"]))

if __name__ == '__main__':
    unittest.main()