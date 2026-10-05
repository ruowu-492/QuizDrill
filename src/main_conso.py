from core.QuesServ import QuestionService, QuestionMode
from os.path import join as pathjoin
from pathlib import Path
from enum import StrEnum
from time import time


BASE = Path(__file__).resolve().parent
QMode = {
    "order":QuestionMode.order, "new":QuestionMode.new, "err":QuestionMode.err,
    "exam":QuestionMode.exam, "mem":QuestionMode.mem
}


class Core:
    QS = QuestionService(BASE / "assets" / "data")
    page = "ModeSet"
    start_time = None
    end_time = None

    def get_mode_txt(self):
        return self.QS.QuesMode.name

    def set_mode(self, mode:str) -> bool:
        if mode not in QMode: return False
        self.QS.QuesMode = QMode[mode]
        return True


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
        pass


if __name__ == "__main__":
    app = ConsoMain()
    app.run_cheduler()