# Wordファイルの解析に関するユーティリティ関数を提供するモジュール

from typing import List
from docx import Document
from docx.text.paragraph import Paragraph
from lxml import etree
from zipfile import ZipFile


# 問の見出しスタイルID
question_heading_style_id = 'af8'
# wordファイルから下線部のrunを抽出する

def get_underline_runs(doc,first_paragraph_index:int,last_paragraph_index:int):
    """ first_paragraph_indexとlast_paragraph_indexの間で underlined runを取得する
    last_paragraph_indexが-1の場合は最後のdocx_fileの最後の段落までを検索する"""
    runs = []
    for p in doc.paragraphs[first_paragraph_index:last_paragraph_index]:
        for run in p.runs:
            # スタイルが1-5-10または1-5-20の場合は下線部として抽出
            if run.style.style_id == '1-5-10': # or run.style.style_id == '1-5-20': 二重傍線スタイル1-5-20は誤爆する？
                runs.append(run)
    return runs

def check_countains_text(doc:Document,text:str, first_paragraph_index:int,last_paragraph_index:int):
    """ first_paragraph_indexとlast_paragraph_indexの間でtextが含まれているかを検索する
    last_paragraph_indexが-1の場合は最後のdocx_fileの最後の段落までを検索する"""
    for p in doc.paragraphs[first_paragraph_index:last_paragraph_index]:
        if text in p.text:
            return True
    return False

def get_previous_text_index_run(sideline_run):
  
    prv = sideline_run._element.getprevious()
    while prv !=  None and (prv.text == None or prv.text == '') :
        prv = prv.getprevious()

    if prv is not None:
        return prv
    else:
        return None

def get_first_question_paragraph_index(doc):
    """ 、question_heading_style_idの見出しを持つ段落のインデックスを返す
    インデックス順に文書が構成されていることを前提とする
    

    """
    # question_heading_style_idの見出しを持つ段落のインデックスを返す
    # インデックス順に文書が構成されていることを前提とする
    # for i, p in enumerate(doc.paragraphs):
    #         for r in p.runs:
    #             if r.style.style_id == question_heading_style_id:
    #                 return i

    # 仮の実装 インデントや空白なしで行頭が「問」で始まる段落を問の見出しとする
    for i, p in enumerate(doc.paragraphs):
        if p.text.startswith("問"):
            return i
        
def get_questions(doc:Document)->List[Paragraph]:
    """docから問から次の問までのPhraseを取得する
    """
    questions=[]
    question_phrases = []
    for p in doc.paragraphs:
        
        if p.text.startswith("問"):
            # 次の問に到達した場合は、現時点の設問文をリストに追加し、設問文を初期化する
            if len(question_phrases) > 0:
                questions.append(question_phrases)
            question_phrases=[p]

        elif len(question_phrases) > 0:
            question_phrases.append(p)
    questions.append(question_phrases)
    return questions

def extract_question_paragraphs(doc: Document) -> List[Paragraph]:
    """
    文書から「問」で始まるパラグラフを抽出する

    Returns:
        List[Paragraph]: 「問」で始まるParagraphオブジェクトのリスト
    """
    question_paragraphs = []
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("問"):
            # 「問」で始まるパラグラフをリストに追加
            question_paragraphs.append(paragraph)
    return question_paragraphs

def split_exam_2_sections(doc:Document):
    """ docを大門ごとに分割する
    大門の先頭は「【」で始まる
    例: 【必答問題】この問題は全員解答してください。 
    """
    sections = []
    section = []
    for p in doc.paragraphs:
        if p.text.startswith("【"):
            if len(section) > 0:
                sections.append(section)
                section = []
        section.append(p.text)
    return sections

def clean_sileline_list_in_page_break(list):
    """リストから改ページで発生するごみを削除する。
    TODO: ちゃんと改ページを判断する

    """
    return [i for i in list if len(i.index_text)<4]


def get_paragraph_text_by_keyword(doc:Document,word:str):
    """docの段落からwordが含まれている段落のテキストを取得する
    """
    for p in doc.paragraphs:
        if word in p.text:
            yield p.text

def get_choice_indexes_from_choices_list(question_phrases):
    """選択肢のリストから選択肢の添え字を取得する
    """
    indexes = []
    for p in question_phrases:
        # フレーズ内で <w:rStyle w:val="2-3-10"/>であるrunを取得する
        for run in p.runs:
            if run.style.style_id == '2-3-10':
                indexes.append(run.text)
        
    return indexes

def find_continuous_run_indices(paragraph:Paragraph, target:str):
    """
    Check if the target string exists as a sequence of characters across the elements
    of the string_list and return the indices where it is found.

    Args:
        string_list (list of str): List of strings to search.
        target (str): The target string to find.

    Returns:
        list of int: List of indices where the target string is found.
    """
    # Join the list into a single continuous string with a delimiter
  
    combined_text = "".join(r.text for r in paragraph.runs)
    if target not in combined_text or len(target) == 0:
        return []


    # Determine which indices of the original list are involved
    indices = []
    offset = 0
    for i, r in enumerate(paragraph.runs):
        for c in r.text:
            if len(c) == 0:
                continue
            if c == target[offset]:
               indices.append(i)
               offset += 1
               if offset == len(target): # offsetがtargetの長さに達したら、後続のtargetの検索を行うため、offsetを0に戻す
                     offset = 0
            else:
                offset = 0
    # indicesの要素をユニークにする
    return list(set(indices))


def get_style_by_id(docx_file_path: str, style_id: str) -> dict:
    """
    styles.xml 内の指定された styleId の設定をオブジェクト形式で返す関数。

    :param docx_file_path: WORDファイルのパス
    :param style_id: 取得したいスタイルの ID (styleId)
    :return: スタイル設定を格納した辞書オブジェクト
    """
    # styles.xml を取得
    with ZipFile(docx_file_path) as docx:
        styles_xml = docx.read("word/styles.xml")
    # 名前空間の定義
    NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    # styles.xml の読み込み
    tree = etree.XML(styles_xml)
  

    # 指定された styleId を持つ <w:style> を検索
    style_element = tree.find(f".//w:style[@w:styleId='{style_id}']", namespaces=NS)
    if style_element is None:
        return {"error": f"Style ID '{style_id}' not found."}

    # スタイル情報を辞書に格納
    style_info = {
        "styleId": style_id,
        "type": style_element.attrib.get(f"{{{NS['w']}}}type", "Not Specified"),
        "customStyle": style_element.attrib.get(f"{{{NS['w']}}}customStyle", "0"),
        "name": None,
        "basedOn": None,
        "link": None,
        "font": {"ascii": None, "hAnsi": None, "eastAsia": None, "hint": None},
        "color": None,
        "size": None,
    }

    # スタイル名
    name_element = style_element.find(f"{{{NS['w']}}}name", namespaces=NS)
    if name_element is not None:
        style_info["name"] = name_element.attrib.get(f"{{{NS['w']}}}val")

    # 継承元スタイル
    based_on_element = style_element.find(f"{{{NS['w']}}}basedOn", namespaces=NS)
    if based_on_element is not None:
        style_info["basedOn"] = based_on_element.attrib.get(f"{{{NS['w']}}}val")

    # リンクされたスタイル
    link_element = style_element.find(f"{{{NS['w']}}}link", namespaces=NS)
    if link_element is not None:
        style_info["link"] = link_element.attrib.get(f"{{{NS['w']}}}val")

    # ランプロパティ <w:rPr> を探索
    rpr_element = style_element.find(f"{{{NS['w']}}}rPr", namespaces=NS)
    if rpr_element is not None:
        # フォント情報
        rfonts_element = rpr_element.find(f"{{{NS['w']}}}rFonts", namespaces=NS)
        if rfonts_element is not None:
            style_info["font"]["ascii"] = rfonts_element.attrib.get(f"{{{NS['w']}}}ascii")
            style_info["font"]["hAnsi"] = rfonts_element.attrib.get(f"{{{NS['w']}}}hAnsi")
            style_info["font"]["eastAsia"] = rfonts_element.attrib.get(f"{{{NS['w']}}}eastAsia")
            style_info["font"]["hint"] = rfonts_element.attrib.get(f"{{{NS['w']}}}hint")

        # 色情報
        color_element = rpr_element.find(f"{{{NS['w']}}}color", namespaces=NS)
        if color_element is not None:
            style_info["color"] = color_element.attrib.get(f"{{{NS['w']}}}val")

        # フォントサイズ
        size_element = rpr_element.find(f"{{{NS['w']}}}sz", namespaces=NS)
        if size_element is not None:
            style_info["size"] = size_element.attrib.get(f"{{{NS['w']}}}val")

    return style_info
