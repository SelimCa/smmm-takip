from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QButtonGroup, QFrame, QSizePolicy,
    QSpinBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

from datetime import date as _today_date
from styles import STYLE
from panel_dashboard import DashboardPanel
from panel_mukellef import MukellefPanel
from panel_beyanname import BeyannamePanel
from panel_cari import CariPanel
from panel_ayarlar import AyarlarPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMMM Takip Sistemi")
        self.setMinimumSize(1400, 720)
        self.resize(1800, 900)
        self.setStyleSheet(STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # Dikey ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet("color: #253447;")
        root.addWidget(line)

        # İçerik alanı
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_stack")
        root.addWidget(self.stack, 1)

        # Paneller
        self.dash_panel  = DashboardPanel()
        self.muk_panel   = MukellefPanel()
        self.beyan_panel = BeyannamePanel()
        self.cari_panel  = CariPanel()
        self.ayar_panel  = AyarlarPanel()

        self.stack.addWidget(self.dash_panel)   # 0
        self.stack.addWidget(self.muk_panel)    # 1
        self.stack.addWidget(self.beyan_panel)  # 2
        self.stack.addWidget(self.cari_panel)   # 3
        self.stack.addWidget(self.ayar_panel)   # 4

        # Durum çubuğu
        self.statusBar().showMessage("SMMM Takip Sistemi  |  Hazır")

        # Başlangıç
        self.nav_btns[0].setChecked(True)
        aktif_yil = self._aktif_yil()
        self.spn_yil.setValue(aktif_yil)
        self._switch(0)

    def _aktif_yil(self):
        """DB'den kaydedilmiş aktif yılı oku, yoksa güncel yılı dön."""
        from db import db
        kayitli = db.get_ayar('aktif_yil', '')
        try:
            return int(kayitli) if kayitli else _today_date.today().year
        except ValueError:
            return _today_date.today().year

    def _yil_degisti(self, yil):
        """Aktif yıl değişince DB'ye kaydet ve ilgili panelleri yenile."""
        from db import db
        db.set_ayar('aktif_yil', str(yil))
        self.yil_lbl.setText(f"📅 {yil}")
        # Beyanname ve dashboard panellerini aktif yıla göre güncelle
        self.beyan_panel.set_yil(yil)
        self.dash_panel.set_yil(yil)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Uygulama logo / başlık
        header = QWidget()
        header.setStyleSheet("background-color: #142030; padding: 16px 0px 14px 0px;")
        hlay = QVBoxLayout(header)
        hlay.setSpacing(4)

        ico = QLabel("📊")
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet("font-size: 30px; background: transparent;")

        title = QLabel("SMMM TAKİP")
        title.setObjectName("app_title")
        title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; "
                            "qproperty-alignment: AlignCenter; background: transparent;")

        sub = QLabel("Beyanname & Cari Takip")
        sub.setObjectName("app_sub")
        sub.setStyleSheet("color: #607D8B; font-size: 11px; "
                          "qproperty-alignment: AlignCenter; background: transparent;")

        hlay.addWidget(ico)
        hlay.addWidget(title)
        hlay.addWidget(sub)
        lay.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #253447; max-height: 1px;")
        lay.addWidget(sep)
        lay.addSpacing(8)

        # Navigasyon butonları
        nav_items = [
            ("🏠   Dashboard",      0),
            ("👥   Mükellefler",    1),
            ("📋   Beyannameler",   2),
            ("💰   Cari Hesap",    3),
            ("⚙️   Ayarlar",       4),
        ]

        self.nav_btns = []
        grp = QButtonGroup(self)
        grp.setExclusive(True)

        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(48)
            btn.clicked.connect(lambda _checked, i=idx: self._switch(i))
            grp.addButton(btn)
            self.nav_btns.append(btn)
            lay.addWidget(btn)

        lay.addStretch()

        # ── Aktif Yıl Seçici ──
        sep_yil = QFrame()
        sep_yil.setFrameShape(QFrame.HLine)
        sep_yil.setStyleSheet("background-color: #253447; max-height: 1px;")
        lay.addWidget(sep_yil)

        yil_widget = QWidget()
        yil_widget.setStyleSheet("background-color: #0F172A; padding: 8px 10px;")
        yil_lay = QVBoxLayout(yil_widget)
        yil_lay.setSpacing(4)
        yil_lay.setContentsMargins(8, 8, 8, 8)

        yil_title = QLabel("Çalışma Yılı")
        yil_title.setStyleSheet(
            "color: #64748B; font-size: 10px; font-weight: bold; "
            "letter-spacing: 1px; background: transparent;")
        yil_title.setAlignment(Qt.AlignCenter)

        self.yil_lbl = QLabel(f"📅 {_today_date.today().year}")
        self.yil_lbl.setStyleSheet(
            "color: #38BDF8; font-size: 18px; font-weight: bold; "
            "background: transparent;")
        self.yil_lbl.setAlignment(Qt.AlignCenter)

        self.spn_yil = QSpinBox()
        self.spn_yil.setRange(2000, 2099)
        self.spn_yil.setValue(_today_date.today().year)
        self.spn_yil.setAlignment(Qt.AlignCenter)
        self.spn_yil.setStyleSheet(
            "QSpinBox { background:#1E293B; color:#F1F5F9; border:1px solid #334155; "
            "border-radius:6px; padding:4px; font-size:13px; font-weight:bold; }"
            "QSpinBox::up-button, QSpinBox::down-button { "
            "background:#334155; border-radius:3px; width:18px; }")
        self.spn_yil.valueChanged.connect(self._yil_degisti)

        yil_lay.addWidget(yil_title)
        yil_lay.addWidget(self.yil_lbl)
        yil_lay.addWidget(self.spn_yil)
        lay.addWidget(yil_widget)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: #253447; max-height: 1px;")
        lay.addWidget(sep2)

        ver = QLabel("v1.0.0")
        ver.setObjectName("ver_label")
        ver.setStyleSheet("color: #37474F; font-size: 11px; "
                          "qproperty-alignment: AlignCenter; padding: 8px; "
                          "background: transparent;")
        lay.addWidget(ver)

        return sidebar

    def _switch(self, index):
        self.stack.setCurrentIndex(index)
        self.nav_btns[index].setChecked(True)
        yil = self.spn_yil.value() if hasattr(self, 'spn_yil') else _today_date.today().year

        # Paneli yenile
        if index == 0:
            self.dash_panel.set_yil(yil)
        elif index == 1:
            self.muk_panel.refresh()
        elif index == 2:
            self.beyan_panel.set_yil(yil)
        elif index == 3:
            self.cari_panel.refresh_clients()
        elif index == 4:
            self.ayar_panel.refresh()
