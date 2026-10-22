from core.QuesServ import QuestionService
from ui.HomePage import home_page
from ui.AnsQuesPage import ansqies_page
from pathlib import Path
from os import environ, getenv
import flet as ft


def get_assets_dir() -> Path:
    default_assets_dir = Path(__file__).parent / "assets"  # 本地开发时的回退路径
    return Path(environ.get("FLET_ASSETS_DIR", str(default_assets_dir))).resolve()

def get_data_dir() -> Path:
    env_path = getenv("FLET_APP_STORAGE_DATA")
    if env_path:
        return Path(env_path)
    fallback = Path.cwd() / "app_data"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

def main(page:ft.Page):
    assetr_dir = get_assets_dir()
    data_path = get_data_dir()
    QS = QuestionService(assetr_dir, data_path)
    page.fonts = {"Sans": "SourceHanSansSC-Regular.otf"}
    page.theme = ft.Theme(font_family="Sans")
    # page.theme_mode = ft.ThemeMode.DARK
    page.window.min_height = 400
    page.window.min_width = 650

    def route_change(e=None):
        page.views.clear()
        if page.route == "/":
            page.views.append(ft.View(route="/", controls=[home_page(QS, page)]))
        elif page.route == "/ansques":
            page.views.append(ft.View(route="/ansques", controls=[ansqies_page(QS, page)]))
            page.update()

    page.title = "QuizDrill"
    page.on_route_change = route_change
    route_change()

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
