# ものづくり_原稿整理ツール 国語


## フォルダ構成## フォルダ構成

```text
manuscript_review/
├── src/                    # ソースコードフォルダ
│   ├── review.py            # メインプログラム
│   └── doc_util.py          # Word関連のユーティリティ
│   └── llm_util.py          # LLM関連のユーティリティ
│   └── check.py　　　　　　　# checkの実装
├── test/                  # テストフォルダ
├── docs/                   # 原稿配置フォルダ
├── requirements.txt        # 必要なパッケージ一覧
└── README.md            # プロジェクト説明
```
# 機能

## フォントチェック機能
指定されたWordファイル内の段落から「問~」形式の文字列を検出し、そのフォントが **MSゴシック**であるかを確認します。

### 問の連番チェックの前提条件
- 一から九十九までの漢数字とする
- 漢数字の〇利用しないものとする"問三〇"とは記載されず、"問三十"と記載されるものとする

### 解説文中に「正答」が含まれているかチェックを追加
- 「●設問解説」～「解答・配点」までのテキストを抜き出し、その中から問から次の問までの文章をLLMに送信する。解説の説明で、正答という表現が使われていないパターンである「したがって、正解は３」のようなものがあればNGとなる。

### エラー条件
- 「問~」のフォントが MSゴシック ではない場合。
