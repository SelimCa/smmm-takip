from datetime import date as _today_date, datetime as _datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox, QComboBox,
    QGroupBox, QCheckBox, QMessageBox, QAbstractItemView,
    QFrame, QSizePolicy, QSpacerItem, QDoubleSpinBox, QScrollArea,
    QDateEdit, QSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont

from db import db, AYLAR
from pdf_utils import pdf_mukellefler


# ──────────────────────────────────────────────
#  Mükellef Ekleme / Düzenleme Diyaloğu
# ──────────────────────────────────────────────
class MukellefDialog(QDialog):
    def __init__(self, mukellef=None, parent=None):
        super().__init__(parent)
        self.mukellef = mukellef
        self.setWindowTitle("Mükellef Ekle" if mukellef is None else "Mükellef Düzenle")
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)
        self.resize(660, 680)
        self.setSizeGripEnabled(True)
        self.setModal(True)
        self._build()
        if mukellef:
            self._fill(mukellef)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 8)
        outer.setSpacing(0)

        # İçeriği scroll edilebilir yap
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner_w = QWidget()
        lay = QVBoxLayout(inner_w)
        lay.setContentsMargins(16, 16, 16, 8)
        lay.setSpacing(12)
        scroll.setWidget(inner_w)
        outer.addWidget(scroll, 1)

        # ── Temel bilgiler ──
        grp_temel = QGroupBox("Temel Bilgiler")
        form = QFormLayout(grp_temel)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        self.edt_vergino = QLineEdit()
        self.edt_vergino.setPlaceholderText("10 veya 11 haneli")
        self.edt_vergino.setMaxLength(11)

        self.edt_unvan = QLineEdit()
        self.edt_unvan.setPlaceholderText("Ad Soyad veya Şirket Ünvanı")

        self.cmb_tip = QComboBox()
        self.cmb_tip.addItem("Gerçek Kişi", "gercek")
        self.cmb_tip.addItem("Tüzel Kişi (Şirket)", "tuzel")

        self.edt_tel   = QLineEdit(); self.edt_tel.setPlaceholderText("0xxx xxx xx xx")
        self.edt_email = QLineEdit(); self.edt_email.setPlaceholderText("ornek@mail.com")
        self.edt_adres = QLineEdit()
        self.edt_sehir = QLineEdit()
        self.edt_vergi_dairesi = QLineEdit()

        form.addRow("Vergi / TC No *", self.edt_vergino)
        form.addRow("Ünvan / Ad Soyad *", self.edt_unvan)
        form.addRow("Mükellef Tipi", self.cmb_tip)
        form.addRow("Telefon", self.edt_tel)
        form.addRow("E-Posta", self.edt_email)
        form.addRow("Adres", self.edt_adres)
        form.addRow("Şehir", self.edt_sehir)
        form.addRow("Vergi Dairesi", self.edt_vergi_dairesi)

        # Kayıt tarihi
        self.dte_kayit = QDateEdit()
        self.dte_kayit.setDisplayFormat("dd.MM.yyyy")
        self.dte_kayit.setCalendarPopup(True)
        self.dte_kayit.setDate(QDate.currentDate())
        self.dte_kayit.setToolTip("Muhasebecilik hizmetinin başladığı tarih — muhasebe bedeli bu tarihten itibaren oluşturulur")
        form.addRow("Kayıt / Başlangıç Tarihi", self.dte_kayit)

        lay.addWidget(grp_temel)

        # ── Ek Firma Bilgileri ──
        grp_ek = QGroupBox("Ek Firma Bilgileri")
        fek = QFormLayout(grp_ek)
        fek.setLabelAlignment(Qt.AlignRight)
        fek.setSpacing(8)

        self.edt_yetkili    = QLineEdit()
        self.edt_yetkili_tc = QLineEdit(); self.edt_yetkili_tc.setPlaceholderText("11 haneli TC")
        self.edt_mersis     = QLineEdit()
        self.edt_ssk_sicil  = QLineEdit()
        self.edt_faal_kod   = QLineEdit(); self.edt_faal_kod.setPlaceholderText("Örn: 681201")

        fek.addRow("Yetkili Kişi", self.edt_yetkili)
        fek.addRow("Yetkili TC No", self.edt_yetkili_tc)
        fek.addRow("Mersis No", self.edt_mersis)
        fek.addRow("SSK Sicil No", self.edt_ssk_sicil)
        fek.addRow("Faaliyet Kodu", self.edt_faal_kod)

        lay.addWidget(grp_ek)

        # ── Beyanname türleri ──
        grp_beyan = QGroupBox("Verilecek Beyannameler")
        blay = QVBoxLayout(grp_beyan)
        blay.setSpacing(6)

        # Satır 1: Aylık
        row1 = QHBoxLayout()
        lbl1 = QLabel("Aylık:")
        lbl1.setStyleSheet("font-weight:bold; color:#3B82F6; min-width:70px;")
        self.chk_kdv1   = QCheckBox("KDV-1")
        self.chk_kdv2   = QCheckBox("KDV-2 (Sorumlu Sıfatıyla)")
        self.chk_muhsgk = QCheckBox("Muhtasar & SGK")
        self.chk_damga  = QCheckBox("Damga Vergisi")
        self.chk_gvk67  = QCheckBox("GVK Geçici 67")
        row1.addWidget(lbl1)
        for c in (self.chk_kdv1, self.chk_kdv2, self.chk_muhsgk, self.chk_damga, self.chk_gvk67):
            row1.addWidget(c)
        row1.addStretch()
        blay.addLayout(row1)

        # Satır 2: 3 Aylık / 4 Aylık
        row2 = QHBoxLayout()
        lbl2 = QLabel("Dönemlik:")
        lbl2.setStyleSheet("font-weight:bold; color:#3B82F6; min-width:70px;")
        self.chk_gecici     = QCheckBox("Geçici Vergi (4 Dönem)")
        self.chk_muhtasar3  = QCheckBox("Muhtasar 3 Aylık")
        row2.addWidget(lbl2)
        row2.addWidget(self.chk_gecici)
        row2.addWidget(self.chk_muhtasar3)
        row2.addStretch()
        blay.addLayout(row2)

        # Satır 3: Yıllık
        row3 = QHBoxLayout()
        lbl3 = QLabel("Yıllık:")
        lbl3.setStyleSheet("font-weight:bold; color:#3B82F6; min-width:70px;")
        self.chk_kurumlar = QCheckBox("Kurumlar Vergisi")
        self.chk_gelir    = QCheckBox("Gelir Vergisi")
        row3.addWidget(lbl3)
        row3.addWidget(self.chk_kurumlar)
        row3.addWidget(self.chk_gelir)
        row3.addStretch()
        blay.addLayout(row3)

        # ── Özel Beyanname Türleri (dinamik) ──
        self._ozel_checkboxlar = {}
        ozel_turler = db.get_ozel_turler()
        if ozel_turler:
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("color:#E2E8F0;")
            blay.addWidget(sep)
            row_ozel = QHBoxLayout()
            lbl_ozel = QLabel("Özel:")
            lbl_ozel.setStyleSheet("font-weight:bold; color:#7C3AED; min-width:70px;")
            row_ozel.addWidget(lbl_ozel)
            periyot_etiket = {'aylik': 'Aylık', '3aylik': '3 Aylık', 'yillik': 'Yıllık'}
            for ot in ozel_turler:
                ad = ot['ad']
                chk = QCheckBox(f"{ad} ({periyot_etiket.get(ot['periyot'], ot['periyot'])})")
                self._ozel_checkboxlar[ad] = chk
                row_ozel.addWidget(chk)
            row_ozel.addStretch()
            blay.addLayout(row_ozel)

        lay.addWidget(grp_beyan)

        # ── Muhasebe Bedeli ──
        grp_ucret = QGroupBox("Muhasebe Bedeli")
        ucret_lay = QHBoxLayout(grp_ucret)
        ucret_lay.setSpacing(16)

        lbl_aylik = QLabel("Ücreti (Ücret Türü):")
        self.cmb_ucret_tip = QComboBox()
        self.cmb_ucret_tip.addItem("Aylık", "aylik")
        self.cmb_ucret_tip.addItem("Yıllık", "yillik")

        lbl_tutar = QLabel("Tutar:")
        self.spn_aylik_ucret = QDoubleSpinBox()
        self.spn_aylik_ucret.setMaximum(9_999_999)
        self.spn_aylik_ucret.setDecimals(2)
        self.spn_aylik_ucret.setSuffix(" ₺")
        self.spn_aylik_ucret.setGroupSeparatorShown(True)
        self.spn_aylik_ucret.setMinimumWidth(130)

        lbl_yillik = QLabel("Yıllık Toplam:")
        self.spn_yillik_ucret = QDoubleSpinBox()
        self.spn_yillik_ucret.setMaximum(99_999_999)
        self.spn_yillik_ucret.setDecimals(2)
        self.spn_yillik_ucret.setSuffix(" ₺")
        self.spn_yillik_ucret.setGroupSeparatorShown(True)
        self.spn_yillik_ucret.setMinimumWidth(150)

        ucret_lay.addWidget(lbl_aylik)
        ucret_lay.addWidget(self.cmb_ucret_tip)
        ucret_lay.addWidget(lbl_tutar)
        ucret_lay.addWidget(self.spn_aylik_ucret)
        ucret_lay.addWidget(lbl_yillik)
        ucret_lay.addWidget(self.spn_yillik_ucret)
        ucret_lay.addStretch()
        lay.addWidget(grp_ucret)

        # Otomatik hesaplama — döngüden kaçınmak için bayrak
        self._ucret_guncelleniyor = False
        self.spn_aylik_ucret.valueChanged.connect(self._aylik_degisti)
        self.spn_yillik_ucret.valueChanged.connect(self._yillik_degisti)

        # ── Butonlar ──
        btn_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Save).setText("💾  Kaydet")
        btn_box.button(QDialogButtonBox.Save).setObjectName("btn_primary")
        btn_box.button(QDialogButtonBox.Cancel).setText("İptal")
        btn_box.accepted.connect(self._save)
        btn_box.rejected.connect(self.reject)

        # "Cariye Aktar" sadece düzenleme modunda (mukellef dolu) görünür
        if self.mukellef:
            self.btn_cari_aktar = QPushButton("📅  Muhasebe Bedelini Cariye Aktar")
            self.btn_cari_aktar.setObjectName("btn_success")
            self.btn_cari_aktar.clicked.connect(self._cariye_aktar_dialog)
            btn_box.addButton(self.btn_cari_aktar, QDialogButtonBox.ActionRole)

        # btn_box scroll dışında, altında sabit görünsün
        lay.addWidget(btn_box)
        outer.addWidget(btn_box)

    def _aylik_degisti(self, deger):
        if self._ucret_guncelleniyor:
            return
        self._ucret_guncelleniyor = True
        self.spn_yillik_ucret.setValue(round(deger * 12, 2))
        self._ucret_guncelleniyor = False

    def _yillik_degisti(self, deger):
        if self._ucret_guncelleniyor:
            return
        self._ucret_guncelleniyor = True
        self.spn_aylik_ucret.setValue(round(deger / 12, 2))
        self._ucret_guncelleniyor = False

    def _cariye_aktar_dialog(self):
        """Dialog içinden doğrudan muhasebe bedelini cariye aktar."""
        if not self.mukellef:
            return
        # Güncel ücret değerlerini mukellef dict'ine yansıt
        m = dict(self.mukellef)
        m['aylik_ucret'] = self.spn_aylik_ucret.value()
        m['yillik_ucret'] = self.spn_yillik_ucret.value()
        dlg = MuhasebeCariDialog(mukellef=m, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            yil, bas_ay = dlg.get_params()
            eklenen, atlanan = db.muhasebe_cariye_aktar(m['id'], yil, bas_ay)
            if eklenen == 0:
                QMessageBox.warning(
                    self, "Zaten Aktarılmış",
                    f"⚠️  {yil} yılı muhasebe fişlerinin tamamı ({atlanan} adet) "
                    f"daha önce cariye aktarılmıştı.\nYeni fiş eklenmedi."
                )
            else:
                QMessageBox.information(
                    self, "Tamamlandı",
                    f"✅ {eklenen} yeni fiş cariye eklendi.\n"
                    f"⏭  {atlanan} fiş zaten mevcuttu, atlandı."
                )

    def _fill(self, m):
        self.edt_vergino.setText(m.get('vergi_no', ''))
        self.edt_unvan.setText(m.get('unvan', ''))
        self.edt_tel.setText(m.get('telefon', ''))
        self.edt_email.setText(m.get('email', ''))
        self.edt_adres.setText(m.get('adres', ''))
        self.edt_sehir.setText(m.get('sehir', ''))
        self.edt_vergi_dairesi.setText(m.get('vergi_dairesi', ''))
        self.edt_yetkili.setText(m.get('yetkili', ''))
        self.edt_yetkili_tc.setText(m.get('yetkili_tc', ''))
        self.edt_mersis.setText(m.get('mersis_no', ''))
        self.edt_ssk_sicil.setText(m.get('ssk_sicil', ''))
        self.edt_faal_kod.setText(m.get('faaliyet_kodu', ''))

        idx = self.cmb_tip.findData(m.get('tip', 'gercek'))
        if idx >= 0:
            self.cmb_tip.setCurrentIndex(idx)

        self.chk_kdv1.setChecked(bool(m.get('kdv1', 0)))
        self.chk_kdv2.setChecked(bool(m.get('kdv2', 0)))
        self.chk_muhsgk.setChecked(bool(m.get('muhsgk', 0)))
        self.chk_gecici.setChecked(bool(m.get('gecici_vergi', 0)))
        self.chk_kurumlar.setChecked(bool(m.get('kurumlar_vergisi', 0)))
        self.chk_gelir.setChecked(bool(m.get('gelir_vergisi', 0)))
        self.chk_muhtasar3.setChecked(bool(m.get('muhtasar_3aylik', 0)))
        self.chk_damga.setChecked(bool(m.get('damga_vergisi', 0)))
        self.chk_gvk67.setChecked(bool(m.get('gvk_67', 0)))

        # Özel beyannameler
        if self._ozel_checkboxlar and m.get('id'):
            atanmis = {r['tur_ad'] for r in db.get_mukellef_ozel_beyanlar(m['id'])}
            for ad, chk in self._ozel_checkboxlar.items():
                chk.setChecked(ad in atanmis)

        aylik = float(m.get('aylik_ucret') or 0)
        yillik = float(m.get('yillik_ucret') or 0)
        self.spn_aylik_ucret.setValue(aylik)
        self.spn_yillik_ucret.setValue(yillik)

    def _save(self):
        vergi_no = self.edt_vergino.text().strip()
        unvan    = self.edt_unvan.text().strip()

        if not vergi_no:
            QMessageBox.warning(self, "Hata", "Vergi / TC numarası boş olamaz.")
            return
        if not unvan:
            QMessageBox.warning(self, "Hata", "Ünvan / Ad Soyad boş olamaz.")
            return
        if not vergi_no.isdigit() or len(vergi_no) not in (10, 11):
            QMessageBox.warning(self, "Hata", "Vergi/TC numarası 10 veya 11 rakam olmalıdır.")
            return

        self.data = {
            'vergi_no':          vergi_no,
            'unvan':             unvan,
            'tip':               self.cmb_tip.currentData(),
            'telefon':           self.edt_tel.text().strip(),
            'email':             self.edt_email.text().strip(),
            'adres':             self.edt_adres.text().strip(),
            'sehir':             self.edt_sehir.text().strip(),
            'vergi_dairesi':     self.edt_vergi_dairesi.text().strip(),
            'yetkili':           self.edt_yetkili.text().strip(),
            'yetkili_tc':        self.edt_yetkili_tc.text().strip(),
            'mersis_no':         self.edt_mersis.text().strip(),
            'ssk_sicil':         self.edt_ssk_sicil.text().strip(),
            'faaliyet_kodu':     self.edt_faal_kod.text().strip(),
            'kayit_tarihi':      self.dte_kayit.date().toString('yyyy-MM-dd'),
            'kdv1':              int(self.chk_kdv1.isChecked()),
            'kdv2':              int(self.chk_kdv2.isChecked()),
            'muhsgk':            int(self.chk_muhsgk.isChecked()),
            'gecici_vergi':      int(self.chk_gecici.isChecked()),
            'kurumlar_vergisi':  int(self.chk_kurumlar.isChecked()),
            'gelir_vergisi':     int(self.chk_gelir.isChecked()),
            'muhtasar_3aylik':   int(self.chk_muhtasar3.isChecked()),
            'damga_vergisi':     int(self.chk_damga.isChecked()),
            'gvk_67':            int(self.chk_gvk67.isChecked()),
            'aylik_ucret':       self.spn_aylik_ucret.value(),
            'yillik_ucret':      self.spn_yillik_ucret.value(),
            'ozel_beyanlar':     [ad for ad, chk in self._ozel_checkboxlar.items() if chk.isChecked()],
        }
        self.accept()


# ──────────────────────────────────────────────
#  Muhasebe Bedeli Cariye Aktarım Diyaloğu
# ──────────────────────────────────────────────
class MuhasebeCariDialog(QDialog):
    def __init__(self, mukellef: dict, parent=None):
        super().__init__(parent)
        self.mukellef = mukellef
        self.setWindowTitle("Muhasebe Bedeli — Cariye Aktar")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build()
        self._preview_guncelle()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        aylik  = float(self.mukellef.get('aylik_ucret') or 0)
        yillik = float(self.mukellef.get('yillik_ucret') or 0)

        info = QLabel(
            f"<b>{self.mukellef['unvan']}</b><br>"
            f"Aylık Muhasebe Bedeli: <b>{aylik:,.2f} ₺</b>  "
            f"| Yıllık: <b>{yillik:,.2f} ₺</b>")
        info.setStyleSheet(
            "background:#EEF6FF; border:1px solid #BDD5EE; "
            "border-radius:4px; padding:10px;")
        info.setWordWrap(True)
        lay.addWidget(info)

        if aylik <= 0:
            uyari = QLabel("⚠️  Bu mükellef için aylık muhasebe bedeli tanımlanmamış.\n"
                           "Önce mükellef düzenleme ekranından ücret girin.")
            uyari.setStyleSheet("color:#B45309; background:#FFFBEB; padding:8px; border-radius:4px;")
            uyari.setWordWrap(True)
            lay.addWidget(uyari)

        grp = QGroupBox("Aktarım Ayarları")
        form = QFormLayout(grp)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.spn_yil = QSpinBox()
        self.spn_yil.setRange(2000, 2099)
        self.spn_yil.setValue(_today_date.today().year)
        self.spn_yil.valueChanged.connect(self._preview_guncelle)
        form.addRow("Aktarım Yılı:", self.spn_yil)

        self.lbl_preview = QLabel("…")
        self.lbl_preview.setWordWrap(True)
        form.addRow("Durum:", self.lbl_preview)

        lay.addWidget(grp)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btn_aktar = btn_box.button(QDialogButtonBox.Ok)
        self.btn_aktar.setText("📅  Cariye Aktar")
        self.btn_aktar.setObjectName("btn_primary")
        self.btn_aktar.setEnabled(aylik > 0)
        btn_box.button(QDialogButtonBox.Cancel).setText("İptal")
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)

    def _preview_guncelle(self):
        yil = self.spn_yil.value()
        mid = self.mukellef['id']
        aylik = float(self.mukellef.get('aylik_ucret') or 0)
        if aylik <= 0:
            self.lbl_preview.setText("—")
            return

        # Kayıt tarihinden başlangıç ayını bul
        kayit = self.mukellef.get('kayit_tarihi') or ''
        bas_ay = 1
        if kayit:
            try:
                dt = _datetime.strptime(str(kayit)[:10], '%Y-%m-%d')
                if dt.year > yil:
                    self.lbl_preview.setStyleSheet("color:#DC2626; font-weight:bold;")
                    self.lbl_preview.setText("❌ Kayıt tarihi bu yıldan sonra!")
                    self.btn_aktar.setEnabled(False)
                    return
                elif dt.year == yil:
                    bas_ay = dt.month
            except Exception:
                pass

        self._bas_ay = bas_ay
        ay_sayisi = 13 - bas_ay
        mevcut_say = db.count_muhasebe_fisler(mid, yil)
        yeni_say = max(0, ay_sayisi - mevcut_say)
        toplam = aylik * ay_sayisi
        yeni_toplam = aylik * yeni_say

        if mevcut_say >= ay_sayisi:
            # Tüm aylar zaten aktarılmış — uyar ve kilitle
            self.btn_aktar.setEnabled(False)
            self.lbl_preview.setStyleSheet(
                "color:#B45309; background:#FFFBEB; "
                "border:1px solid #FCD34D; border-radius:4px; "
                "padding:6px; font-weight:bold;")
            self.lbl_preview.setText(
                f"⚠️  {yil} yılı için tüm muhasebe fişleri ({mevcut_say} adet) "
                f"zaten cariye aktarılmış!\n"
                f"Tekrar aktarıma gerek yoktur."
            )
            return

        self.btn_aktar.setEnabled(True)
        self.lbl_preview.setStyleSheet("color:#059669; font-weight:bold;")
        self.lbl_preview.setText(
            f"{AYLAR[bas_ay]}'dan itibaren {ay_sayisi} ay\n"
            f"✅ Zaten mevcut: {mevcut_say} fiş  |  "
            f"➕ Eklenecek: {yeni_say} fiş\n"
            f"Toplam tutar: {toplam:,.2f} ₺  |  Yeni: {yeni_toplam:,.2f} ₺"
        )

    def get_params(self):
        return self.spn_yil.value(), getattr(self, '_bas_ay', 1)


# ──────────────────────────────────────────────
#  Mükellefler Paneli
# ──────────────────────────────────────────────
COLS = ["#", "Vergi / TC No", "Ünvan / Ad Soyad", "Tip", "Telefon",
        "Beyanname Türleri", "Aylık Ücret", "Durum"]


class MukellefPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._show_passive = False
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(12)

        # ── Başlık satırı ──
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("👥  Mükellef Yönetimi")
        title.setObjectName("page_title")
        sub = QLabel("Mükellef ekleyin, düzenleyin ve beyanname türlerini belirleyin")
        sub.setObjectName("page_subtitle")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        btn_new = QPushButton("➕  Yeni Mükellef")
        btn_new.setObjectName("btn_primary")
        btn_new.setFixedHeight(38)
        btn_new.setMinimumWidth(155)
        btn_new.clicked.connect(self._new)
        header_row.addLayout(title_col, 1)
        header_row.addWidget(btn_new)
        outer.addLayout(header_row)

        # ── Toolbar şeridi ──
        toolbar = QWidget()
        toolbar.setObjectName("toolbar_strip")
        tlay = QHBoxLayout(toolbar)
        tlay.setContentsMargins(8, 6, 8, 6)
        tlay.setSpacing(8)

        self.search_edt = QLineEdit()
        self.search_edt.setObjectName("search_box")
        self.search_edt.setPlaceholderText("  🔍  Mükellef ara (isim veya vergi no)…")
        self.search_edt.setFixedHeight(34)
        self.search_edt.textChanged.connect(self._filter)

        btn_edit = QPushButton("✏️  Düzenle")
        btn_edit.setObjectName("btn_icon")
        btn_edit.setFixedHeight(34)
        btn_edit.clicked.connect(self._edit)

        btn_cariye_aktar = QPushButton("📅  Cariye Aktar")
        btn_cariye_aktar.setObjectName("btn_success")
        btn_cariye_aktar.setFixedHeight(34)
        btn_cariye_aktar.setToolTip("Seçili mükellefin muhasebe bedelini cariye aylık fiş olarak aktar")
        btn_cariye_aktar.clicked.connect(self._cariye_aktar)

        self.btn_toggle_pasif = QPushButton("👁  Pasif Göster")
        self.btn_toggle_pasif.setObjectName("btn_icon")
        self.btn_toggle_pasif.setFixedHeight(34)
        self.btn_toggle_pasif.setCheckable(True)
        self.btn_toggle_pasif.clicked.connect(self._toggle_passive)

        btn_del = QPushButton("🗑  Pasife Al")
        btn_del.setObjectName("btn_danger")
        btn_del.setFixedHeight(34)
        btn_del.clicked.connect(self._delete)

        tlay.addWidget(self.search_edt, 1)
        tlay.addWidget(btn_edit)
        tlay.addWidget(btn_cariye_aktar)
        tlay.addWidget(self.btn_toggle_pasif)
        tlay.addWidget(btn_del)

        btn_pdf = QPushButton("📄  PDF Rapor")
        btn_pdf.setObjectName("btn_secondary")
        btn_pdf.setFixedHeight(34)
        btn_pdf.setToolTip("Mükellefleri PDF olarak kaydet")
        btn_pdf.clicked.connect(self._pdf_rapor)
        tlay.addWidget(btn_pdf)

        outer.addWidget(toolbar)

        # ── Tablo ──
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(len(COLS))
        self.tbl.setHorizontalHeaderLabels(COLS)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.SingleSelection)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setShowGrid(False)
        self.tbl.doubleClicked.connect(self._edit)

        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        outer.addWidget(self.tbl, 1)

        # ── Alt çubuk ──
        bottom = QHBoxLayout()
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        hint = QLabel("💡  Çift tıklayarak düzenleyebilirsiniz")
        hint.setStyleSheet("color: #CBD5E1; font-size: 11px;")
        bottom.addWidget(self.status_lbl)
        bottom.addStretch()
        bottom.addWidget(hint)
        outer.addLayout(bottom)

        self._all_data = []

    # ── veri ──

    def refresh(self):
        self._all_data = db.get_mukellefler(sadece_aktif=not self._show_passive)
        self._render(self._all_data)

    def _pdf_rapor(self):
        data = [r for r in self._all_data]  # görünen veri
        if not data:
            QMessageBox.information(self, "Bilgi", "Gösterilecek mükellefleri olmayan bir liste var.")
            return
        pdf_mukellefler(data, parent=self)

    def _render(self, mukellefler):
        self.tbl.setRowCount(len(mukellefler))
        for row, m in enumerate(mukellefler):
            # Beyanname türleri özeti
            turleri = []
            if m.get('kdv1'):             turleri.append("KDV1")
            if m.get('kdv2'):             turleri.append("KDV2")
            if m.get('muhsgk'):           turleri.append("MUHSGK")
            if m.get('damga_vergisi'):    turleri.append("DAMGA")
            if m.get('gvk_67'):           turleri.append("GVK67")
            if m.get('gecici_vergi'):     turleri.append("GEC.VRG")
            if m.get('muhtasar_3aylik'):  turleri.append("MUH3AY")
            if m.get('kurumlar_vergisi'): turleri.append("KURUMLAR")
            if m.get('gelir_vergisi'):    turleri.append("GELİR")

            tip_text = "Gerçek Kişi" if m['tip'] == 'gercek' else "Tüzel Kişi"
            aktif    = bool(m['aktif'])

            aylik = float(m.get('aylik_ucret') or 0)
            ucret_str = f"{aylik:,.0f} ₺" if aylik > 0 else "—"

            items = [
                QTableWidgetItem(str(row + 1)),
                QTableWidgetItem(m['vergi_no']),
                QTableWidgetItem(m['unvan']),
                QTableWidgetItem(tip_text),
                QTableWidgetItem(m.get('telefon', '')),
                QTableWidgetItem("  ".join(turleri) if turleri else "—"),
                QTableWidgetItem(ucret_str),
                QTableWidgetItem("✅ Aktif" if aktif else "🔴 Pasif"),
            ]

            items[0].setData(Qt.UserRole, m['id'])

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if not aktif:
                    item.setForeground(QColor("#CBD5E1"))
                self.tbl.setItem(row, col, item)
            self.tbl.setRowHeight(row, 36)

        self.status_lbl.setText(
            f"Toplam {len(mukellefler)} mükellef gösteriliyor"
            + ("  (pasifler dahil)" if self._show_passive else ""))

    def _filter(self, text):
        text = text.lower().strip()
        if not text:
            self._render(self._all_data)
            return
        filtered = [
            m for m in self._all_data
            if text in m['unvan'].lower() or text in m['vergi_no']
        ]
        self._render(filtered)

    def _selected_id(self):
        rows = self.tbl.selectedItems()
        if not rows:
            return None
        return self.tbl.item(self.tbl.currentRow(), 0).data(Qt.UserRole)

    # ── eylemler ──

    def _new(self):
        dlg = MukellefDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                new_id = db.add_mukellef(dlg.data)
                if new_id:
                    db.set_mukellef_ozel_beyanlar(new_id, dlg.data.get('ozel_beyanlar', []))
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kayıt eklenemedi:\n{e}")

    def _cariye_aktar(self):
        mid = self._selected_id()
        if mid is None:
            QMessageBox.information(self, "Bilgi", "Lütfen bir mükellef seçin.")
            return
        m = db.get_mukellef(mid)
        if not m:
            return
        dlg = MuhasebeCariDialog(mukellef=m, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            yil, bas_ay = dlg.get_params()
            eklenen, atlanan = db.muhasebe_cariye_aktar(mid, yil, bas_ay)
            if eklenen == 0:
                QMessageBox.warning(
                    self, "Zaten Aktarılmış",
                    f"⚠️  {yil} yılı muhasebe fişlerinin tamamı ({atlanan} adet) "
                    f"daha önce cariye aktarılmıştı.\nYeni fiş eklenmedi."
                )
            else:
                QMessageBox.information(
                    self, "Tamamlandı",
                    f"✅ {eklenen} yeni fiş cariye eklendi.\n"
                    f"⏭  {atlanan} fiş zaten mevcuttu, atlandı."
                )

    def _edit(self):
        mid = self._selected_id()
        if mid is None:
            QMessageBox.information(self, "Bilgi", "Lütfen bir mükellef seçin.")
            return
        m = db.get_mukellef(mid)
        dlg = MukellefDialog(mukellef=m, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                db.update_mukellef(mid, dlg.data)
                db.set_mukellef_ozel_beyanlar(mid, dlg.data.get('ozel_beyanlar', []))
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Güncelleme hatası:\n{e}")

    def _delete(self):
        mid = self._selected_id()
        if mid is None:
            QMessageBox.information(self, "Bilgi", "Lütfen bir mükellef seçin.")
            return
        m = db.get_mukellef(mid)
        reply = QMessageBox.question(
            self, "Onay",
            f"'{m['unvan']}' mükellefini pasife almak istediğinize emin misiniz?\n"
            "Cari kayıtları ve beyannameleri korunacaktır.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.set_mukellef_aktif(mid, False)
            self.refresh()

    def _toggle_passive(self, checked):
        self._show_passive = checked
        self.btn_toggle_pasif.setText("👁  Pasif Gizle" if checked else "👁  Pasif Göster")
        self.btn_toggle_pasif.setStyleSheet(
            "background-color:#FEF3C7;color:#92400E;border:1px solid #FCD34D;" if checked else "")
        self.refresh()
