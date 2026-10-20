from core.QuesServ import QuestionService
from ui.HomePage import Home
from ui.AnsQuesPage import ansqies_page
from pathlib import Path
from os import environ
import flet as ft


def get_assets_dir() -> Path:
    default_assets_dir = Path(__file__).parent / "assets"  # 本地开发时的回退路径
    return Path(environ.get("FLET_ASSETS_DIR", str(default_assets_dir))).resolve()


def main(page:ft.Page):
    assetr_dir = get_assets_dir()
    QS = QuestionService(assetr_dir/"data")
    page.fonts = {"Sans": "SourceHanSansSC-Regular.otf"}
    page.theme = ft.Theme(font_family="Sans")
    # page.theme_mode = ft.ThemeMode.DARK
    page.window.min_height = 400
    page.window.min_width = 650

    def route_change(e=None):
        page.views.clear()
        if page.route == "/":
            page.views.append(ft.View(route="/", controls=[ft.SafeArea(
                expand=True,
                content=Home(QS)
            )]))
        elif page.route == "/ansques":
            page.views.append(ft.View(route="/ansques", controls=[ansqies_page(QS, page)]))
            page.update()

    page.title = "QuizDrill"
    page.on_route_change = route_change
    route_change()

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
