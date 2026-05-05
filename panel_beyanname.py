from datetime import date
import os
import tempfile

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QCheckBox,
    QDateEdit, QDoubleSpinBox, QLineEdit, QMessageBox,
    QGroupBox, QFrame, QSpinBox, QAbstractItemView, QProgressDialog
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from db import db, AYLAR, donem_label, beyanname_son_gun
from styles import CLR_GREEN, CLR_RED, CLR_ORANGE, CLR_YELLOW, CLR_WHITE
from pdf_utils import pdf_beyannameler

# Renk sabitlerini tamamla
CLR_BLUE   = "#DBEAFE"
CLR_PURPLE = "#EDE9FE"
CLR_GRAY   = "#E2E8F0"  # Bu ay yok / Atlandı


def _odeme_goster(odendi_flag, odeme_tipi, verildi_flag):
    """Ödendi sütununda görünecek metni döner."""
    if odendi_flag:
        if odeme_tipi == 'smmm':
            return "🏦 SMMM Ödedi"
        elif odeme_tipi == 'mukellef':
            return "💰 Mükellef Ödedi"
        return "✅ Ödendi"
    elif not verildi_flag:
        return "➖"
    return "❌ Ödenmedi"


# ──────────────────────────────────────────────
#  Beyanname Düzenleme Diyaloğu
# ──────────────────────────────────────────────
class BeyannameDialog(QDialog):
    def __init__(self, beyanname: dict, parent=None):
        super().__init__(parent)
        self.b = beyanname
        self.setWindowTitle(
            f"{beyanname['tur']}  —  {beyanname['unvan']}")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._build()
        self._fill()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        # Bilgi başlığı
        info = QLabel(
            f"<b>{self.b['unvan']}</b>  |  {self.b['tur']}  |  "
            f"{donem_label(self.b['tur'], self.b['yil'], self.b['donem'])}")
        info.setStyleSheet(
            "background:#EEF6FF; border:1px solid #BDD5EE; border-radius:4px; padding:8px;")
        info.setWordWrap(True)
        lay.addWidget(info)

        # Beyanname durumu
        grp_ver = QGroupBox("Beyanname Durumu")
        fv = QFormLayout(grp_ver)
        fv.setLabelAlignment(Qt.AlignRight)
        fv.setSpacing(8)

        self.chk_verildi = QCheckBox("Beyanname Verildi")
        self.chk_verildi.stateChanged.connect(self._toggle_verildi)

        self.dte_verilme = QDateEdit()
        self.dte_verilme.setDisplayFormat("dd.MM.yyyy")
        self.dte_verilme.setCalendarPopup(True)
        self.dte_verilme.setDate(QDate.currentDate())

        self.dte_son_gun = QDateEdit()
        self.dte_son_gun.setDisplayFormat("dd.MM.yyyy")
        self.dte_son_gun.setCalendarPopup(True)
        self.dte_son_gun.setDate(QDate.currentDate())

        fv.addRow(self.chk_verildi)
        fv.addRow("Verilme Tarihi:", self.dte_verilme)
        fv.addRow("Son Gün:", self.dte_son_gun)
        lay.addWidget(grp_ver)

        # Ödeme durumu
        grp_ode = QGroupBox("Ödeme Durumu")
        fo = QFormLayout(grp_ode)
        fo.setLabelAlignment(Qt.AlignRight)
        fo.setSpacing(8)

        self.chk_odendi = QCheckBox("Vergi Ödendi")
        self.chk_odendi.stateChanged.connect(self._toggle_odendi)

        self.cmb_odeme_tipi = QComboBox()
        self.cmb_odeme_tipi.addItem("💰  Mükellef Ödedi", 'mukellef')
        self.cmb_odeme_tipi.addItem("🏦  SMMM Ödedi (Carisine Borç Kaydedilir)", 'smmm')

        self.dte_odeme = QDateEdit()
        self.dte_odeme.setDisplayFormat("dd.MM.yyyy")
        self.dte_odeme.setCalendarPopup(True)
        self.dte_odeme.setDate(QDate.currentDate())

        self.spn_tutar = QDoubleSpinBox()
        self.spn_tutar.setMaximum(99_999_999)
        self.spn_tutar.setDecimals(2)
        self.spn_tutar.setSuffix(" ₺")
        self.spn_tutar.setGroupSeparatorShown(True)

        fo.addRow(self.chk_odendi)
        fo.addRow("Ödeyen:", self.cmb_odeme_tipi)
        fo.addRow("Ödeme Tarihi:", self.dte_odeme)
        fo.addRow("Vergi Tutarı:", self.spn_tutar)
        lay.addWidget(grp_ode)

        # Açıklama
        self.edt_aciklama = QLineEdit()
        self.edt_aciklama.setPlaceholderText("Açıklama (isteğe bağlı)")
        lay.addWidget(QLabel("Açıklama:"))
        lay.addWidget(self.edt_aciklama)

        # Butonlar
        btn_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Save).setText("💾  Kaydet")
        btn_box.button(QDialogButtonBox.Save).setObjectName("btn_primary")
        btn_box.button(QDialogButtonBox.Cancel).setText("İptal")
        btn_box.accepted.connect(self._save)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)

    def _fill(self):
        b = self.b
        verildi = bool(b.get('verildi', 0))
        self.chk_verildi.setChecked(verildi)
        self.dte_verilme.setEnabled(verildi)
        if b.get('verilme_tarihi'):
            d = QDate.fromString(str(b['verilme_tarihi'])[:10], "yyyy-MM-dd")
            if d.isValid():
                self.dte_verilme.setDate(d)
        if b.get('son_gun'):
            d = QDate.fromString(str(b['son_gun'])[:10], "yyyy-MM-dd")
            if d.isValid():
                self.dte_son_gun.setDate(d)

        odendi = bool(b.get('odendi', 0))
        self.chk_odendi.setChecked(odendi)
        self.cmb_odeme_tipi.setEnabled(odendi)
        self.dte_odeme.setEnabled(odendi)
        self.spn_tutar.setEnabled(odendi)
        # Ödeme tipini seç
        ot = b.get('odeme_tipi') or 'mukellef'
        idx = self.cmb_odeme_tipi.findData(ot)
        if idx >= 0:
            self.cmb_odeme_tipi.setCurrentIndex(idx)
        if b.get('odeme_tarihi'):
            d = QDate.fromString(str(b['odeme_tarihi'])[:10], "yyyy-MM-dd")
            if d.isValid():
                self.dte_odeme.setDate(d)
        self.spn_tutar.setValue(float(b.get('tutar', 0)))
        self.edt_aciklama.setText(b.get('aciklama', ''))

    def _toggle_verildi(self, state):
        e = bool(state)
        self.dte_verilme.setEnabled(e)

    def _toggle_odendi(self, state):
        e = bool(state)
        self.cmb_odeme_tipi.setEnabled(e)
        self.dte_odeme.setEnabled(e)
        self.spn_tutar.setEnabled(e)

    def _save(self):
        self.result_data = {
            'verildi':         int(self.chk_verildi.isChecked()),
            'verilme_tarihi':  self.dte_verilme.date().toString("yyyy-MM-dd")
                               if self.chk_verildi.isChecked() else None,
            'son_gun':         self.dte_son_gun.date().toString("yyyy-MM-dd"),
            'odendi':          int(self.chk_odendi.isChecked()),
            'odeme_tipi':      self.cmb_odeme_tipi.currentData()
                               if self.chk_odendi.isChecked() else None,
            'odeme_tarihi':    self.dte_odeme.date().toString("yyyy-MM-dd")
                               if self.chk_odendi.isChecked() else None,
            'tutar':           self.spn_tutar.value(),
            'aciklama':        self.edt_aciklama.text().strip(),
        }
        # Dialog'dan SMMM ödemesi seçildiyse cari kaydı uyarısı
        if (self.chk_odendi.isChecked() and
                self.cmb_odeme_tipi.currentData() == 'smmm' and
                self.spn_tutar.value() > 0 and
                not self.b.get('odendi')):
            self.result_data['_cari_borc_ekle'] = True
        self.accept()


# ──────────────────────────────────────────────
#  Beyannameler Paneli
# ──────────────────────────────────────────────
# Sütun tanımları
COLS = [
    "Mükellef",        # 0
    "Vergi No",         # 1
    "Beyanname Türü",  # 2
    "Dönem",            # 3
    "Son Gün",          # 4
    "Verildi",          # 5
    "Verilme Tarihi",   # 6
    "Ödendi",           # 7
    "Tutar (₺)",        # 8
    "Açıklama",         # 9
    "PDF",              # 10
]


class BeyannamePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(12)

        # Başlık
        title = QLabel("📋  Beyanname Takibi")
        title.setObjectName("page_title")
        outer.addWidget(title)

        # ── Dönem seçimi ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        lbl_yil = QLabel("Yıl:")
        lbl_yil.setStyleSheet("font-weight: bold;")
        self.spn_yil = QSpinBox()
        self.spn_yil.setRange(2000, 2099)
        self.spn_yil.setValue(date.today().year)
        self.spn_yil.setFixedWidth(80)

        lbl_ay = QLabel("Ay:")
        lbl_ay.setStyleSheet("font-weight: bold;")
        self.cmb_ay = QComboBox()
        for i, ay in enumerate(AYLAR[1:], 1):
            self.cmb_ay.addItem(ay, i)
        self.cmb_ay.setCurrentIndex(date.today().month - 1)
        self.cmb_ay.setFixedWidth(110)

        btn_yukle = QPushButton("🔄  Dönemi Yükle")
        btn_yukle.setObjectName("btn_primary")
        btn_yukle.setFixedHeight(34)
        btn_yukle.clicked.connect(self._load)

        # Mükellef filtresi
        lbl_fil = QLabel("Mükellef:")
        lbl_fil.setStyleSheet("font-weight: bold;")
        self.cmb_filter = QComboBox()
        self.cmb_filter.setMinimumWidth(200)
        self.cmb_filter.currentIndexChanged.connect(self._apply_filter)

        # Durum filtresi
        lbl_durum = QLabel("Durum:")
        lbl_durum.setStyleSheet("font-weight: bold;")
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItem("— Tüm Durumlar —", "tumu")
        self.cmb_durum.addItem("✅ Verildi", "verildi")
        self.cmb_durum.addItem("❌ Verilmedi", "verilmedi")
        self.cmb_durum.addItem("💰 Ödendi", "odendi")
        self.cmb_durum.addItem("⚠️ Ödenmedi", "odenmedi")
        self.cmb_durum.addItem("🔴 Süre Geçti", "sure_gecti")
        self.cmb_durum.addItem("⏭ Bu Ay Yok", "bu_ay_yok")
        self.cmb_durum.setMinimumWidth(160)
        self.cmb_durum.currentIndexChanged.connect(self._apply_filter)

        # Beyanname türü filtresi
        lbl_tur = QLabel("Tür:")
        lbl_tur.setStyleSheet("font-weight: bold;")
        self.cmb_tur = QComboBox()
        self.cmb_tur.addItem("— Tüm Türler —", None)
        self.cmb_tur.setMinimumWidth(180)
        self.cmb_tur.currentIndexChanged.connect(self._apply_filter)

        toolbar.addWidget(lbl_yil)
        toolbar.addWidget(self.spn_yil)
        toolbar.addWidget(lbl_ay)
        toolbar.addWidget(self.cmb_ay)
        toolbar.addWidget(btn_yukle)
        toolbar.addSpacing(20)
        toolbar.addWidget(lbl_fil)
        toolbar.addWidget(self.cmb_filter, 1)
        toolbar.addSpacing(16)
        toolbar.addWidget(lbl_durum)
        toolbar.addWidget(self.cmb_durum)
        toolbar.addSpacing(16)
        toolbar.addWidget(lbl_tur)
        toolbar.addWidget(self.cmb_tur)
        outer.addLayout(toolbar)
        # ── Hızlı işlem butonları ──
        quick = QHBoxLayout()
        quick.setSpacing(8)

        self.btn_ver = QPushButton("✅  Verildi İşaretle")
        self.btn_ver.setObjectName("btn_success")
        self.btn_ver.setFixedHeight(34)
        self.btn_ver.setToolTip("Seçili beyannameyi bugün verildi olarak işaretle")
        self.btn_ver.clicked.connect(self._hizli_verildi)

        self.btn_ode_mukellef = QPushButton("💰  Mükellef Ödedi")
        self.btn_ode_mukellef.setObjectName("btn_primary")
        self.btn_ode_mukellef.setFixedHeight(34)
        self.btn_ode_mukellef.setToolTip("Vergiyi mükellef kendi ödedi")
        self.btn_ode_mukellef.clicked.connect(self._hizli_odendi_mukellef)

        self.btn_ode_smmm = QPushButton("🏦  SMMM Ödedi")
        self.btn_ode_smmm.setObjectName("btn_warning")
        self.btn_ode_smmm.setFixedHeight(34)
        self.btn_ode_smmm.setToolTip("Vergiyi SMMM ödedi — mükellefin carisine borç kaydedilir")
        self.btn_ode_smmm.clicked.connect(self._hizli_odendi_smmm)

        self.btn_geri = QPushButton("↩  Verilmedi Yap")
        self.btn_geri.setObjectName("btn_warning")
        self.btn_geri.setFixedHeight(34)
        self.btn_geri.setToolTip("Seçili beyannameyi verilmedi durumuna al")
        self.btn_geri.clicked.connect(self._hizli_geri_al)

        self.btn_odeme_iptal = QPushButton("🔴  Ödemeyi İptal")
        self.btn_odeme_iptal.setObjectName("btn_danger")
        self.btn_odeme_iptal.setFixedHeight(34)
        self.btn_odeme_iptal.setToolTip("Ödeme bilgilerini sıfırla. SMMM ödemesiyse cari kaydı da silinebilir.")
        self.btn_odeme_iptal.clicked.connect(self._hizli_odeme_iptal)

        self.btn_atla = QPushButton("⏭  Bu Ay Yok")
        self.btn_atla.setObjectName("btn_secondary")
        self.btn_atla.setFixedHeight(34)
        self.btn_atla.setToolTip("Bu beyanname bu ay verilmeyecek (tevkifat yok, vb.) — gri ile işaretle")
        self.btn_atla.clicked.connect(self._hizli_atla)

        self.btn_tumverildi = QPushButton("✅✅  Tümünü Verildi İşaretle")
        self.btn_tumverildi.setObjectName("btn_secondary")
        self.btn_tumverildi.setFixedHeight(34)
        self.btn_tumverildi.setToolTip("Görünen tüm beyannameleri verildi olarak işaretle")
        self.btn_tumverildi.clicked.connect(self._hizli_tumu_verildi)

        lbl_ipucu = QLabel("ℹ️  Çift tıklayarak detayları düzenleyebilirsiniz")
        lbl_ipucu.setStyleSheet("color:#94A3B8; font-size:11px;")

        quick.addWidget(self.btn_ver)
        quick.addWidget(self.btn_ode_mukellef)
        quick.addWidget(self.btn_ode_smmm)
        quick.addWidget(self.btn_geri)
        quick.addWidget(self.btn_odeme_iptal)
        quick.addWidget(self.btn_atla)
        quick.addSpacing(12)
        quick.addWidget(self.btn_tumverildi)
        quick.addStretch()
        quick.addWidget(lbl_ipucu)

        btn_pdf = QPushButton("📄  PDF Rapor")
        btn_pdf.setObjectName("btn_secondary")
        btn_pdf.setFixedHeight(34)
        btn_pdf.setToolTip("Görünen beyannameleri PDF olarak dışa aktar")
        btn_pdf.clicked.connect(self._pdf_rapor)
        quick.addWidget(btn_pdf)

        btn_zirve_tara = QPushButton("🔍  Zirve'den Tara")
        btn_zirve_tara.setObjectName("btn_primary")
        btn_zirve_tara.setFixedHeight(34)
        btn_zirve_tara.setToolTip("Tüm yıllar taranır — bulunan beyanname PDF'leri DB'ye kaydedilir ve Verildi işaretlenir")
        btn_zirve_tara.clicked.connect(self._zirve_tara)
        quick.addWidget(btn_zirve_tara)

        outer.addLayout(quick)

        # ── Toplu işlem çubuğu ──
        toplu = QHBoxLayout()
        toplu.setSpacing(8)
        lbl_toplu = QLabel("Seçili satırlar:")
        lbl_toplu.setStyleSheet("font-weight:bold; color:#475569;")

        self.btn_toplu_verildi = QPushButton("✅ Toplu Verildi")
        self.btn_toplu_verildi.setObjectName("btn_success")
        self.btn_toplu_verildi.setFixedHeight(30)
        self.btn_toplu_verildi.setToolTip("Seçili tüm beyannameleri bugün verildi olarak işaretle (Ctrl/Shift ile çoklu seçim)")
        self.btn_toplu_verildi.clicked.connect(lambda: self._toplu_durum('verildi'))

        self.btn_toplu_mukellef = QPushButton("💰 Toplu Mükellef Ödedi")
        self.btn_toplu_mukellef.setObjectName("btn_primary")
        self.btn_toplu_mukellef.setFixedHeight(30)
        self.btn_toplu_mukellef.clicked.connect(lambda: self._toplu_durum('odendi_mukellef'))

        self.btn_toplu_geri = QPushButton("↩ Toplu Verilmedi")
        self.btn_toplu_geri.setObjectName("btn_warning")
        self.btn_toplu_geri.setFixedHeight(30)
        self.btn_toplu_geri.clicked.connect(lambda: self._toplu_durum('geri_al'))

        self.btn_toplu_atla = QPushButton("⏭ Toplu Bu Ay Yok")
        self.btn_toplu_atla.setObjectName("btn_secondary")
        self.btn_toplu_atla.setFixedHeight(30)
        self.btn_toplu_atla.clicked.connect(lambda: self._toplu_durum('atla'))

        self.lbl_secili_sayi = QLabel("(hiç seçili yok)")
        self.lbl_secili_sayi.setStyleSheet("color:#64748B; font-size:11px;")

        toplu.addWidget(lbl_toplu)
        toplu.addWidget(self.btn_toplu_verildi)
        toplu.addWidget(self.btn_toplu_mukellef)
        toplu.addWidget(self.btn_toplu_geri)
        toplu.addWidget(self.btn_toplu_atla)
        toplu.addWidget(self.lbl_secili_sayi)
        toplu.addStretch()
        outer.addLayout(toplu)

        self.summary_lbl = QLabel("")
        self.summary_lbl.setStyleSheet(
            "background:#EEF6FF; border:1px solid #BDD5EE; border-radius:4px; "
            "padding: 6px 12px; font-size: 13px;")
        outer.addWidget(self.summary_lbl)

        # ── Renk açıklaması ──
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for renk, aciklama in [
            (CLR_GREEN,  "✅ Verildi + Ödendi"),
            (CLR_BLUE,   "✅ Verildi / Ödeme Bekleniyor"),
            (CLR_ORANGE, "✅ Verildi / Ödenmedi"),
            (CLR_RED,    "❌ Süre Geçti!"),
            (CLR_WHITE,  "⏳ Bekliyor"),
            (CLR_GRAY,   "⏭ Bu Ay Yok"),
        ]:
            lbl = QLabel(f"█ {aciklama}")
            lbl.setStyleSheet(
                f"background:{renk}; border:1px solid #ccc; "
                f"border-radius:3px; padding:2px 8px; font-size:11px;")
            legend.addWidget(lbl)
        legend.addStretch()
        outer.addLayout(legend)

        # ── Tablo ──
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(COLS))
        self.tbl.setHorizontalHeaderLabels(COLS)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.ExtendedSelection)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.doubleClicked.connect(self._edit)
        self.tbl.itemSelectionChanged.connect(self._secim_degisti)
        self.tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tbl.setWordWrap(False)

        hdr = self.tbl.horizontalHeader()
        hdr.setStretchLastSection(False)
        # Excel gibi: her sütun bağımsız, diğerlerini etkilemez
        col_widths = [220, 110, 120, 160, 100, 90, 120, 130, 90, 150, 70]
        for i, w in enumerate(col_widths):
            hdr.setSectionResizeMode(i, QHeaderView.Interactive)
            hdr.setMinimumSectionSize(60)
            self.tbl.setColumnWidth(i, w)
        outer.addWidget(self.tbl, 1)

        # Alt durum çubuğu
        self.alt_durum = QLabel("")
        self.alt_durum.setStyleSheet("color:#94A3B8; font-size:11px; padding:2px 0;")
        outer.addWidget(self.alt_durum)

    # ── Veri ──

    def refresh(self):
        self._load()

    def set_yil(self, yil: int):
        """Ana pencereden aktif yıl değişince güncelle."""
        if self.spn_yil.value() != yil:
            self.spn_yil.setValue(yil)  # valueChanged sinyali _load() tetikler
        else:
            self._load()  # Zaten aynı yılsa sadece yenile

    def _pdf_rapor(self):
        if not self._data:
            QMessageBox.information(self, "Bilgi", "PDF oluşturmak için önce dönemi yükleyin.")
            return
        ay_adi = self.cmb_ay.currentText()
        yil = self.spn_yil.value()
        pdf_beyannameler(self._data, yil, ay_adi, parent=self)

    def _zirve_tara(self):
        from zirve_beyanname_tara import tara_ve_aktar
        prog = QProgressDialog("Zirve klasörleri taranıyor...", None, 0, 0, self)
        prog.setWindowTitle("Zirve Tarama")
        prog.setWindowModality(Qt.WindowModal)
        prog.setMinimumDuration(0)
        prog.setValue(0)

        mesajlar = []
        def progress_cb(msg):
            mesajlar.append(msg)
            prog.setLabelText(msg)
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()

        sonuc = tara_ve_aktar(progress_cb=progress_cb)
        prog.close()

        # Tabloyu yenile
        self._load()

        ozet = (
            f"✅ Tarama tamamlandı!\n\n"
            f"Yeni PDF kaydedildi : {sonuc['eklenen']}\n"
            f"Güncellenen PDF     : {sonuc['guncellenen']}\n"
            f"Verildi işaretlendi : {sonuc['verildi_isaret']}\n"
        )
        if sonuc['hatalar']:
            ozet += f"\n⚠️ Hatalar ({len(sonuc['hatalar'])}):\n"
            ozet += "\n".join(sonuc['hatalar'][:10])
        QMessageBox.information(self, "Zirve Tarama Sonucu", ozet)

    def _ac_pdf(self, b):
        """DB'den PDF'i geçici dosyaya yazıp açar."""
        sonuc = db.get_beyanname_pdf(b['mukellef_id'], b['tur'], b['yil'], b['donem'])
        if not sonuc or not sonuc.get('pdf_data'):
            QMessageBox.warning(self, "PDF Bulunamadı", "Bu beyanname için kayıtlı PDF yok.")
            return
        try:
            dosya_adi = sonuc.get('dosya_adi') or f"{b['tur']}_{b['yil']}_{b['donem']}.pdf"
            tmp_dir = tempfile.gettempdir()
            tmp_path = os.path.join(tmp_dir, dosya_adi)
            with open(tmp_path, 'wb') as f:
                f.write(bytes(sonuc['pdf_data']))
            os.startfile(tmp_path)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF açılamadı:\n{e}")



    def _load(self):
        yil = self.spn_yil.value()
        ay  = self.cmb_ay.currentData()
        self._data = db.get_ay_beyannameleri(yil, ay)

        # Mükellef filtre combo'sunu doldur
        self.cmb_filter.blockSignals(True)
        prev_id = self.cmb_filter.currentData()
        self.cmb_filter.clear()
        self.cmb_filter.addItem("— Tümü —", None)
        seen = {}
        for b in self._data:
            if b['mukellef_id'] not in seen:
                seen[b['mukellef_id']] = b['unvan']
                self.cmb_filter.addItem(b['unvan'], b['mukellef_id'])
        idx = self.cmb_filter.findData(prev_id)
        self.cmb_filter.setCurrentIndex(max(0, idx))
        self.cmb_filter.blockSignals(False)

        # Tür filtre combo'sunu doldur
        self.cmb_tur.blockSignals(True)
        prev_tur = self.cmb_tur.currentData()
        self.cmb_tur.clear()
        self.cmb_tur.addItem("— Tüm Türler —", None)
        turler = sorted({b['tur'] for b in self._data})
        for t in turler:
            self.cmb_tur.addItem(t, t)
        idx_tur = self.cmb_tur.findData(prev_tur)
        self.cmb_tur.setCurrentIndex(max(0, idx_tur))
        self.cmb_tur.blockSignals(False)

        self._apply_filter()

    def _apply_filter(self):
        today_str = date.today().isoformat()
        fid   = self.cmb_filter.currentData()
        durum = self.cmb_durum.currentData()
        tur   = self.cmb_tur.currentData()

        filtered = self._data

        # Mükellef filtresi
        if fid is not None:
            filtered = [b for b in filtered if b['mukellef_id'] == fid]

        # Tür filtresi
        if tur is not None:
            filtered = [b for b in filtered if b['tur'] == tur]

        # Durum filtresi
        if durum == "verildi":
            filtered = [b for b in filtered if b['verildi'] and not b.get('atlandi')]
        elif durum == "verilmedi":
            filtered = [b for b in filtered if not b['verildi'] and not b.get('atlandi')]
        elif durum == "odendi":
            filtered = [b for b in filtered if b['odendi'] and not b.get('atlandi')]
        elif durum == "odenmedi":
            filtered = [b for b in filtered
                        if b['verildi'] and not b['odendi'] and not b.get('atlandi')]
        elif durum == "sure_gecti":
            filtered = [b for b in filtered
                        if not b['verildi'] and not b.get('atlandi')
                        and b.get('son_gun') and b['son_gun'] < today_str]
        elif durum == "bu_ay_yok":
            filtered = [b for b in filtered if b.get('atlandi')]

        self._render(filtered)

    def _render(self, beyanlar):
        today_str = date.today().isoformat()
        self.tbl.setRowCount(len(beyanlar))

        toplam   = len(beyanlar)
        atlandi  = sum(1 for b in beyanlar if b.get('atlandi'))
        aktif    = [b for b in beyanlar if not b.get('atlandi')]
        verildi  = sum(1 for b in aktif if b['verildi'])
        odendi   = sum(1 for b in aktif if b['odendi'])
        gecmis   = sum(1 for b in aktif
                       if not b['verildi'] and b.get('son_gun') and b['son_gun'] < today_str)

        for row, b in enumerate(beyanlar):
            verildi_flag = bool(b['verildi'])
            odendi_flag  = bool(b['odendi'])
            atlandi_flag = bool(b.get('atlandi', 0))
            son_gun_str  = b.get('son_gun') or ''
            # Son günü okunabilir formata çevir: yyyy-MM-dd → dd.MM.yyyy
            son_gun_goster = ''
            if son_gun_str:
                try:
                    from datetime import datetime as _dt
                    son_gun_goster = _dt.strptime(son_gun_str[:10], '%Y-%m-%d').strftime('%d.%m.%Y')
                except Exception:
                    son_gun_goster = son_gun_str

            # Arka plan rengi
            if atlandi_flag:
                bg = CLR_GRAY
            elif verildi_flag and odendi_flag:
                bg = CLR_GREEN
            elif verildi_flag and not odendi_flag and son_gun_str and son_gun_str < today_str:
                bg = CLR_ORANGE
            elif verildi_flag and not odendi_flag:
                bg = CLR_BLUE
            elif not verildi_flag and son_gun_str and son_gun_str < today_str:
                bg = CLR_RED
            else:
                bg = CLR_WHITE

            if atlandi_flag:
                verildi_goster = "⏭ Bu Ay Yok"
                odeme_goster   = "—"
            else:
                verildi_goster = "✅ Verildi" if verildi_flag else "❌ Verilmedi"
                odeme_goster   = _odeme_goster(odendi_flag, b.get('odeme_tipi'), verildi_flag)

            row_data = [
                b['unvan'],
                b['vergi_no'],
                b['tur'],
                donem_label(b['tur'], b['yil'], b['donem']),
                son_gun_goster,
                verildi_goster,
                b.get('verilme_tarihi') or "—",
                odeme_goster,
                f"{float(b.get('tutar', 0)):,.2f}" if b.get('tutar') else "—",
                b.get('aciklama', ''),
            ]

            for col, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setBackground(QColor(bg))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if col == 0:
                    item.setData(Qt.UserRole, b)
                self.tbl.setItem(row, col, item)

            # PDF sütunu (kolon 10)
            has_pdf = db.has_beyanname_pdf(b['mukellef_id'], b['tur'], b['yil'], b['donem'])
            if has_pdf:
                btn_ac = QPushButton("📄 Aç")
                btn_ac.setFixedHeight(26)
                btn_ac.setStyleSheet(
                    "QPushButton{background:#2563EB;color:white;border-radius:4px;"
                    "font-size:11px;padding:0 8px;}"
                    "QPushButton:hover{background:#1D4ED8;}")
                _b = dict(b)
                btn_ac.clicked.connect(lambda _, bd=_b: self._ac_pdf(bd))
                self.tbl.setCellWidget(row, 10, btn_ac)
            else:
                item_pdf = QTableWidgetItem("—")
                item_pdf.setBackground(QColor(bg))
                item_pdf.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(row, 10, item_pdf)

        self.summary_lbl.setText(
            f"📊  Toplam: <b>{toplam}</b>  |  "
            f"✅ Verilen: <b>{verildi}</b>  |  "
            f"❌ Bekleyen: <b>{len(aktif) - verildi}</b>  |  "
            f"⏰ Süresi Geçen: <b style='color:#EF4444'>{gecmis}</b>  |  "
            f"💰 Ödenen: <b>{odendi}</b>  |  "
            f"⏭ Bu Ay Yok: <b>{atlandi}</b>")

        self.alt_durum.setText(
            f"Son güncelleme: {date.today().strftime('%d.%m.%Y')}  |  "
            f"Çift tıklayarak detay düzenleme yapabilirsiniz.")

    # ── Hızlı işlem yöntemleri ──

    def _get_selected_beyanname(self):
        row = self.tbl.currentRow()
        if row < 0:
            return None
        item = self.tbl.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _get_selected_beyannameler(self):
        """Seçili tüm satırların beyanname dict listesini döner."""
        secili_satirlar = set(idx.row() for idx in self.tbl.selectedIndexes())
        sonuc = []
        for row in sorted(secili_satirlar):
            item = self.tbl.item(row, 0)
            if item:
                b = item.data(Qt.UserRole)
                if b:
                    sonuc.append(b)
        return sonuc

    def _secim_degisti(self):
        sayi = len(set(idx.row() for idx in self.tbl.selectedIndexes()))
        if sayi == 0:
            self.lbl_secili_sayi.setText("(hiç seçili yok)")
        elif sayi == 1:
            self.lbl_secili_sayi.setText("1 satır seçili")
        else:
            self.lbl_secili_sayi.setText(f"{sayi} satır seçili")

    def _toplu_durum(self, islem):
        beyanlar = self._get_selected_beyannameler()
        if not beyanlar:
            QMessageBox.information(self, "Bilgi",
                "Lütfen işlem yapmak istediğiniz satırları seçin.\n"
                "Birden fazla satır için Ctrl veya Shift ile seçim yapabilirsiniz.")
            return

        today = date.today().isoformat()
        islem_adi = {
            'verildi': 'Verildi İşaretle',
            'odendi_mukellef': 'Mükellef Ödedi İşaretle',
            'geri_al': 'Verilmedi Yap',
            'atla': 'Bu Ay Yok İşaretle',
        }.get(islem, islem)

        cevap = QMessageBox.question(
            self, "Toplu İşlem Onayı",
            f"<b>{len(beyanlar)}</b> beyanname için '<b>{islem_adi}</b>' uygulanacak.\nDevam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No)
        if cevap != QMessageBox.Yes:
            return

        hata = 0
        for b in beyanlar:
            try:
                if islem == 'verildi':
                    if b.get('atlandi'):
                        continue
                    son_gun = b.get('son_gun') or beyanname_son_gun(b['tur'], b['yil'], b['donem']) or today
                    db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
                        **b, 'verildi': 1, 'verilme_tarihi': today, 'son_gun': son_gun,
                    })
                elif islem == 'odendi_mukellef':
                    if not b.get('verildi') or b.get('atlandi'):
                        continue
                    db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
                        **b, 'odendi': 1, 'odeme_tarihi': today, 'odeme_tipi': 'mukellef',
                    })
                elif islem == 'geri_al':
                    db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
                        **b, 'verildi': 0, 'verilme_tarihi': None,
                        'odendi': 0, 'odeme_tarihi': None, 'atlandi': 0,
                    })
                elif islem == 'atla':
                    db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
                        **b, 'atlandi': 1, 'verildi': 0,
                    })
            except Exception:
                hata += 1

        self._load()
        basari = len(beyanlar) - hata
        mesaj = f"✅ {basari} beyanname güncellendi."
        if hata:
            mesaj += f"\n⚠️ {hata} kayıt güncellenemedi."
        QMessageBox.information(self, "Toplu İşlem Tamamlandı", mesaj)

    def _hizli_verildi(self):
        b = self._get_selected_beyanname()
        if not b:
            QMessageBox.information(self, "Bilgi", "Lütfen bir beyanname satırı seçin.")
            return
        today = date.today().isoformat()
        # Son gün boşsa otomatik hesapla
        son_gun = b.get('son_gun') or beyanname_son_gun(b['tur'], b['yil'], b['donem']) or today
        db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
            **b,
            'verildi': 1,
            'verilme_tarihi': today,
            'son_gun': son_gun,
        })
        self._load()

    def _hizli_odendi_mukellef(self):
        b = self._get_selected_beyanname()
        if not b:
            QMessageBox.information(self, "Bilgi", "Lütfen bir beyanname satırı seçin.")
            return
        if not b.get('verildi'):
            QMessageBox.warning(self, "Uyarı",
                "Beyanname henüz verildi olarak işaretlenmemiş.\nÖnce 'Verildi İşaretle' butonuna basın.")
            return
        today = date.today().isoformat()
        db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
            **b,
            'odendi': 1,
            'odeme_tarihi': today,
            'odeme_tipi': 'mukellef',
        })
        self._load()

    def _hizli_odendi_smmm(self):
        b = self._get_selected_beyanname()
        if not b:
            QMessageBox.information(self, "Bilgi", "Lütfen bir beyanname satırı seçin.")
            return
        if not b.get('verildi'):
            QMessageBox.warning(self, "Uyarı",
                "Beyanname henüz verildi olarak işaretlenmemiş.\nÖnce 'Verildi İşaretle' butonuna basın.")
            return

        # Tutar sorulsun
        from PyQt5.QtWidgets import QInputDialog
        tutar_mevcut = float(b.get('tutar') or 0)
        tutar, ok = QInputDialog.getDouble(
            self, "SMMM Ödedi — Tutar",
            f"{b['unvan']}\n{b['tur']} — {donem_label(b['tur'], b['yil'], b['donem'])}\n\nÖdenen vergi tutarı (₺):",
            value=tutar_mevcut, min=0, max=99_999_999, decimals=2)
        if not ok:
            return

        today = date.today().isoformat()
        db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
            **b,
            'odendi': 1,
            'odeme_tarihi': today,
            'odeme_tipi': 'smmm',
            'tutar': tutar,
        })

        # Cari hesaba borç kaydı ekle
        if tutar > 0:
            aciklama = (
                f"SMMM tarafından ödenen vergi — "
                f"{b['tur']} / {donem_label(b['tur'], b['yil'], b['donem'])}"
            )
            db.add_cari(
                mukellef_id=b['mukellef_id'],
                tarih=today,
                aciklama=aciklama,
                borc=tutar,
                alacak=0.0,
                fisno=f"BEYAN-{b['tur'][:3]}-{b['yil']}-{b['donem']}"
            )
            QMessageBox.information(
                self, "Kaydedildi",
                f"✅ Ödeme kaydedildi.\n"
                f"💳 {b['unvan']} carisine {tutar:,.2f} ₺ borç eklendi."
            )
        self._load()

    def _hizli_geri_al(self):
        b = self._get_selected_beyanname()
        if not b:
            QMessageBox.information(self, "Bilgi", "Lütfen bir beyanname satırı seçin.")
            return
        db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
            **b,
            'verildi': 0,
            'verilme_tarihi': None,
            'odendi': 0,
            'odeme_tarihi': None,
            'odeme_tipi': None,
            'atlandi': 0,
        })
        self._load()

    def _hizli_odeme_iptal(self):
        b = self._get_selected_beyanname()
        if not b:
            QMessageBox.information(self, "Bilgi", "Lütfen bir beyanname satırı seçin.")
            return
        if not b.get('odendi'):
            QMessageBox.information(self, "Bilgi", "Bu beyanname zaten ödenmedi olarak işaretli.")
            return

        # SMMM ödemesiyse cari kaydını silmek ister mi?
        cari_sil = False
        if b.get('odeme_tipi') == 'smmm' and float(b.get('tutar') or 0) > 0:
            fisno = f"BEYAN-{b['tur'][:3]}-{b['yil']}-{b['donem']}"
            reply = QMessageBox.question(
                self, "Cari Kaydı",
                f"Bu ödeme SMMM tarafından yapılmıştı.\n\n"
                f"Mükellef carisindeki ilgili borç kaydı ({float(b.get('tutar',0)):,.2f} ₺) "
                f"da silinsin mi?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                cari_sil = True
                db.delete_cari_by_fisno(b['mukellef_id'], fisno)

        db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
            **b,
            'odendi': 0,
            'odeme_tarihi': None,
            'odeme_tipi': None,
            'tutar': 0.0,
        })

        mesaj = "✅ Ödeme iptal edildi."
        if cari_sil:
            mesaj += "\n📃 Cari borç kaydı da silindi."
        QMessageBox.information(self, "İptal Edildi", mesaj)
        self._load()

    def _hizli_atla(self):
        b = self._get_selected_beyanname()
        if not b:
            QMessageBox.information(self, "Bilgi", "Lütfen bir beyanname satırı seçin.")
            return
        # Zaten atlandıysa geri al
        if b.get('atlandi'):
            db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
                **b, 'atlandi': 0
            })
        else:
            db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
                **b,
                'atlandi': 1,
                'verildi': 0,
                'verilme_tarihi': None,
                'odendi': 0,
                'odeme_tarihi': None,
                'odeme_tipi': None,
                'tutar': 0.0,
            })
        self._load()

    def _hizli_tumu_verildi(self):
        fid = self.cmb_filter.currentData()
        if fid is None:
            filtered = self._data
        else:
            filtered = [b for b in self._data if b['mukellef_id'] == fid]
        bekleyenler = [b for b in filtered if not b['verildi']]
        if not bekleyenler:
            QMessageBox.information(self, "Bilgi", "Bekleyen beyanname yok.")
            return
        reply = QMessageBox.question(
            self, "Onay",
            f"{len(bekleyenler)} adet beyanname verildi olarak işaretlenecek.\n"
            "Emin misiniz?",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        today = date.today().isoformat()
        for b in bekleyenler:
            db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], {
                **b,
                'verildi': 1,
                'verilme_tarihi': today,
                'son_gun': b.get('son_gun') or today,
            })
        self._load()

    # ── Detay düzenleme (çift tıklama) ──

    def _edit(self):
        row = self.tbl.currentRow()
        if row < 0:
            return
        item = self.tbl.item(row, 0)
        if item is None:
            return
        b = item.data(Qt.UserRole)
        if b is None:
            return

        dlg = BeyannameDialog(beyanname=b, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            rd = dlg.result_data
            cari_borc = rd.pop('_cari_borc_ekle', False)
            db.upsert_beyanname(b['mukellef_id'], b['tur'], b['yil'], b['donem'], rd)
            # SMMM ödediyse cari borç kaydı
            if cari_borc:
                aciklama = (
                    f"SMMM tarafından ödenen vergi — "
                    f"{b['tur']} / {donem_label(b['tur'], b['yil'], b['donem'])}"
                )
                db.add_cari(
                    mukellef_id=b['mukellef_id'],
                    tarih=rd.get('odeme_tarihi') or date.today().isoformat(),
                    aciklama=aciklama,
                    borc=rd.get('tutar', 0),
                    alacak=0.0,
                    fisno=f"BEYAN-{b['tur'][:3]}-{b['yil']}-{b['donem']}"
                )
                QMessageBox.information(
                    self, "Kaydedildi",
                    f"✅ Beyanname güncellendi.\n"
                    f"📃 {b['unvan']} carisine {rd.get('tutar', 0):,.2f} ₺ borç eklendi."
                )
            self._load()
