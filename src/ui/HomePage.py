import flet as ft
import webbrowser
from core.QuesServ import QuestionMode

QMode = {"顺序练习":QuestionMode.order, "仅练错题":QuestionMode.err,
         "仅练新题":QuestionMode.new, "背题模式":QuestionMode.mem}
QInfo = {"顺序练习":"提供全部题目,从最近一个没做过的题目开始",
         "仅练错题":"提供你答错过的题目,如果有的话",
         "仅练新题":"提供你没做过的题目,如果有的话",
         "背题模式":"提供全部题目,并奉上正确答案"}

@ft.control
class HomeButton(ft.Button):
    def init(self):
        self.style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))

class Home(ft.Column):
    def __init__(self, ques_serv):
        super().__init__()
        self.QS = ques_serv
        mode_txt = {QuestionMode.order:"顺序练习", QuestionMode.err:"仅练错题",
                    QuestionMode.new:"仅练新题", QuestionMode.mem:"背题模式"}
        if self.QS.QuesMode == QuestionMode.exam:
            self.QS.QuesMode = QuestionMode.err
        mode_txt = mode_txt[self.QS.QuesMode]
        pass_rate = self.QS.get_pass_rate()
        parc_info = self.QS.get_ans_ques_info()
        stxt = (f"题库总量为{parc_info["ques_len"]},你已经答了{parc_info["pract_number"]}题,占比{parc_info["comple_deg"]:.2%}.\n"
                f"其中你答对了{parc_info["corr_len"]}题,答错了{parc_info["err_len"]}题,准确率{parc_info["accuracy"]:.1%}.")
        #更新概览和保持模式选择
        self.passrate_txt.current.value = f"预测通过率: {pass_rate:.1%}"
        self.statisti_txt.current.value = stxt
        self.practice_drop.current.value = mode_txt
        self.practice_item.current.title.value = mode_txt
        self.practice_item.current.subtitle.value = QInfo[mode_txt]

    def init(self):
        self.controls = [
            self._appbar(),    #顶部面板
            self._overview(),  #练习概览
            self._training()   #练习选择
        ]

    def _appbar(self):
        return ft.AppBar(
        title=ft.Text("QuizDrill - Demo ver"),
        center_title=False,
        bgcolor=ft.Colors.BLUE_GREY_400,
        actions=[
            ft.PopupMenuButton(
                key="popup",
                items=[
                    ft.PopupMenuItem(content="重置数据"),   #绑定数据重置接口
                    ft.PopupMenuItem(content="检查更新"),   #绑定检查更新
                    ft.PopupMenuItem(content="项目仓库",
                                     on_click=lambda e: webbrowser.open("https://github.com/ruowu-492/QuizDrill"))    #绑定跳转链接
                ],
            ),
        ],
    )

    def _overview(self):
        self.passrate_txt = ft.Ref[ft.Text]()
        self.statisti_txt = ft.Ref[ft.Text]()
        body = ft.Column(
            controls = [
                ft.Container(
                    alignment = ft.Alignment.CENTER,
                    content = ft.Text("", size=24, color=ft.Colors.RED, ref=self.passrate_txt)  #通过率
                ),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("", ref=self.statisti_txt)  #练习概览
                )
            ]
        )
        return body

    def _training(self):
        self.practice_item = ft.Ref[ft.ListTile]()
        self.practice_drop = ft.Ref[ft.Dropdown]()
        body = ft.ExpansionTile(
            title=ft.Text("训练", size=20),
            expanded=True,
            controls=[
                ft.ListTile(
                    title=ft.Text("练习模式", size=16),
                    trailing=
                    ft.Dropdown(
                        ref = self.practice_drop,
                        on_select=self.mode_set,
                        options=[
                            ft.DropdownOption("顺序练习"),
                            ft.DropdownOption("仅练错题"),
                            ft.DropdownOption("仅练新题"),
                            ft.DropdownOption("背题模式")
                        ]
                    )
                ),
                ft.ListTile(
                    title=ft.Text("顺序练习", size=16),
                    subtitle=ft.Text("提供全部题目,从最近一个没做过的题目开始练习", size=11),
                    trailing=HomeButton(content="开始练习", on_click=self.start_exercise),  # 需绑定页面切换
                    ref=self.practice_item),
                ft.ListTile(
                    title=ft.Text("模拟考试", size=16),
                    subtitle=ft.Text("你将有45分钟去答随机的50题,60分及格", size=11),
                    trailing=HomeButton(content="开始考试", on_click=self.start_exam),  # 需绑定页面切换
                )
            ],
        )
        return body

    def start_exam(self, e):
        self.QS.QuesMode = QuestionMode.exam
        e.page.navigate("/ansques")

    def start_exercise(self, e):
        e.page.navigate("/ansques")

    def mode_set(self, e):
        ures = e.control.value
        self.QS.QuesMode = QMode[ures]
        self.practice_item.current.title.value = ures
        self.practice_item.current.subtitle.value = QInfo[ures]