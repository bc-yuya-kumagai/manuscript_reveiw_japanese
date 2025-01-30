from src.doc_util import get_style_by_id, kanji_number_to_arabic_number, extract_question_number
from unittest.mock import MagicMock
from docx import Document

# テスト対象のサンプルファイルパス
SAMPLE_DOCX_PATH = "tests/resources/スタイル付_【問題A】自動原稿整理PoC_サンプル原稿（指摘箇所コメント付）.docx"


def test_get_style_by_id():
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




# 漢数字をアラビア数字に変換する関数のテスト
def test_kanji_number_to_arabic_number():
    test_cases = [
        # 単一の漢数字
        ("〇", "0"),
        ("一", "1"),
        ("二", "2"),
        ("三", "3"),
        ("四", "4"),
        ("五", "5"),
        ("六", "6"),
        ("七", "7"),
        ("八", "8"),
        ("九", "9"),

        # 連続した漢数字
        ("一二三", "123"),
        ("四五六", "456"),
        ("七八九", "789"),
        ("九〇", "90"),

        # 大きな数字
        ("二〇二四", "2024"),  # 西暦表記
        ("五六七八九〇一", "5678901"),

        # 漢数字以外の文字を含むケース
        ("漢字一二三", "123"),  # 文字混じり
        ("テスト五六", "56"),
        ("123四五六", "456"),  # すでに数字が入っている場合

        # 漢数字がない場合
        ("漢字だけ", ""),
        ("", ""),  # 空文字
    ]

    for kanji_input, expected in test_cases:
        assert kanji_number_to_arabic_number(kanji_input) == expected, f"Failed for input: {kanji_input}"
