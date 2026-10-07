from core.QuesServ import QuestionService, QuestionMode, QuesBody
from core.QuesServ import QuestionSwitchError, QuestionEndError, ToIndexError, ZeroIndexError
from pathlib import Path
from time import time
from re import match as re_match


BASE = Path(__file__).resolve().parent
QMode = {
    "order":QuestionMode.order, "new":QuestionMode.new, "err":QuestionMode.err,
    "exam":QuestionMode.exam, "mem":QuestionMode.mem
}


def time_fmt(sec:int) ->str:
    """将秒数格式化为时分秒"""
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f" {h}时{m}分{s}秒 "

def ans_summa(s_time:int, e_time:int, correct:int, error:int) ->str:
    """生成答题总结"""
    time_use = e_time - s_time
    total = correct+error
    if total != 0:
        accur = correct/total
    else:
        accur = 0
    return (f"练习结束!\n"
            f"用时:{time_fmt(time_use)}\n"
            f"本次练习你答了{total}题,其中正确{correct}题,错误{error}题,准确率{accur:.1%}。")


class Core:
    QS = QuestionService(BASE / "assets" / "data")
    Page = "ModeSet"
    QS.init_ques()
    def __init__(self):
        self.Ready = self.QS.init_ques()

    def get_mode_txt(self):
        return self.QS.QuesMode.name

    def set_mode(self, mode:str) -> bool:
        if mode not in QMode: return False
        self.QS.QuesMode = QMode[mode]
        self.Ready = self.QS.init_ques()
        return True

    def propose_ques(self, qbody:QuesBody|None=None) ->tuple[int,tuple, bool]:
        """向用户提问并返回问题信息"""
        if not qbody:
            qbody = self.QS.get_next_ques()
        qopt = qbody.opts
        if len(qbody.opts) > 2:
            qopt = f"\nA. {qopt[0]}\nB. {qopt[1]}\nC. {qopt[2]}\nD. {qopt[3]}"
            opts_list = ("A", "B", "C", "D")
        else:
            qopt = "\nA. 对\nB. 错"
            opts_list = ("A", "B")
        ans_alr = "本次练习已回答过该题，再次回答会覆盖记录!\n" if qbody.ans_alr else ""
        print(f"{ans_alr}第{self.QS.QBase.ques_curr + 1}题: {qbody.ques}"
              f"{qopt}\n\n"
              f"tip: 上一题: UP ;下一题: DOWN ;跳转至题: TO(题号) ;题号范围: RANGE ;结束练习: HOME,获取帮助: HELP。")
        return qbody.qid, opts_list, qbody.ans_alr

    def commit_reply(self, qid:int=-1, opts_list:tuple=(), reply:str="") ->tuple[str, any]:
        """在答题界面询问并响应用户回答"""
        commite_list = (*opts_list, "UP", "DOWN", "TO", "RANGE", "HOME", "HELP") #所有有效回复
        ures = reply
        if not reply:
            ures = input("请回复: ")
        while True:
            if not (ures in commite_list or "TO" in ures):
                ures = input("无效输入\n重新回复: ")
                continue
            if ures in opts_list:
                return "Grading", self.QS.reply(qid, ures)
            else:
                try:
                    match ures:
                        case "UP":
                            return "QBody", self.QS.get_prev_ques()
                        case "DOWN":
                            return "QBody", self.QS.get_next_ques()
                        case "HOME":
                            return "ToHome", None
                        case "RANGE":
                            res = self.QS.get_ques_len()
                            print(f"当前可用题号范围:1~{res}题。")
                            ures = input("请回复: ")
                        case "HELP":
                            print(f"当前可用回复: ", commite_list,
                                  "\ntip: 上一题: UP ;下一题: DOWN ;跳转至题: TO(题号) ;题号范围: RANGE ;结束练习: HOME,获取帮助: HELP")
                            ures = input("\n请回复: ")
                        case _:
                            index = re_match(r"TO\(([0-9]+)\)", ures)
                            if index is None:
                                ures = input("TO命令的合法格式应为\"TO(题号)\",如\"TO(1)\"即切换到第一题。\n重新回复: ")
                                continue
                            index = int(index.group(1))
                            return "QBody", self.QS.to_index(index)
                except ToIndexError:
                    ures = input("指定题号不存在,你可能需要使用RANGE查看题号范围\n重新回复： ")
                except QuestionSwitchError:
                    if self.QS.QBase.ques_curr == 0:
                        ures = input("当前已经是第一题\n重新回复: ")
                    else:
                        ures = input("当前已经是最后一题，可尝试切换题号，或练习模式针对练习新题或错题\n重新回复: ")
                except ZeroIndexError:
                        ures = input("指定的题号不能为0\n重新回复: ")


class ConsoMain(Core):
    def run_cheduler(self):
        """页面调度器"""
        while not self.Page == "Exit":
            match self.Page:
                case "ModeSet":
                    self.mode_guide_page()
                case "Home":
                    self.home_page()
                case "AnsQues":
                    self.ans_ques_page()
                case "Reset":
                    self.reset_page()

    def mode_guide_page(self):
        print(f"当前练习模式为: {self.get_mode_txt()}\n"
               "可用练习模式:\n"
               "order:  顺序练习，从最近一道没做过的题开始练习\n"
               "new:    新题模式，只练没做过的题\n"
               "err:    错题模式，只练做错的题\n"
               "exam:   考试模式，按考试规则进行模拟考试\n"
               "mem:    背题模式，直接提供每题的正确答案\n")
        ures = input("选择新的练习模式(回车以取消更改):")
        ures = ures.lower()   #适配交互习惯
        while True:
            if ures == '' or self.set_mode(ures):
                self.Page = "Home"
                return
            else:
                ures = input(f"没有 \"{ures}\" 模式\n重新选择: ")

    def home_page(self):
        print("\n"
              "******************************\n"
              "|  欢迎使用QuizDrill控制台版本!  |\n"
              "******************************\n\n"
              " A.开始练习 B.修改模式\n"
              " C.重置数据 D.退出程序")
        while True:
            ures = input("提供选项以进行下一步:")
            ures = ures.lower()
            match ures:
                case "a":
                    self.Page = "AnsQues"
                    return
                case "b":
                    self.Page = "ModeSet"
                    return
                case "c":
                    self.Page = "Reset"
                    return
                case "d":
                    self.Page = "Exit"
                    return

    def reset_page(self):
        self.Page = "Home"
        ures = input("\n警告: 重置操作不可恢复，请详细考虑接下来的操作!\n"
                     "A.重置练习记录\n"
                     "B.重置考试记录\n"
                     "C.重建数据库\n\n"
                     "提供选项以进行下一步(选项外的输入直接返回主页):")
        match ures.lower():
            case "a":
                ures = input("\n输入\"ok\"确认重置,否则返回主页: ") == "ok"
                if ures: self.QS.reset_stat() ; print("已重置练习记录!")
            case "b":
                ures = input("\n输入\"ok\"确认重置,否则返回主页: ") == "ok"
                if ures: self.QS.reset_exams() ; print("已重置考试记录!")
            case "c":
                ures = input("警告: 本操作将清空练习数据并根据题库重建练习状态映射,这可能解决某些异常或题库变更问题。\n"
                             "输入\"ok\"确认重置,否则返回主页: ") == "ok"
                if ures: self.QS.rebuilt_data_base() ; print("已重建状态表!")


    def ans_ques_page(self):
        if not self.Ready:
            self.Page = "ModeSet"
            input("(当前模式无可练习内容，回车以选取新的模式)")
            return
        if self.QS.QuesMode == QuestionMode.mem:
            self.mem_mode_page()
            return
        s_time = int(time()) ; currect = 0 ; error = 0
        qid, opts_list, ans_alr= self.propose_ques()
        err = False
        ans_end = lambda :input(f"{ans_summa(s_time, int(time()), currect, error)}\n(按回车返回主页)")
        try:
            while True:
                if not err: res = self.commit_reply(qid, opts_list)
                err = False
                match res[0]:
                    case "Grading":
                        res = res[1]
                        if res["res"]:
                            if not ans_alr: currect += 1
                            print("回答正确!")
                        else:
                            if not ans_alr: error += 1
                            ans = res["ans"]
                            print(f"回答错误,正确答案是:{ans}")
                            input("(回车以进入下一题)")
                        if self.QS.QuesMode == QuestionMode.exam:
                            used_time = int(time()) - s_time
                            if used_time < 3600:  #一小时考试时间
                                print(f"剩余考试时间: {time_fmt(3600-used_time)}")
                            else:
                                print("\n考试时间结束!当前答题结果不计入成绩。")
                                if res and currect != 0: currect -= 1
                                raise QuestionEndError("Exam end.")
                        try:
                            qid, opts_list, ans_alr = self.propose_ques()
                        except QuestionSwitchError:
                            err = True
                            ures = input("当前已经是最后一题，可尝试切换练习模式针对练习新题或错题\n请回复: ")
                            res = self.commit_reply(reply=ures)
                    case "QBody":
                        qbody = res[1]
                        qid, opts_list, ans_alr = self.propose_ques(qbody)
                    case "ToHome":
                        self.Page = "Home"
                        if self.QS.QuesMode == QuestionMode.exam:
                            print(f"手动结算考试不进考试记录!\n本次考试得分: {currect}分")
                        ans_end()
                        return
        except QuestionEndError:
            if self.QS.QuesMode == QuestionMode.exam:
                self.QS.submit_exam(s_time, used_time, currect)
                print(f"本次考试得分: {currect}分")
            ans_end()
            self.Page = "Home"

    def mem_mode_page(self):
        print("背题模式需手动控制题号!")
        opts_list = ()
        qid, _,_ = self.propose_ques()
        while True:
            ans = self.QS.QBase.get_ans_opt(qid)
            print(f"正确答案: {ans}")   #不先打印初次进入不会提供答案
            res = self.commit_reply(qid, opts_list)
            match res[0]:
                case "QBody":
                   qbody = res[1]
                   qid, _,_ = self.propose_ques(qbody)
                case "ToHome":
                    self.Page = "Home"
                    return


if __name__ == "__main__":
    app = ConsoMain()
    app.run_cheduler()
    pass