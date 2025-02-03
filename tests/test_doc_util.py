from src.doc_util import get_style_by_id
import unittest
from docx import Document
from src.doc_util import extract_sections
from src.entity import Section


# テスト対象のサンプルファイルパス
SAMPLE_DOCX_PATH = "tests/resources/スタイル付_【問題A】自動原稿整理PoC_サンプル原稿（指摘箇所コメント付）.docx"





class TestDocUtil(unittest.TestCase):

    def setUp(self):
        # テスト用のドキュメントを作成
        self.doc = Document()
        self.doc.add_paragraph("一 大門1")
        self.doc.add_paragraph("これは大門1の内容です。")
        self.doc.add_paragraph("二 大門2")
        self.doc.add_paragraph("これは大門2の内容です。")

    def test_extract_sections(self):
        sections = extract_sections(self.doc)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].section_number, "一 大門1")
        self.assertEqual(sections[0].body_text, "これは大門1の内容です。")
        self.assertEqual(sections[1].section_number, "二 大門2")
        self.assertEqual(sections[1].body_text, "これは大門2の内容です。")
    
    def test_extract_sections_from_docx(self):
        doc = Document(SAMPLE_DOCX_PATH)
        sections = extract_sections(doc)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].section_number, "一")
        self.assertEqual(sections[0].body_text, "これは大門1の内容です。")
        self.assertEqual(sections[1].section_number, "二 大門2")
        self.assertEqual(sections[1].body_text, "これは大門2の内容です。")

    def test_get_style_by_id(self):
        """get_style_by_id のテスト"""
        style_id = "2-10"  # テスト対象の styleId

        # 期待されるスタイルデータ
        expected_style_data = {
            "styleId": "2-10",
            "type": "character",
            "customStyle": "1",
            "name": "2-1_設問_番号 (文字)",
            "basedOn": "DefaultParagraphFont",
            "link": "2-1",
            "font": {
                "ascii": "MS Gothic",
                "hAnsi": "MS Gothic",
                "eastAsia": "MS Gothic",
                "hint": None,
            },
            "color": "ED7D31",
            "size": "21",
        }

        # 関数を実行して結果を取得
        result = get_style_by_id(SAMPLE_DOCX_PATH, style_id)

        # 期待値と比較
        assert result == expected_style_data, (
            f"Expected {expected_style_data}, but got {result}"
        )
if __name__ == '__main__':
    unittest.main()



