from core.QuesServ import QuestionService, QuestionMode, StrideIndexError,QuestionEndError , QuesBody
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
    return f" {h} : {m} : {s} "

def ans_summa(s_time:int, e_time:int, correct:int, error:int) ->str:
    """生成答题总结"""
    time_use = e_time - s_time
    total = correct+error
    accur = (correct//total) if (correct or error) else 0 #0==False,防止除0
    return (f"练习结束!\n"
            f"用时:{time_fmt(time_use)}\n"
            f"本次练习你答了{total}题,其中正确{correct}题,错误{error}题,准确率{accur}%")


class Core:
    QS = QuestionService(BASE / "assets" / "data")
    Opts_dict = {"A":0, "B":1, "C":2, "D":3}
    page = "ModeSet"

    def get_mode_txt(self):
        return self.QS.QuesMode.name

    def set_mode(self, mode:str) -> bool:
        if mode not in QMode: return False
        self.QS.QuesMode = QMode[mode]
        return True

    def propose_ques(self, qbody:QuesBody|None=None) ->tuple[int,tuple]:
        if not qbody:
            qbody = self.QS.get_next_ques()
        qopt = qbody.opts
        if len(qbody.opts) > 2:
            qopt = f"\nA. {qopt[0]}\nB. {qopt[1]}\nC. {qopt[2]}\nD. {qopt[3]}"
            opts_list = ("A", "B", "C", "D")
        else:
            qopt = "\nA. 对\nB. 错"
            opts_list = ("A", "B")
        print(f"第{qbody.qid + 1}题： {qbody.ques}\n"
              f"{qopt}\n"
              f"tip: 上一题: UP ; 下一题: DOWN ;跳转至题: TO(题号) ;题号范围: RANGE ;结束练习: HOME")
        return qbody.qid, opts_list

    def commit_reply(self, qid:int, opts_list:tuple) ->tuple[str, any]:
        """在答题界面询问并响应用户回答"""
        commite_list = (*opts_list, "UP", "DOWN", "TO", "RANGE", "HOME")   #所有有效回复
        ures = input("请回复: ")
        while True:
            if ures not in commite_list:
                ures = input("无效输入，重新回复: ")
                continue
            if ures in opts_list:
                ures = self.Opts_dict[ures]
                return "Grading", self.QS.reply(qid, ures)
            else:
                try:
                    match ures:
                        case "UP":
                            return "QBody", self.QS.get_prev_ques()
                        case "DOWN":
                            return "QBody", self.QS.get_next_ques()
                        case "HOME":
                            self.page = "Home"
                            return "ToHome", None
                        case "TO":
                            index = re_match(r"TO\(([0-9]+)\)", ures)
                            if index is None:
                                ures = input("TO命令的合法格式应为\"TO(题号)\"，重新回复: ")
                                continue
                            index = int(index.group(1))
                            return "QBody", self.QS.to_index(index)
                        case "RANGE":
                            res = self.QS.get_ques_len()
                            print(f"当前可用题号范围:1~{res}题。")
                            ures = input("请回复: ")
                except StrideIndexError:
                    ures = input("指定题号不存在,你可能需要使用RANGE查看题号范围,重新回复： ")
                except IndexError:
                    ures = input("超出题号范围,重新回复: ")


class ConsoMain(Core):
    def run_cheduler(self):
        """页面调度器"""
        while not self.page == "Exit":
            match self.page:
                case "ModeSet":
                    self.mode_guide_page()
                case "Home":
                    self.home_page()
                case "AnsQues":
                    self.ans_ques_page()

    def mode_guide_page(self):
        print(f"当前练习模式为: {self.get_mode_txt()}\n"
               "可用练习模式:\n"
               "order:  顺序练习，从最近一道没做过的题开始练习\n"
               "new:    新题模式，只练没做过的题\n"
               "err:    错题模式，只练做错的题\n"
               "exam:   考试模式，按考试规则进行模拟考试\n"
               "mem:    背题模式，直接提供每题的正确答案\n")
        while True:
            ures = input("选择新的练习模式(回车以取消更改):")
            if ures == '' or self.set_mode(ures):
                self.page = "Home"
                return
            else:
                print(f"没有 \"{ures}\" 模式,请重新选择\n")

    def home_page(self):
        print("******************************\n"
              "|  欢迎使用QuizDrill控制台版本!  |\n"
              "******************************\n\n"
              " A.开始练习 B.修改模式 C.退出程序 \n")
        while True:
            ures = input("提供选项以进行下一步:")
            match ures:
                case "A":
                    self.page = "AnsQues"
                    return
                case "B":
                    self.page = "ModeSet"
                    return
                case "C":
                    self.page = "Exit"
                    return

    def ans_ques_page(self):
        s_time = time() ; currect = 0 ; error = 0
        qid, opts_list = self.propose_ques()
        ans_end = lambda :input(f"{ans_summa(int(s_time), int(time()), currect, error)}\n(按回车返回主页)")
        try:
            while True:
                res = self.commit_reply(qid, opts_list)
                match res:
                    case "Grading":
                        if res[0]:
                            currect += 1
                        else:
                            error +=1
                        self.propose_ques()
                    case "QBody":
                        qbody = res[1]
                        self.propose_ques(qbody)
                    case "ToHome":
                        ans_end()
                        return
        except QuestionEndError:
            ans_end()


if __name__ == "__main__":
    app = ConsoMain()
    app.run_cheduler()