from src.doc_util import get_style_by_id, kanji_number_to_arabic_number, extract_question_number, extract_annotation_text_to_list, extract_main_text_and_annotation_to_main_text
from unittest.mock import MagicMock
from unittest.mock import MagicMock
from docx.text.paragraph import Paragraph


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
def test_extract_annotation_text_to_list():
    """傍注のリストが正しく抽出されることを確認"""

    def create_mock_paragraph(text):
        """Paragraph モックオブジェクトを作成"""
        mock_p = MagicMock(spec=Paragraph)
        mock_p.text = text
        return mock_p

    # `Paragraph` オブジェクトのリストとしてモックを作成
    mock_document = [
        create_mock_paragraph("これは問題文です。"),
        create_mock_paragraph("これは第二の問題文です。"),
        create_mock_paragraph("（注）１　騒擾――さわぎみだれること。"),  # 傍注の開始
        create_mock_paragraph("　　　２　碁会所や撞球場――「碁会所」は囲碁を打てる場所。「撞球場」はビリヤード場。"),
        create_mock_paragraph("　　　３　元服――昔、貴族や武家の男子が成人することを示した儀式。"),
        create_mock_paragraph("問一　二重傍線部ⓐ・ⓑの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。"),  # 収集が停止するべき
    ]

    annotations = extract_annotation_text_to_list(mock_document)

    # デバッグ用に出力
    print(f"Extracted annotations: {annotations}")

    # 期待される結果
    expected = ["騒擾", "碁会所や撞球場", "元服"]

    assert annotations == expected, f"期待される結果: {expected}, 取得した結果: {annotations}"


def test_extract_main_text_and_annotation_to_main_text():
    """問題本文が正しく抽出されることを確認"""

    def create_mock_paragraph(text):
        mock_p = MagicMock(spec=Paragraph)
        mock_p.text = text
        return mock_p

    mock_document = [
        create_mock_paragraph("これは問題文です。"),
        create_mock_paragraph("これは第二の問題文です。"),
        create_mock_paragraph("（注）"),
        create_mock_paragraph("１　漢字――意味の説明"),
        create_mock_paragraph("２　別の単語――別の意味の説明"),
    ]

    main_text = extract_main_text_and_annotation_to_main_text(mock_document)

    # 期待される結果
    expected_texts = ["これは問題文です。", "これは第二の問題文です。"]

    assert len(main_text) == len(expected_texts), "本文の段落数が期待と異なります"

    for i, paragraph in enumerate(main_text):
        assert paragraph.text == expected_texts[i], f"段落 {i} の内容が期待と異なります"
