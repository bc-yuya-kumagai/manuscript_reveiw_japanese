# チェック系の関数をまとめたモジュール
import logging
import re
from typing import List
import src.llm_util
from docx.text.paragraph import Paragraph
# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SideLine:
    def __init__(self, index_text:str, passage:str):
        """ 傍線部のテキストとそのテキストとその添え字を保持するクラス
        """
        self.passage = passage # 傍線部のテキスト
        self.index_text = index_text # 傍線部の添え字
    
    def __str__(self):
        return f'添え字：{self.index_text}、傍線部：{self.passage}'
    
class InvalidItem:
    """エラー情報を保持するクラス
    将来的にはWordファイルの指摘箇所の情報を保持出来るように拡張したい
    """
    def __init__(self, type:str, message:str):
        self.type = type
        self.message = message

def check_duplicated_index(passage_sideLine_list):
    """リストから重複する添え字を取得する
    """
    invalid_text_indexis = []
    for item in passage_sideLine_list:
        if item.index_text in invalid_text_indexis:
            continue

        index_count = sum(i.index_text == item.index_text for i in passage_sideLine_list)
        logger.info(item.index_text)
        if index_count > 1:
            invalid_text_indexis.append(item.index_text)

            msg = f'添え字「{item.index_text}」が{index_count}件存在します'
            for i in passage_sideLine_list:
                if i.index_text == item.index_text:
                    msg+=f'傍線部：{i.passage}'
            
            yield InvalidItem(type="傍線添え字重複", message=msg)

# 以下のリストは、添え字のリストのセットを表す
# 前提条件: 問題文中の添え字や添え字の囲み記号はあらかじめ決められた範囲内であること（出現前範囲が予測できること）
VALID_INDEX_LIST_SET = [
    ["1","2","3","4","5","6","7","8","9","10"],
    ["１","２","３","４","５","６","７","８","９","１０"],
    ["あ","い","う","え","お"],
    ["ア","イ","ウ","エ","オ"],
    ["ｱ","ｲ","ｳ","ｴ","ｵ"],
    ["a","b","c","d","e"],
    ["A","B","C","D","E"],
    ["ⓐ","ⓑ","ⓒ","ⓓ","ⓔ"],
]
blackets = ['(', ')', '（', '）','「', '」', '『', '』', '【', '】', '[', ']']


def can_construct_from_index_lists(input_list,offset:int)->List[InvalidItem]:
    """input_listがVALID_INDEX_LIST_SETのリストのサブリストの先頭から始まる配列で構成されているかをチェックする
    """
    max_match_index = 0
    if offset >= len(input_list):
        return []
    for valid_index_list in VALID_INDEX_LIST_SET:
        for i in range(min(len(input_list[offset:]), len(valid_index_list))):
            # valid_index_list[:i+1]がinput_listの先頭からi+1個の要素と一致するかをチェックする
            if input_list[offset:offset+i+1] == valid_index_list[:i+1]:
                max_match_index += 1
                logger.info(f'一致：{input_list[offset:offset+i+1]}')
                continue
            else:
                # 一致しない場合は、次のVALID_INDEX_LIST_SETのリストをチェックする
                break
    if max_match_index == 0:
        return [InvalidItem(type="添え字不正", message=f'添え字が不正です:{input_list[offset]}')]
    elif offset+max_match_index == len(input_list):
        return []
    
    result = can_construct_from_index_lists(input_list,offset+max_match_index)

    return result

def check_choice_index_sequence(choice_indexes):
    """選択肢の添え字が連番で記載されているかをチェックする
    """
    offset = 0
    standard_sequences= (["１","２","３","４","５","６","７","８","９","１０"], ["1","2","3","4","5","6","7","8","9","10"])
    standard_sequence = None
    for ss in standard_sequences:
        if set(choice_indexes).issubset(set(ss)):
            standard_sequence = ss
            break
    if standard_sequence is None:
        return InvalidItem(type="選択肢不正", message=f'選択肢の添え字が規定外の文字種です:{choice_indexes}')
    
    for ci in choice_indexes:
        if ci == standard_sequence[offset]:
            offset += 1
        elif offset == 0:
            return InvalidItem(type="選択肢不正", message=f'選択肢の添え字が不正です:{ci}')
        else:  
            offset = 0



def check_jumped_index(passage_sideLine_list) -> List[InvalidItem]:
    """リストから飛び番号を取得する
    """
    
    pattern = '[' + re.escape(''.join(blackets)) + ']'

    striped_set = set()
    for i, item in enumerate(passage_sideLine_list):
        striped_set.add(re.sub(pattern, '', item.index_text))
 
    sorted_index_list = sorted(striped_set)

    return can_construct_from_index_lists(sorted_index_list,0)



def check_mapping_sileline_index_userd_in_questions(passage_sideLine_list, slideline_questions):
    """傍線部の添え字がすべて設問の中で参照されているかをチェックする
    """
    indexes_master = [i.index_text for i in passage_sideLine_list]
    indexes_memo = indexes_master.copy()
    keyword = "傍線部"
    # sideline_questionsから添え字を取得する 
    # ”傍線部<添え字1>・<添え字2>・<添え字3>"という形式で記載されている。"・"で連結された文字列を添え字として取得する
    # 例: "二重傍線部ⓐ・ⓑの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。" -> 「ⓐ」、「ⓑ」を取得する
    for line in slideline_questions:
        text_indexes_in_question_text = src.llm_util.get_text_indexes_from_question(line)
        for index_text in indexes_master: 
            if index_text in text_indexes_in_question_text:
                if index_text in indexes_memo:
                    indexes_memo.remove(index_text) 

        if len(indexes_memo) == 0:
            return True
    return InvalidItem(type="添え字不足", message=f'傍線部の添え字{str(indexes_memo)}が設問の中で参照されていません')

def check_mapping_sileline_index_appear_in_passage(passage_sideLine_list, slideline_questions):
    """ 設問の中の添え字が問題文中に現れるかをチェックする
        設問中にどのような形式で添え字が記載されているかは
        "傍線部1・2"、"傍線部1または2"、"傍線部1または2"とか"傍線部1、2"などバリエーションが多いのでルールベースでの取得が難しいためLLMで取得する
    """
    indexes = [i.index_text for i in passage_sideLine_list]
    not_used_indexes = []

    for question_line in slideline_questions:
        text_indexes_in_question_text = src.llm_util.get_text_indexes_from_question(question_line)
        # indexes_memoからindexes_memoを削除する
        for idx in text_indexes_in_question_text:
            if idx not in indexes:
                not_used_indexes.append(idx)
        if len(not_used_indexes) == 0:
            return True
    return InvalidItem(type="添え字不足", message=f'傍線部の添え字{str(not_used_indexes)}が設問の中で参照されていません')

def get_question_type(question_text:str):
    """引数で与えられた問題文から、選択問題か記述問題かを取得する"""
    return src.llm_util.get_question_type(question_text)["type"]

def get_choice_indexes(question_text:str):
    """引数で与えられた問題文から、選択肢の添え字を取得する"""
    return src.llm_util.get_choice_indexes(question_text)

def check_choices_mapping(question_phrases:str):
    try:
        """設問文にある選択肢のバリエーションが実際の選択肢に存在するかをチェックする
        """
        question_text = '\n'.join([q.text for q in question_phrases])
        # 選択肢リストの中から選択肢の添え字を取得する
        # 空文字にスタイルが入っていることがあるので無視する
        choice_indexes = [i for i in src.doc_util.get_choice_indexes_from_choices_list(question_phrases) if i != ""]

        # 設問文の文章の中から、選択肢の添え字を取得する
        question_indexes = src.llm_util.get_choice_indexes_from_question_text(question_text)
        
        #   設問文内の添え字が選択肢内の添え字に含まれているかをチェックする
        for qidx in question_indexes["choices"]:
                    if qidx not in choice_indexes:
                        yield InvalidItem(type="選択肢不足", message=f'設問文内の選択肢{qidx}が選択肢の一覧に存在しません')
        #   選択肢内の添え字が設問文内の添え字に含まれているかをチェックする
        for choice_index in choice_indexes:
                if choice_index not in question_indexes["choices"]:
                    yield InvalidItem(type="設問文での選択肢不足", message=f'選択肢の一覧内の選択肢{choice_index}が設問文に存在しません')
    except Exception as e:
        logger.error(f'エラー：{e}: {question_text}')  
        raise e
      


def check_choices2question_mapping(question_text:str):
    """実際の選択肢のバリエーションが設問文に存在するかをチェックする
    """
    results =  src.llm_util.check_choices2question_mapping(question_text)
    InvalidItems = []
    for result in results:
        InvalidItems.append(InvalidItem(type=result["type"], message=result["message"]))
    return InvalidItems

def check_choices_sequence(question_phrases:str):
    """選択肢が連番で記載されているかをチェックする
    """
    # 選択肢リストの中から選択肢の添え字を取得する
    # 空文字にスタイルが入っていることがあるので無視する
    choice_indexes = [i for i in src.doc_util.get_choice_indexes_from_choices_list(question_phrases) if i != ""]

    choice_indexes.count

    result = check_choice_index_sequence(choice_indexes)
    if isinstance(result, InvalidItem):
        return InvalidItem(type=result.type, message=result.message)
    return None

def check_font_of_unfit_item(paragraphs:List[Paragraph]):
    """「適当でないもの」がMSゴシックであるかチェックする
    """
    for paragraph in paragraphs:
        hit_indexis = src.doc_util.find_continuous_run_indices(paragraph=paragraph, target="適当でないもの")
        # hit_indexisに該当するrunのフォントがMSゴシックであるかをチェックする 1つでもMSゴシックでないものがあればエラー
        if any(paragraph.runs[hit_index].font.name != "MS ゴシック" for hit_index in hit_indexis):
            return InvalidItem(type="フォント不正", message=f'「適当でないもの」のフォントがMSゴシックではありません')
        
def check_question_font(docx_file_path:str ,paragraphs:List[Paragraph]):
    """「問~」がMSゴシックかチェック
    """
    for paragraph in paragraphs:
        for run in paragraph.runs:
            if run.text.isspace() or run.text is None:
                break
            elif run.text:
                if "MS Gothic" != src.doc_util.get_style_by_id(docx_file_path, run.style.style_id)["font"]["ascii"]:
                    return InvalidItem(type="フォント不正", message=f'「問~」のフォントがMSゴシックではありません')
