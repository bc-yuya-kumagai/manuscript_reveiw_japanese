import json

import requests
# dotenvを利用して環境変数を読み込む
from dotenv import load_dotenv
import os
import logging
load_dotenv()


# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

querystring = {"api-version":"2024-02-15-preview"}

url = os.environ.get('AOAI_ENDPOINT')

url = "https://ver-oai-commonoai-009.openai.azure.com/openai/deployments/ver-commonoai-gpt4o-mini/chat/completions"

querystring = {"api-version":"2024-02-15-preview"}

check_payload_template = {
    "messages": [
        {
            "role": "system",
            "content": "あなたは校正担当者です。今回は国語のテストの問題の校正を行います。\n{{TASK}}"
        },
        {
            "role": "user"
        }
    ],
    "max_tokens": 4096,
    "response_format":{ "type": "json_object" },

}

headers = {
    "Content-Type": "application/json",
    "api-key": f"{os.environ.get('AOAI_API_KYE')}"
}

def qreate_task__payload(task_text:str, user_text:str):
    # check_payload_templateをdeep copy
    payload = json.loads(json.dumps(check_payload_template))
    payload["messages"][0]["content"] = payload["messages"][0]["content"].replace("{{TASK}}", task_text.replace("　", "  "))
    payload["messages"][1]["content"] = user_text.replace("　", "  ")
    return payload


def get_text_indexes_from_question(question_text:str):
    task_text = """テストの設問文が与えられますので、あなたはその文中から、本文にあると推測される傍線部の添え字をすべてピックアップしてください。
    解答に際してはJSON形式の配列を回答してください["1", "2","3"]
    添え字の型はすべてstringです。
    
    例: "二重傍線部ⓐ・ⓑの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。"であれば、{"result":["ⓐ","ⓑ"]} と回答してください。
    添え字の種類は様々で、1,2だったり、（あ）,（い）,（う）だったりします。また、問題文中の表現も多様です
    1 から 10であったり、a～dのように中間の添え字を省略する場合があります。"""

    # payloadを作成
    payload = qreate_task__payload(task_text, question_text) 
    
    # リクエストを送信
    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

    # レスポンスからcontentの文字列を取得
    response_content = response.json()['choices'][0]['message']['content']

    # contentをJSONとしてパースしてPythonのリストに変換
    parsed_content = json.loads(response_content)

    return parsed_content['result']

def get_question_type(question_text:str):
    """引数で与えられた問題文から、選択問題か記述問題かを取得する"""
    task_text="""あなたは、この設問が選択式か、記述式かを以下のJSON形式
{"type": "選択式"} または {"type": "記述式"} のどちらかを回答してください。
選択式の列挙形式行のは地面に番号があるもの
１　外に出すことなく
２　感情を無視して
３　無意識に示す
４　意図的に作る
５　冷静に保つ

行の先頭にはリード文がありその後方にスペースでインデントをそろえて選択肢並ぶ場合があります。

                        １　突然考えを起こした
                        ２　しばらく無駄に考えた
ⓐ　じっと思いを巡らせて  ３　深く考え続けた
                        ４　何も思い浮かばなかった
                        ５　ただ面倒に感じた
"""

    # payloadを作成
    payload = qreate_task__payload(task_text, question_text) 
    
    # リクエストを送信
    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

    # レスポンスからcontentの文字列を取得
    response_content = response.json()['choices'][0]['message']['content']

    # contentをJSONとしてパースしてPythonのリストに変換
    parsed_content = json.loads(response_content)
    
    return parsed_content

def check_question2choices_mapping(question_text:str):
    """設問文にある選択肢のバリエーションが実際の選択肢に存在するかをチェックする"""

    task_text = """選択問題の設問と選択肢が与えられます。あなたは、この設問文内に示された選択肢が、実際の選択肢に存在するかを確認し、
    設問文の選択肢が不足していた場合それぞれの内容を回答してください。
    その際、形式はJSONのリスト形式となります。
    [{"type":"選択肢不足","message":"設問中の選択肢3が実際の選択肢に存在しません"},{"type":"選択肢不足","message":"設問中の選択肢4が実際の選択肢に存在しません"}]
    回答内容が1件しかない場合も要素1の配列として、
     {"type":"選択肢不足","message":"設問中の選択肢4が実際の選択肢に存在しません"}]
    のように回答してください。
    
設問中の選択肢は
"本文中における意味として最も適当なものを1,2,3,4,5のうちからそれぞれ一つずつ選び、番号で答えよ。"
    のように個別に列挙される場合と
"本文中における意味として最も適当なものを1～5のうちからそれぞれ一つずつ選び、番号で答えよ。" 
のように範囲指定される場合があります。範囲指定された場合は、範囲内の選択肢がすべて存在するかを確認してください。
設問文で示される選択肢が、すべて実際の選択肢に存在する場合は空のリスト
[]
を回答してください。

選択式の列挙形式行のは地面に番号があるもの
１　外に出すことなく
２　感情を無視して
３　無意識に示す
４　意図的に作る
５　冷静に保つ

行の先頭にはリード文がありその後方にスペースでインデントをそろえて選択肢並ぶ場合があります。

                        １　突然考えを起こした
                        ２　しばらく無駄に考えた
ⓐ　じっと思いを巡らせて  ３　深く考え続けた
                        ４　何も思い浮かばなかった
                        ５　ただ面倒に感じた

    """
    # payloadを作成
    payload = qreate_task__payload(task_text, question_text) 
    logger.info(f"payload[{json.dumps(payload,ensure_ascii=False)}]")

    # リクエストを送信
    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

    # レスポンスからcontentの文字列を取得
    response_content = response.json()['choices'][0]['message']['content']
    # contentをJSONとしてパースしてPythonのリストに変換
    parsed_content = json.loads(response_content)
    # parsed_contentが配列かどうかをチェック
    if not isinstance(parsed_content, list):
        parsed_content = [parsed_content]

    logger.info(parsed_content)
    return parsed_content



def check_choices2question_mapping(question_text:str):
    """実際の選択肢のバリエーションが設問文に存在するかをチェックする"""

    task_text = """選択問題の設問と選択肢が与えられます。あなたは、問題内で示される選択肢が、設問文に存在するかを確認し、
    選択肢が設問文に示されていない場合、それぞれの内容を回答してください。
    その際、形式はJSONのリスト形式で、以下のように回答してください。
    [{"type":"設問文での選択肢記載漏れ","message":"設問中の選択肢3が設問文に存在しません"},{"type":"設問文での選択肢記載漏れ","message":"設問中の選択肢4が設問文に存在しません"}]
選択で示される選択肢が、すべて設問文に存在する場合は空のリスト
[]
を回答してください。
    
設問中の選択肢は
"本文中における意味として最も適当なものを1,2,3,4,5のうちからそれぞれ一つずつ選び、番号で答えよ。"
    のように個別に列挙される場合と
"本文中における意味として最も適当なものを1～5のうちからそれぞれ一つずつ選び、番号で答えよ。" 
のように範囲指定される場合があります。範囲指定された場合は、範囲内の選択肢がすべて存在するかを確認してください。

選択式の列挙形式行のは地面に番号があるもの
１　外に出すことなく
２　感情を無視して
３　無意識に示す
４　意図的に作る
５　冷静に保つ

行の先頭にはリード文がありその後方にスペースでインデントをそろえて選択肢並ぶ場合があります。

                        １　突然考えを起こした
                        ２　しばらく無駄に考えた
ⓐ　じっと思いを巡らせて  ３　深く考え続けた
                        ４　何も思い浮かばなかった
                        ５　ただ面倒に感じた
    """
    # payloadを作成
    payload = qreate_task__payload(task_text, question_text) 
    logger.info(f"payload[{json.dumps(payload,ensure_ascii=False)}]")
    # リクエストを送信
    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

    # レスポンスからcontentの文字列を取得
    response_content = response.json()['choices'][0]['message']['content']
    # contentをJSONとしてパースしてPythonのリストに変換
    parsed_content = json.loads(response_content)
    if not isinstance(parsed_content, list):
        parsed_content = [parsed_content]
    logger.info(parsed_content)
    return parsed_content
