from typing import List, Callable

class Interval:
    def __init__(self, items: List[object], start: int, end: int):
        self.items = items
        self.start = start
        self.end = end
    
def extract_intervals(
    data: List,
    is_start: Callable[[any], bool],
    is_end: Callable[[any], bool]
) -> List[Interval]:
    """リストデータから区間を抽出する
    開始と終了の間の区間を取得する
    開始の後にさらに開始が来た場合は、終了を待たずに新しい区間が開始されたものと判定する
    リストの最後に終了がない場合は、リストの最後尾までを最後の区間として取得する
    
    Args:
        data (List): 区間を抽出するリストデータ
        is_start (Callable[[any], bool]): 区間の開始を判定する関数
        is_end (Callable[[any], bool]): 区間の終了を判定する関数

    Returns:
        List[Interval]: 抽出された区間のリスト

    """
    intervals = []
    stack = []
    for i, item in enumerate(data):
        try:
            if is_start(item):
                if stack:
                    intervals.append(Interval(stack.pop(), start, i))
                stack.append([item])
                start = i
            elif is_end(item):
                if stack:
                    stack[-1].append(item)
                    intervals.append(Interval(stack.pop(), start, i))
            elif stack:
                stack[-1].append(item)
        except Exception as e:
            print(e)
            raise e
    if stack:
        intervals.append(Interval(stack.pop(), start, len(data)))
    return intervals

# 変換テーブルを作成
zenkaku2hankaku_table = str.maketrans({
    '０': '0',
    '１': '1',
    '２': '2',
    '３': '3',
    '４': '4',
    '５': '5',
    '６': '6',
    '７': '7',
    '８': '8',
    '９': '9',
})
