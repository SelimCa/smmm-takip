import os
from datetime import date as _today_date

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QFrame, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QSpinBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from db import db
from zirve_import import zirve_mukellef_listesi, zirve_iceri_aktar



class AyarlarPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        # Başlık
        title = QLabel("⚙️  Ayarlar")
        title.setObjectName("page_title")
        outer.addWidget(title)

        sub = QLabel("Zirve Net entegrasyonu ve uygulama ayarları")
        sub.setObjectName("page_subtitle")
        outer.addWidget(sub)

        # ── Zirve Veri Yolu Kartı ──
        zirve_card = QFrame()
        zirve_card.setObjectName("settings_card")
        zirve_lay = QVBoxLayout(zirve_card)
        zirve_lay.setSpacing(12)

        card_title = QLabel("📁  Zirve Net Veri Klasörü")
        card_title.setObjectName("settings_card_title")
        card_desc = QLabel(
            "Zirve Net programının mükellef verilerinin bulunduğu ana klasörü belirtin.\n"
            "Her mükellef bu klasör altında ayrı bir alt klasör olmalıdır.")
        card_desc.setObjectName("settings_card_desc")
        card_desc.setWordWrap(True)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)

        self.edt_yol = QLineEdit()
        self.edt_yol.setPlaceholderText(r"Örnek: C:\zirvenetfinansman\zirvedata")
        self.edt_yol.setMinimumHeight(36)

        btn_gozat = QPushButton("📂  Gözat")
        btn_gozat.setObjectName("btn_outline")
        btn_gozat.setFixedHeight(36)
        btn_gozat.setMinimumWidth(100)
        btn_gozat.clicked.connect(self._gozat)

        btn_kaydet_yol = QPushButton("💾  Kaydet")
        btn_kaydet_yol.setObjectName("btn_primary")
        btn_kaydet_yol.setFixedHeight(36)
        btn_kaydet_yol.setMinimumWidth(90)
        btn_kaydet_yol.clicked.connect(self._kaydet_yol)

        path_row.addWidget(self.edt_yol, 1)
        path_row.addWidget(btn_gozat)
        path_row.addWidget(btn_kaydet_yol)

        # Klasör durumu
        self.yol_status = QLabel("")
        self.yol_status.setStyleSheet("font-size: 12px;")

        zirve_lay.addWidget(card_title)
        zirve_lay.addWidget(card_desc)
        zirve_lay.addLayout(path_row)
        zirve_lay.addWidget(self.yol_status)
        outer.addWidget(zirve_card)

        # ── Mükellef İçe Aktarma Kartı ──
        import_card = QFrame()
        import_card.setObjectName("settings_card")
        import_lay = QVBoxLayout(import_card)
        import_lay.setSpacing(12)

        import_title = QLabel("👥  Zirve'den Mükellef Aktar")
        import_title.setObjectName("settings_card_title")
        import_desc = QLabel(
            "Zirve klasöründe bulunan mükellefler aşağıda listelenir. "
            "Seçili olanları veya tümünü sisteme aktarabilirsiniz.\n"
            "Zaten kayıtlı olan mükellefler tekrar eklenmez.")
        import_desc.setObjectName("settings_card_desc")
        import_desc.setWordWrap(True)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_tara = QPushButton("🔍  Klasörü Tara")
        btn_tara.setObjectName("btn_outline")
        btn_tara.setFixedHeight(34)
        btn_tara.clicked.connect(self._tara)

        btn_aktar_hepsi = QPushButton("⬇️  Tümünü Aktar")
        btn_aktar_hepsi.setObjectName("btn_success")
        btn_aktar_hepsi.setFixedHeight(34)
        btn_aktar_hepsi.clicked.connect(self._aktar_hepsi)

        self.import_status = QLabel("")
        self.import_status.setStyleSheet("font-size: 12px; font-weight: bold;")

        btn_row.addWidget(btn_tara)
        btn_row.addWidget(btn_aktar_hepsi)
        btn_row.addStretch()
        btn_row.addWidget(self.import_status)

        # Tarama sonuç tablosu
        self.tbl_zirve = QTableWidget()
        self.tbl_zirve.setColumnCount(3)
        self.tbl_zirve.setHorizontalHeaderLabels(["Mükellef Adı", "Klasör Adı", "Durum"])
        self.tbl_zirve.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_zirve.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_zirve.setAlternatingRowColors(True)
        self.tbl_zirve.verticalHeader().setVisible(False)
        self.tbl_zirve.setMaximumHeight(280)

        hdr = self.tbl_zirve.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        import_lay.addWidget(import_title)
        import_lay.addWidget(import_desc)
        import_lay.addLayout(btn_row)
        import_lay.addWidget(self.tbl_zirve)
        outer.addWidget(import_card)

        # ── Yıl Yönetimi Kartı ──
        yil_card = QFrame()
        yil_card.setObjectName("settings_card")
        yil_lay = QVBoxLayout(yil_card)
        yil_lay.setSpacing(12)

        yil_title = QLabel("📅  Yıl Yönetimi")
        yil_title.setObjectName("settings_card_title")
        yil_desc = QLabel(
            "Yeni bir mali yıl açın. Her aktif mükellefi için mevcut yıl sonu bakiyesi "
            "yeni yılın 1 Ocak tarihine '<i>… yılından devir</i>' fişi olarak aktarılır.\n"
            "Zaten devir fişi oluşturulmuş olan mükelleflerin fişi tekrar oluşturulmaz.")
        yil_desc.setObjectName("settings_card_desc")
        yil_desc.setWordWrap(True)

        yil_row = QHBoxLayout()
        yil_row.setSpacing(10)

        lbl_mevcut = QLabel("Mevcut Yıl:")
        lbl_mevcut.setStyleSheet("font-weight:bold;")
        self.spn_mevcut_yil = QSpinBox()
        self.spn_mevcut_yil.setRange(2000, 2099)
        self.spn_mevcut_yil.setValue(_today_date.today().year)
        self.spn_mevcut_yil.setFixedWidth(90)

        lbl_yeni = QLabel("→  Yeni Yıl:")
        lbl_yeni.setStyleSheet("font-weight:bold;")
        self.spn_yeni_yil = QSpinBox()
        self.spn_yeni_yil.setRange(2001, 2100)
        self.spn_yeni_yil.setValue(_today_date.today().year + 1)
        self.spn_yeni_yil.setFixedWidth(90)

        btn_yil_ac = QPushButton("🚀  Yeni Yıl Aç (Bakiyeleri Devret)")
        btn_yil_ac.setObjectName("btn_primary")
        btn_yil_ac.setFixedHeight(36)
        btn_yil_ac.clicked.connect(self._yeni_yil_ac)

        self.yil_status = QLabel("")
        self.yil_status.setStyleSheet("font-size: 12px;")

        yil_row.addWidget(lbl_mevcut)
        yil_row.addWidget(self.spn_mevcut_yil)
        yil_row.addWidget(lbl_yeni)
        yil_row.addWidget(self.spn_yeni_yil)
        yil_row.addSpacing(12)
        yil_row.addWidget(btn_yil_ac)
        yil_row.addStretch()

        yil_lay.addWidget(yil_title)
        yil_lay.addWidget(yil_desc)
        yil_lay.addLayout(yil_row)
        yil_lay.addWidget(self.yil_status)
        outer.addWidget(yil_card)

        # ── Özel Beyanname Türleri Kartı ──
        ozel_card = QFrame()
        ozel_card.setObjectName("settings_card")
        ozel_lay = QVBoxLayout(ozel_card)
        ozel_lay.setSpacing(12)

        ozel_title = QLabel("📋  Özel Beyanname Türleri")
        ozel_title.setObjectName("settings_card_title")
        ozel_desc = QLabel(
            "Listede olmayan özel beyanname türleri tanımlayın. "
            "Tanımlanan türler Mükellef düzenleme ekranında seçilebilir hale gelir.")
        ozel_desc.setObjectName("settings_card_desc")
        ozel_desc.setWordWrap(True)

        # Ekleme formu
        form_row = QHBoxLayout()
        form_row.setSpacing(8)

        lbl_ad = QLabel("Tür Adı:")
        lbl_ad.setStyleSheet("font-weight:bold;")
        self.edt_ozel_ad = QLineEdit()
        self.edt_ozel_ad.setPlaceholderText("Örn: BA/BS, E-Fatura, İstihdam")
        self.edt_ozel_ad.setFixedHeight(34)
        self.edt_ozel_ad.setMinimumWidth(180)

        lbl_per = QLabel("Periyot:")
        lbl_per.setStyleSheet("font-weight:bold;")
        self.cmb_ozel_periyot = QComboBox()
        self.cmb_ozel_periyot.addItem("Aylık", "aylik")
        self.cmb_ozel_periyot.addItem("3 Aylık (Dönemlik)", "3aylik")
        self.cmb_ozel_periyot.addItem("Yıllık", "yillik")
        self.cmb_ozel_periyot.setFixedHeight(34)
        self.cmb_ozel_periyot.currentIndexChanged.connect(self._ozel_periyot_degisti)

        lbl_gun = QLabel("Son Gün:")
        lbl_gun.setStyleSheet("font-weight:bold;")
        self.spn_ozel_gun = QSpinBox()
        self.spn_ozel_gun.setRange(1, 31)
        self.spn_ozel_gun.setValue(26)
        self.spn_ozel_gun.setFixedHeight(34)
        self.spn_ozel_gun.setFixedWidth(70)
        self.lbl_gun_aciklama = QLabel("(izleyen ayın)")
        self.lbl_gun_aciklama.setStyleSheet("color:#64748B; font-size:11px;")

        btn_ozel_ekle = QPushButton("➕  Ekle")
        btn_ozel_ekle.setObjectName("btn_success")
        btn_ozel_ekle.setFixedHeight(34)
        btn_ozel_ekle.clicked.connect(self._ozel_tur_ekle)

        form_row.addWidget(lbl_ad)
        form_row.addWidget(self.edt_ozel_ad, 1)
        form_row.addWidget(lbl_per)
        form_row.addWidget(self.cmb_ozel_periyot)
        form_row.addWidget(lbl_gun)
        form_row.addWidget(self.spn_ozel_gun)
        form_row.addWidget(self.lbl_gun_aciklama)
        form_row.addSpacing(8)
        form_row.addWidget(btn_ozel_ekle)

        # Mevcut türler tablosu
        self.tbl_ozel = QTableWidget()
        self.tbl_ozel.setColumnCount(4)
        self.tbl_ozel.setHorizontalHeaderLabels(["Tür Adı", "Periyot", "Son Gün", ""])
        self.tbl_ozel.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_ozel.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_ozel.verticalHeader().setVisible(False)
        self.tbl_ozel.setMaximumHeight(200)
        hdr_o = self.tbl_ozel.horizontalHeader()
        hdr_o.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr_o.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr_o.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr_o.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        ozel_lay.addWidget(ozel_title)
        ozel_lay.addWidget(ozel_desc)
        ozel_lay.addLayout(form_row)
        ozel_lay.addWidget(self.tbl_ozel)
        outer.addWidget(ozel_card)

        outer.addStretch()

    def refresh(self):
        yol = db.get_zirve_yolu()
        self.edt_yol.setText(yol)
        self._kontrol_yol(yol)
        self._ozel_tablo_yenile()

    def _ozel_periyot_degisti(self):
        periyot = self.cmb_ozel_periyot.currentData()
        if periyot == 'aylik':
            self.lbl_gun_aciklama.setText("(izleyen ayın)")
            self.spn_ozel_gun.setRange(1, 31)
        elif periyot == '3aylik':
            self.lbl_gun_aciklama.setText("(dönem bitimini izleyen ayın)")
            self.spn_ozel_gun.setRange(1, 31)
        elif periyot == 'yillik':
            self.lbl_gun_aciklama.setText("= kaçıncı ay sonu (örn: 4 = Nisan)")
            self.spn_ozel_gun.setRange(1, 12)
            self.spn_ozel_gun.setValue(4)

    def _ozel_tur_ekle(self):
        ad = self.edt_ozel_ad.text().strip().upper()
        if not ad:
            QMessageBox.warning(self, "Hata", "Tür adı boş olamaz.")
            return
        periyot  = self.cmb_ozel_periyot.currentData()
        son_gun  = self.spn_ozel_gun.value()
        db.add_ozel_tur(ad, periyot, son_gun)
        self.edt_ozel_ad.clear()
        self._ozel_tablo_yenile()
        QMessageBox.information(self, "Eklendi", f"'{ad}' türü eklendi.\nMükellef düzenleme ekranında görünecek.")

    def _ozel_tur_sil(self, ad):
        cevap = QMessageBox.question(
            self, "Sil",
            f"'{ad}' türünü silmek istiyor musunuz?\nTüm mükellef atamalarından da kaldırılır.",
            QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            db.delete_ozel_tur(ad)
            self._ozel_tablo_yenile()

    def _ozel_tablo_yenile(self):
        turler = db.get_ozel_turler()
        self.tbl_ozel.setRowCount(len(turler))
        periyot_etiket = {'aylik': 'Aylık', '3aylik': '3 Aylık', 'yillik': 'Yıllık'}
        for i, t in enumerate(turler):
            self.tbl_ozel.setItem(i, 0, QTableWidgetItem(t['ad']))
            self.tbl_ozel.setItem(i, 1, QTableWidgetItem(periyot_etiket.get(t['periyot'], t['periyot'])))
            self.tbl_ozel.setItem(i, 2, QTableWidgetItem(str(t['son_gun_gunu'])))
            btn_sil = QPushButton("🗑 Sil")
            btn_sil.setFixedHeight(26)
            btn_sil.setStyleSheet(
                "QPushButton{background:#EF4444;color:white;border-radius:4px;"
                "font-size:11px;padding:0 8px;}"
                "QPushButton:hover{background:#DC2626;}")
            _ad = t['ad']
            btn_sil.clicked.connect(lambda _, a=_ad: self._ozel_tur_sil(a))
            self.tbl_ozel.setCellWidget(i, 3, btn_sil)

    def _gozat(self):
        mevcut = self.edt_yol.text().strip() or r"C:\\"
        yol = QFileDialog.getExistingDirectory(
            self, "Zirve Veri Klasörünü Seçin", mevcut)
        if yol:
            self.edt_yol.setText(os.path.normpath(yol))
            self._kontrol_yol(yol)

    def _kontrol_yol(self, yol):
        if not yol:
            self.yol_status.setText("")
            return
        if os.path.isdir(yol):
            klasorler = [
                d for d in os.listdir(yol)
                if os.path.isdir(os.path.join(yol, d))
            ]
            self.yol_status.setText(
                f"✅  Klasör bulundu — {len(klasorler)} alt klasör içeriyor")
            self.yol_status.setStyleSheet("font-size: 12px; color: #059669;")
        else:
            self.yol_status.setText("❌  Klasör bulunamadı veya erişilemiyor")
            self.yol_status.setStyleSheet("font-size: 12px; color: #DC2626;")

    def _kaydet_yol(self):
        yol = self.edt_yol.text().strip()
        if not yol:
            QMessageBox.warning(self, "Hata", "Klasör yolu boş olamaz.")
            return
        if not os.path.isdir(yol):
            reply = QMessageBox.question(
                self, "Klasör Bulunamadı",
                "Belirtilen klasör mevcut değil. Yine de kaydetmek istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        db.set_zirve_yolu(yol)
        self._kontrol_yol(yol)
        QMessageBox.information(self, "Kaydedildi", "Zirve klasör yolu kaydedildi.")

    def _tara(self):
        yol = self.edt_yol.text().strip() or db.get_zirve_yolu()
        if not os.path.isdir(yol):
            QMessageBox.warning(self, "Hata",
                "Klasör bulunamadı. Lütfen önce geçerli bir yol girin ve kaydedin.")
            return

        mukellefler = zirve_mukellef_listesi(yol)
        mevcut = {m['unvan'].upper() for m in db.get_mukellefler(sadece_aktif=False)}

        self.tbl_zirve.setRowCount(len(mukellefler))
        for row, m in enumerate(mukellefler):
            kayitli = m['unvan'].upper() in mevcut
            self.tbl_zirve.setItem(row, 0, QTableWidgetItem(m['unvan']))
            self.tbl_zirve.setItem(row, 1, QTableWidgetItem(m['klasor_adi']))

            durum = QTableWidgetItem("✅ Zaten Kayıtlı" if kayitli else "⬇️ Aktarılabilir")
            durum.setForeground(
                QColor("#059669") if kayitli else QColor("#1D4ED8"))
            self.tbl_zirve.setItem(row, 2, durum)

        self.import_status.setText(
            f"{len(mukellefler)} mükellef bulundu  "
            f"({sum(1 for m in mukellefler if m['unvan'].upper() not in mevcut)} yeni)")
        self.import_status.setStyleSheet("font-size: 12px; color: #1D4ED8; font-weight: bold;")

    def _aktar_hepsi(self):
        yol = self.edt_yol.text().strip() or db.get_zirve_yolu()
        if not os.path.isdir(yol):
            QMessageBox.warning(self, "Hata",
                "Klasör bulunamadı. Lütfen önce geçerli bir yol girin.")
            return

        sonuc = zirve_iceri_aktar(yol)
        msg = (
            f"✅  {sonuc['eklenen']} mükellef eklendi\n"
            f"⏭  {sonuc['atlanan']} mükellef zaten kayıtlıydı (atlandı)"
        )
        if sonuc['hatalar']:
            msg += f"\n\n⚠️ Hatalar:\n" + "\n".join(sonuc['hatalar'][:10])

        QMessageBox.information(self, "İçe Aktarma Tamamlandı", msg)
        self._tara()  # listeyi yenile

        if sonuc['eklenen'] > 0:
            self.import_status.setText(
                f"✅  {sonuc['eklenen']} yeni mükellef eklendi!")
            self.import_status.setStyleSheet(
                "font-size: 12px; color: #059669; font-weight: bold;")

    def _yeni_yil_ac(self):
        mevcut = self.spn_mevcut_yil.value()
        yeni   = self.spn_yeni_yil.value()

        if yeni <= mevcut:
            QMessageBox.warning(self, "Hata",
                "Yeni yıl, mevcut yıldan büyük olmalıdır.")
            return

        mukellefler = db.get_mukellefler()
        # Devir fişi oluşturulacak mükellefleri say (bakiyesi sıfır olmayanlar)
        devir_olacak = sum(
            1 for m in mukellefler
            if db.get_bakiye(m['id']) != 0
        )

        reply = QMessageBox.question(
            self, "Yeni Yıl Açılışı",
            f"<b>{yeni} yılı açılacak.</b><br><br>"
            f"• {len(mukellefler)} aktif mükellef kontrol edilecek<br>"
            f"• {devir_olacak} mükellefin {mevcut} yıl sonu bakiyesi "
            f"<b>'{mevcut}'dan devir</b> fişi olarak {yeni} yılına aktarılacak<br>"
            f"• Zaten devir fişi olan mükellefler tekrar işlenmeyecek<br><br>"
            f"Devam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        eklenen = db.yeni_yil_ac(mevcut, yeni)

        mesaj = (
            f"✅ {yeni} yılı başarıyla açıldı!\n\n"
            f"📃 {eklenen} mükellef için devir fişi oluşturuldu.\n"
            f"⏭  {devir_olacak - eklenen} mükellef için fiş zaten mevcuttu veya bakiye sıfırdı."
        )
        QMessageBox.information(self, "Yıl Açıldı", mesaj)
        self.yil_status.setText(
            f"✅  {yeni} yılı açıldı — {eklenen} devir fişi oluşturuldu")
        self.yil_status.setStyleSheet("font-size: 12px; color: #059669; font-weight: bold;")
