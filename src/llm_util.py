import json
from typing import List

import requests
# dotenvを利用して環境変数を読み込む
from dotenv import load_dotenv
import os
import logging
from pydantic import BaseModel
load_dotenv()


# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

querystring = {"api-version":"2024-02-15-preview"}

url = os.environ.get('AOAI_ENDPOINT')


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
    try:
        # リクエストを送信
        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        if response.status_code != 200:
            logger.error(f"response[{response.json()}]")
            raise Exception(f"response[{response.json()}]")  
        # レスポンスからcontentの文字列を取得
        response_content = response.json()['choices'][0]['message']['content']

        # contentをJSONとしてパースしてPythonのリストに変換
        parsed_content = json.loads(response_content)

        return parsed_content['result']

    except Exception as e:
        logger.error(f"response[{response.json()}]")
        raise e
def get_question_type(question_text:str):
    """引数で与えられた問題文から、選択問題か記述問題かを取得する"""
    task_text="""あなたは、この設問が選択式か、記述式かを以下のJSON形式
{"type": "選択式"} または {"type": "記述式"} のどちらかを回答してください。
選択式の列挙形式には以下の2種類があります。
1. フラットに並んだ文字列の行頭に番号があるもの
    １　外に出すことなく
    ２　感情を無視して
    ３　無意識に示す
    ４　意図的に作る
    ５　冷静に保つ

2. 行の先頭には見出し文がありその後方にインデントを行って選択肢が並ぶもの
（以下では、「ⓐ　じっと思いを巡らせて 」の配下に選択肢１～５が並んでいます）
                        １　突然考えを起こした
                        ２　しばらく無駄に考えた
ⓐ　じっと思いを巡らせて  ３　深く考え続けた
                        ４　何も思い浮かばなかった
                        ５　ただ面倒に感じた

            
"""

    # payloadを作成
    payload = qreate_task__payload(task_text, question_text) 
    try:
        # リクエストを送信
        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        if response.status_code != 200:
            logger.error(f"response[{response.json()}]")
            raise Exception(f"response[{response.json()}]")
        # レスポンスからcontentの文字列を取得
        response_content = response.json()['choices'][0]['message']['content']

        # contentをJSONとしてパースしてPythonのリストに変換
        parsed_content = json.loads(response_content)
        
        return parsed_content
    except Exception as e:
        logger.error(f"response[{response.json()}]")
    raise e    

class ChoiceINdexesFromChoices(BaseModel):
    def __init__(self, head_line:str, choices:List[str]):
        self.head_line = head_line
        self.choices = choices
class ChoiceIndexesFromChoicesList(BaseModel):
    def __init__(self, choice_indexes:List[ChoiceINdexesFromChoices]):
        self.choice_indexes = choice_indexes


def get_choice_indexes_from_choices_list(question_text:str):
    """選択肢のインデックスを取得する"""
    task_text = """選択肢を含んだ設問が与えられますので、あなたはその設問文中から、選択肢の見出しとその下の選択肢のインデックスをすべてピックアップしてください。
その際、形式はJSONの配列形式となります。
[{"head_line":"<選択肢見出しのテキスト>","choices":["<インデックス１>","<インデックス２>","<インデックス３>","<インデックス４>","<インデックス５>"]}]
要素数が1の場合もオブジェクトではなく、配列で返してください。
要素数が0の場合は空の配列を返してください。
選択肢見出しが存在しない場合は、head_lineには空文字を設定してください。

選択式の列挙形式には複数のパターンがあるので、以下の例を参考にしてください。
1. 選択肢見出しが存在しない、フラットに並んだ文字列の行頭に番号があるもの

１　外に出すことなく
２　感情を無視して
３　無意識に示す
４　意図的に作る
５　冷静に保つ

この場合の応答は 
[{"head_line":"","choices":["１","２","３","４","５"]}]
となる


2. 選択肢見出しが存在し、行の先頭に見出し文がありその後方にインデントを行って選択肢が並ぶもの

例2.1
                        １　突然考えを起こした
                        ２　しばらく無駄に考えた
ⓐ　じっと思いを巡らせて  ３　深く考え続けた
                        ４　何も思い浮かばなかった
                        ５　ただ面倒に感じた
この場合の応答は 
[{"head_line":"ⓐ　じっと思いを巡らせて","choices":["１","２","３","４","５"]}]
となる

例2.2
　Ｘ　　１　〈翠たち〉がエスニック調の美しい羽色をもつこと
　　　　２　〈翠たち〉がカメラに本能的な恐怖心を抱いていること
　　　　３　〈翠たち〉がそばに人がいても餌を食べるほど馴れたこと
　　　　４　〈翠たち〉が先祖の遺伝子を受け継いでいること
この場合の応答は 
[{"head_line":"Ｘ","choices":["１","２","３","４"]}]
となる

選択肢は段組みや、改行で分かれて並ぶことがあります。その場合も選択肢の見出しと選択肢のペアを把握してください。

見出しと、選択肢のは複数列挙される場合があり、その列挙形式も様々で、

例2.3
見出しと選択肢のペアが、段組みされて横に並ぶもの
　　　　　　１　読むのに苦労しない　　　　　　　　　　　　　　　１　長々しく責めとがめること
　　　　　　　２　普及するような　　　　　　　　　　　　　　　　　２　非難を抑えきれずに口にすること
ⓐ　十全な　　３　誤解する余地がない　　　ⓑ　もどかしい繰り言　　３　はがゆくて何度も言うこと
　　　　　　　４　感心するような　　　　　　　　　　　　　　　　　４　まとまらない気持ちを伝えること
　　　　　　　５　欠けたところがない　　　　　　　　　　　　　　　５　焦って要領を得ない説明をすること
この場合の応答は 
[{"head_line":"ⓐ　十全な","choices"choices":["１","２","３","４","５"]},{"head_line":"ⓑ　もどかしい繰り言","choices":["１","２","３","４","５"]}]

例2.4
見出しなしで、選択肢が段組みされて横に並ぶもの
　　　　　　　　　　　１　数年来不仲であった　　　　　　　　　　　　　　１　たいそう自慢していた
　　　　　　　　　　　２　美しい盛りの年齢の　　　　　　　　　　　　　　２　大変富み栄えていた
　　　　　　　　　　　３　長年連れ添ってきた　　　　　　　　　　　　　　３　非常に苦労していた
　　　　　　　　　　　４　貧しさを嫌う年頃の　　　　　　　　　　　　　　４　とても厳しい態度でいた
この場合の応答は
[{"head_line":"","choices":["１","２","３","４"]},{"head_line":"","choices":["１","２","３","４"]}]
となる


例2.5
見出しと選択肢のペアが、改行で分かれて並ぶもの

　Ｙ　　１　日本産のカラスと帰化したインコの違い
　　　　２　〈翠たち〉が今日もベランダに来たかどうか
　　　　３　カラスとインコが土地に順応しているかどうか
　　　　４　〈翠たち〉のもつ数代前の大陸での生活記録
　Ｚ　　１　受け継いだものにこだわらず新たに記憶を蓄積していくこと
　　　　２　遠い外国に移り住んでそこで土地に順応していくこと
　　　　３　先祖の記憶が時空を超えて新たに受け継がれていくこと
　　　　４　強制的に連行されても異国でたくましく生きていくこと
この場合の応答は 
[{"head_line":"Ｙ","choices":["１","２","３","４"]},{"head_line":"Ｚ","choices":["１","２","３","４"]}]



    """
    # payloadを作成
    payload = qreate_task__payload(task_text, question_text) 

    logger.info(f"payload[{json.dumps(payload,ensure_ascii=False)}]")
    try:
        # リクエストを送信
        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        if response.status_code != 200:
            logger.error(f"response[{response.json()}]")
            raise Exception(f"response[{response.json()}]")
        # レスポンスからcontentの文字列を取得
        response_content = response.json()['choices'][0]['message']['content']
        # contentをJSONとしてパースしてPythonのリストに変換
        parsed_content = json.loads(response_content)
        # parsed_contentが配列かどうかをチェック
        
        if not isinstance(parsed_content, list):
            parsed_content = [parsed_content]

        logger.info(parsed_content)
        return parsed_content
    except Exception as e:
        logger.error(f"response[{response.json()}]")
        raise e
def get_choice_indexes_from_question_text(question_text:str):
    """設問文から選択肢のバリエーションを取得する"""
    task_text = """選択肢を含んだ設問が与えられます。前半に設問文があり、後半に選択肢の具体的な内容が記載されています。あなたは前半設問文の中から選択肢インデックスのリストを作成してください。。
その際、形式はJSONの配列形式となります。
{"question":"設問文中のインデックスのリスト抽出の選択肢の根拠となる箇所", "choices":["<選択肢インデックス１>","<選択肢インデックス２>","<選択肢インデックス３>","<選択肢インデックス４>","<選択肢インデックス５>"]}
 
例えば、設問が以下のような場合
問一　二重傍線部ⓐ・ⓑの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。
　　　　　　　　　　　１　この上なく集中して
　　　　　　　　　　　２　ひたすらまっすぐに
ⓐ　しごく無造作に　　３　きわめてたやすく
　　　　　　　　　　　４　すぐに目標を定めて
　　　　　　　　　　　５　まったく余裕なしに

"問一　二重傍線部ⓐ・ⓑの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。"
の部分が設問文に当たり、
"１～５のうちからそれぞれ一つずつ選び、"との記述があるため、以下のように回答してください。
{"question":"１～５","choices":["１","２","３","４","５"]}
となります。
設問文以外の箇所については無視してください。
問三  二重傍線部Aの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。
                      １  この上なく集中して
                      ２  ひたすらまっすぐに
ⓐ  しごく 無造作に   
                      ３  すぐに目標を定めて
という設問文が与えられた場合の解答は以下のように回答してください
{"question":"１～５", "choices":["１","２","３","４","５"]}


応答の際、以下の場合に気を付けてください
選択肢の要素数が1の場合もオブジェクトではなく、配列で返してください。
選択肢の要素数が0の場合は空の配列を返してください。
"""

    # payloadを作成
    payload = qreate_task__payload(task_text, question_text)
    logger.info(f"payload[{json.dumps(payload,ensure_ascii=False)}]")
    try:
        # リクエストを送信
        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        if response.status_code != 200:
            logger.error(f"response[{response.json()}]")
            raise Exception(f"response[{response.json()}]")        
        # レスポンスからcontentの文字列を取得
        response_content = response.json()['choices'][0]['message']['content']
        # parsed_contentが配列かどうかをチェック
        parsed_content = json.loads(response_content)

        return parsed_content
    except Exception as e:
        logger.error(f"response[{response.json()}]")
        raise e

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
    try:
        # リクエストを送信
        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        if response.status_code != 200:
            logger.error(f"response[{response.json()}]")
            raise Exception(f"response[{response.json()}]")
        # レスポンスからcontentの文字列を取得
        response_content = response.json()['choices'][0]['message']['content']
        # contentをJSONとしてパースしてPythonのリストに変換
        parsed_content = json.loads(response_content)
        if not isinstance(parsed_content, list):
            parsed_content = [parsed_content]
        logger.info(parsed_content)
        return parsed_content
    except Exception as e:
        logger.error(f"response[{response.json()}]")
        raise e
    

def check_keyword_in_explanation(content: str, keyword: str) -> dict:
    """
    指定された単語が問題文の引用であればチェックせず、解説の文章に含まれている場合は結果とどの部分かを返却する。

    Args:
        content (str): 入力された文章。
        keyword (str): チェックする単語。

    Returns:
        dict: 結果を含むJSON形式の辞書。
    """
    messages = [
        {
            "role": "system",
            "content": (
                f"Check the text to see if it contains the **exact keyword** '{keyword}' (case-sensitive). "
                "The keyword must match exactly, without considering synonyms, derived words, or similar phrases. "
                "Evaluate only the explanation section, and ignore the problem statement. "
                "Return True only if the exact keyword is found in the explanation section."
            )
        },
        {
            "role": "user",
            "content": (
                "Evaluate the following text for the presence of the exact keyword in the explanation section:\n"
                "===\n"
                f"{content}\n"
                "===\n"
            )
        }
    ]

    json_schema = {
        "name": "KeywordCheckResponse",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "isFind": {
                    "type": "boolean",
                    "description": "Indicates whether the specified keyword was found in the text."
                },
                "content": {
                    "type": ["string", "null"],
                    "description": "The text where the keyword was found, or null if not found."
                }
            },
            "required": ["isFind", "content"],
            "additionalProperties": False
        }
    }

    payload = {
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": json_schema
        }
    }

    # リクエスト送信
    try:
        response = requests.post(url, headers=headers, json=payload, params={"api-version":"2024-08-01-preview"})
        response.raise_for_status()
        return response.json()  # JSONレスポンスを返す
    except Exception as e:
        logger.error(f"response[{response.json()}]")
        raise e