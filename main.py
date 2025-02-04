from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from docx import Document
import logging
import os
from src import doc_util
from src import check as ck
from src.check import InvalidItem, SideLine
from src.entity import Section

app = FastAPI()

# CORSの設定（必要に応じて）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ロギングの設定を最初に行う
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# temp_problem_file_path, temp_solution_file_path
def analyze_problem_doc(problem_doc, temp_problem_file_path):
    invalid_list = []
    # # チェックエラーリスト
    # invalid_list = {
    #     "problem": [],  # 問題のチェックエラー
    #     "solution": [],  # 解説のチェックエラー
    #     "common": []  # 問題・解説共通のチェックエラー
    # }
    problem_invalid_list = []
    # 問題のみのチェック
    if problem_doc:
        sections:List[Section] = doc_util.extract_sections(problem_doc)
        for section in sections:
            # 問の見出しが最初に始まる箇所を特定 <- これが、問題文と設問の境界になる
            first_question_paragraph_index:int = doc_util.get_first_question_paragraph_index(problem_doc,start = section.star_paragraph_index, end=section.end_paragraph_index)
            if not first_question_paragraph_index:
                return {"errors":[{"type":"INDEX_NOT_FOUND","message":"問の見出しスタイルIDが見つかりませんでした"}]}
            
            # 傍線部取得（問題文の中から傍線部のrunを取得）
            passage_side_line_runs = doc_util.get_underline_runs(problem_doc, 0, first_question_paragraph_index-1)

            passage_sideLine_list = []
            for run in passage_side_line_runs:
                passage_sideLine_list.append( SideLine(index_text=doc_util.get_previous_text_index_run(run).text, passage=run.text))

            # ページ区切り箇所にゴミが残るのでそれを削除
            passage_sideLine_list = doc_util.clean_sileline_list_in_page_break(passage_sideLine_list)
            # 傍線部の添え字重複チェック
            problem_invalid_list += ck.check_duplicated_index(passage_sideLine_list)

        # 問のテキストを設問ごとにリストでの取得
        question_texts = doc_util.get_questions(problem_doc, start= section.star_paragraph_index, end=section.end_paragraph_index)

        # 選択肢設問の設問文で、「適切」ではなく「適当」となっているかチェックし、適切ならエラーを返す
        check_keyword_exact_match_in_question_statement = ck.check_keyword_exact_match_in_question(question_texts)
        if isinstance(check_keyword_exact_match_in_question_statement, InvalidItem):
            problem_invalid_list.append(check_keyword_exact_match_in_question_statement)

        # 傍線部の連番飛びチェック
        jumped = ck.check_jumped_index(passage_sideLine_list)
        if isinstance(jumped,InvalidItem):
            problem_invalid_list.append(jumped)

        # 傍線部の添え字が設問内で参照されているかチェック
        slideline_questions = list(doc_util.get_paragraph_text_by_keyword(problem_doc, "傍線部"))
        result_sl_mapping = ck.check_mapping_sileline_index_userd_in_questions(passage_sideLine_list, slideline_questions)
        if isinstance(result_sl_mapping, InvalidItem):
            problem_invalid_list.append(result_sl_mapping)

        # 設問内の添字が問題文中にあるかチェック
        result_sl_mapping = ck.check_mapping_sileline_index_appear_in_passage(passage_sideLine_list, slideline_questions)
        if isinstance(result_sl_mapping, InvalidItem):
            problem_invalid_list.append(result_sl_mapping)

        # 選択肢のチェック
        for question in question_texts:
            question_text = "\n".join([q.text for q in question])
            if ck.get_question_type(question_text) == "選択式":
                errors = ck.check_choices_mapping(question)
                problem_invalid_list.extend(errors)
        
        # 選択肢に重複や歯抜けがないかチェック
        for question in question_texts:
            question_text = "\n".join([q.text for q in question])
            if ck.get_question_type(question_text) == "選択式":
                errors = ck.check_choices_sequence(question)
                problem_invalid_list.append(errors)
                
        # 「適当でないもの」がMSゴシックであるかチェック
        for question in question_texts:
            result_check_font_of_unfit_item = ck.check_font_of_unfit_item(question)
            if isinstance(result_check_font_of_unfit_item, InvalidItem):
                problem_invalid_list.append(result_check_font_of_unfit_item)

        # 選択肢設問の設問文で、「適切」ではなく「適当」となっているかチェックし、適切ならエラーを返す
        check_keyword_exact_match_in_question_statement = ck.check_keyword_exact_match_in_question(question_texts)
        if isinstance(check_keyword_exact_match_in_question_statement, InvalidItem):
            problem_invalid_list.append(check_keyword_exact_match_in_question_statement)
        
        # 文書から「問」で始まるパラグラフを抽出する
        extract_paragraphs = doc_util.extract_question_paragraphs(problem_doc)

        # 「問~」がMSゴシックかチェック
        check_heading_question_font_item = ck.check_heading_question_font(temp_problem_file_path, extract_paragraphs)
        if isinstance(check_heading_question_font_item, InvalidItem):
            problem_invalid_list.append(check_heading_question_font_item)

        # 設問番号が順番通りになっているかチェック
        check_kanji_number_orders =  ck.check_kanji_question_index_order(extract_paragraphs)
        for error in check_kanji_number_orders:
            problem_invalid_list.append(error)

        #傍注の説明の内容が本文に入っているかチェック
        check_exists_annotation_result = ck.check_exists_annotation(problem_doc)
        if isinstance(check_exists_annotation_result, InvalidItem):
            problem_invalid_list.append(check_exists_annotation_result)

        # 設問の漢字書き取り問題に指定されたフレーズが含まれているかチェック
        check_writing_kanji_phrase_error = ck.check_phrase_in_kanji_writing_question(question_texts)
        if isinstance(check_writing_kanji_phrase_error, InvalidItem):
            problem_invalid_list.append(check_writing_kanji_phrase_error)

        # 漢字読み取り問題時に、「（現代仮名遣いでよい。）」というフレーズが使われているかチェック
        check_kanji_reading_missing_result = ck.check_kanji_reading_missing_expressions(question_texts)
        if isinstance(check_kanji_reading_missing_result, InvalidItem):
            problem_invalid_list.append(check_kanji_reading_missing_result)
    return problem_invalid_list

def analyze_solution_doc(solution_doc):
    invalid_list = []
    # 解説のみのチェック
    if solution_doc:
        # 解説中に正答番号を指すものに対して、正答というフレーズが正しく使用されているか確認する。
        check_explanation_of_questions_error = ck.check_explanation_of_questions_include_word(solution_doc)
        if isinstance(check_explanation_of_questions_error, InvalidItem):
            invalid_list["solution"].append(check_explanation_of_questions_error)
        
        # 記述設問の際、解説のポイントが存在しているかチェック
        check_answer_point = ck.check_answer_contains_points(solution_doc)
        if isinstance(check_answer_point, InvalidItem):
            invalid_list["solution"].append(check_answer_point)
    return invalid_list

def analyze_common_doc(problem_doc, solution_doc):
    invalid_list = []
    # 問題と解説両方をチェック
    if problem_doc and solution_doc:
        # 問のテキストを設問ごとにリストでの取得
        problem_texts = doc_util.get_questions(problem_doc)
        solution_texts = doc_util.get_questions(solution_doc)

        # 大問の配点をチェックする。
        part_question_score_check = ck.check_part_question_score(problem_doc, solution_doc)
        if isinstance(part_question_score_check, InvalidItem):
            invalid_list["common"].append(part_question_score_check)

        # 問題文で文字数について言及されているものと解説文の文字数が一致しているかチェック
        check_question_and_answer_word_count=ck.check_question_sentence_word_count(problem_texts, solution_texts)
        if isinstance(check_question_and_answer_word_count, InvalidItem):
            invalid_list["common"].append(check_question_and_answer_word_count)
    return invalid_list

def analyze_docx(temp_problem_file_path, temp_solution_file_path):
    """
    docx_file_pathで指定されたWordファイルを分析し、
    不備リストとメッセージを返す関数。
    """
    problem_doc = []
    solution_doc = []
    if temp_problem_file_path:
        problem_doc = Document(temp_problem_file_path)
    if temp_solution_file_path:
        solution_doc = Document(temp_solution_file_path)

    invalid_list = {
        "problem": [],
        "solution": [],
        "common": []
    }

    if problem_doc:
        invalid_list["problem"] = analyze_problem_doc(problem_doc,temp_problem_file_path=temp_problem_file_path)

    if solution_doc:
        invalid_list["solution"] = analyze_solution_doc(solution_doc)

    if problem_doc and solution_doc:
        invalid_list["common"] = analyze_common_doc(problem_doc, solution_doc)

    for category in ["problem", "solution", "common"]:
        invalid_list[category] = [error for error in invalid_list[category] if error is not None]

    result = {
        category: errors if errors else [{"message": "問題なし"}]
        for category, errors in invalid_list.items()
    }

    return result


@app.get("/", response_class=HTMLResponse)
async def home_page():
    # 簡易的なアップロードフォーム
    return """
        <html>
            <head>
                <title>国語原稿チェックツール 機能検証画面</title>
                <script>
                    function displayResponse(data) {
                        const output = document.getElementById('responseOutput');
                        output.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                        document.getElementById('loadingMessage').style.display = 'none';
                    }
                </script>
            </head>
            <body>
                <h1>Wordファイルアップロード</h1>
                <form id="uploadForm" action="/upload" enctype="multipart/form-data" method="post">
                    <label for="problem_file">問題ファイル (問題文):</label>
                    <input id="problem_file" name="problem_file" type="file" accept=".docx"><br><br>
                    
                    <label for="solution_file">解説ファイル (解説文):</label>
                    <input id="solution_file" name="solution_file" type="file" accept=".docx"><br><br>
                    
                    <input type="submit" value="アップロードしてチェック">
                </form>
                
                <div id="loadingMessage" style="display: none; font-weight: bold; color: blue; margin-top: 10px;">処理中...</div>
                <div id="responseOutput" style="white-space: pre-wrap; border: 1px solid #ccc; padding: 10px; margin-top: 20px;"></div>
                
                <script>
                    document.getElementById('uploadForm').addEventListener('submit', function(event) {
                        event.preventDefault();
                        
                        const formData = new FormData();
                        const problemFile = document.getElementById('problem_file').files[0];
                        const solutionFile = document.getElementById('solution_file').files[0];
                        
                        if (problemFile) {
                            formData.append('problem_file', problemFile);
                        }
                        
                        if (solutionFile) {
                            formData.append('solution_file', solutionFile);
                        }
                        
                        if (!problemFile && !solutionFile) {
                            alert('少なくとも1つのファイルを選択してください。');
                            return;
                        }
                        
                        document.getElementById('loadingMessage').style.display = 'block';
                        document.getElementById('responseOutput').innerHTML = '';
                        
                        fetch('/upload', {
                            method: 'POST',
                            body: formData
                        }).then(response => response.json())
                        .then(data => displayResponse(data))
                        .catch(error => {
                            document.getElementById('responseOutput').innerHTML = '<pre>エラーが発生しました: ' + error + '</pre>';
                            document.getElementById('loadingMessage').style.display = 'none';
                        });
                    });
                </script>
            </body>
        </html>
    """

async def save_temp_file(docx_file: UploadFile) -> str:
    """一時ファイルとしてdocxファイルを保存し、ファイルパスを返す"""
    temp_file_path = f"temp_{docx_file.filename}"
    with open(temp_file_path, "wb") as f:
        f.write(await docx_file.read())
    return temp_file_path

def delete_temp_file(file_path: str):
    """一時ファイルを削除する"""
    try:
        os.remove(file_path)
    except OSError as e:
        logger.error(f"Error deleting file {file_path}: {e}")

@app.post("/upload")
async def check_docx(problem_file: UploadFile = File(None), solution_file: UploadFile = File(None)):
    temp_problem_file_path = None
    temp_solution_file_path = None
    if problem_file:
        temp_problem_file_path = await save_temp_file(problem_file)
    if solution_file:
        temp_solution_file_path = await save_temp_file(solution_file)

    try:
        # 分析実行
        result = analyze_docx(temp_problem_file_path, temp_solution_file_path)
    finally:
        # 一時ファイル削除
        if problem_file:
            delete_temp_file(temp_problem_file_path)
        if solution_file:
            delete_temp_file(temp_solution_file_path)

    return result
