from core.QuesServ import QuestionMode, QuestionService
from datetime import datetime
from enum import Enum
import flet as ft

class ResetType(Enum):
    practice = 0
    exam = 1
    database = 2

QMode = {"顺序练习":QuestionMode.order, "仅练错题":QuestionMode.err,
         "仅练新题":QuestionMode.new, "背题模式":QuestionMode.mem}
QInfo = {"顺序练习":"提供全部题目,从最近一个没做过的题目开始",
         "仅练错题":"提供你答错过的题目,如果有的话",
         "仅练新题":"提供你没做过的题目,如果有的话",
         "背题模式":"提供全部题目,并奉上正确答案"}

def ans_time_fmt(sec:int) ->str:
    """将秒数格式化为分-秒"""
    m, s = divmod(sec, 60)
    return f"{m}分{s}秒"

class HomeButton(ft.Button):
    def init(self):
        self.style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))

def build_exams_row(items):
    body = []
    for record in items:
        row = ft.DataRow(
            cells=[
                ft.DataCell(
                    datetime.fromtimestamp(record["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
                ),
                ft.DataCell(
                    ans_time_fmt(record["time_use"])
                ),
                ft.DataCell(ft.Text(
                    str(record["score"])+"分",
                    color=ft.Colors.GREEN if record["score"] >= 80 else None)
                )
            ]
        )
        body.append(row)
    return body


class Home:
    passrate_txt = ft.Ref[ft.Text]()
    statisti_txt = ft.Ref[ft.Text]()
    practice_item = ft.Ref[ft.ListTile]()
    practice_drop = ft.Ref[ft.Dropdown]()
    theme_mode_toggle = ft.Ref[ft.IconButton]()

    def __init__(self, ques_serv:QuestionService, page:ft.Page):
        super().__init__()
        self.QS = ques_serv
        self.page = page

    def init(self):
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

    def appbar(self):
        return ft.AppBar(
        title=ft.Text("QuizDrill - v1.1"),
        center_title=False,
        bgcolor=ft.Colors.BLUE_GREY_400,
        actions=[
            ft.IconButton(
                key="theme_mode_toggle",
                ref=self.theme_mode_toggle,
                icon=(
                    ft.Icons.WB_SUNNY_OUTLINED
                    if self.page.theme_mode == ft.ThemeMode.LIGHT
                    else ft.Icons.WB_SUNNY
                ),
                on_click=self.toggle_theme_mode,
            ),
            ft.PopupMenuButton(
                key="popup",
                items=[
                    ft.PopupMenuItem(content=ft.TextButton("重置数据", on_click=self.on_reset)),   #绑定数据重置接口
                    ft.PopupMenuItem(content=ft.TextButton("检查更新", on_click=self.app_update)),   #绑定检查更新
                    ft.PopupMenuItem(content=ft.TextButton(
                        "项目仓库",
                        action=ft.OpenUrl("https://github.com/ruowu-492/QuizDrill", ft.UrlTarget.BLANK)
                    ))
                ],
            ),
        ],
    )

    def overview(self):
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

    def training(self):
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
                    trailing=HomeButton(content="开始练习", on_click=lambda e:e.page.navigate("/ansques")),  # 需绑定页面切换
                    ref=self.practice_item),
                ft.ListTile(
                    title=ft.Text("模拟考试", size=16),
                    subtitle=ft.Text("你将有45分钟去答随机的50题,80分及格", size=11),
                    trailing=HomeButton(content="开始考试", on_click=self.start_exam),  # 需绑定页面切换
                )
            ],
        )
        return body

    def exam_statisti(self):
        return ft.ExpansionTile(
            expand=True,
            title=ft.Text("考试记录", size=20),
            controls=self.exams_table()
        )

    def exams_table(self):
        exam_items = self.QS.get_exam_record()
        if not exam_items:
            body = ft.Text("暂无考试记录", text_align=ft.TextAlign.CENTER, size=15)
        else:
            body = ft.DataTable(
                expand=True,
                columns=[
                    ft.DataColumn(label="考试时间"),
                    ft.DataColumn(label="考试用时"),
                    ft.DataColumn(label="得分")
                ],
                rows=build_exams_row(exam_items)
            )
        return body

    def toggle_theme_mode(self, e: ft.Event[ft.IconButton]):
        self.page.theme_mode = (
            ft.ThemeMode.DARK
            if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.theme_mode_toggle.icon = (
            ft.Icons.WB_SUNNY_OUTLINED
            if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.Icons.WB_SUNNY
        )

    def on_reset(self, e):
        dialog = ft.AlertDialog(
            modal=True,
            title="重置数据",
            content=ft.Column(
                height=130,
                controls=[
                    ft.Button("重置练习数据",
                              on_click=lambda e: (self.page.pop_dialog(), self.reset_data(ResetType.practice))),
                    ft.Button("重置考试数据",
                              on_click=lambda e: (self.page.pop_dialog(), self.reset_data(ResetType.exam))),
                    ft.Button("重建练习状态",
                              on_click=lambda e: (self.page.pop_dialog(), self.reset_data(ResetType.database)))
                ]
            ),
            actions=[ft.Button("取消操作", on_click=lambda e: self.page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.show_dialog(dialog)

    def reset_data(self, reset_type):
        match reset_type:
            case ResetType.practice:
                content = ft.Text("该操作将重置练习数据且不可逆, 请谨慎选择!", color=ft.Colors.RED)
                on_click = lambda :(self.QS.reset_stat(), self.init(), self.page.update(), self.page.pop_dialog())
            case ResetType.exam:
                content = ft.Text("该操作将清空考试统计且不可逆, 请谨慎选择!", color=ft.Colors.RED)
                on_click = lambda: (self.QS.reset_exams(), self.init(),  self.page.update(), self.page.pop_dialog())
            case ResetType.database:
                content = ft.Text("该操作将根据题库当前内容重新建立状态映射表,这也会重置练习数据且不可逆,请谨慎操作!\n\n"
                                  "备注: 对于状态映射错位和题库发生有效更新等情况可能修复某些疑问。", color=ft.Colors.RED)
                on_click = lambda: (self.QS.rebuilt_data_base(), self.init(),  self.page.update(), self.page.pop_dialog())
        dialog = ft.AlertDialog(
            modal=True,
            title="警告!",
            content=content,
            actions=[
                ft.Button("确认", on_click=on_click),
                ft.Button("取消", on_click=lambda e:self.page.pop_dialog())
            ]
        )
        self.page.show_dialog(dialog)

    def app_update(self, e):
        dialog = ft.AlertDialog(
            modal=True,
            title="关于更新",
            content=ft.Text("突然不想继续倒腾自动更新的事了,那需要额外引入联网支持去我的仓库下载版本文件进行比对,最近手搓的东西已经很多了。\n"
                "虽说我之前搓的云奏下载器刚好能满足自动下载安装包的需求,但我估摸着这项目近期也没啥更新吧。\n"
                "哦,说起这个我还规划了多用户多题库来着,但再肝下去迟早撑不住(多种含义)。\n"
                "所以我选择直接在这留下我在gitee的发行仓库。\n"
                "或者你也可以试试前往我存源码的GitHub仓库尝试与我取得联系啥的。\n"
                "\n————2026-10-23-05"),
            actions=[ft.Button("Gitee",
                               on_click=lambda e:self.page.pop_dialog(),
                               action=ft.OpenUrl("https://gitee.com/ruowu47927/quiz-drill_releases/releases", ft.UrlTarget.BLANK)
                               ),
                ft.Button("GitHub",
                          on_click=lambda e:self.page.pop_dialog(),
                          action=ft.OpenUrl("https://github.com/ruowu-492/QuizDrill", ft.UrlTarget.BLANK)
                          ),
                ft.Button("Close", on_click=lambda e: self.page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.show_dialog(dialog)

    def start_exam(self, e):
        self.QS.QuesMode = QuestionMode.exam
        e.page.navigate("/ansques")

    def mode_set(self, e):
        ures = e.control.value
        self.QS.QuesMode = QMode[ures]
        self.practice_item.current.title.value = ures
        self.practice_item.current.subtitle.value = QInfo[ures]

def home_page(ques_serv, page):
    H = Home(ques_serv, page)
    body = ft.SafeArea(
        expand = True,
        content = ft.Column(
            expand = True,
            controls = [
                H.appbar(),
                H.overview(),
                ft.ListView(
                    expand=True,
                    spacing=5,
                    controls = [
                        H.training(),
                        H.exam_statisti()
                    ]
                )
            ]
        )
    )
    H.init()
    return body