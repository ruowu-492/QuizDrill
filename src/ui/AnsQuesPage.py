from ui.Custom import CountdownTimer, QIndexList
from core.QuesServ import QuestionMode, QuestionService
from core.QuesServ import QuestionEndError
from enum import IntEnum
from time import time
import flet as ft

class ExamStat(IntEnum):
    pause = 0
    timeout = 1
    fail = 2
    submit = 3

def ans_time_fmt(sec:int) ->str:
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
    return (f"用时:{ans_time_fmt(time_use)}\n"
            f"本次练习你答了{total}题,其中正确{correct}题,错误{error}题,准确率{accur:.1%}。")

option_dict = {0: "A", 1: "B", 2: "C", 3: "D"}
progre_txt = ft.Ref[ft.Text]()   #答题进度
ques_text = ft.Ref[ft.Text]()    #问题
ques_opt = ft.Ref[ft.ListView]()   #选项

class QuesEvens:
    currect = 0 ; error = 0 ;qbody = None
    ques_end = False ; is_fail = False
    def __init__(self, QS:QuestionService, page:ft.Page):
        self.QS = QS
        self.QS.init_ques()
        self.is_exam = self.QS.QuesMode == QuestionMode.exam
        self.is_mem = self.QS.QuesMode == QuestionMode.mem
        self.ques_len = QS.get_ques_len()
        self.QList = QIndexList()
        self.QList.build_items(self.ques_len, on_click=self.to_ques)
        self.timer = CountdownTimer(time=2700, on_finish=self.exam_to_home, data=ExamStat.timeout)
        self.progre_dict = {}  # 如果用户对于某题回答正确该value为True,否则为用户选择的索引
        self.s_time = int(time())
        self.page = page

    def to_home(self, e=None):
        if self.is_exam:
            self.exam_to_home(stat=ExamStat.pause)
        else:
            dialog = ft.AlertDialog(
                modal=True,
                title="练习结束!",
                content=ft.Text(ans_summa(self.s_time, int(time()), self.currect, self.error)),
                actions=[ft.Button("回家", on_click=lambda e:self.page.navigate("/"))],
                actions_alignment=ft.MainAxisAlignment.END
            )
            self.page.show_dialog(dialog)

    def exam_to_home(self, e=None, stat:ExamStat=None):
        self.timer.stop()
        if stat is None:
            stat = e.control.data
        time_use = int(time())-self.s_time
        match stat:
            case ExamStat.pause:
                if self.ques_end:
                    self.QS.submit_exam(self.s_time, time_use, self.currect*2)
                    dialog = ft.AlertDialog(
                        modal=True,
                        title="考试结束，成绩合格!",
                        content=ft.Text(f"本次考试成绩为: {self.currect*2}分"
                                        f"{ans_summa(self.s_time, int(time()), self.currect, self.error)}"),
                        actions=[ft.Button("回家庆祝", on_click=lambda e: self.page.navigate("/"))],
                        actions_alignment=ft.MainAxisAlignment.END
                    )
                    self.page.show_dialog(dialog)
                else:
                    dialog = ft.AlertDialog(
                        modal=True,
                        title="考试已暂停!",
                        content=ft.Text("已为你暂停考试，也可直接返回主页，但不会显示练习总结且不会记录本次考试。"),
                        actions=[
                            ft.Button("回家", on_click=lambda e: self.page.navigate("/")),
                            ft.Button("继续考试", on_click=lambda e: (self.timer.start(), self.page.pop_dialog()))
                        ],
                        actions_alignment=ft.MainAxisAlignment.END
                    )
                    self.page.show_dialog(dialog)
            case ExamStat.fail:
                dialog = ft.AlertDialog(
                    modal=True,
                    title="本次考试成绩已不合格!",
                    content=ft.Text("你现在可选继续考试或直接提交成绩。"),
                    actions=[
                        ft.Button("继续考试", on_click=lambda e: (self.timer.start(), self.page.pop_dialog())),
                        ft.Button("回家练习", on_click=lambda e: (
                            self.QS.submit_exam(self.s_time, time_use, self.currect * 2),
                            self.page.navigate("/")))],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                self.page.show_dialog(dialog)
            case ExamStat.timeout:
                self.QS.submit_exam(self.s_time, time_use, self.currect * 2)
                if self.currect*2 >=80:
                    title = "时间到,成绩合格!"
                else:
                    title = "时间到,成绩不合格!"
                dialog = ft.AlertDialog(
                    modal=True,
                    title=title,
                    content=ft.Text(f"本次考试成绩为: {self.currect * 2}分"
                                    f"{ans_summa(self.s_time, int(time()), self.currect, self.error)}"),
                    actions=[ft.Button("回家练习", on_click=lambda e: self.page.navigate("/"))],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                self.page.show_dialog(dialog)
            case ExamStat.submit:
                dialog = ft.AlertDialog(
                    modal=True,
                    title="准备提交!",
                    content=ft.Text(f"本次考试已获得{self.currect*2}分，及格分为80分，确认提交?"),
                    actions=[
                        ft.Button("继续考试", on_click=lambda e: (self.timer.start(), self.page.pop_dialog())),
                        ft.Button("确认提交", on_click=lambda e: (
                            self.QS.submit_exam(self.s_time, time_use, self.currect * 2),
                            self.page.navigate("/")))],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                self.page.show_dialog(dialog)

    def on_opt(self, e):
        ures = e.control.key
        qid = self.qbody.qid
        self.progre_dict[qid] = ures
        qindex = self.QS.QBase.ques_curr
        currect = self.qbody.ans_index
        if currect == ures:   #回答正确
            self.QList.update_item(qindex, ft.Colors.GREEN)
            self.currect += 1
        else:
            self.QList.update_item(qindex, ft.Colors.RED)
            self.error += 1
        progre_txt.current.value = f"{len(self.progre_dict)} / {self.ques_len}"
        self.QS.reply(qid, option_dict[ures])
        if not self.is_fail and self.is_exam and self.error*2 > 20:
            self.is_fail = True
            self.exam_to_home(stat=ExamStat.fail)
        if len(self.progre_dict) == self.ques_len:
            self.to_home()
        self.update_ques(switch=False)
        progre_txt.current.update()
        ques_opt.current.update()

    def to_ques(self, e):
        self.qbody = self.QS.to_index(e.control.key)
        self.update_ques(switch=False)
        ques_text.current.update()
        ques_opt.current.update()
        e.page.pop_dialog()

    def switch_ques_page(self, e):
        e.page.show_dialog(
            ft.BottomSheet(
                fullscreen=True,
                show_drag_handle=True,
                content=ft.Container(
                padding=ft.Padding.all(10),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self.QList,
                        ft.Button("退出跳题页", on_click=lambda: e.page.pop_dialog()),
                    ],
                ),),
            )
        )

    def next_ques(self, e=None):
        self.update_ques()

    def prev_ques(self, e):
        self.update_ques(False)

    def update_ques(self, direction:bool=True, switch:bool=True):
        try:
            if switch:
                if direction:
                    self.qbody = self.QS.QBase.get_ques()
                else:
                    self.qbody = self.QS.QBase.get_ques(False)
            ques_text.current.value = f"第{self.QS.QBase.ques_curr+1}题: {self.qbody.ques}"
            i = 0 ; body = [] ; qid = self.qbody.qid
            if self.is_mem:
                ans_alr = True
                self.progre_dict[qid] = self.qbody.ans_index
            else:
                self.qbody = self.QS.QBase.get_a_ques(qid)  #确保数据最新
                ans_alr = self.qbody.ans_alr
            for opt in self.qbody.opts:
                style = None
                index = option_dict[i]
                if ans_alr:
                    if self.qbody.ans_index == i:
                        style = ft.ButtonStyle(color=ft.Colors.GREEN, bgcolor=ft.Colors.GREEN_50)
                    elif self.progre_dict[qid] == i:   #用户回答
                        style = ft.ButtonStyle(color=ft.Colors.RED)
                body.append(
                    ft.TextButton(
                        key=i,
                        content=ft.Text(f"{index}. {opt}"),
                        style=style,
                        disabled=ans_alr,
                        on_click=self.on_opt
                    )
                )
                i += 1
            ques_opt.current.controls = body
        except QuestionEndError:
            self.to_home()
        except IndexError:
            pass


class AnsQues(QuesEvens):
    def __init__(self, ques_serv, page):
        super().__init__(ques_serv, page)

    def topbar(self):
        body = ft.Row(
            controls=[
                ft.Container(
                    content=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.to_home),  # 绑定返回处理
                    expand=1,
                    alignment=ft.Alignment.CENTER_LEFT
                )]
        )
        if self.is_exam:  # 判断是否处于考试模式
            body.controls.append(self.timer)
        body.controls.append(ft.Row(
            controls=[
                ft.Text(f"0 / {self.ques_len}", ref=progre_txt),
                ft.IconButton(ft.Icons.GRID_VIEW, on_click=self.switch_ques_page)],  # 绑定跳题面板
            alignment=ft.MainAxisAlignment.END,
            spacing=5,
            expand=1,
        )
        )
        return body

    def ansques(self):
        body = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Text("question.", size=20, ref=ques_text),
                ft.Divider(),  # 分隔线
                ft.ListView(
                    expand=True,
                    spacing=5,
                    ref=ques_opt
                )
            ]
        )
        return body

    def switchques(self):
        body = ft.Row(
            height=25,
            controls=[
                ft.Row(expand=1, controls=[ft.Button("上一题", expand=True, on_click=self.prev_ques)]),
            ]
        )
        if self.is_exam:
            body.controls.append(ft.Button("交卷", on_click=self.exam_to_home, data=ExamStat.submit))
        body.controls.append(ft.Row(expand=1, controls=[ft.Button("下一题", expand=True, on_click=self.next_ques)]))
        self.next_ques()
        return body


def ansqies_page(ques_serv, page:ft.Page):
    AQ = AnsQues(ques_serv, page)
    page.on_view_pop = AQ.to_home
    body = ft.SafeArea(
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                AQ.topbar(),      #顶部信息条
                AQ.ansques(),     #中部答题区
                AQ.switchques()   #底部切题区
            ]
        )
    )
    return body