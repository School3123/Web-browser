import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView

class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Simple Browser")
        self.setGeometry(100, 100, 1024, 768)

        # ブラウザエンジンのセットアップ
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))
        self.setCentralWidget(self.browser)

        # ナビゲーションバーの作成
        navbar = QToolBar()
        self.addToolBar(navbar)

        # 戻るボタン
        back_btn = QAction('Back', self)
        back_btn.triggered.connect(self.browser.back)
        navbar.addAction(back_btn)

        # 進むボタン
        forward_btn = QAction('Forward', self)
        forward_btn.triggered.connect(self.browser.forward)
        navbar.addAction(forward_btn)

        # 更新ボタン
        reload_btn = QAction('Reload', self)
        reload_btn.triggered.connect(self.browser.reload)
        navbar.addAction(reload_btn)

        # URLバー
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # URLが変わったときにバーを更新
        self.browser.urlChanged.connect(self.update_url)

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith('http'):
            url = 'https://' + url
        self.browser.setUrl(QUrl(url))

    def update_url(self, q):
        self.url_bar.setText(q.toString())

if __name__ == '__main__':
    # Linux(Codespaces)での実行時に必要な引数設定
    app = QApplication(sys.argv)
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec_())
