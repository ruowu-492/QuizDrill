import flet as ft
from enum import IntEnum
import asyncio

class ExamStat(IntEnum):
    timeout = 1

class CountdownTimer(ft.Text):
    def __init__(self, duration_seconds:int, on_finish=None):
        super().__init__()
        self.total_duration = duration_seconds   #总时长
        self.remaining = duration_seconds  #剩余时间
        self.on_finish = on_finish  # 倒计时结束时的回调事件
        self.is_running = False
        self.is_paused = False
        self.task = None

    def did_mount(self):
        self.start()

    def will_unmount(self):
        self.stop()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.task = self.page.run_task(self._run_timer)

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False
        if not self.is_running:
            self.start()

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()

    def get_current_time(self) -> int:
        return self.remaining

    async def _run_timer(self):
        while self.remaining >= 0 and self.is_running:
            if not self.is_paused:
                #更新显示
                mins, secs = divmod(self.remaining, 60)
                self.value = f"{mins:02d}:{secs:02d}"
                self.update()
                if self.remaining == 0:
                    if self.on_finish:
                        self.on_finish(ExamStat.timeout)  #触发时间到事件
                    self.is_running = False
                    break
                self.remaining -= 1
            await asyncio.sleep(1)

@ft.control
class QIndexList(ft.GridView):
    expand:bool = True
    runs_count:int = 5
    max_extent:int = 65

    def build_items(self, quanti:int, on_click=None):
        """构建初始跳题表"""
        for qindex in range(1, quanti+1):
            self.controls.append(
                ft.Container(
                    key=qindex,
                    bgcolor=ft.Colors.BLUE_200,
                    border_radius = 20,
                    alignment=ft.Alignment.CENTER,
                    on_click = on_click,
                    content=ft.Text(str(qindex),size=18)
                )
            )

    def update_item(self, index:int, color:ft.Colors):
        """更新对应题索引的背景色"""
        item = self.controls[index]
        item.bgcolor = color

# QL = QIndexList()
# QL.build_items(100)
# def main(page):
#     sheet = ft.BottomSheet(
#         fullscreen=True,
#         show_drag_handle=True,
#         content=ft.Container(
#             padding=ft.Padding.all(10),
#             content=ft.Column(
#                 horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#                 controls=[
#                     QL,
#                     ft.Button("退出跳题页", on_click=lambda: page.pop_dialog()),
#                 ],
#             ),
#         ),
#     )
#     page.add(ft.Column(
#         controls=[
#             ft.Button(
#                 "Display button sheet.",
#                 on_click=lambda e: page.show_dialog(sheet)
#             )
#         ]
#     ))
# ft.run(main)