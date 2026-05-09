import re
import subprocess
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog as tk_filedialog

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFileDialog, QMessageBox, QTextEdit, QTabWidget,
    QFrame, QGroupBox, QFormLayout, QComboBox, QTextBrowser
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from edefter_excel import export_yevmiye_to_excel, inspect_yevmiye_input

try:
    from lxml import etree
    LXML_AVAILABLE = True
except Exception as _lxml_exc:
    etree = None
    LXML_AVAILABLE = False
    LXML_IMPORT_ERROR = str(_lxml_exc)


# ──────────────────────────────────────────────
# E-Defter İşlevleri
# ──────────────────────────────────────────────

def extract_stylesheet_href(xml_path: Path) -> str | None:
    """XML dosyasından stylesheet href'i çıkar."""
    head = xml_path.read_text(encoding="utf-8", errors="ignore")[:1024]
    match = re.search(r'<\?xml-stylesheet[^>]*href=["\']([^"\']+)["\']', head)
    return match.group(1) if match else None


def resolve_xslt_path(xml_path: Path) -> Path:
    """XML dosyasına uygun XSLT dosyasını bul."""
    href = extract_stylesheet_href(xml_path)
    candidates: list[Path] = []

    if href:
        candidates.append((xml_path.parent / href).resolve())

    stem_upper = xml_path.stem.upper()
    if "-Y-" in stem_upper or stem_upper.endswith("-Y-000000"):
        candidates.append((xml_path.parent / "yevmiye.xslt").resolve())
    if "-K-" in stem_upper or stem_upper.endswith("-K-000000"):
        candidates.append((xml_path.parent / "kebir.xslt").resolve())
    if "-B-" in stem_upper or "-YB-" in stem_upper or "-KB-" in stem_upper:
        candidates.append((xml_path.parent / "berat.xslt").resolve())

    candidates.extend(
        [
            (xml_path.parent / "yevmiye.xslt").resolve(),
            (xml_path.parent / "kebir.xslt").resolve(),
            (xml_path.parent / "berat.xslt").resolve(),
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Uygun XSLT dosyası bulunamadı. XML ile aynı klasörde yevmiye.xslt, kebir.xslt veya berat.xslt olmalı."
    )


def transform_xml_to_html(xml_path: str | Path, html_path: str | Path | None = None) -> Path:
    """XML dosyasını XSLT ile HTML'e dönüştür."""
    if not LXML_AVAILABLE:
        raise RuntimeError("lxml modülü bulunamadı. E-Defter önizleme için lxml gereklidir.")

    xml_file = Path(xml_path).expanduser().resolve()
    if not xml_file.exists():
        raise FileNotFoundError(f"XML dosyası bulunamadı: {xml_file}")
    
    xslt_path = resolve_xslt_path(xml_file)
    output = Path(html_path).expanduser().resolve() if html_path else xml_file.with_suffix(".html")

    xml_parser = etree.XMLParser(resolve_entities=False, recover=True, huge_tree=True)
    xml_tree = etree.parse(str(xml_file), parser=xml_parser)
    xslt_tree = etree.parse(str(xslt_path), parser=xml_parser)

    transform = etree.XSLT(xslt_tree)
    result = transform(xml_tree)
    html_text = str(result)
    output.write_text(html_text, encoding="utf-8")
    return output


def detect_edge_path() -> Path:
    """Microsoft Edge'i bul."""
    edge_candidates = (
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    )
    for candidate in edge_candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Microsoft Edge bulunamadı. PDF çıktısı için Edge kurulu olmalı.")


def export_pdf_from_html(html_path: str | Path, pdf_path: str | Path) -> Path:
    """HTML dosyasını Edge ile PDF'ye dönüştür."""
    html_file = Path(html_path).expanduser().resolve()
    pdf_file = Path(pdf_path).expanduser().resolve()
    edge_path = detect_edge_path()
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(edge_path),
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        f"--print-to-pdf={pdf_file}",
        html_file.as_uri(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if completed.returncode != 0 or not pdf_file.exists():
        raise RuntimeError(
            "PDF oluşturulamadı. "
            + (completed.stderr.strip() or completed.stdout.strip() or "Edge komutu başarısız oldu.")
        )
    return pdf_file


# ──────────────────────────────────────────────
# Arka Plan İşçi (Threading)
# ──────────────────────────────────────────────

class EDefterWorker(QThread):
    """XML→HTML→PDF dönüşüm işçi."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)  # Başarılı sonuç
    error = pyqtSignal(str)     # Hata

    def __init__(self, xml_path: Path, operation: str, output_path: Path | None = None):
        super().__init__()
        self.xml_path = xml_path
        self.operation = operation  # "preview", "html", "pdf"
        self.output_path = output_path

    def run(self):
        try:
            if self.operation == "preview":
                self.progress.emit("Önizleme oluşturuluyor...")
                preview_dir = Path(tempfile.gettempdir()) / "edefter_bot_preview"
                preview_dir.mkdir(parents=True, exist_ok=True)
                preview_path = preview_dir / f"{self.xml_path.stem}-preview.html"
                transform_xml_to_html(self.xml_path, preview_path)
                self.finished.emit(str(preview_path))

            elif self.operation == "html":
                self.progress.emit("HTML oluşturuluyor...")
                html_path = transform_xml_to_html(self.xml_path, self.output_path)
                self.finished.emit(str(html_path))

            elif self.operation == "pdf":
                self.progress.emit("HTML oluşturuluyor...")
                html_path = transform_xml_to_html(self.xml_path)
                self.progress.emit("PDF oluşturuluyor...")
                pdf_path = export_pdf_from_html(html_path, self.output_path)
                self.finished.emit(str(pdf_path))

        except Exception as exc:
            self.error.emit(str(exc))


class YevmiyeExcelWorker(QThread):
    """PDF/XML/HTML -> Excel dönüşüm işçisi."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, input_path: Path, output_path: Path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            self.progress.emit("Excel aktarımı hazırlanıyor...")
            result = export_yevmiye_to_excel(self.input_path, self.output_path, transform_xml_to_html)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


# ──────────────────────────────────────────────
# E-Defter Panel
# ──────────────────────────────────────────────

class EDefterPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.xml_path: Path | None = None
        self.xslt_path: Path | None = None
        self.html_path: Path | None = None
        self.excel_input_path: Path | None = None
        self.worker: EDefterWorker | None = None
        self.excel_worker: YevmiyeExcelWorker | None = None
        self.last_xml_dir = Path.home()  # Son açılan XML klasörü
        self.last_save_dir = Path.home()  # Son kaydetme klasörü
        self._build()

    def _build(self):
        """Panel UI oluştur."""
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(16, 16, 16, 16)

        # Başlık
        title = QLabel("📄  E-Defter Görüntüle")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lay.addWidget(title)

        subtitle = QLabel(
            "E-defter dosyalarını görüntüleyin, PDF/XML yevmiye kayıtlarını Excel'e aktarın"
        )
        subtitle.setStyleSheet("color: #607D8B; font-size: 11px;")
        lay.addWidget(subtitle)

        # Dosya seçim grubu
        grp_file = QGroupBox("XML Dosyası Seçimi")
        grp_file.setStyleSheet("QGroupBox { border: 1px solid #BDD7EE; border-radius: 4px; padding-top: 8px; }")
        lay_file = QFormLayout(grp_file)

        self.lbl_xml = QLineEdit()
        self.lbl_xml.setReadOnly(True)
        self.lbl_xml.setPlaceholderText("XML dosyası seçilmedi")
        lay_file.addRow("XML Dosyası:", self.lbl_xml)

        self.lbl_xslt = QLineEdit()
        self.lbl_xslt.setReadOnly(True)
        self.lbl_xslt.setPlaceholderText("-")
        lay_file.addRow("Kullanılan XSLT:", self.lbl_xslt)

        self.btn_choose = QPushButton("XML Seç")
        self.btn_choose.clicked.connect(self._choose_xml)
        lay_file.addRow("", self.btn_choose)

        lay.addWidget(grp_file)

        # İşlem butonları
        grp_ops = QGroupBox("İşlemler")
        grp_ops.setStyleSheet("QGroupBox { border: 1px solid #BDD7EE; border-radius: 4px; padding-top: 8px; }")
        lay_ops = QHBoxLayout(grp_ops)

        self.btn_preview = QPushButton("Önizle")
        self.btn_preview.clicked.connect(self._preview_xml)
        self.btn_preview.setEnabled(False)

        self.btn_html = QPushButton("HTML Kaydet")
        self.btn_html.clicked.connect(self._export_html)
        self.btn_html.setEnabled(False)

        self.btn_pdf = QPushButton("PDF Kaydet")
        self.btn_pdf.clicked.connect(self._export_pdf)
        self.btn_pdf.setEnabled(False)

        self.btn_open = QPushButton("Tarayıcıda Aç")
        self.btn_open.clicked.connect(self._open_in_browser)
        self.btn_open.setEnabled(False)

        lay_ops.addWidget(self.btn_preview)
        lay_ops.addWidget(self.btn_html)
        lay_ops.addWidget(self.btn_pdf)
        lay_ops.addWidget(self.btn_open)
        lay.addWidget(grp_ops)

        grp_excel = QGroupBox("Zirve Yevmiye Excel Aktarım")
        grp_excel.setStyleSheet("QGroupBox { border: 1px solid #BDD7EE; border-radius: 4px; padding-top: 8px; }")
        lay_excel = QFormLayout(grp_excel)

        excel_info = QLabel(
            "PDF raporu, XML veya HTML seçebilirsiniz. PDF seçilirse yevmiye kaynağı otomatik bulunur."
        )
        excel_info.setWordWrap(True)
        excel_info.setStyleSheet("color: #607D8B; font-size: 11px;")
        lay_excel.addRow(excel_info)

        self.lbl_excel_input = QLineEdit()
        self.lbl_excel_input.setReadOnly(True)
        self.lbl_excel_input.setPlaceholderText("PDF, XML veya HTML dosyası seçilmedi")
        lay_excel.addRow("Kaynak Dosya:", self.lbl_excel_input)

        self.lbl_excel_source = QLineEdit()
        self.lbl_excel_source.setReadOnly(True)
        self.lbl_excel_source.setPlaceholderText("-")
        lay_excel.addRow("Çözülen Yevmiye:", self.lbl_excel_source)

        excel_buttons = QHBoxLayout()
        self.btn_choose_excel = QPushButton("PDF/XML/HTML Seç")
        self.btn_choose_excel.clicked.connect(self._choose_excel_input)

        self.btn_export_excel = QPushButton("Excel Kaydet")
        self.btn_export_excel.clicked.connect(self._export_excel_from_yevmiye)
        self.btn_export_excel.setEnabled(False)

        excel_buttons.addWidget(self.btn_choose_excel)
        excel_buttons.addWidget(self.btn_export_excel)
        lay_excel.addRow("", excel_buttons)

        lay.addWidget(grp_excel)

        # Sekmeler: Log ve Bilgi
        self.notebook = QTabWidget()
        
        # Önizleme sekmesi
        self.preview_browser = QTextBrowser()
        self.preview_browser.setReadOnly(True)
        self.preview_browser.setFont(QFont("Segoe UI", 10))
        self.notebook.addTab(self.preview_browser, "👁️  Önizleme")
        
        # Log sekmesi
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.setPlaceholderText("İşlem günlüğü burada görünecek...")
        self.notebook.addTab(self.log, "📋  Günlük")

        # Bilgi sekmesi
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setFont(QFont("Segoe UI", 10))
        info_text.setMarkdown("""
### E-Defter Görüntüleyici Kullanımı

1. **XML Seç**: E-defter XML dosyasını seçin
2. **Önizle**: HTML önizlemesini görmek için "Önizle" butonuna tıklayın
3. **HTML Kaydet**: HTML çıktısını diskte kaydetmek için tıklayın
4. **PDF Kaydet**: Edge aracılığıyla PDF olarak dışa aktarın
5. **Tarayıcıda Aç**: HTML'i varsayılan tarayıcıda açın

### Zirve Yevmiye Excel Aktarımı

1. **PDF/XML/HTML Seç**: Zirve raporu PDF'si, yevmiye XML'i veya HTML çıktısını seçin
2. **Excel Kaydet**: Yevmiye fişlerini tek adımda Excel dosyasına aktarın
3. PDF seçildiğinde sistem rapor içinden veya aynı klasörden uygun yevmiye kaynağını otomatik bulur

**Desteklenen E-Defter Türleri:**
- Yevmiye Defteri (-Y-)
- Kütüphane Defteri (-K-)
- Berat (-B-, -YB-, -KB-)

**Gereksinimler:**
- Microsoft Edge (PDF çıktısı için)
- XSLT dosyası (yevmiye.xslt, kebir.xslt, berat.xslt)
        """)
        self.notebook.addTab(info_text, "ℹ️  Bilgi")

        lay.addWidget(self.notebook, 1)

        # Durum çubuğu
        self.lbl_status = QLabel("Hazır")
        self.lbl_status.setStyleSheet("color: #607D8B; font-size: 10px; padding-top: 4px;")
        lay.addWidget(self.lbl_status)

        if not LXML_AVAILABLE:
            self.lbl_status.setText("lxml eksik: E-Defter işlemleri kullanılamaz")
            self._write_log("❌ lxml modülü bulunamadı. Bu panel için lxml gerekli.")
            self._write_log(f"❌ Hata detayı: {LXML_IMPORT_ERROR}")

        self._write_log("Uygulamaya hoş geldiniz. XML dosyası seçerek başlayabilirsiniz.")

    def _write_log(self, message: str):
        """Günlüğe mesaj yaz."""
        self.log.append(message)

    def _choose_xml(self):
        """XML dosyası seç (tkinter filedialog kullanır)."""
        if not LXML_AVAILABLE:
            QMessageBox.critical(
                self,
                "Eksik Bağımlılık",
                "lxml modülü bulunamadı. E-Defter kullanımı için güncel sürümü yeniden kurun."
            )
            return

        self._write_log("📂 Dosya seçme diyaloğu açılıyor...")
        
        # Gizli root window oluştur (tkinter dialog için gerekli)
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        try:
            file_path = tk_filedialog.askopenfilename(
                title="E-Defter XML Seç",
                initialdir=str(self.last_xml_dir),
                filetypes=[("XML Dosyaları", "*.xml"), ("Tüm Dosyalar", "*.*")]
            )
            
            root.destroy()
            
            if not file_path:
                self._write_log("❌ Dosya seçimi iptal edildi")
                return

            self.xml_path = Path(file_path)
            self.last_xml_dir = self.xml_path.parent  # Son klasörü kaydet
            self.lbl_xml.setText(str(self.xml_path))

            try:
                self.xslt_path = resolve_xslt_path(self.xml_path)
                self.lbl_xslt.setText(str(self.xslt_path))
                self.btn_preview.setEnabled(True)
                self.btn_html.setEnabled(True)
                self.btn_pdf.setEnabled(True)
                self._write_log(f"✅ XML seçildi: {self.xml_path.name}")
                self._write_log(f"✅ XSLT bulundu: {self.xslt_path.name}")
                # Otomatik önizleme başlat
                self._preview_xml()
            except Exception as exc:
                self.lbl_xslt.setText("-")
                self.btn_preview.setEnabled(False)
                self.btn_html.setEnabled(False)
                self.btn_pdf.setEnabled(False)
                QMessageBox.critical(self, "XSLT Hatası", str(exc))
                self._write_log(f"❌ Hata: {exc}")
        except Exception as exc:
            root.destroy()
            self._write_log(f"❌ Dialog hatası: {exc}")
            QMessageBox.critical(self, "Dosya Seçme Hatası", str(exc))

    def _choose_excel_input(self):
        """Excel aktarımı için PDF/XML/HTML dosyası seç."""
        self._write_log("📂 Excel aktarımı için kaynak dosya seçiliyor...")

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        try:
            file_path = tk_filedialog.askopenfilename(
                title="Yevmiye Kaynağı Seç",
                initialdir=str(self.last_xml_dir),
                filetypes=[
                    ("Desteklenen Dosyalar", "*.pdf *.xml *.html"),
                    ("PDF Dosyaları", "*.pdf"),
                    ("XML Dosyaları", "*.xml"),
                    ("HTML Dosyaları", "*.html"),
                    ("Tüm Dosyalar", "*.*"),
                ]
            )

            root.destroy()

            if not file_path:
                self._write_log("❌ Excel aktarım kaynağı seçimi iptal edildi")
                return

            self.excel_input_path = Path(file_path)
            self.last_xml_dir = self.excel_input_path.parent
            self.lbl_excel_input.setText(str(self.excel_input_path))

            try:
                info = inspect_yevmiye_input(self.excel_input_path)
                resolved_source = info.get("resolved_source")
                self.lbl_excel_source.setText(str(resolved_source) if resolved_source else "-")
                self.btn_export_excel.setEnabled(True)
                self._write_log(f"✅ Excel kaynağı seçildi: {self.excel_input_path.name}")
                self._write_log(f"✅ {info.get('message')}")
            except Exception as exc:
                self.lbl_excel_source.setText("-")
                self.btn_export_excel.setEnabled(False)
                self._write_log(f"❌ Excel kaynak çözümleme hatası: {exc}")
                QMessageBox.warning(self, "Kaynak Bulunamadı", str(exc))
        except Exception as exc:
            root.destroy()
            self._write_log(f"❌ Dialog hatası: {exc}")
            QMessageBox.critical(self, "Dosya Seçme Hatası", str(exc))

    def _preview_xml(self):
        """Önizlemeyi göster."""
        if not LXML_AVAILABLE:
            QMessageBox.critical(self, "Eksik Bağımlılık", "lxml modülü bulunamadı.")
            return

        if not self.xml_path:
            QMessageBox.warning(self, "Uyarı", "Önce bir XML dosyası seçiniz.")
            return

        self._disable_buttons()
        self.lbl_status.setText("Önizleme oluşturuluyor...")

        self.worker = EDefterWorker(self.xml_path, "preview")
        self.worker.progress.connect(self._write_log)
        self.worker.finished.connect(self._on_preview_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_preview_done(self, html_path: str):
        """Önizleme tamamlandığında."""
        self.html_path = Path(html_path)
        self._write_log(f"✅ Önizleme hazır: {self.html_path.name}")
        self.btn_open.setEnabled(True)
        self.lbl_status.setText("Önizleme hazır")
        self._enable_buttons()

        # HTML'i preview browser'a yükle
        try:
            html_content = self.html_path.read_text(encoding='utf-8')
            self.preview_browser.setHtml(html_content)
            # Önizleme sekmesine otomatik switch yap (index 0)
            self.notebook.setCurrentIndex(0)
            self._write_log(f"📺 Önizleme görüntüleniyor...")
        except Exception as exc:
            self._write_log(f"❌ Önizleme yükleme hatası: {exc}")

    def _export_html(self):
        """HTML dosyasını kaydet."""
        if not LXML_AVAILABLE:
            QMessageBox.critical(self, "Eksik Bağımlılık", "lxml modülü bulunamadı.")
            return

        if not self.xml_path:
            QMessageBox.warning(self, "Uyarı", "Önce bir XML dosyası seçiniz.")
            return

        # tkinter file dialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        suggested = self.xml_path.with_suffix(".html")
        save_path = tk_filedialog.asksaveasfilename(
            title="HTML Kaydet",
            initialfile=suggested.name,
            initialdir=str(self.last_save_dir),
            filetypes=[("HTML Dosyaları", "*.html"), ("Tüm Dosyalar", "*.*")]
        )
        root.destroy()

        if not save_path:
            self._write_log("❌ HTML kaydetme iptal edildi")
            return

        self.last_save_dir = Path(save_path).parent  # Son kaydetme klasörünü kaydet

        self._disable_buttons()
        self.lbl_status.setText("HTML oluşturuluyor...")

        self.worker = EDefterWorker(self.xml_path, "html", Path(save_path))
        self.worker.progress.connect(self._write_log)
        self.worker.finished.connect(self._on_html_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_html_done(self, html_path: str):
        """HTML export tamamlandığında."""
        self.html_path = Path(html_path)
        self._write_log(f"✅ HTML kaydedildi: {self.html_path}")
        self.btn_open.setEnabled(True)
        self.lbl_status.setText("HTML kaydedildi")
        self._enable_buttons()

        # HTML'i preview browser'a yükle
        try:
            html_content = self.html_path.read_text(encoding='utf-8')
            self.preview_browser.setHtml(html_content)
            # Önizleme sekmesine otomatik switch yap (index 0)
            self.notebook.setCurrentIndex(0)
            self._write_log(f"📺 HTML görüntüleniyor...")
        except Exception as exc:
            self._write_log(f"❌ HTML yükleme hatası: {exc}")

        QMessageBox.information(
            self,
            "Başarılı",
            f"HTML kaydedildi:\n{self.html_path}"
        )

    def _export_pdf(self):
        """PDF dosyasını kaydet."""
        if not LXML_AVAILABLE:
            QMessageBox.critical(self, "Eksik Bağımlılık", "lxml modülü bulunamadı.")
            return

        if not self.xml_path:
            QMessageBox.warning(self, "Uyarı", "Önce bir XML dosyası seçiniz.")
            return

        # tkinter file dialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        suggested_pdf = self.xml_path.with_suffix(".pdf")
        save_path = tk_filedialog.asksaveasfilename(
            title="PDF Kaydet",
            initialfile=suggested_pdf.name,
            initialdir=str(self.last_save_dir),
            filetypes=[("PDF Dosyaları", "*.pdf"), ("Tüm Dosyalar", "*.*")]
        )
        root.destroy()

        if not save_path:
            self._write_log("❌ PDF kaydetme iptal edildi")
            return

        self.last_save_dir = Path(save_path).parent  # Son kaydetme klasörünü kaydet

        self._disable_buttons()
        self.lbl_status.setText("PDF oluşturuluyor...")

        self.worker = EDefterWorker(self.xml_path, "pdf", Path(save_path))
        self.worker.progress.connect(self._write_log)
        self.worker.finished.connect(self._on_pdf_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_pdf_done(self, pdf_path: str):
        """PDF export tamamlandığında."""
        self._write_log(f"✅ PDF kaydedildi: {pdf_path}")
        self.lbl_status.setText("PDF kaydedildi")
        self._enable_buttons()

        QMessageBox.information(
            self,
            "Başarılı",
            f"PDF kaydedildi:\n{pdf_path}"
        )

    def _open_in_browser(self):
        """HTML'i tarayıcıda aç."""
        if self.html_path and self.html_path.exists():
            import webbrowser
            webbrowser.open(self.html_path.as_uri())
            self._write_log(f"🌐 Tarayıcıda açıldı: {self.html_path.name}")
        else:
            QMessageBox.warning(self, "Uyarı", "Önce bir HTML önizlemesi oluşturun.")

    def _export_excel_from_yevmiye(self):
        """PDF/XML/HTML kaynağından Excel üret."""
        if not self.excel_input_path:
            QMessageBox.warning(self, "Uyarı", "Önce bir PDF, XML veya HTML dosyası seçiniz.")
            return

        try:
            info = inspect_yevmiye_input(self.excel_input_path)
        except Exception as exc:
            QMessageBox.critical(self, "Kaynak Hatası", str(exc))
            self._write_log(f"❌ Excel aktarımı başlamadı: {exc}")
            return

        resolved_source = info.get("resolved_source")
        default_stem = self.excel_input_path.stem
        if isinstance(resolved_source, Path):
            default_stem = resolved_source.stem

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        save_path = tk_filedialog.asksaveasfilename(
            title="Excel Kaydet",
            initialfile=f"{default_stem}.xlsx",
            initialdir=str(self.last_save_dir),
            filetypes=[("Excel Dosyaları", "*.xlsx"), ("Tüm Dosyalar", "*.*")]
        )
        root.destroy()

        if not save_path:
            self._write_log("❌ Excel kaydetme iptal edildi")
            return

        self.last_save_dir = Path(save_path).parent
        self._disable_buttons()
        self.lbl_status.setText("Excel aktarımı yapılıyor...")

        self.excel_worker = YevmiyeExcelWorker(self.excel_input_path, Path(save_path))
        self.excel_worker.progress.connect(self._write_log)
        self.excel_worker.finished.connect(self._on_excel_done)
        self.excel_worker.error.connect(self._on_error)
        self.excel_worker.start()

    def _on_excel_done(self, result: object):
        """Excel aktarımı tamamlandığında."""
        if not isinstance(result, dict):
            self._on_error("Excel aktarım sonucu okunamadı.")
            return

        output_path = Path(str(result["output_path"]))
        resolved_source = result.get("resolved_source")
        row_count = int(result.get("row_count", 0))

        if resolved_source:
            self.lbl_excel_source.setText(str(resolved_source))

        self._write_log(f"✅ Excel kaydedildi: {output_path}")
        self._write_log(f"✅ Aktarılan yevmiye satırı: {row_count}")
        self.lbl_status.setText(f"Excel kaydedildi ({row_count} satır)")
        self._enable_buttons()

        QMessageBox.information(
            self,
            "Başarılı",
            f"Excel kaydedildi:\n{output_path}\n\nAktarılan satır: {row_count}"
        )

    def _on_error(self, error_msg: str):
        """Hata oluştuğunda."""
        self._write_log(f"❌ Hata: {error_msg}")
        self.lbl_status.setText("Hata oluştu")
        self._enable_buttons()
        QMessageBox.critical(self, "Hata", error_msg)

    def _disable_buttons(self):
        """İşlem butonlarını devre dışı bırak."""
        self.btn_preview.setEnabled(False)
        self.btn_html.setEnabled(False)
        self.btn_pdf.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.btn_choose_excel.setEnabled(False)
        self.btn_export_excel.setEnabled(False)

    def _enable_buttons(self):
        """İşlem butonlarını etkinleştir."""
        if self.xml_path:
            self.btn_preview.setEnabled(True)
            self.btn_html.setEnabled(True)
            self.btn_pdf.setEnabled(True)
            if self.html_path:
                self.btn_open.setEnabled(True)
        self.btn_choose_excel.setEnabled(True)
        if self.excel_input_path:
            self.btn_export_excel.setEnabled(True)

    def refresh(self):
        """Panel yenilenme (sidebar'dan çağrılır)."""
        pass

    def set_yil(self, yil):
        """Yıl değişikliğini işle (dashboard/beyanname panelleri gibi)."""
        pass
