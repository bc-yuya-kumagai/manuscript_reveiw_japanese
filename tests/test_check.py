import unittest
from src.check import check_choices_mapping
from src.doc_util import  extract_question_paragraphs
from src.check import check_heading_question_font
from docx import Document

# テスト対象のサンプルファイルパス
SAMPLE_DOCX_PATH = "tests/resources/スタイル付_【問題A】自動原稿整理PoC_サンプル原稿（指摘箇所コメント付）.docx"


class TestCanConstructFromIndexLists(unittest.TestCase):
    def test_check_choices_mapping_valid(self):
        """正常系のテスト - 選択肢が正しくマッピングされている場合"""
        question_text = """
        次の文章について、最も適切なものを1～4から選べ。
        
        1 選択肢その1
        2 選択肢その2
        3 選択肢その3
        4 選択肢その4
        """
        
        # リストに変換して検証（ジェネレータから）
        results = list(check_choices_mapping(question_text))
        assert len(results) == 0  # エラーがないことを確認

    def test_check_choices_mapping_missing_choice(self):
        """異常系のテスト - 設問文で参照される選択肢が実際の選択肢にない場合"""
        question_text = """
        次の文章について、最も適切なものを1～5から選べ。
        
        1 選択肢その1
        2 選択肢その2
        3 選択肢その3
        4 選択肢その4
        """
        
        results = list(check_choices_mapping(question_text))
        assert len(results) > 0
        assert any(r.type == "選択肢不足" for r in results)
        assert any("選択肢5" in r.message for r in results)

    def test_check_choices_mapping_extra_choice(self):
        """異常系のテスト - 実際の選択肢が設問文で参照されていない場合"""
        question_text = """
        次の文章について、最も適切なものを1～2から選べ。
        
        1　山田
        2　森口
        3　佐藤
        """
        
        results = list(check_choices_mapping(question_text))
        assert len(results) > 0
        assert any(r.type == "設問文での選択肢不足" for r in results)
        assert any("選択肢3" in r.message for r in results)

    def test_check_choices_mapping_unknown_errors(self):
        """異常系のテスト - 複数のエラーがある場合"""
        question_text = """問一　二重傍線部ⓐ・ⓑの本文中における意味として最も適当なものを、次の各群の１～５のうちからそれぞれ一つずつ選び、番号で答えよ。
　　　　　　　　　　　１　この上なく集中して
　　　　　　　　　　　２　ひたすらまっすぐに
ⓐ　しごく無雑作に　　３　きわめて軽はずみに
　　　　　　　　　　　４　すぐに目標を定めて
　　　　　　　　　　　５　まったく余裕なしに

　　　　　　　　１　様々に解釈した
　　　　　　　　２　繰り返し考えた
ⓑ　反芻した　　３　好ましく感じた
　　　　　　　　４　一つずつ検証した
　　　　　　　　５　心に刻んだ
"""
        
        results = list(check_choices_mapping(question_text))
        assert len(results) == 0


    def test_check_choices_mapping_unknown_errors2(self):

        question_text="""問六　Ａさんたちのグループは、授業で【文章Ⅰ】を読んだ後、より理解を深めるために本文中に登場するインコについて話し合いをすることになった。次の【文章Ⅱ】は、同じ「夢の子供」の【文章Ⅰ】より後の部分で、「私」が子供のころ母親の麻子と二人で一週間ほど暮らした過疎の山村を改めて訪ねて行き、神社に立ち寄ってそこで祭りに参加した体験を追想した後に続く場面である。【文章Ⅰ】と【文章Ⅱ】を踏まえ、【会話文】における空欄　Ｘ　～　Ｚ　に当てはまる内容として最も適当なものを、後の各群の１～４のうちからそれぞれ一つずつ選び、番号で答えよ。

【文章Ⅱ】
カラスの鳴き声がしじまを破った。私は身震いして追想からさめた。一部だけ色のついたモノクロの短編映画を見ったような気がした。カラスたちは神社を囲む杉のに一羽ずつとまって、怪しみながら私を見おろしていた。
　神社の一帯をねぐらにしているのだろう。私が泉と暮らしている近辺にもカラスは多いが、日が沈むころになると黒雲のように固まって町を出ていく。〈翠たち〉は今日もベランダに来ただろうか、と考えた。遠い外国のことを考えるようなで。日本産のカラスと帰化したインコとは、どちらがんでいる土地に順応しているかといえば、それはカラスに決まっている。大昔から日本で暮らしていて、別の国から強制連行されたわけではないのだから。でも記憶の豊かさからいうと、インコにはかなわないだろう。何しろ〈翠たち〉の体には数代前の大陸での生活記録が刷りこまれているのである。その記憶が海を越えて、時間を超えてったとしたら？　もしかしたらよそ者であるインコによる新しい伝説が、私たちの町でも進行中なのかも……。
【会話文】
Ａさん――主人公の「私」は〈翠たち〉に対して特別な思いを抱いているようですね。
Ｂさん――そうですね。【文章Ⅰ】でも「彼女がいなくなってからも〈翠たち〉に夢中になっている」（69・70行目）と書かれています。
Ｃさん――ということは、亡くなった母親というきっかけとは関わりなく、「私」自身がベランダに現れる〈翠たち〉に執着してい　　　るということでしょうか。【文章Ⅰ】を読むと、「私」が特に　Ｘ　にこだわっているように思われます。
Ｄさん――たしかにそう読めますね。だからこそ、管理人との会話が頭から離れなかったのでしょう。では、そのことと【文章Ⅱ】で書かれていることとは、どう関わるのでしょうか。
Ｂさん――「私」が追想からさめるきっかけとなった「カラスの鳴き声」は、【文章Ⅰ】でインコの鳴き声が出てくるという点で関　　　　　　　　係がありそうに思われます。
Ａさん――はい、たしかにそれはそうなのですが、カラスをきっかけに「私」の思いは〈翠たち〉の方へと向かっていますから、単　独でカラスに意味があるわけではなさそうです。
Ｄさん――なるほど、ということは　Ｙ　の方により重要な意味があるのではないでしょうか。「私」はカラスがインコにはかなわないと考えているのですから。
Ｃさん――そうなると、「私」は単純に大昔から暮らしている土地に棲みつづけることよりも、　Ｚ　に関心を抱いていて、そこに　　価値をしているということでしょうか。
Ａさん――そのように解釈できますね。「夢の子供」の中のインコの意味合いをより深く理解できたように思います。

　１　〈翠たち〉がエスニック調の美しい羽色をもつこと
　　　　２　〈翠たち〉がカメラに本能的な恐怖心を抱いていること
　　　　３　〈翠たち〉がそばに人がいてもえさを食べるほど馴れたこと
　　　　４　〈翠たち〉が先祖の遺伝子を受け継いでいること

　１　カラスがインコよりも土地に順応していること
　　　　２　〈翠たち〉が今日もベランダに来たかどうか
　　　　３　カラスやインコの日本で暮らした記憶の豊かさ
　　　　４　〈翠たち〉のもつ数代前の大陸での生活記録
　１　受け継いだものにこだわらず新たに記憶を蓄積していくこと
　　　　２　遠い外国に移り住んでその土地に順応していくこと
　　　　３　先祖の記憶が時空を超えて新たに受け継がれていくこと
　　　　４　強制的に連行されても異国でたくましく生きていくこと
"""
        results = list(check_choices_mapping(question_text))
        assert len(results) == 0

def test_heading_font_check():
    """既存のサンプルファイルを用いて font_analyzer 関数をテストする。"""
    doc = Document(SAMPLE_DOCX_PATH)
    extract_paragraphs = extract_question_paragraphs(doc)

    # check_heading_question_font の結果を確認
    check_heading_question_font_item = check_heading_question_font(SAMPLE_DOCX_PATH, extract_paragraphs)

    # 結果が None であることを期待
    assert check_heading_question_font_item is None, f"check_heading_question_font の結果が None ではありません: {check_heading_question_font_item}"


if __name__ == '__main__':
    unittest.main()
