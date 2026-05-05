from datetime import date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from db import db, AYLAR


class StatCard(QFrame):
    """Tek bir istatistik kartı"""
    def __init__(self, title, value, color="#2980B9", parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setMinimumHeight(110)
        self.setMinimumWidth(170)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setObjectName("stat_value")
        self.val_lbl.setAlignment(Qt.AlignCenter)
        self.val_lbl.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {color};")

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("stat_label")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setStyleSheet("font-size: 12px; color: #7F8C8D;")

        lay.addWidget(self.val_lbl)
        lay.addWidget(self.title_lbl)

    def update_value(self, value):
        self.val_lbl.setText(str(value))


class DashboardPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(16)

        # Başlık
        now = date.today()
        self.title_lbl = QLabel(f"📊  Dashboard  —  {AYLAR[now.month]} {now.year}")
        self.title_lbl.setObjectName("page_title")
        outer.addWidget(self.title_lbl)

        # ── İstatistik kartları ──
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)

        self.card_mukellef  = StatCard("Aktif Mükellef",      "—", "#2980B9")
        self.card_verildi   = StatCard("Bu Ay Verilen",        "—", "#27AE60")
        self.card_verilmedi = StatCard("Bu Ay Bekleyen",       "—", "#E74C3C")
        self.card_borc      = StatCard("Toplam Alacak (Borç)", "—", "#8E44AD")
        self.card_alacak    = StatCard("Toplam Ödenen",        "—", "#16A085")

        for card in (self.card_mukellef, self.card_verildi,
                     self.card_verilmedi, self.card_borc, self.card_alacak):
            cards_row.addWidget(card)

        outer.addLayout(cards_row)

        # ── Bu ay bekleyen beyanname tablosu ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #DDE1E7; max-height:1px;")
        outer.addWidget(sep)

        pending_title = QLabel("⏰  Bu Ay Bekleyen Beyannameler")
        pending_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1A2535; padding: 4px 0;")
        outer.addWidget(pending_title)

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(
            ["Mükellef", "Vergi No", "Beyanname Türü", "Dönem", "Durum"])
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        outer.addWidget(self.tbl, 1)

    def set_yil(self, yil: int):
        """Ana pencereden aktif yıl değişince güncelle."""
        self.refresh(yil=yil)

    def refresh(self, yil: int = None):
        now = date.today()
        if yil is None:
            yil = now.year
        self.title_lbl.setText(f"📊  Dashboard  —  {yil}")
        stats = db.get_dashboard_stats(yil, now.month)

        self.card_mukellef.update_value(stats['mukellef_sayisi'])
        self.card_verildi.update_value(stats['beyan_verildi'])
        self.card_verilmedi.update_value(stats['beyan_verilmedi'])
        self.card_borc.update_value(f"{stats['toplam_borc']:,.2f} ₺")
        self.card_alacak.update_value(f"{stats['toplam_alacak']:,.2f} ₺")

        # Bekleyen beyanname tablosu
        beyanlar = db.get_ay_beyannameleri(yil, now.month)
        bekleyenler = [b for b in beyanlar if not b['verildi']]

        self.tbl.setRowCount(len(bekleyenler))
        from db import donem_label
        for row, b in enumerate(bekleyenler):
            self.tbl.setItem(row, 0, QTableWidgetItem(b['unvan']))
            self.tbl.setItem(row, 1, QTableWidgetItem(b['vergi_no']))
            self.tbl.setItem(row, 2, QTableWidgetItem(b['tur']))
            self.tbl.setItem(row, 3, QTableWidgetItem(donem_label(b['tur'], b['yil'], b['donem'])))

            durum_item = QTableWidgetItem("⏳ Bekliyor")
            durum_item.setForeground(QColor("#E74C3C"))
            self.tbl.setItem(row, 4, durum_item)
