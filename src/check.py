# チェック系の関数をまとめたモジュール
import logging
import re
import src.doc_util
from typing import List
import src.llm_util
from docx import Document
from docx.text.paragraph import Paragraph
import json
import jaconv
from docx import Document
# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 大問の点数を取得する正規表現



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
        self.section_number:str = None
        self.question_number:str = ""

from typing import Generator

def check_duplicated_index(passage_sideLine_list) -> Generator[InvalidItem, None, None]:
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
        return [InvalidItem(type="添え字不正", message=f'添え字が不正です:"{input_list[offset]}"')]
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
        return InvalidItem(type="選択肢不正", message=f'選択肢番号に規定外の文字種があります:{choice_indexes}')
    
    for ci in choice_indexes:
        if ci == standard_sequence[offset]:
            offset += 1
        elif ci == standard_sequence[0]:
            offset = 1
        else:
            return InvalidItem(type="選択肢不正", message=f'選択肢番号の順序が不正です:{"、".join(choice_indexes)}')


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
    # カタカナ記号を全て全角にする # indexes_memo の要素をuniqueにする
    indexes_memo = list(set([jaconv.h2z(i.index_text) for i in passage_sideLine_list]))
    
    # sideline_questionsから添え字を取得する 
    # ”傍線部<添え字1>・<添え字2>・<添え字3>"という形式で記載されている。"・"で連結された文字列を添え字として取得する
    # 例: "二重傍線部ⓐ・ⓑの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。" -> 「ⓐ」、「ⓑ」を取得する
    for line in slideline_questions:
        text_indexes_in_question_text = src.llm_util.get_text_indexes_from_question(line)
        for q_idx in text_indexes_in_question_text:
            if jaconv.h2z(q_idx) in indexes_memo:
                indexes_memo.remove(jaconv.h2z(q_idx))
        if len(indexes_memo) == 0:
            return True
    return InvalidItem(type="添え字不足", message=f'傍線部の添え字{str(indexes_memo)}が設問の中で参照されていません')

def check_mapping_sileline_index_appear_in_passage(passage_sideLine_list, slideline_questions):
    """ 設問の中の添え字が問題文中に現れるかをチェックする
        設問中にどのような形式で添え字が記載されているかは
        "傍線部1・2"、"傍線部1または2"、"傍線部1または2"とか"傍線部1、2"などバリエーションが多いのでルールベースでの取得が難しいためLLMで取得する
    """
    indexes = [jaconv.h2z(i.index_text) for i in passage_sideLine_list]
    not_used_indexes = []

    for question_line in slideline_questions:
        text_indexes_in_question_text = src.llm_util.get_text_indexes_from_question(question_line)
        # indexes_memoからindexes_memoを削除する
        for idx in text_indexes_in_question_text:
            if jaconv.h2z(idx) not in indexes:
                not_used_indexes.append(idx)
        if len(not_used_indexes) == 0:
            return True
    return InvalidItem(type="添え字不足", message=f'傍線部の添え字{str(not_used_indexes)}が問題文の中で参照されていません')

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
                        yield InvalidItem(type="設問文での選択肢不足", message=f'選択肢の一覧内の選択肢"{choice_index}"が設問文に存在しません') 
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

def check_choices_sequence(question_phrases:List[Paragraph]):
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

def check_explanation_of_questions_include_word(doc: Document, start:int, end:int):
    """
    解説文章の中に、「正答」以外の単語が含まれていないかをチェックします。
    
    Args:
        doc (Document): 対象となる文書オブジェクト。
    
    Returns:
        InvalidItem: 表記ゆれが検出された場合のエラー情報を返します。
    """
    # 解説文のリストを取得
    explanation_question_list = src.doc_util.get_explanation_of_questions(doc,start,end)
    # 各解説文についてチェック
    for explanation_question_text in explanation_question_list:
        # 解説文にキーワードが含まれているかをチェック
        check_result = src.llm_util.check_explanation_question_include_keyword(explanation_question_text)
        # 評価対象であり、キーワードが見つからない場合
        if check_result["is_evaluation_target"] is True and check_result["is_keyword_found"] is False:
            # エラー文を短縮して表示用に加工
            if len(explanation_question_text) > 15:
                error_text_one_line = explanation_question_text[:12] + "..."
            else:
                error_text_one_line = explanation_question_text
            # エラーメッセージを構築
            error_message = (
                f"解説中の正答を述べている文章に、「正答」という単語が使われていない箇所があります。"
                f"[「{error_text_one_line}」付近で誤って「{check_result['error_similar_words']}」のように使用されています。]\n"
            )
            if error_message:
                # 表記ゆれエラーを返す
                return InvalidItem(type="解説文での表記ゆれエラー", message=error_message)

def check_keyword_exact_match_in_question(paragraphs_lists:List[Paragraph]):
    """設問に正しく「適当」が使用されているかチェックする"""
    result = ""
    combined_questions = []
    for paragraphs in paragraphs_lists:
        for paragraph in paragraphs:
            paragraph_text = paragraph.text.strip()
            if paragraph_text.startswith("問"):
                if result:
                    combined_questions.append(result.strip())
                result = paragraph_text
            else:
                result += "\n" + paragraph_text
    if result:
        combined_questions.append(result.strip())

    # 出力結果
    for q_index , combined in enumerate(combined_questions, start=1):
        result = json.loads(src.llm_util.check_tekitou_exact_match_in_question_statement(combined)["choices"][0]["message"]["content"])        
        if result["is_evaluated"] is True and result["is_exact_match"] is False:
            invalid_item = InvalidItem(type="表記ルールエラー", message=f'問{q_index}に「適当」が正しく使用されていません [{result["incorrect_usages"]}]')
            invalid_item.question_number = q_index
            logger.info(invalid_item.message)
            yield invalid_item
        
def check_heading_question_font(docx_file_path:str ,paragraphs:List[Paragraph]):
    """「問~」がMSゴシックかチェック
    """
    for paragraph in paragraphs:
        buffer = src.doc_util.font_analyzer(docx_file_path, paragraph)  # 段落内のテキスト情報を一時的に保持する
        question_no = None  # 検出した「問〇」の番号を格納する変数

        # 段落全体のテキストを結合
        combined_text = "".join([content["text"] for content in buffer])

        kanji_numbers = [
            "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
            "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"
        ][::-1]

        # 「問〇」の形式を検出
        for kanji in kanji_numbers:
            keyword = f"問{kanji}"
            if keyword in combined_text:
                question_no = keyword
                break

        # 判定
        if question_no is not None:
            buffer_question_no = ""
            for content in buffer:
                if buffer_question_no == keyword:
                    break
                if "ＭＳ ゴシック" != content["font"] and "MS Gothic" != content["font"]:
                    return InvalidItem(type="フォント不正", message=f'「{question_no}」のフォントがMSゴシックではありません')
                buffer_question_no += content["text"]

def check_part_question_score(question_doc:Document, answer_doc:Document):
    
    main_score_list = src.doc_util.extract_question_number(question_doc)
    answer_score_list = src.doc_util.extract_question_number(answer_doc)

    question_dict = {q["question_title"]: q["question_score"] for q in main_score_list}
    answer_dict = {a["question_title"]: a["question_score"] for a in answer_score_list}
    
    # 問題にあるのに解答にないもの
    missing_in_answer = [q for q in question_dict if q not in answer_dict]
    
    # 解答にあるのに問題にないもの
    extra_in_answer = [a for a in answer_dict if a not in question_dict]
    
    # 点数不一致のリスト
    score_mismatch = {
        q: (question_dict[q], answer_dict[q])
        for q in question_dict if q in answer_dict and question_dict[q] != answer_dict[q]
    }
    
    error_messages = []
    if missing_in_answer:
        error_messages.append(f'問題にあるが解答にない: {missing_in_answer}')
    if extra_in_answer:
        error_messages.append(f'解答にあるが問題にない: {extra_in_answer}')
    if score_mismatch:
        error_messages.append(f'点数不一致: {score_mismatch}')
    
    if error_messages:
        return InvalidItem(type="大問の配点検証エラー", message="; ".join(error_messages))

# 本文から傍注のテキストを抜き出す正規表現をコンパイル
annotation_extend_main_text_pattern = re.compile(r"（注[^）]*）.*?。")
def check_exists_annotation(doc: Document, start:int, end:int):
    """
    傍注が本文内にすべて含まれているか検査する関数。

    Parameters:
        doc (Document): チェック対象のドキュメントオブジェクト。

    Returns:
        InvalidItem: 傍注が本文内に含まれていない場合のエラー情報。
        None: 全ての傍注が本文内に正しく含まれている場合。
    """
    # 本文と傍注を抽出
    main_texts_and_annotation_texts = src.doc_util.extract_main_text(doc, start, end)

    # # 本文中から傍注の文章を抽出
    annotation_sentences = []
    missing_annotations = []  # 本文内に存在しない傍注のリスト
    found_count = 0  # 本文内に存在する傍注の数
    for main_text_and_annotation in main_texts_and_annotation_texts:
        # 本文と傍注から傍注のみを抽出
        annotation_list = src.doc_util.extract_annotation_text_to_list(main_text_and_annotation)
        # 本文と傍注から本文のみを抽出
        main_text_list = src.doc_util.extract_main_text_and_annotation_to_main_text(main_text_and_annotation)
        
        # 本文中から傍注の文章を抽出
        annotation_sentences = [] # 本文から傍注部分を抽出し格納するリスト
        for paragraph in main_text_list:
            matches = annotation_extend_main_text_pattern.findall(paragraph.text)
            if matches:
                annotation_sentences.extend(matches)

        # 傍注リストの各項目が本文内に存在するかチェック
        for annotation_name in annotation_list:
            occurrence_count = sum(annotation_name in sentence for sentence in annotation_sentences)
            # 傍注が本文内に存在しない場合
            if occurrence_count == 0:
                missing_annotations.append(annotation_name)
            else:
                found_count += occurrence_count

    # OKの数と本文内の傍注数が一致しているか確認
    if found_count != len(annotation_sentences) and missing_annotations:
        missing_annotation_names = ",".join(missing_annotations)
        return InvalidItem(type="傍注箇所エラー", message=f"傍注部分の「{missing_annotation_names}」が、本文の注に含まれていません。")
    elif found_count != len(annotation_sentences):
        return InvalidItem(type="傍注箇所エラー", message="本文の傍注部分で、注の説明に含まれていないものがあります。")

def check_answer_contains_points(doc:Document,start:int,end:int):
    """記述設問の場合に、解説のポイントが含まれているかチェックする"""
    question_explanation_list = src.doc_util.get_explanation_of_questions(doc,start,end)
            
    for question in question_explanation_list:
        
        if "記述設問" in question:
            if "解答のポイント" not in question:
                # 文字を丸める
                error_question = ""
                if len(question) > 15:
                    error_question = question[:15] + "…"
                else:
                    error_question = question
                # Exceptionを発火
                return InvalidItem(type="フレーズ不足", message=f"{error_question}に、記述設問の場合解説のポイントが含まれていません。")

def check_phrase_in_kanji_writing_question(question_texts: List[Paragraph]) -> Generator[InvalidItem, None, None]:
    """
    設問の漢字書き取り問題に指定されたフレーズが含まれているかチェックします。

    Args:
        question_texts List[Paragraph]: 各問の文言を1要素としたList。

    Returns:
        InvalidItem: 指定フレーズが不足している場合のエラーメッセージを含むオブジェクト。
    """
    # 設問内の段落ごとに処理を行う
    for q_idx, paragraphs in enumerate(question_texts):
        # 各段落のテキストを改行で結合して一つの設問テキストを作成
        question_text = "\n".join(paragraph.text for paragraph in paragraphs)
        
        # 現代仮名遣いの指定フレーズが含まれているかチェック
        result = src.llm_util.check_phrase_in_writing_question(question_text)
        
        # 条件を満たす場合、エラーを生成
        if not result["is_target_evaluation"] or result["is_valid"]:
            return None
        
        # エラー表示用に設問テキストの先頭行を取得（最大15文字）
        error_text_one_line = question_text.splitlines()[0][:15]
        # 15文字を超える場合は末尾を "..." に丸める
        if len(question_text.splitlines()[0]) > 15:
            error_text_one_line = error_text_one_line[:12] + "..."
        
        # エラーメッセージを追加
        error_text = f"「{error_text_one_line}」付近で、「（楷書ではっきり大きく書くこと。）」というフレーズが不足しています。\n"

        # エラー内容を含むオブジェクトを返す
        result = InvalidItem(type="漢字書取り指示文不足", message=error_text)
        result.question_number=q_idx+1
        yield result
        
def convert_kanji_number_to_int(kanji_number)->int:
    """漢数字を数値に変換する
    不正な値があった場合はValueErrorを返す
    """
    kanji_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    if len(kanji_number) == 1:
        return kanji_map[kanji_number]
    
    elif len(kanji_number) == 2:
        if kanji_number == "十十":
            raise ValueError(f"不正な漢数字です: {kanji_number}")
        
        if kanji_number[0] == "十":
            return 10 + kanji_map[kanji_number[1]]
        
        elif kanji_number[1] == "十":
            return kanji_map[kanji_number[0]] * 10
        else:
            raise ValueError(f"不正な漢数字です: {kanji_number}")
    elif len(kanji_number) == 3:
        # 3文字の場合、1文字目に"一"がある場合は不正
        if kanji_number[0] == "一":
            raise ValueError(f"不正な漢数字です: {kanji_number}")
        
        # 3文字の場合、"十"は必ず2文字目になるはず、1文字目、3文字目はNG"
        # 三十一"はOK "十一二","一二十"はNG
        if kanji_number[0] == "十":
            raise ValueError(f"不正な漢数字です: {kanji_number}")
        if kanji_number[1] != "十":
            raise ValueError(f"不正な漢数字です: {kanji_number}")
        if kanji_number[2] == "十":
            raise ValueError(f"不正な漢数字です: {kanji_number}")


        return kanji_map[kanji_number[0]] * 10 + kanji_map[kanji_number[2]]
    else:
        raise ValueError(f"不正な漢数字です: {kanji_number}")
    
def check_number_order(numbers:List[int], kanji_index:List[str]) -> None:
    """整数のリストが連番になっているかをチェックする
    """
    for i in range(1, len(numbers)):
        if numbers[i] != numbers[i-1] + 1:
            yield InvalidItem(type="問の番号不正", message=f"問題番号が連番になっていません: {kanji_index[i-1]}の次に{kanji_index[i]}があります")

# 問の漢数字パターン
kanji_question_pattern = re.compile(r"問([一二三四五六七八九十]+)")

def check_kanji_question_index_order(paragraphs: List[object]) -> None:
    """段落が「問[漢数字]」で始まり、順番通りになっているかチェック"""
    integers = []
    kanji_index = [] # 問の漢数字を保持するリストメッセージ出力用に利用する

    errors = []
    for paragraph in paragraphs:

        text = "".join(paragraph.text)
        if text.startswith("問"):
            match = kanji_question_pattern.match(text)
            if match:
                kanji = match.group(1)
                kanji_index.append(kanji)
                try:
                    int_value = convert_kanji_number_to_int(kanji)
                    integers.append(int_value)
                except ValueError as e:
                    errors.append(InvalidItem(type="問の番号不正", message=str("len({kanji_index}+1)番目の問の番号の漢数字が不正です: {kanji}")))
            else:
                # textを" "または"、"、"。”、"　"で分割して、最初の要素を取得する
                invalid_index = re.split(r"[、　。 ]", text)[0]
                errors.append(InvalidItem(type="問の番号不正", message=f"問の番号が漢数字になっていません: {invalid_index}"))
    # integersの整数の値が1からの連番になっているかをチェックする
    if integers[0] != 1:
        errors.append(InvalidItem(type="問の番号不正", message=f"問の番号が一から始まっていません: {kanji_index[0]}"))
    # 連番チェック
    order_error = check_number_order(integers, kanji_index) 
    for oe in order_error:
        errors.append(oe)

    return errors

def check_kanji_reading_missing_expressions(question_texts: Document):
    error_text = ""
    for q_index, paragraphs in enumerate(question_texts):
        question_text = ""
        for paragraph in paragraphs:
            question_text += str(paragraph.text) + "\n"
        result = src.llm_util.check_modern_kana_usage(question_text)
        if not result["is_target_evaluation"] or result["is_modern_kana_usage_specified"]:
            return None

        error_text_one_line = question_text.splitlines()[0]
        # 15文字以上だと丸める
        if len(error_text_one_line) > 15:
            error_text_one_line = error_text_one_line[:15 - 3] + "..."
        
        error_text += f"「{error_text_one_line}」付近で、「（現代仮名遣いでよい。）」というフレーズが不足しています。\n"
    
        result_item  =  InvalidItem(type="漢字読み取り指示文不足", message=error_text)
        result_item.question_number = q_index+1

def check_question_sentence_word_count(question_texts, answer_texts):
    """問題文で文字数について言及されているものと解説文の文字数が一致しているかチェック"""
    question_list = []
    answer_list = []

    # 質問部分のテキストを抽出
    for paragraphs in question_texts:
        question_text = ""
        for paragraph in paragraphs:
            question_text += paragraph.text
        if question_text:
            question_list.append(src.llm_util.extract_question_sentence_word_count(question_text))
    
    # 解説部分のテキストを抽出
    answer_record_flg = False
    for paragraphs in answer_texts:
        answer_text = ""
        for paragraph in paragraphs:
            if paragraph.text == "●本文解説":
                answer_record_flg = True
                break
            if answer_record_flg is False:
                answer_text += paragraph.text
        if answer_text:
            answer_list.append(src.llm_util.extract_question_sentence_word_count(answer_text))

    # 評価
    # 結果を格納するリスト
    mismatched_word_count = []
    
    # `is_target_evaluation` が True の項目をフィルタリング
    target_questions = [q for q in question_list if q['is_target_evaluation']]
    target_answers = [a for a in answer_list if a['is_target_evaluation']]
    
    # 質問番号をキーにした辞書を作成（高速なアクセスのため）
    question_dict = {q['question_no']: q for q in target_questions}
    answer_dict = {a['question_no']: a for a in target_answers}
    
    # 質問リストをループして得点の一致を確認
    for question in target_questions:
        question_no = question['question_no']
        question_word_count = question['word_count'] 
        
        # 解説内にこの設問の文字数について言及されているか確認
        answer = answer_dict.get(question_no)
        if not answer:
            mismatched_word_count.append({
                'question_no': question_no,
                'reason': '解説内にこの設問の文字数について言及されていません。'
            })
            continue
        
        answer_score = answer['word_count']
        
        # 文字数が一致しているか確認
        if question_word_count != answer_score:
            mismatched_word_count.append({
                'question_no': question_no,
                'reason': '文字数が一致していません。'
            })
    
    # 解説リストをループして、解説にのみ言及されている文字数がないか確認
    for answer in target_answers:
        answer_no = answer['question_no']
        if answer_no not in question_dict:
            mismatched_word_count.append({
                'question_no': answer_no,
                'reason': '解説文にのみ文字数が言及されています。'
            })
            
    # 結果を返す
    if len(mismatched_word_count) > 0:
        problem_message= ""
        for mismatch in mismatched_word_count:
            problem_message += f'問題番号：{mismatch["question_no"]}、理由：{mismatch["reason"]}\n'
            
        return InvalidItem(type="指定文字数不一致", message=f'問題と解説で指定されている文字数に一致していないものがあります。[{problem_message}]')
    
def check_not_ordinary_kanji_without_ruby(doc:Document, start:int, end:int)->Generator[InvalidItem, None, None]:
    """常用漢字以外の漢字にルビがついていることをチェックする"""
    # ルビが付いている漢字のリストを取得
    runs_with_not_ordinary_kanji = src.doc_util.get_runs_with_not_ordinary_kanji_without_ruby(doc.paragraphs[start:end+1])
    # ルビが付いている漢字が通常の漢字かチェック
    for kanji, parag in runs_with_not_ordinary_kanji:
        yield InvalidItem(type="ルビの欠如", message=f"非常用漢字「{kanji}」にルビがついていません。 該当段落[{parag.text}]")

# def check_modern_translation(doc:Document, start:int end:int):
#     """現代仮名遣いで書かれているかチェックする"""
#     # 本文解説のブロックを取得する
#     # 現代語訳のブロックを取得する
#     # 本文解説のブロックから引用文リストを取得する
#     # 現代語訳のブロックに引用文リストが含まれているかチェックする
            

