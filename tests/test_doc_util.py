from src.doc_util import get_style_by_id


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



