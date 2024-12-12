from src import doc_util
from src import llm_util
from src.check import InvalidItem,SideLine
import src.check as ck
import os 
from docx import Document
import re
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    docx_file = 'docs/【問題A】自動原稿整理PoC_サンプル原稿（指摘箇所コメント付）.docx'

    doc = Document(docx_file)
    first_question_paragraph_index:int = doc_util.get_first_question_paragraph_index(doc)
    if not first_question_paragraph_index:
        logger.error('問の見出しスタイルIDが見つかりませんでした')
        os._exit(1)
        
    passage_side_line_runs = doc_util.get_underline_runs(doc, 0, first_question_paragraph_index-1)
    # question_side_lines = doc_util.get_underline_runs(doc, first_question_paragraph_index, -1)
    # 傍線部のひとつ前のrunを傍線の添え字Indexとして、添え字と傍線部のテキストをマップにする
    passage_sideLine_list = []
    for run in passage_side_line_runs:
        passage_sideLine_list.append( SideLine(index_text=doc_util.get_previous_text_index_run(run).text, passage=run.text))

  
    ## 傍線部の添え字毎の件数を取得する
    # FIXME ページの変わり目だと、傍線部の添え字が重複してしまう
    passage_sideLine_list = doc_util.clean_sileline_list_in_page_break(passage_sideLine_list)
    invalid_list = []
   
    # 傍線部の添え字が重複しているかをチェックする
    invalid_list += ck.check_duplicated_index(passage_sideLine_list)
    if(len(invalid_list) == 0):
        logger.info('傍線部の添え字が重複していない')
        
    # 傍線部の連番に飛びがないかチェックする
    check_jumped_index_result =  ck.check_jumped_index(passage_sideLine_list)
    if isinstance(check_jumped_index_result,InvalidItem):
        invalid_list.append(check_jumped_index_result)
    else:
        logger.info('傍線部の連番に飛びがない')
    # 傍線部の添え字がすべて設問の中で参照されているかをチェックする
    slideline_questions = list(doc_util.get_paragraph_text_by_keyword(doc, "傍線部"))

    result_sl_mapping = ck.check_mapping_sileline_index_userd_in_questions(passage_sideLine_list, slideline_questions)
    if isinstance(result_sl_mapping,InvalidItem):
        invalid_list.append(result_sl_mapping)
    else:
        logger.info('傍線部の添え字がすべて設問の中で参照されている')
    # 設問の中の添え字が問題文中に現れるかをチェックする
    result_sl_mapping = ck.check_mapping_sileline_index_appear_in_passage(passage_sideLine_list, slideline_questions)

    if isinstance(result_sl_mapping,InvalidItem):
        invalid_list.append(result_sl_mapping)
    else:
        logger.info('設問の中の添え字が問題文中に現れる')
    
    ## エラー出力
    if invalid_list:
        for i in invalid_list:
            logger.error(f'エラー：{i.type}、{i.message}')
