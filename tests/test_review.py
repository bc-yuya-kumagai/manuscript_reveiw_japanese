import unittest
# src配下のreview.pyをimportする
from src.check import can_construct_from_index_lists


class TestCanConstructFromIndexLists(unittest.TestCase):
    def test_empty_index_lists(self):
        results =   can_construct_from_index_lists([],0)
        # 空のリストが返ってきたらOK
        self.assertEqual(len(results), 0)

    def test_single_character_match(self):
        results = can_construct_from_index_lists(["a"],0)
         # 空のリストが返ってきたらOK
        self.assertEqual(len(results), 0)

    def test_single_character_no_match(self):
        results = can_construct_from_index_lists(["xx"],0)
        # 空のリストが返ってきたらOK
        self.assertEqual(len(results), 1)

    def test_multiple_characters_match(self):
        results =can_construct_from_index_lists(["a", "b"],0)
        # 空のリストが返ってきたらOK
        self.assertEqual(len(results), 0)

    def test_multiple_characters_no_match(self):
        results = can_construct_from_index_lists(["1","a","b","x"],0)
        
        self.assertEqual(len(results), 1)
    
    def test_complex_case(self):
        results = can_construct_from_index_lists(["1","a","b","あ","い","う"],0)
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()