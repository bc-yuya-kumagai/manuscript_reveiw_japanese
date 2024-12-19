# チェック系の関数をまとめたモジュール
import logging
import re
import src.llm_util
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
    ["1","2","3","4","5","6"],
    ["あ","い","う","え","お"],
    ["ア","イ","ウ","エ","オ"],
    ["ｱ","ｲ","ｳ","ｴ","ｵ"],
    ["a","b","c","d","e"],
    ["A","B","C","D","E"],
    ["ⓐ","ⓑ","ⓒ","ⓓ","ⓔ"],
]
blackets = ['(', ')', '（', '）','「', '」', '『', '』', '【', '】', '[', ']']


def can_construct_from_index_lists(input_list):
    # 再帰的またはメモ化して解く方法が自然
    # DPやバックトラックで実装できるが、ここではバックトラックで簡単に書く

    if len(input_list)==0:
        return None
    
    # メモ化用の辞書
    memo = {}

    def backtrack(start_index):
        # 入力リストをすべてカバーできたらTrue
        if start_index == len(input_list):
            return True

        # メモチェック
        if start_index in memo:
            return memo[start_index]

        # ここからindex_list_setを調べていく
        for candidate in VALID_INDEX_LIST_SET:
            # candidateがinput_list[start_index:]の先頭にマッチするか確認
            candidate_length = len(candidate)
            # 入力リストの範囲内かつcandidateが完全一致するか
            if start_index + candidate_length <= len(input_list) and input_list[start_index:start_index+candidate_length] == candidate:
                # マッチした場合は、その後続が成立するかを再帰的に確認
                if backtrack(start_index + candidate_length):
                    memo[start_index] = True
                    return True
            else:
                # 部分的なマッチ（先頭から一致するが全部はマッチしない）を考慮するため、
                # candidateと入力リストの先頭部分がどこまで一致するかを見て、
                # 一致した部分だけでよいのか確認する必要がある。

                # candidateを短く切り詰めながら先頭一致を探る
                # 例えば candidateが ["a","b","c","d","e"] で
                # input_listが ["a","1","2","3","4"] の場合
                # まず "a" は一致するが、その先は合わない
                # よって "a" だけを使い、その後に続く["1","2","3","4"]を次に回す
                match_len = 0
                for i in range(min(candidate_length, len(input_list)-start_index)):
                    if candidate[i] == input_list[start_index + i]:
                        match_len += 1
                    else:
                        break
                # match_lenが0でなければ、その部分列だけ使用して次へ進める
                if match_len > 0:
                    if backtrack(start_index + match_len):
                        memo[start_index] = True
                        return True

        memo[start_index] = False
        if start_index > 0:
            return InvalidItem(type="添え字飛び", message=f'添え字「{input_list[start_index]}」と「{input_list[start_index]}」の間に飛びがあります')

    return backtrack(0)

def check_jumped_index(passage_sideLine_list):
    """リストから飛び番号を取得する
    """
    
    pattern = '[' + re.escape(''.join(blackets)) + ']'

    striped_set = set()
    for i, item in enumerate(passage_sideLine_list):
        striped_set.add(re.sub(pattern, '', item.index_text))
 
    sorted_index_list = sorted(striped_set)
    logger.info(can_construct_from_index_lists(sorted_index_list))
    return can_construct_from_index_lists(sorted_index_list)



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

def check_question2choices_mapping(question_text:str):
    """設問文にある選択肢のバリエーションが実際の選択肢に存在するかをチェックする
    """
    results =  src.llm_util.check_question2choices_mapping(question_text)
    InvalidItems = []
    for result in results:
        InvalidItems.append(InvalidItem(type=result["type"], message=result["message"]))
    return InvalidItems

def check_choices2question_mapping(question_text:str):
    """実際の選択肢のバリエーションが設問文に存在するかをチェックする
    """
    results =  src.llm_util.check_choices2question_mapping(question_text)
    InvalidItems = []
    for result in results:
        InvalidItems.append(InvalidItem(type=result["type"], message=result["message"]))
    return InvalidItems



