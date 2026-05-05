import sys
import os

from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QColor

from db import db
from main_window import MainWindow
from update_checker import UpdateChecker, UpdateDialog
from license import verify as _verify_license


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SMMM Takip")
    app.setOrganizationName("SMMM")
    app.setStyle("Fusion")

    # Varsayılan font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── Lisans kontrolü (pencere açılmadan önce) ──────────────
    _splash = None

    def _show_progress(mesaj: str):
        nonlocal _splash
        pix = QPixmap(420, 70)
        pix.fill(QColor('#1E293B'))
        _splash = QSplashScreen(pix, Qt.WindowStaysOnTopHint)
        _splash.showMessage(
            f"  🔐  {mesaj}",
            Qt.AlignLeft | Qt.AlignVCenter,
            QColor('#94D2FF')
        )
        _splash.show()
        app.processEvents()

    lic_ok, lic_msg = _verify_license(show_progress_cb=_show_progress)

    if _splash:
        _splash.close()

    if lic_ok is False:
        QMessageBox.critical(
            None,
            "⛔  Lisans Hatası",
            f"Bu bilgisayarda uygulamayı çalıştırma yetkisi yok.\n\n{lic_msg}"
        )
        sys.exit(1)
    # lic_ok is None → geliştirici modu, devam et
    # ─────────────────────────────────────────────────────────

    # Veritabanı bağlantısı
    ok, msg = db.connect()
    if not ok:
        QMessageBox.critical(None, "Veritabanı Hatası",
                             f"Veritabanı açılamadı:\n{msg}")
        sys.exit(1)

    window = MainWindow()
    window.show()

    # ── Açılışta arka planda güncelleme kontrolü ──
    _checker = UpdateChecker()

    def _guncelleme_bulundu(surum, url, notlar):
        dlg = UpdateDialog(surum, url, notlar, parent=window)
        dlg.exec_()

    _checker.update_available.connect(_guncelleme_bulundu)
    _checker.check_in_background()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
