STYLE = """
/* ════════════════════════════════════════════
   SMMM TAKİP – Modern Arayüz
   ════════════════════════════════════════════ */

/* ── Genel ── */
QMainWindow, QWidget {
    background-color: #F4F6FA;
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    font-size: 13px;
    color: #1E293B;
}

/* ── Sidebar ── */
QWidget#sidebar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #1E293B, stop:1 #0F172A);
    border-right: 1px solid #334155;
}
QLabel#app_logo_lbl {
    font-size: 34px;
    background: transparent;
    qproperty-alignment: AlignCenter;
    padding-top: 8px;
}
QLabel#app_title {
    color: #F8FAFC;
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 1px;
    qproperty-alignment: AlignCenter;
    background: transparent;
}
QLabel#app_sub {
    color: #64748B;
    font-size: 10px;
    qproperty-alignment: AlignCenter;
    background: transparent;
    padding-bottom: 4px;
}
QFrame#sidebar_divider {
    background-color: #334155;
    max-height: 1px;
    border: none;
}
QLabel#nav_section {
    color: #475569;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.5px;
    padding: 14px 20px 4px 20px;
    background: transparent;
}
QPushButton#nav_btn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    text-align: left;
    padding: 11px 20px;
    font-size: 13px;
    border-radius: 0px;
    border-left: 3px solid transparent;
}
QPushButton#nav_btn:hover {
    background-color: rgba(255,255,255,0.06);
    color: #E2E8F0;
    border-left: 3px solid #3B82F6;
}
QPushButton#nav_btn:checked {
    background-color: rgba(59,130,246,0.18);
    color: #FFFFFF;
    font-weight: bold;
    border-left: 3px solid #3B82F6;
}
QLabel#ver_label {
    color: #334155;
    font-size: 10px;
    qproperty-alignment: AlignCenter;
    padding: 8px;
    background: transparent;
}

/* ── İçerik alanı ── */
QWidget#content_area {
    background-color: #F4F6FA;
}

/* ── Sayfa başlığı ── */
QLabel#page_title {
    font-size: 20px;
    font-weight: bold;
    color: #0F172A;
    padding: 2px 0px;
}
QLabel#page_subtitle {
    font-size: 12px;
    color: #64748B;
}

/* ── Toolbar şeridi ── */
QWidget#toolbar_strip {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
}

/* ── Butonlar ── */
QPushButton {
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
    outline: none;
}
QPushButton#btn_primary {
    background-color: #3B82F6;
    color: white;
    border: none;
}
QPushButton#btn_primary:hover   { background-color: #2563EB; }
QPushButton#btn_primary:pressed { background-color: #1D4ED8; }
QPushButton#btn_primary:disabled{ background-color: #93C5FD; }

QPushButton#btn_success {
    background-color: #10B981;
    color: white;
    border: none;
}
QPushButton#btn_success:hover   { background-color: #059669; }
QPushButton#btn_success:pressed { background-color: #047857; }

QPushButton#btn_danger {
    background-color: #EF4444;
    color: white;
    border: none;
}
QPushButton#btn_danger:hover   { background-color: #DC2626; }
QPushButton#btn_danger:pressed { background-color: #B91C1C; }

QPushButton#btn_warning {
    background-color: #F59E0B;
    color: white;
    border: none;
}
QPushButton#btn_warning:hover  { background-color: #D97706; }

QPushButton#btn_secondary {
    background-color: #64748B;
    color: white;
    border: none;
}
QPushButton#btn_secondary:hover { background-color: #475569; }

QPushButton#btn_outline {
    background-color: transparent;
    color: #3B82F6;
    border: 1.5px solid #3B82F6;
}
QPushButton#btn_outline:hover {
    background-color: #EFF6FF;
}

QPushButton#btn_icon {
    background-color: #F1F5F9;
    color: #475569;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton#btn_icon:hover {
    background-color: #E2E8F0;
    color: #1E293B;
}

/* ── Arama kutusu ── */
QLineEdit#search_box {
    border: 1.5px solid #E2E8F0;
    border-radius: 20px;
    padding: 7px 14px 7px 36px;
    background-color: #FFFFFF;
    font-size: 13px;
    color: #1E293B;
}
QLineEdit#search_box:focus {
    border-color: #3B82F6;
    background-color: #FAFBFF;
}

/* ── Tablolar ── */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #E2E8F0;
    alternate-background-color: #F8FAFC;
    selection-background-color: #DBEAFE;
    selection-color: #1E3A8A;
    font-size: 13px;
    color: #111827;
    outline: none;
}
QTableWidget::item {
    padding: 7px 12px;
    border-bottom: 1px solid #E2E8F0;
    font-size: 13px;
    color: #111827;
}
QTableWidget::item:selected {
    background-color: #DBEAFE;
    color: #1E3A8A;
}
QHeaderView::section {
    background-color: #1E293B;
    border: none;
    border-bottom: 2px solid #3B82F6;
    border-right: 1px solid #334155;
    padding: 10px 12px;
    font-weight: bold;
    font-size: 13px;
    color: #F1F5F9;
    letter-spacing: 0.3px;
}
QHeaderView::section:last { border-right: none; }

/* ── Input alanları ── */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    border: 1.5px solid #E2E8F0;
    border-radius: 6px;
    padding: 7px 10px;
    background-color: #FFFFFF;
    font-size: 13px;
    color: #1E293B;
    selection-background-color: #DBEAFE;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border-color: #3B82F6;
    background-color: #FAFBFF;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
    padding-right: 4px;
}
QComboBox QAbstractItemView {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    background: #FFFFFF;
    selection-background-color: #DBEAFE;
    outline: none;
}

/* ── GroupBox ── */
QGroupBox {
    font-weight: bold;
    font-size: 12px;
    border: 1.5px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    background-color: #FFFFFF;
    color: #1E293B;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #3B82F6;
    font-size: 12px;
    background: #FFFFFF;
}

/* ── Stat kartları ── */
QFrame#stat_card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 4px;
}
QLabel#stat_value {
    font-size: 30px;
    font-weight: bold;
    color: #3B82F6;
    qproperty-alignment: AlignCenter;
    background: transparent;
}
QLabel#stat_label {
    font-size: 12px;
    color: #94A3B8;
    qproperty-alignment: AlignCenter;
    background: transparent;
}
QLabel#stat_icon {
    font-size: 24px;
    qproperty-alignment: AlignCenter;
    background: transparent;
}

/* ── Badge ── */
QLabel#badge_green {
    background-color: #D1FAE5;
    color: #065F46;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}
QLabel#badge_red {
    background-color: #FEE2E2;
    color: #991B1B;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}
QLabel#badge_blue {
    background-color: #DBEAFE;
    color: #1E40AF;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}
QLabel#badge_gray {
    background-color: #F1F5F9;
    color: #475569;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}

/* ── Dialog ── */
QDialog {
    background-color: #F4F6FA;
}
QDialogButtonBox QPushButton {
    min-width: 90px;
}

/* ── ScrollBar ── */
QScrollBar:vertical {
    width: 7px;
    background: transparent;
    margin: 2px 0;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #94A3B8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { height: 7px; background: transparent; }
QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

/* ── StatusBar ── */
QStatusBar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #1E293B, stop:1 #0F172A);
    color: #64748B;
    font-size: 12px;
    border-top: 1px solid #334155;
}
QStatusBar::item { border: none; }

/* ── Tab widget ── */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background: #FFFFFF;
}
QTabBar::tab {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 18px;
    margin-right: 2px;
    color: #64748B;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: #FFFFFF;
    color: #3B82F6;
    font-weight: bold;
    border-bottom: 2px solid #3B82F6;
}
QTabBar::tab:hover { color: #3B82F6; }

/* ── Ayarlar sayfası özel ── */
QFrame#settings_card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 6px;
}
QLabel#settings_card_title {
    font-size: 14px;
    font-weight: bold;
    color: #1E293B;
}
QLabel#settings_card_desc {
    font-size: 12px;
    color: #64748B;
}

/* ── Mükellef kart listesi ── */
QFrame#muk_card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}
QFrame#muk_card:hover {
    border-color: #3B82F6;
    background-color: #FAFBFF;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #1E293B;
    color: #F8FAFC;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

/* ── Checkbox ── */
QCheckBox {
    spacing: 8px;
    color: #1E293B;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #CBD5E1;
    border-radius: 4px;
    background: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border-color: #3B82F6;
    image: none;
}
QCheckBox::indicator:hover { border-color: #3B82F6; }

/* ── Separator ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background-color: #E2E8F0;
    border: none;
    max-height: 1px;
}
"""

# Python tarafında kullanmak için renk sabitleri
CLR_GREEN  = "#D1FAE5"
CLR_RED    = "#FEE2E2"
CLR_YELLOW = "#FEF9C3"
CLR_ORANGE = "#FED7AA"
CLR_WHITE  = "#FFFFFF"
CLR_BLUE   = "#DBEAFE"
