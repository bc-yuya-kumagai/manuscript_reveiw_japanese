import json

import requests
# dotenvを利用して環境変数を読み込む
from dotenv import load_dotenv
import os
load_dotenv()

querystring = {"api-version":"2024-02-15-preview"}

url = os.environ.get('AOAI_ENDPOINT')

url = "https://ver-oai-commonoai-009.openai.azure.com/openai/deployments/ver-commonoai-gpt4o-mini/chat/completions"

querystring = {"api-version":"2024-02-15-preview"}


headers = {
    "Content-Type": "application/json",
    "api-key": f"{os.environ.get('AOAI_API_KYE')}"
}
def get_text_indexes_from_question(question_text:str):
    payload = {
    "messages": [
        {
            "role": "system",
            "content": "あなたは校正担当者です。今回は国語のテストの問題の校正を行います。\nテストの設問文が与えられますので、あなたはその文中から、本文にあると推測される傍線部の添え字をすべてピックアップしてください。\n解答に際してはJSON形式の配列を回答してください[\"1\", \"2\",\"3\"]\n添え字の型はすべてstringです。\n\n例: \"二重傍線部ⓐ・ⓑの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。\"であれば、[\"ⓐ\", \"ⓑ\"]\" と回答してください。\n添え字の種類は様々で、1,2だったり、（あ）,（い）,（う）だったりします。また、問題文中の表現も多様です\n1 から 10であったり、a～dのように中間の添え字を省略する場合があります。"
        },
        {
            "role": "user"
        }
    ],
    "max_tokens": 4096
}
    # リクエストのcontentを設定
    payload['messages'][1]['content'] = question_text
    # リクエストを送信
    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

    # レスポンスからcontentの文字列を取得
    response_content = response.json()['choices'][0]['message']['content']

    # contentをJSONとしてパースしてPythonのリストに変換
    parsed_content = json.loads(response_content)

    return parsed_content