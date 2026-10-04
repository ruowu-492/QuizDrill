import sqlite3
from enum import Enum, IntEnum, StrEnum
from os.path import join as path_join
from random import sample
from json import load


# 数据库操作枚举
class OptionEnum(Enum):
    pass
class StatEnum(OptionEnum):
    NotAns = None
    AnsCorrect = True
    AnsError = False
class TypeEnum(OptionEnum):
    Chose = True
    Jubg = False
class ColumnEnum(StrEnum):
    ID = "ID"
    STAT = "STAT"
    TYPE = "TYPE"
class DBEnum:
    Column = ColumnEnum
    Stat = StatEnum
    Type = TypeEnum
# 工作模式枚举
class QuestionMode(IntEnum):
    NULL = 0
    Order = 1
    NewQues = 2
    ErrQues = 3
    Exam = 4
    MemQues = 5


class QuesBody:
    def __init__(self, qid: int, question: str, options: list[str], answer:int|None=None, ans_aly:bool=False):
        self.qid = qid
        self.ques = question
        self.opts = options
        self.ans = answer
        self.ans_aly = ans_aly

    def keys(self):
        return "qid", "ques", "opts", "ans", "ans_aly"

    def __getitem__(self, item):
        return getattr(self, item)


class DBBase:
    def __init__(self, db_path):
        self.DB = sqlite3.connect(path_join(db_path, "database.db"))

    def select_id(self, column:DBEnum.Column, value:OptionEnum, need_min:bool=False) -> sqlite3.Cursor:
        """在数据库查找符合需求的id"""
        val = "ID"
        if need_min: val = "MIN(ID)"
        return self.DB.execute(f"SELECT {val} FROM QUES WHERE {column.value} IS ?", (value.value,))

    def update_stat(self, qid: int, stat: bool):
        """更新答题数据,自动提交事务"""
        par = (stat, qid)
        self.DB.execute("UPDATE QUES SET STAT = ? WHERE ID = ?", par)
        self.DB.commit()

    def get_ans_sly(self, qid:int) -> bool:
        res = self.DB.execute("SELECT STAT FROM QUES WHERE ID = ?", (qid,))
        res = res.fetchall()[0]   #fetchall以tuple[tuple]返回，需先拿到预期的行tuple
        # STAT=NULL为未回答，对应None。如查询结果是None会返回True，即已回答，需取反为正确含义
        return not res[0] is None

    def exec(self, sql: str, par: dict | tuple | list = ()) -> sqlite3.Cursor:
        """执行自定义SQL并自动提交事务"""
        res = self.DB.execute(sql, par)
        self.DB.commit()
        return res


class QuestionBase(DBBase):
    ques_list = []
    ques_curr = None
    exam_score = None

    def __init__(self, path) -> None:
        super().__init__(path)
        with open(path_join(path, "question.json"), "r", encoding="utf-8") as f:
            ques = load(f)
            self.QUES = {int(qid): que for qid, que in ques.items()}
        #如果QUES表不存在则新建并初始化
        db_res = self.exec("SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='QUES')")
        if not db_res.fetchone()[0]:
            self.exec("CREATE TABLE QUES(ID INT PRIMARY KEY NOT NULL,STAT BOOL,TYPE BOOL)")
            self.rebuild_db()

    def null_mode_init(self):
        raise TypeError("Question mode not set.")

    def order_mode_init(self):
        db_res = self.select_id(DBEnum.Column.STAT, DBEnum.Stat.NotAns, need_min=True)
        res = db_res.fetchone()
        self.ques_curr = res[0]-1001   #初始ID为1000，对应索引0，随后递增
        self.ques_list = list(self.QUES)

    def new_mode_init(self):
        self.ques_curr = -1
        db_res = self.select_id(DBEnum.Column.STAT, DBEnum.Stat.NotAns)
        self.ques_list = [res[0] for res in db_res.fetchall()]

    def err_mode_init(self):
        self.ques_curr = -1
        db_res = self.select_id(DBEnum.Column.STAT, DBEnum.Stat.AnsError)
        self.ques_list = [res[0] for res in db_res.fetchall()]

    def exam_mode_init(self):
        self.ques_curr = -1
        db_res = self.select_id(DBEnum.Column.TYPE, DBEnum.Type.Chose)
        choice = [qid[0] for qid in db_res.fetchall()]
        choice = sample(choice, 80)
        db_res = self.select_id(DBEnum.Column.TYPE, DBEnum.Type.Jubg)
        jubg = [qid[0] for qid in db_res.fetchall()]
        jubg = sample(jubg, 20)
        self.ques_list = choice + jubg

    def mem_mode_init(self):
        self.ques_list = list(self.QUES)
        self.ques_curr = -1

    def get_correct_ans(self, qid: int) -> int:
        qbody = self.QUES[qid]
        return qbody["correct_index"]

    def get_a_ques(self, qid:int) -> QuesBody:
        body = self.QUES[qid]
        return QuesBody(qid, body["question"], body["optstion"], body["correct_index"])

    def rebuild_db(self):
        """清空现有状态表，然后根据题库重建映射"""
        qids = tuple(self.QUES)
        qtypes = []
        for qid in qids:
            qbody = self.QUES[qid]
            if len(qbody["options"]) > 2:
                qtypes.append(True)
            else:
                qtypes.append(False)
        self.exec("DELETE FROM QUES")
        par = []
        for i,t in zip(qids, qtypes):
            tmp = (i,t)
            par.append(tmp)
        self.DB.executemany("INSERT INTO QUES VALUES (?, NULL, ?)",par)
        self.DB.commit()

    def get_ques(self, direction:bool=True) -> QuesBody:
        if direction:
            self.ques_curr += 1
        else:
            self.ques_curr -= 1
        if self.ques_curr < 0:
            self.ques_curr = -1
            raise IndexError("list index out of range.")
        qid = self.ques_list[self.ques_curr]
        qbody = self.QUES[qid]
        ans = qbody["correct_index"]
        ans_aly = self.get_ans_sly(qid)
        return QuesBody(qid, qbody["question"], qbody["options"], ans, ans_aly)


class QuestionService:
    QuesMode = QuestionMode.NULL

    def __init__(self, assets_path):
        """题目管理接口初始化时需提供跨平台的资源文件夹路径"""
        self.QBase = QuestionBase(assets_path)

    def initques(self):
        match self.QuesMode:
            case QuestionMode.NULL:
                self.QBase.null_mode_init()
            case QuestionMode.Order:
                self.QBase.order_mode_init()
            case QuestionMode.NewQues:
                self.QBase.new_mode_init()
            case QuestionMode.ErrQues:
                self.QBase.err_mode_init()
            case QuestionMode.Exam:
                self.QBase.exam_mode_init()
            case QuestionMode.MemQues:
                self.QBase.mem_mode_init()

    def reply(self, qid: int, answei: int) -> tuple[bool, int]:
        """处理用户回答,返回判题结果和正确答案"""
        ans = self.QBase.get_correct_ans(qid)
        res = answei == ans
        self.QBase.update_stat(qid, res)
        return res, ans

    def to_index(self, index: int) -> QuesBody:
        self.QBase.ques_curr = index-1
        return self.QBase.get_a_ques(index)

    def get_ques_len(self) -> int:
        return len(self.QBase.QUES)

    def reset_stat(self):
        self.QBase.exec("UPDATE QUES SET STAT = NULL")

    def rebuilt_data_base(self):
        self.QBase.rebuild_db()

    def get_down_ques(self) -> QuesBody:
        return self.QBase.get_ques()

    def get_up_ques(self) -> QuesBody:
        return self.QBase.get_ques(False)


if __name__ == "__main__":
    from pathlib import Path
    BASE = Path(__file__).resolve().parent.parent
    ASSETS = BASE / "assets" / "data"
    QS = QuestionService(ASSETS)
    pass
    # QS.QuesMode = QuestionMode.Order
    # QS.initques()
    # QS.get_down_ques()
    # QS.QuesMode = QuestionMode.NewQues
    # QS.initques()
    # QS.QuesMode = QuestionMode.ErrQues
    # QS.initques()
    # QS.QuesMode = QuestionMode.Exam
    # QS.initques()
    # QS.QuesMode = QuestionMode.MemQues
    # QS.initques()
    # QS.get_down_ques()
    # QS.to_index(10)
    pass