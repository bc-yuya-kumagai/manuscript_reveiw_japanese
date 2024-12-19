# Wordファイルの解析に関するユーティリティ関数を提供するモジュール

from docx import Document


# 問の見出しスタイルID
question_heading_style_id = 'af8'
# wordファイルから下線部のrunを抽出する

def get_underline_runs(doc,first_paragraph_index:int,last_paragraph_index:int):
    """ first_paragraph_indexとlast_paragraph_indexの間で underlined runを取得する
    last_paragraph_indexが-1の場合は最後のdocx_fileの最後の段落までを検索する"""
    runs = []
    for p in doc.paragraphs[first_paragraph_index:last_paragraph_index]:
        for run in p.runs:
            if run.underline:
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
        
def get_question_texts(doc:Document):
    """docから問から次の問までのテキストを取得する
    """
    questions=[]
    question_text = ""
    for p in doc.paragraphs:
        
        if p.text.startswith("問"):
            # 次の問に到達した場合は、現時点の設問文をリストに追加し、設問文を初期化する
            if len(question_text) > 0:
                questions.append(question_text)
            question_text = p.text+"\n"

        elif len(question_text) > 0:
            question_text += (p.text+"\n")
    return questions

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