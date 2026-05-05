"""
SMMM TAKİP — GitHub Güncelleme Denetleyici

Açılışta arka planda GitHub Releases API'yi kontrol eder.
Yeni sürüm bulunursa kullanıcıya dialog gösterir.
Onay verilirse kurulum dosyasını indirir ve sessizce yükler.
"""

import sys
import os
import json
import tempfile
import subprocess
import urllib.request
import urllib.error

from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QMessageBox
)

from version import APP_VERSION, GITHUB_REPO


# ─────────────────────────────────────────────────────────────
#  Yardımcı: sürüm karşılaştırma
# ─────────────────────────────────────────────────────────────

def _ver_tuple(v: str):
    """'1.2.3'  →  (1, 2, 3)"""
    try:
        return tuple(int(x) for x in v.lstrip('v').split('.'))
    except Exception:
        return (0,)


# ─────────────────────────────────────────────────────────────
#  İndirme iş parçacığı
# ─────────────────────────────────────────────────────────────

class _DownloadThread(QThread):
    progress_signal = pyqtSignal(int)    # 0-100
    finished_signal = pyqtSignal(str)    # indirilen dosya yolu
    error_signal    = pyqtSignal(str)    # hata mesajı

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            req = urllib.request.Request(
                self.url,
                headers={'User-Agent': 'SMMM-Takip-Updater'}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                toplam = int(resp.headers.get('Content-Length', 0))
                indirilen = 0
                tmp = tempfile.NamedTemporaryFile(suffix='.exe', delete=False)
                while True:
                    parca = resp.read(65536)
                    if not parca:
                        break
                    tmp.write(parca)
                    indirilen += len(parca)
                    if toplam > 0:
                        self.progress_signal.emit(int(indirilen / toplam * 100))
                tmp.close()
            self.finished_signal.emit(tmp.name)
        except Exception as e:
            self.error_signal.emit(str(e))


# ─────────────────────────────────────────────────────────────
#  Güncelleme dialogu
# ─────────────────────────────────────────────────────────────

class UpdateDialog(QDialog):
    def __init__(self, yeni_surum: str, download_url: str, aciklama: str, parent=None):
        super().__init__(parent)
        self.yeni_surum   = yeni_surum
        self.download_url = download_url
        self._thread      = None

        self.setWindowTitle("🆕  Yeni Güncelleme Mevcut")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._build_ui(aciklama)

    def _build_ui(self, aciklama: str):
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 20, 20, 20)

        # Başlık
        lbl_baslik = QLabel(
            f"<b style='font-size:14px;'>SMMM Takip — v{self.yeni_surum} yayınlandı!</b><br>"
            f"<span style='color:#64748B;'>Mevcut sürümünüz: v{APP_VERSION}</span>"
        )
        lbl_baslik.setTextFormat(Qt.RichText)
        lay.addWidget(lbl_baslik)

        # Değişiklik notları
        if aciklama and aciklama.strip():
            lbl_notlar_bslk = QLabel("<b>Değişiklikler:</b>")
            lay.addWidget(lbl_notlar_bslk)
            lbl_notlar = QLabel(aciklama[:1000])
            lbl_notlar.setWordWrap(True)
            lbl_notlar.setStyleSheet(
                "color:#475569; font-size:11px; background:#F8FAFC; "
                "border:1px solid #E2E8F0; border-radius:4px; padding:8px;"
            )
            lay.addWidget(lbl_notlar)

        # İlerleme çubuğu (başta gizli)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setVisible(False)
        lay.addWidget(self.progress)

        self.lbl_durum = QLabel("")
        self.lbl_durum.setStyleSheet("color:#64748B; font-size:11px;")
        lay.addWidget(self.lbl_durum)

        # Butonlar
        btn_lay = QHBoxLayout()
        self.btn_guncelle = QPushButton("⬇️  Şimdi Güncelle ve Yeniden Başlat")
        self.btn_guncelle.setObjectName("btn_success")
        self.btn_guncelle.setFixedHeight(38)
        self.btn_guncelle.clicked.connect(self._indir_ve_kur)

        self.btn_sonra = QPushButton("Sonra Hatırlat")
        self.btn_sonra.setFixedHeight(38)
        self.btn_sonra.clicked.connect(self.reject)

        btn_lay.addWidget(self.btn_guncelle)
        btn_lay.addWidget(self.btn_sonra)
        lay.addLayout(btn_lay)

    def _indir_ve_kur(self):
        self.btn_guncelle.setEnabled(False)
        self.btn_sonra.setEnabled(False)
        self.progress.setVisible(True)
        self.lbl_durum.setText("Güncelleme indiriliyor, lütfen bekleyin...")

        self._thread = _DownloadThread(self.download_url)
        self._thread.progress_signal.connect(self._guncelle_progress)
        self._thread.finished_signal.connect(self._kurulum_baslat)
        self._thread.error_signal.connect(self._hata)
        self._thread.start()

    def _guncelle_progress(self, yuzde: int):
        self.progress.setValue(yuzde)
        self.lbl_durum.setText(f"İndiriliyor... %{yuzde}")

    def _kurulum_baslat(self, dosya_yolu: str):
        self.lbl_durum.setText("Kurulum başlatılıyor, uygulama kapanıyor...")
        try:
            # /SILENT: kullanıcıya soru sormadan kur
            # /CLOSEAPPLICATIONS: çalışan eski sürümü kapat
            # /RESTARTAPPLICATIONS: kurulum bittikten sonra yeniden başlat
            subprocess.Popen(
                [dosya_yolu, '/SILENT', '/CLOSEAPPLICATIONS', '/RESTARTAPPLICATIONS'],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
            sys.exit(0)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kurulum başlatılamadı:\n{e}")
            self._kurulum_iptal()

    def _hata(self, mesaj: str):
        QMessageBox.critical(
            self, "İndirme Hatası",
            f"Güncelleme indirilemedi:\n{mesaj}\n\n"
            f"İnternet bağlantınızı kontrol edip tekrar deneyin."
        )
        self._kurulum_iptal()

    def _kurulum_iptal(self):
        self.btn_guncelle.setEnabled(True)
        self.btn_sonra.setEnabled(True)
        self.progress.setVisible(False)
        self.lbl_durum.setText("")

    def closeEvent(self, event):
        # İndirme devam ediyorsa thread'i durdur
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait(2000)
        super().closeEvent(event)


# ─────────────────────────────────────────────────────────────
#  Güncelleme denetleyici (arka planda çalışır)
# ─────────────────────────────────────────────────────────────

class UpdateChecker(QObject):
    """
    Kullanım:
        checker = UpdateChecker()
        checker.update_available.connect(lambda surum, url, notlar: ...)
        checker.check_in_background()
    """
    update_available = pyqtSignal(str, str, str)  # yeni_surum, download_url, aciklama

    def check_in_background(self):
        """Arka planda GitHub API'yi kontrol eder. UI'ı bloklamaz."""
        self._thread = QThread()
        self._worker = _CheckWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.result.connect(self._on_result)
        self._worker.result.connect(self._thread.quit)
        self._thread.start()

    def _on_result(self, surum: str, url: str, aciklama: str):
        if surum:
            self.update_available.emit(surum, url, aciklama)


class _CheckWorker(QObject):
    result = pyqtSignal(str, str, str)

    def run(self):
        if not GITHUB_REPO or '/' not in GITHUB_REPO or 'GITHUB_KULLANICISI' in GITHUB_REPO:
            self.result.emit('', '', '')
            return
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(
                api_url,
                headers={'User-Agent': 'SMMM-Takip-Updater', 'Accept': 'application/vnd.github.v3+json'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            latest = data.get('tag_name', '').lstrip('v')
            if not latest:
                self.result.emit('', '', '')
                return

            if _ver_tuple(latest) <= _ver_tuple(APP_VERSION):
                self.result.emit('', '', '')
                return

            download_url = ''
            for asset in data.get('assets', []):
                if asset.get('name', '').lower().endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                self.result.emit('', '', '')
                return

            aciklama = data.get('body', '') or ''
            self.result.emit(latest, download_url, aciklama)

        except Exception:
            self.result.emit('', '', '')
