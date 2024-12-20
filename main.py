from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from docx import Document
import logging
import os
from src import doc_util
from src import check as ck
from src.check import InvalidItem, SideLine

app = FastAPI()

# CORSの設定（必要に応じて）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def analyze_docx(docx_file_path: str):
    """
    docx_file_pathで指定されたWordファイルを分析し、
    不備リストとメッセージを返す関数。
    """
    doc = Document(docx_file_path)

    # 問の見出しが最初に始まる箇所を特定
    first_question_paragraph_index:int = doc_util.get_first_question_paragraph_index(doc)
    if not first_question_paragraph_index:
        return {"errors":[{"type":"INDEX_NOT_FOUND","message":"問の見出しスタイルIDが見つかりませんでした"}]}
    
    # 傍線部取得
    passage_side_line_runs = doc_util.get_underline_runs(doc, 0, first_question_paragraph_index-1)

    passage_sideLine_list = []
    for run in passage_side_line_runs:
        passage_sideLine_list.append( SideLine(index_text=doc_util.get_previous_text_index_run(run).text, passage=run.text))

    # ページ区切り等による添字のクリーニング
    passage_sideLine_list = doc_util.clean_sileline_list_in_page_break(passage_sideLine_list)
    invalid_list = []

    # 傍線部の添え字重複チェック
    invalid_list += ck.check_duplicated_index(passage_sideLine_list)

    # 傍線部の連番飛びチェック
    jumped = ck.check_jumped_index(passage_sideLine_list)
    if isinstance(jumped,InvalidItem):
        invalid_list.append(jumped)

    # 傍線部の添え字が設問内で参照されているかチェック
    slideline_questions = list(doc_util.get_paragraph_text_by_keyword(doc, "傍線部"))
    result_sl_mapping = ck.check_mapping_sileline_index_userd_in_questions(passage_sideLine_list, slideline_questions)
    if isinstance(result_sl_mapping, InvalidItem):
        invalid_list.append(result_sl_mapping)

    # 設問内の添字が問題文中にあるかチェック
    result_sl_mapping = ck.check_mapping_sileline_index_appear_in_passage(passage_sideLine_list, slideline_questions)
    if isinstance(result_sl_mapping, InvalidItem):
        invalid_list.append(result_sl_mapping)

    # 選択肢関連チェック
    get_question_texts = doc_util.get_question_texts(doc)
    for question in get_question_texts:
        if ck.get_question_type(question) == "選択式":
            errors = ck.check_choices_mapping(question)
            invalid_list.extend(errors)
    
    # 結果整形
    result = {"errors":[]}
    if invalid_list:
        for i in invalid_list:
            result["errors"].append({"type": i.type, "message": i.message})
    else:
        result["message"] = "問題なし"
    return result


@app.get("/", response_class=HTMLResponse)
async def home_page():
    # 簡易的なアップロードフォーム
    return """
    <html>
        <head><title>Word Check</title></head>
        <body>
            <h1>Wordファイルアップロード</h1>
            <form action="/upload" enctype="multipart/form-data" method="post">
            <input name="docx_file" type="file" accept=".docx">
            <input type="submit" value="アップロードしてチェック">
            </form>
        </body>
    </html>
    """


@app.post("/upload")
async def upload_and_check(docx_file: UploadFile = File(...)):
    if docx_file.content_type not in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="docxファイルをアップロードしてください")

    # 一時ファイルとして保存
    temp_file_path = f"temp_{docx_file.filename}"
    with open(temp_file_path, "wb") as f:
        f.write(await docx_file.read())

    # 分析実行
    result = analyze_docx(temp_file_path)

    # 一時ファイル削除
    os.remove(temp_file_path)

    return result
