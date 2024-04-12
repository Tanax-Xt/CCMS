from PyQt6 import uic


class WidgetMixin:
    title: str = None
    ui_path: str = None
    
    def __init__(self) -> None:
        if self.ui_path:
            uic.loadUi(self.ui_path, self)

        title = self.get_title()

        if title:
            self.setWindowTitle(title)

        self.setup_ui()
        
    def setup_ui(self) -> None:
        pass
    
    def get_title(self) -> str:
        return self.title
