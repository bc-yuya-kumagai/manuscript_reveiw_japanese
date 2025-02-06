from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class QuestionFormat(Enum):
    SELECTION = "選択式"
    DESCRIPTIVE = "記述式"
    KANJI_WRITING = "漢字の書き取り"
    KANJI_READING = "漢字の読み取り"

class Choice(BaseModel):
    """選択肢
    選択肢のテキストと、正解かどうかを保持する
    """
    index: str

class Question(BaseModel):
    """問題
    問題番号、問題文、問題形式、選択肢を保持する
    """
    number: str
    text: str
    format: QuestionFormat
    choices: Optional[List[Choice]] = None

class SideLine(BaseModel):
    """傍線部
    傍線の種類と、添え字、棒線がかかるテキストを保持する
    """
    type: str
    index: str
    text: str

class Note(BaseModel):
    """注釈
    注釈の種類と、注釈がかかるテキストを保持する
    """
    index: str
    text: str

class Section(BaseModel):
    section_number: str
    body_text: Optional[str] = None
    questions: Optional[List[Question]] = []
    side_lines: Optional[List[SideLine]] = []
    notes: Optional[List[Note]] = []
    star_paragraph_index: Optional[int] = None
    end_paragraph_index: Optional[int] = None
    exam_category: Optional[str] = None
    score: Optional[int] = None