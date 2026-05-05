"""
Cari Hesap Paneli
  - Ana ekran: Tüm mükelleflerin borç / alacak / bakiye özeti
  - Çift tıklama: Ekstre penceresi (detay + fiş girişi)
"""

from datetime import date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QLineEdit,
    QDateEdit, QDoubleSpinBox, QMessageBox, QFrame,
    QGroupBox, QAbstractItemView, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QColor, QFont

from db import db
from pdf_utils import pdf_cari_liste, pdf_ekstre


# ═══════════════════════════════════════════════════════════
#  Fiş Giriş Diyaloğu
# ═══════════════════════════════════════════════════════════
class CariDialog(QDialog):
    def __init__(self, tip: str, parent=None):
        super().__init__(parent)
        self.tip = tip
        self.setWindowTitle("Borç Fişi Girişi" if tip == 'borc' else "Alacak Fişi Girişi")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        renk    = "#FADBD8" if self.tip == 'borc' else "#D5F5E3"
        renk_txt= "#922B21" if self.tip == 'borc' else "#1E8449"
        tip_lbl = QLabel("🔴  BORÇ FİŞİ" if self.tip == 'borc' else "🟢  ALACAK FİŞİ")
        tip_lbl.setStyleSheet(
            f"background:{renk}; color:{renk_txt}; border-radius:4px; "
            f"padding:8px; font-weight:bold; font-size:14px;")
        tip_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(tip_lbl)

        grp = QGroupBox("Fiş Bilgileri")
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.dte_tarih = QDateEdit(QDate.currentDate())
        self.dte_tarih.setDisplayFormat("dd.MM.yyyy")
        self.dte_tarih.setCalendarPopup(True)

        self.edt_aciklama = QLineEdit()
        self.edt_aciklama.setPlaceholderText("Açıklama giriniz (zorunlu)")

        self.spn_tutar = QDoubleSpinBox()
        self.spn_tutar.setMaximum(99_999_999)
        self.spn_tutar.setDecimals(2)
        self.spn_tutar.setSuffix(" ₺")
        self.spn_tutar.setGroupSeparatorShown(True)
        self.spn_tutar.setMinimum(0.01)

        self.edt_fisno = QLineEdit()
        self.edt_fisno.setPlaceholderText("Fiş no (isteğe bağlı)")

        form.addRow("Tarih *:", self.dte_tarih)
        form.addRow("Açıklama *:", self.edt_aciklama)
        form.addRow("Tutar *:", self.spn_tutar)
        form.addRow("Fiş No:", self.edt_fisno)
        lay.addWidget(grp)

        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Save).setText("💾  Kaydet")
        btn_box.button(QDialogButtonBox.Save).setObjectName("btn_primary")
        btn_box.button(QDialogButtonBox.Cancel).setText("İptal")
        btn_box.accepted.connect(self._save)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)

    def _save(self):
        if not self.edt_aciklama.text().strip():
            QMessageBox.warning(self, "Hata", "Açıklama boş olamaz.")
            return
        self.result = {
            'tarih':    self.dte_tarih.date().toString("yyyy-MM-dd"),
            'aciklama': self.edt_aciklama.text().strip(),
            'tutar':    self.spn_tutar.value(),
            'fisno':    self.edt_fisno.text().strip(),
        }
        self.accept()


# ═══════════════════════════════════════════════════════════
#  Ekstre Penceresi  (tek mükellefin detayı)
# ═══════════════════════════════════════════════════════════
EKSTRE_COLS = ["#", "Tarih", "Fiş No", "Açıklama", "Borç (₺)", "Alacak (₺)", "Bakiye (₺)"]

CLR_BORC   = "#FADBD8"
CLR_ALACAK = "#D5F5E3"


# ═══════════════════════════════════════════════════════════
#  Virman Diyaloğu  — Bir cariden diğerine tutar transferi
# ═══════════════════════════════════════════════════════════
class VirmanDialog(QDialog):
    def __init__(self, kaynak_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄  Cariler Arası Virman")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._mukellefler = db.get_mukellefler(sadece_aktif=True)
        self._kaynak_id = kaynak_id
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        # Bilgi başlığı
        info = QLabel(
            "<b>Virman İşlemi</b><br>"
            "Kaynak cari hesaptan alacak fişi, hedef cari hesaba borç fişi oluşturulur.")
        info.setStyleSheet(
            "background:#EEF6FF; border:1px solid #BDD5EE; "
            "border-radius:4px; padding:10px;")
        info.setWordWrap(True)
        lay.addWidget(info)

        grp = QGroupBox("Virman Bilgileri")
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        # Kaynak mükellef
        self.cmb_kaynak = QComboBox()
        self.cmb_kaynak.setMinimumWidth(280)
        for m in self._mukellefler:
            self.cmb_kaynak.addItem(f"{m['unvan']}  ({m['vergi_no']})", m['id'])
        if self._kaynak_id:
            idx = self.cmb_kaynak.findData(self._kaynak_id)
            if idx >= 0:
                self.cmb_kaynak.setCurrentIndex(idx)
        self.cmb_kaynak.currentIndexChanged.connect(self._kaynak_degisti)

        # Hedef mükellef
        self.cmb_hedef = QComboBox()
        self.cmb_hedef.setMinimumWidth(280)
        for m in self._mukellefler:
            self.cmb_hedef.addItem(f"{m['unvan']}  ({m['vergi_no']})", m['id'])

        # Otomatik farklı seç
        if self.cmb_kaynak.currentIndex() == 0 and len(self._mukellefler) > 1:
            self.cmb_hedef.setCurrentIndex(1)

        # Tarih
        self.dte_tarih = QDateEdit(QDate.currentDate())
        self.dte_tarih.setDisplayFormat("dd.MM.yyyy")
        self.dte_tarih.setCalendarPopup(True)

        # Tutar
        self.spn_tutar = QDoubleSpinBox()
        self.spn_tutar.setMaximum(99_999_999)
        self.spn_tutar.setDecimals(2)
        self.spn_tutar.setSuffix(" ₺")
        self.spn_tutar.setGroupSeparatorShown(True)
        self.spn_tutar.setMinimum(0.01)

        # Açıklama
        self.edt_aciklama = QLineEdit()
        self.edt_aciklama.setPlaceholderText("Virman açıklaması (zorunlu)")
        self.edt_aciklama.setText("Cariler arası virman")

        # Fiş no
        self.edt_fisno = QLineEdit()
        self.edt_fisno.setPlaceholderText("Fiş no (isteğe bağlı)")
        from datetime import date as _d
        self.edt_fisno.setText(f"VRM-{_d.today().strftime('%Y%m%d')}")

        form.addRow("Kaynak Cari *:", self.cmb_kaynak)
        form.addRow("Hedef Cari *:", self.cmb_hedef)
        form.addRow("Tarih *:", self.dte_tarih)
        form.addRow("Tutar *:", self.spn_tutar)
        form.addRow("Açıklama *:", self.edt_aciklama)
        form.addRow("Fiş No:", self.edt_fisno)
        lay.addWidget(grp)

        # Özet etiketi
        self.lbl_ozet = QLabel("")
        self.lbl_ozet.setStyleSheet(
            "background:#F0FDF4; border:1px solid #86EFAC; "
            "border-radius:4px; padding:8px; font-size:12px;")
        self.lbl_ozet.setWordWrap(True)
        lay.addWidget(self.lbl_ozet)
        self._ozet_guncelle()

        self.cmb_kaynak.currentIndexChanged.connect(self._ozet_guncelle)
        self.cmb_hedef.currentIndexChanged.connect(self._ozet_guncelle)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btn_ok = btn_box.button(QDialogButtonBox.Ok)
        self.btn_ok.setText("🔄  Virmani Uygula")
        self.btn_ok.setObjectName("btn_primary")
        btn_box.button(QDialogButtonBox.Cancel).setText("İptal")
        btn_box.accepted.connect(self._kaydet)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)

    def _kaynak_degisti(self):
        """Kaynak değişince hedef aynıysa otomatik kaydır."""
        k_idx = self.cmb_kaynak.currentIndex()
        h_idx = self.cmb_hedef.currentIndex()
        if k_idx == h_idx:
            new_idx = 1 if k_idx != 1 else 0
            self.cmb_hedef.setCurrentIndex(new_idx)

    def _ozet_guncelle(self):
        k_unvan = self.cmb_kaynak.currentText()
        h_unvan = self.cmb_hedef.currentText()
        self.lbl_ozet.setText(
            f"📤  <b>Kaynak:</b> {k_unvan}<br>"
            f"&nbsp;&nbsp;&nbsp;&nbsp;→ Bu hesaba <b>Alacak</b> fişi girilir (borç azalır / alacak artar)<br>"
            f"📥  <b>Hedef:</b> {h_unvan}<br>"
            f"&nbsp;&nbsp;&nbsp;&nbsp;→ Bu hesaba <b>Borç</b> fişi girilir"
        )
        self.lbl_ozet.setTextFormat(Qt.RichText)

    def _kaydet(self):
        kaynak_id = self.cmb_kaynak.currentData()
        hedef_id  = self.cmb_hedef.currentData()
        if kaynak_id == hedef_id:
            QMessageBox.warning(self, "Hata", "Kaynak ve hedef aynı mükellef olamaz!")
            return
        if not self.edt_aciklama.text().strip():
            QMessageBox.warning(self, "Hata", "Açıklama boş olamaz.")
            return
        tarih     = self.dte_tarih.date().toString("yyyy-MM-dd")
        tutar     = self.spn_tutar.value()
        aciklama  = self.edt_aciklama.text().strip()
        fisno     = self.edt_fisno.text().strip()

        k_unvan = self.cmb_kaynak.currentText().split("  (")[0]
        h_unvan = self.cmb_hedef.currentText().split("  (")[0]

        # Kaynak → Alacak
        db.add_cari(
            kaynak_id, tarih,
            f"{aciklama}  [Virman → {h_unvan}]",
            0, tutar, fisno
        )
        # Hedef → Borç
        db.add_cari(
            hedef_id, tarih,
            f"{aciklama}  [Virman ← {k_unvan}]",
            tutar, 0, fisno
        )
        self.accept()


class EkstreDialog(QDialog):
    def __init__(self, mukellef_id, unvan, vergi_no, parent=None):
        super().__init__(parent)
        self.mid    = mukellef_id
        self.unvan  = unvan
        self.setWindowTitle(f"📋  Ekstre — {unvan}")
        self.setMinimumSize(860, 560)
        self.setModal(True)
        self._build()
        self._load()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        # Başlık
        hdr = QLabel(f"<b>{self.unvan}</b>")
        hdr.setStyleSheet(
            "background:#EEF6FF; border:1px solid #BDD5EE; border-radius:4px; "
            "padding:8px 14px; font-size:14px;")
        lay.addWidget(hdr)

        # Araç çubuğu
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_borc = QPushButton("🔴  Borç Fişi Gir")
        btn_borc.setObjectName("btn_danger")
        btn_borc.setFixedHeight(34)
        btn_borc.clicked.connect(lambda: self._add_fis('borc'))

        btn_alacak = QPushButton("🟢  Alacak Fişi Gir")
        btn_alacak.setObjectName("btn_success")
        btn_alacak.setFixedHeight(34)
        btn_alacak.clicked.connect(lambda: self._add_fis('alacak'))

        btn_sil = QPushButton("🗑  Satır Sil")
        btn_sil.setObjectName("btn_secondary")
        btn_sil.setFixedHeight(34)
        btn_sil.clicked.connect(self._delete_row)

        btn_pdf = QPushButton("📄  PDF Ekstre")
        btn_pdf.setObjectName("btn_secondary")
        btn_pdf.setFixedHeight(34)
        btn_pdf.setToolTip("Bu mükellefin ekstresini PDF olarak kaydet")
        btn_pdf.clicked.connect(self._pdf_ekstre)

        toolbar.addWidget(btn_borc)
        toolbar.addWidget(btn_alacak)
        toolbar.addWidget(btn_sil)
        toolbar.addWidget(btn_pdf)
        toolbar.addStretch()
        lay.addLayout(toolbar)

        # Tablo
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(EKSTRE_COLS))
        self.tbl.setHorizontalHeaderLabels(EKSTRE_COLS)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.SingleSelection)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(False)

        hdr2 = self.tbl.horizontalHeader()
        hdr2.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(3, QHeaderView.Stretch)
        hdr2.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        lay.addWidget(self.tbl, 1)

        # Özet çubuğu
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#DDE1E7; max-height:1px;")
        lay.addWidget(sep)

        bottom = QHBoxLayout()
        self.lbl_borc   = QLabel("Toplam Borç: —")
        self.lbl_alacak = QLabel("Toplam Alacak: —")
        self.lbl_net    = QLabel("Net Bakiye: —")
        for lbl in (self.lbl_borc, self.lbl_alacak, self.lbl_net):
            lbl.setStyleSheet("font-weight:bold; font-size:13px;")
        bottom.addWidget(self.lbl_borc)
        bottom.addWidget(self.lbl_alacak)
        bottom.addStretch()
        bottom.addWidget(self.lbl_net)
        lay.addLayout(bottom)

        btn_kapat = QPushButton("Kapat")
        btn_kapat.setObjectName("btn_secondary")
        btn_kapat.setFixedHeight(34)
        btn_kapat.clicked.connect(self.accept)
        lay.addWidget(btn_kapat, 0, Qt.AlignRight)

    def _load(self):
        hareketler = db.get_cari(self.mid)
        self.tbl.setRowCount(len(hareketler))

        running = 0.0
        tb = 0.0
        ta = 0.0

        for row, h in enumerate(hareketler):
            borc   = float(h['borc'])
            alacak = float(h['alacak'])
            running += borc - alacak
            tb += borc
            ta += alacak

            bg = CLR_BORC if borc > 0 else (CLR_ALACAK if alacak > 0 else "#FFFFFF")
            bk_str = f"{running:+,.2f}" if running != 0 else "0,00"

            row_data = [
                str(row + 1),
                str(h['tarih'])[:10],
                h.get('fisno', ''),
                h['aciklama'],
                f"{borc:,.2f}"   if borc   else "—",
                f"{alacak:,.2f}" if alacak else "—",
                bk_str,
            ]

            for col, val in enumerate(row_data):
                item = QTableWidgetItem(val)
                item.setBackground(QColor(bg))
                item.setTextAlignment(Qt.AlignVCenter | (Qt.AlignRight if col >= 4 else Qt.AlignLeft))
                if col == 0:
                    item.setData(Qt.UserRole, h['id'])
                if col == 6:
                    item.setForeground(QColor("#C0392B" if running > 0 else "#1E8449" if running < 0 else "#2C3E50"))
                self.tbl.setItem(row, col, item)

        net = tb - ta
        self.lbl_borc.setText(f"Toplam Borç: <b style='color:#C0392B'>{tb:,.2f} ₺</b>")
        self.lbl_borc.setTextFormat(Qt.RichText)
        self.lbl_alacak.setText(f"Toplam Alacak: <b style='color:#1E8449'>{ta:,.2f} ₺</b>")
        self.lbl_alacak.setTextFormat(Qt.RichText)

        if net > 0:
            net_lbl = f"<b style='color:#C0392B'>Alacağımız (Borçlu): {net:,.2f} ₺</b>"
        elif net < 0:
            net_lbl = f"<b style='color:#1E8449'>Borçlumuz (Alacaklı): {abs(net):,.2f} ₺</b>"
        else:
            net_lbl = "<b>Bakiye: 0,00 ₺ (Sıfır)</b>"
        self.lbl_net.setText(net_lbl)
        self.lbl_net.setTextFormat(Qt.RichText)

    def _add_fis(self, tip):
        dlg = CariDialog(tip=tip, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            r = dlg.result
            if tip == 'borc':
                db.add_cari(self.mid, r['tarih'], r['aciklama'], r['tutar'], 0, r['fisno'])
            else:
                db.add_cari(self.mid, r['tarih'], r['aciklama'], 0, r['tutar'], r['fisno'])
            self._load()

    def _delete_row(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Lütfen bir satır seçin.")
            return
        item = self.tbl.item(row, 0)
        if item is None:
            return
        hid = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Onay", "Bu cari hareketi silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.delete_cari(hid)
            self._load()

    def _pdf_ekstre(self):
        hareketler = db.get_cari(self.mid)
        if not hareketler:
            QMessageBox.information(self, "Bilgi", "Bu mükelleffe ait cari hareket yok.")
            return
        pdf_ekstre(hareketler, self.unvan, parent=self)


# ═══════════════════════════════════════════════════════════
#  Ana Cari Hesap Paneli  — Tüm mükelleflerin özet listesi
# ═══════════════════════════════════════════════════════════
LISTE_COLS = [
    "#",              # 0
    "Mükellef",       # 1
    "Vergi / TC No",  # 2
    "Tip",            # 3
    "Toplam Borç (₺)",   # 4
    "Toplam Alacak (₺)", # 5
    "Net Bakiye (₺)",    # 6
    "Durum",          # 7
]


class CariPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(12)

        # Başlık
        hdr_row = QHBoxLayout()
        title = QLabel("💰  Cari Hesap")
        title.setObjectName("page_title")
        sub = QLabel("Mükellef seçerek fiş girişi yapın veya çift tıklayarak ekstre görün")
        sub.setObjectName("page_subtitle")
        t_col = QVBoxLayout()
        t_col.setSpacing(2)
        t_col.addWidget(title)
        t_col.addWidget(sub)

        btn_fis_borc = QPushButton("🔴  Borç Fişi Gir")
        btn_fis_borc.setObjectName("btn_danger")
        btn_fis_borc.setFixedHeight(38)
        btn_fis_borc.clicked.connect(lambda: self._fis_gir('borc'))

        btn_fis_alacak = QPushButton("🟢  Alacak Fişi Gir")
        btn_fis_alacak.setObjectName("btn_success")
        btn_fis_alacak.setFixedHeight(38)
        btn_fis_alacak.clicked.connect(lambda: self._fis_gir('alacak'))

        btn_virman = QPushButton("🔄  Virman")
        btn_virman.setObjectName("btn_warning")
        btn_virman.setFixedHeight(38)
        btn_virman.setToolTip("Bir cari hesaptan diğerine tutar transferi")
        btn_virman.clicked.connect(self._virman)

        hdr_row.addLayout(t_col, 1)
        hdr_row.addWidget(btn_fis_borc)
        hdr_row.addWidget(btn_fis_alacak)
        hdr_row.addWidget(btn_virman)
        outer.addLayout(hdr_row)

        # Özet bant
        self.ozet_lbl = QLabel("")
        self.ozet_lbl.setStyleSheet(
            "background:#EEF6FF; border:1px solid #BDD5EE; border-radius:4px; "
            "padding:6px 14px; font-size:13px;")
        outer.addWidget(self.ozet_lbl)

        # Arama çubuğu
        arama_row = QHBoxLayout()
        arama_row.setSpacing(8)
        arama_ikon = QLabel("🔍")
        arama_ikon.setStyleSheet("font-size:15px;")
        self.edt_ara = QLineEdit()
        self.edt_ara.setPlaceholderText("Mükellef adı veya vergi numarasına göre ara...")
        self.edt_ara.setFixedHeight(34)
        self.edt_ara.setClearButtonEnabled(True)
        self.edt_ara.textChanged.connect(self._ara)
        arama_row.addWidget(arama_ikon)
        arama_row.addWidget(self.edt_ara)
        outer.addLayout(arama_row)

        # Tablo
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(LISTE_COLS))
        self.tbl.setHorizontalHeaderLabels(LISTE_COLS)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.SingleSelection)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setShowGrid(True)
        self.tbl.doubleClicked.connect(self._ekstre_ac)

        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        outer.addWidget(self.tbl, 1)

        # Genel toplam çubuğu
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#DDE1E7; max-height:1px;")
        outer.addWidget(sep)

        bottom = QHBoxLayout()
        self.lbl_gen_borc   = QLabel("—")
        self.lbl_gen_alacak = QLabel("—")
        self.lbl_gen_net    = QLabel("—")
        for lbl in (self.lbl_gen_borc, self.lbl_gen_alacak, self.lbl_gen_net):
            lbl.setStyleSheet("font-weight:bold; font-size:13px;")

        ipucu = QLabel("💡 Çift tıklayarak ekstre açabilirsiniz")
        ipucu.setStyleSheet("color:#94A3B8; font-size:11px;")

        bottom.addWidget(self.lbl_gen_borc)
        bottom.addWidget(QLabel(" | "))
        bottom.addWidget(self.lbl_gen_alacak)
        bottom.addStretch()
        bottom.addWidget(ipucu)
        bottom.addWidget(self.lbl_gen_net)

        btn_pdf = QPushButton("📄  PDF Rapor")
        btn_pdf.setObjectName("btn_secondary")
        btn_pdf.setFixedHeight(34)
        btn_pdf.setToolTip("Cari hesap listesini PDF olarak kaydet")
        btn_pdf.clicked.connect(self._pdf_rapor)
        bottom.addSpacing(12)
        bottom.addWidget(btn_pdf)

        outer.addLayout(bottom)

    # ── Veri ──

    def refresh(self):
        """Ana pencereden çağrılır."""
        self.refresh_clients()

    def _pdf_rapor(self):
        bakiyeler = db.get_tum_bakiyeler()
        if not bakiyeler:
            QMessageBox.information(self, "Bilgi", "Gösterilecek cari kayıt yok.")
            return
        pdf_cari_liste(bakiyeler, parent=self)

    def _ara(self, metin):
        metin = metin.strip().lower()
        for row in range(self.tbl.rowCount()):
            unvan_item = self.tbl.item(row, 1)
            vno_item   = self.tbl.item(row, 2)
            unvan = unvan_item.text().lower() if unvan_item else ""
            vno   = vno_item.text().lower()   if vno_item   else ""
            esles = (not metin) or (metin in unvan) or (metin in vno)
            self.tbl.setRowHidden(row, not esles)

    def refresh_clients(self):
        bakiyeler = db.get_tum_bakiyeler()
        self.tbl.setRowCount(len(bakiyeler))

        gen_borc   = 0.0
        gen_alacak = 0.0
        borclu_sayi = 0

        for row, m in enumerate(bakiyeler):
            borc   = float(m['toplam_borc'])
            alacak = float(m['toplam_alacak'])
            net    = borc - alacak
            gen_borc   += borc
            gen_alacak += alacak

            if net > 0:
                bg = "#FEE2E2"   # Borçlu (kırmızımsı)
                durum = "🔴 Borçlu"
                borclu_sayi += 1
            elif net < 0:
                bg = "#D1FAE5"   # Alacaklı (yeşilimsi)
                durum = "🟢 Alacaklı"
            else:
                bg = "#FFFFFF"
                durum = "⚪ Sıfır"

            tip_text = "Gerçek" if m.get('tip', 'gercek') == 'gercek' else "Tüzel"

            net_str = f"{net:+,.2f}" if net != 0 else "0,00"

            row_data = [
                str(row + 1),
                m['unvan'],
                m['vergi_no'],
                tip_text,
                f"{borc:,.2f}"   if borc   else "—",
                f"{alacak:,.2f}" if alacak else "—",
                net_str,
                durum,
            ]

            for col, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setBackground(QColor(bg))
                item.setTextAlignment(
                    Qt.AlignVCenter | (Qt.AlignRight if col in (4, 5, 6) else Qt.AlignLeft))
                if col == 0:
                    item.setData(Qt.UserRole, m['id'])
                if col == 6:
                    item.setForeground(
                        QColor("#C0392B" if net > 0 else "#1E8449" if net < 0 else "#2C3E50"))
                self.tbl.setItem(row, col, item)
            self.tbl.setRowHeight(row, 34)

        # Genel toplamlar
        gen_net = gen_borc - gen_alacak
        self.lbl_gen_borc.setText(
            f"Toplam Borç: <b style='color:#C0392B'>{gen_borc:,.2f} ₺</b>")
        self.lbl_gen_borc.setTextFormat(Qt.RichText)
        self.lbl_gen_alacak.setText(
            f"Toplam Alacak: <b style='color:#1E8449'>{gen_alacak:,.2f} ₺</b>")
        self.lbl_gen_alacak.setTextFormat(Qt.RichText)

        if gen_net > 0:
            net_lbl = f"<b style='color:#C0392B'>Net (Alacağımız): {gen_net:,.2f} ₺</b>"
        elif gen_net < 0:
            net_lbl = f"<b style='color:#1E8449'>Net (Borçlumuz): {abs(gen_net):,.2f} ₺</b>"
        else:
            net_lbl = "<b>Net Bakiye: 0,00 ₺</b>"
        self.lbl_gen_net.setText(net_lbl)
        self.lbl_gen_net.setTextFormat(Qt.RichText)

        self.ozet_lbl.setText(
            f"📊  Toplam <b>{len(bakiyeler)}</b> aktif mükellef  |  "
            f"🔴 Borçlu: <b>{borclu_sayi}</b>  |  "
            f"🟢 Alacaklı / Sıfır: <b>{len(bakiyeler) - borclu_sayi}</b>")

        # Arama filtresi korunuyor
        self._ara(self.edt_ara.text())

    # ── Seçili mükellef ──

    def _selected_mukellef(self):
        row = self.tbl.currentRow()
        if row < 0:
            return None, None
        item = self.tbl.item(row, 0)
        if item is None:
            return None, None
        mid   = item.data(Qt.UserRole)
        unvan = self.tbl.item(row, 1).text() if self.tbl.item(row, 1) else ""
        vno   = self.tbl.item(row, 2).text() if self.tbl.item(row, 2) else ""
        return mid, unvan

    # ── Eylemler ──

    def _ekstre_ac(self):
        mid, unvan = self._selected_mukellef()
        if mid is None:
            return
        m = db.get_mukellef(mid)
        vno = m['vergi_no'] if m else ""
        dlg = EkstreDialog(mid, unvan, vno, parent=self)
        dlg.exec_()
        self.refresh_clients()   # Fiş girildiyse bakiye güncelle

    def _fis_gir(self, tip):
        mid, unvan = self._selected_mukellef()
        if mid is None:
            QMessageBox.information(self, "Bilgi",
                "Lütfen önce listeden bir mükellef seçin.")
            return
        dlg = CariDialog(tip=tip, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            r = dlg.result
            if tip == 'borc':
                db.add_cari(mid, r['tarih'], r['aciklama'], r['tutar'], 0, r['fisno'])
            else:
                db.add_cari(mid, r['tarih'], r['aciklama'], 0, r['tutar'], r['fisno'])
            self.refresh_clients()

    def _virman(self):
        mid, _ = self._selected_mukellef()
        dlg = VirmanDialog(kaynak_id=mid, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh_clients()
            QMessageBox.information(
                self, "Virman Tamamlandı",
                "✅ Virman işlemi başarıyla uygulandı.\n"
                "Kaynak hesaba alacak, hedef hesaba borç fişi girildi."
            )
