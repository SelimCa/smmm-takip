"""
PDF Rapor Yardımcıları  —  reportlab tabanlı
Tüm paneller bu modüldeki fonksiyonları kullanır.
"""

import os
from datetime import date as _date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Font: Türkçe karakter desteği için Windows Arial ──────
_FONT_REGISTERED = False

def _ensure_font():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    win_fonts = "C:/Windows/Fonts"
    candidates = [
        ("Arial",      os.path.join(win_fonts, "arial.ttf")),
        ("Arial-Bold", os.path.join(win_fonts, "arialbd.ttf")),
    ]
    for name, path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception:
                pass
    _FONT_REGISTERED = True

def _font(bold=False):
    _ensure_font()
    name = "Arial-Bold" if bold else "Arial"
    try:
        from reportlab.pdfbase.pdfmetrics import getFont
        getFont(name)
        return name
    except Exception:
        return "Helvetica-Bold" if bold else "Helvetica"


def _cell(text, style_key="normal", st=None):
    """Metni Paragraph'a sarar — otomatik kaydırma için."""
    if st is None:
        st = _styles()
    return Paragraph(str(text) if text else "—", st[style_key])


def _hdr_cell(text, st=None):
    if st is None:
        st = _styles()
    return Paragraph(str(text), st["hdr_cell"])


# ── Ortak renkler ─────────────────────────────────────────
C_DARK    = colors.HexColor("#1E293B")
C_HEADER  = colors.HexColor("#1E3A5F")
C_BLUE    = colors.HexColor("#DBEAFE")
C_GREEN   = colors.HexColor("#D1FAE5")
C_RED     = colors.HexColor("#FEE2E2")
C_GRAY    = colors.HexColor("#F1F5F9")
C_BORDER  = colors.HexColor("#CBD5E1")
C_WHITE   = colors.white
C_RED_TXT = colors.HexColor("#C0392B")
C_GRN_TXT = colors.HexColor("#1E8449")
C_ORG_TXT = colors.HexColor("#D97706")


def _styles():
    _ensure_font()
    f = _font()
    fb = _font(bold=True)
    s = getSampleStyleSheet()
    base = dict(fontName=f, fontSize=10, leading=14)
    return {
        "title":    ParagraphStyle("title",    fontName=fb, fontSize=16, textColor=C_DARK, leading=22, spaceAfter=2),
        "subtitle": ParagraphStyle("subtitle", fontName=f,  fontSize=10, textColor=colors.HexColor("#64748B"), leading=14, spaceAfter=8),
        "normal":   ParagraphStyle("normal",   **base),
        "bold":     ParagraphStyle("bold",     fontName=fb, fontSize=10, leading=14),
        "small":    ParagraphStyle("small",    fontName=f,  fontSize=8,  textColor=colors.HexColor("#6B7280"), leading=12),
        "right":    ParagraphStyle("right",    fontName=f,  fontSize=10, alignment=TA_RIGHT, leading=14),
        "hdr_cell": ParagraphStyle("hdr_cell", fontName=fb, fontSize=8.5, textColor=C_WHITE, leading=12, alignment=TA_CENTER),
        "cell":     ParagraphStyle("cell",     fontName=f,  fontSize=8,  leading=11),
        "cell_r":   ParagraphStyle("cell_r",   fontName=f,  fontSize=8,  leading=11, alignment=TA_RIGHT),
    }


def _header_table(doc_title: str, subtitle: str = "") -> list:
    """Sayfanın üstüne basılacak başlık bloku."""
    st = _styles()
    items = [
        Paragraph(doc_title, st["title"]),
    ]
    if subtitle:
        items.append(Paragraph(subtitle, st["subtitle"]))
    items.append(Paragraph(
        f"Oluşturma Tarihi: {_date.today().strftime('%d.%m.%Y')}",
        st["small"]
    ))
    items.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=10))
    return items


def _table_style(header_rows=1) -> TableStyle:
    cmds = [
        # Header
        ("BACKGROUND",   (0, 0), (-1, header_rows - 1), C_HEADER),
        ("TEXTCOLOR",    (0, 0), (-1, header_rows - 1), C_WHITE),
        ("FONTNAME",     (0, 0), (-1, header_rows - 1), _font(bold=True)),
        ("FONTSIZE",     (0, 0), (-1, header_rows - 1), 9),
        ("ALIGN",        (0, 0), (-1, header_rows - 1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUND",(0, header_rows), (-1, -1),
            [C_WHITE, C_GRAY]),
        ("FONTNAME",     (0, header_rows), (-1, -1), _font()),
        ("FONTSIZE",     (0, header_rows), (-1, -1), 8.5),
        ("GRID",         (0, 0), (-1, -1), 0.4, C_BORDER),
        ("ROWHEIGHT",    (0, 0), (-1, -1), 18),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    return TableStyle(cmds)


def _save_dialog(parent, default_name: str) -> str | None:
    """Dosya kaydet diyaloğu — dosya yolunu döner veya None."""
    from PyQt5.QtWidgets import QFileDialog
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "PDF Olarak Kaydet",
        os.path.join(os.path.expanduser("~"), "Desktop", default_name),
        "PDF Dosyası (*.pdf)"
    )
    return path if path else None


def _open_pdf(path: str):
    """PDF dosyasını varsayılan görüntüleyici ile aç."""
    try:
        os.startfile(path)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════
#  1. MÜKELLEFler LİSTESİ PDF
# ══════════════════════════════════════════════════════════
def pdf_mukellefler(mukellefler: list, parent=None):
    path = _save_dialog(parent, "mukellefler_listesi.pdf")
    if not path:
        return

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    st = _styles()
    story = _header_table("Mükellef Listesi", f"Toplam {len(mukellefler)} mükellef")

    # Sayfa genişliği: A4 - kenar boşlukları = 21 - 3 = 18 cm
    PW = 18 * cm
    col_widths = [0.8*cm, 2.8*cm, 5.5*cm, 2.2*cm, 2.5*cm, 4.2*cm]

    header = [[
        _hdr_cell("#", st), _hdr_cell("Vergi/TC No", st),
        _hdr_cell("Ünvan / Ad Soyad", st), _hdr_cell("Tip", st),
        _hdr_cell("Telefon", st), _hdr_cell("Beyanname Türleri", st),
    ]]

    rows = []
    for i, m in enumerate(mukellefler, 1):
        beyan_listesi = []
        if m.get('kdv1'):             beyan_listesi.append("KDV-1")
        if m.get('kdv2'):             beyan_listesi.append("KDV-2")
        if m.get('muhsgk'):           beyan_listesi.append("MUH/SGK")
        if m.get('gecici_vergi'):     beyan_listesi.append("Gec.V")
        if m.get('kurumlar_vergisi'): beyan_listesi.append("KV")
        if m.get('gelir_vergisi'):    beyan_listesi.append("GV")
        if m.get('muhtasar_3aylik'):  beyan_listesi.append("Muh.3A")
        if m.get('damga_vergisi'):    beyan_listesi.append("DV")
        if m.get('gvk_67'):           beyan_listesi.append("GVK67")

        rows.append([
            _cell(str(i), "cell", st),
            _cell(m.get('vergi_no', ''), "cell", st),
            _cell(m.get('unvan', ''), "cell", st),
            _cell(m.get('tip', ''), "cell", st),
            _cell(m.get('telefon', '') or '—', "cell", st),
            _cell(", ".join(beyan_listesi) or "—", "cell", st),
        ])

    tbl = Table(header + rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_table_style())
    story.append(tbl)

    doc.build(story)
    _open_pdf(path)


# ══════════════════════════════════════════════════════════
#  2. BEYANNAME PANELİ PDF  —  A4 Yatay
# ══════════════════════════════════════════════════════════
def pdf_beyannameler(beyanlar: list, yil: int, ay_adi: str, parent=None):
    path = _save_dialog(parent, f"beyannameler_{yil}_{ay_adi}.pdf")
    if not path:
        return

    doc = SimpleDocTemplate(
        path, pagesize=landscape(A4),   # YATAY — 29.7 cm
        leftMargin=1.2*cm, rightMargin=1.2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    st = _styles()
    story = _header_table(
        "Beyanname Takip Raporu",
        f"{ay_adi} {yil}  —  Toplam {len(beyanlar)} kayit"
    )

    # Kullanılabilir genişlik: 29.7 - 2.4 = 27.3 cm
    col_widths = [0.7*cm, 6.5*cm, 2.8*cm, 3.8*cm, 2.5*cm, 2.5*cm, 2.8*cm, 2.5*cm, 3.2*cm]
    # Sütunlar:    #       Mükellef   Tür       Dönem      Son Gün  Verildi  Ödendi   Tutar    Açıklama

    header = [[
        _hdr_cell("#", st),
        _hdr_cell("Mükellef", st),
        _hdr_cell("Tür", st),
        _hdr_cell("Dönem", st),
        _hdr_cell("Son Gün", st),
        _hdr_cell("Verildi?", st),
        _hdr_cell("Ödendi?", st),
        _hdr_cell("Tutar (₺)", st),
        _hdr_cell("Açıklama", st),
    ]]

    rows = []
    from db import donem_label as _dl
    for i, b in enumerate(beyanlar, 1):
        if b.get('verildi'):
            verildi = "Verildi"
        elif b.get('atlandi'):
            verildi = "Atlandı"
        else:
            verildi = "Bekliyor"

        if b.get('odendi'):
            tip = b.get('odeme_tipi', '')
            odendi = "SMMM" if tip == 'smmm' else "Mükellef"
        else:
            odendi = "—"

        tutar = b.get('tutar') or ''
        tutar_str = f"{float(tutar):,.2f}" if tutar else "—"

        rows.append([
            _cell(str(i), "cell", st),
            _cell(b.get('unvan') or '', "cell", st),
            _cell(b.get('tur', ''), "cell", st),
            _cell(_dl(b.get('tur', ''), b.get('yil', ''), b.get('donem', '')), "cell", st),
            _cell(str(b.get('son_gun') or '')[:10], "cell", st),
            _cell(verildi, "cell", st),
            _cell(odendi, "cell", st),
            _cell(tutar_str, "cell_r", st),
            _cell(b.get('aciklama') or '—', "cell", st),
        ])

    tbl = Table(header + rows, colWidths=col_widths, repeatRows=1)
    style = _table_style()

    for idx, b in enumerate(beyanlar):
        r = idx + 1
        if b.get('atlandi'):
            style.add("BACKGROUND", (0, r), (-1, r), colors.HexColor("#E2E8F0"))
        elif b.get('verildi'):
            style.add("BACKGROUND", (0, r), (-1, r), colors.HexColor("#D1FAE5"))
        else:
            style.add("BACKGROUND", (0, r), (-1, r), colors.HexColor("#FEE2E2"))

    tbl.setStyle(style)
    story.append(tbl)

    story.append(Spacer(1, 10))
    verildi_c  = sum(1 for b in beyanlar if b.get('verildi'))
    bekleyen_c = sum(1 for b in beyanlar if not b.get('verildi') and not b.get('atlandi'))
    atlandi_c  = sum(1 for b in beyanlar if b.get('atlandi'))
    odendi_c   = sum(1 for b in beyanlar if b.get('odendi'))
    story.append(Paragraph(
        f"<b>Ozet:</b>  Verildi: {verildi_c}   Bekliyor: {bekleyen_c}   "
        f"Atlandi: {atlandi_c}   Odendi: {odendi_c}",
        st["normal"]
    ))

    doc.build(story)
    _open_pdf(path)


# ══════════════════════════════════════════════════════════
#  3. CARİ HESAP LİSTESİ PDF
# ══════════════════════════════════════════════════════════
def pdf_cari_liste(bakiyeler: list, parent=None):
    path = _save_dialog(parent, "cari_hesap_listesi.pdf")
    if not path:
        return

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    st = _styles()
    story = _header_table("Cari Hesap Listesi", f"Toplam {len(bakiyeler)} mükellef")

    col_widths = [0.8*cm, 6*cm, 2.8*cm, 2*cm, 2.8*cm, 2.8*cm, 3*cm]
    header = [[
        _hdr_cell("#", st), _hdr_cell("Mükellef", st),
        _hdr_cell("Vergi/TC No", st), _hdr_cell("Tip", st),
        _hdr_cell("Toplam Borç", st), _hdr_cell("Toplam Alacak", st),
        _hdr_cell("Net Bakiye", st),
    ]]

    rows = []
    gen_borc = gen_alacak = 0.0
    for i, m in enumerate(bakiyeler, 1):
        borc   = float(m.get('toplam_borc', 0))
        alacak = float(m.get('toplam_alacak', 0))
        net    = borc - alacak
        gen_borc   += borc
        gen_alacak += alacak

        rows.append([
            _cell(str(i), "cell", st),
            _cell(m.get('unvan') or '', "cell", st),
            _cell(m.get('vergi_no', ''), "cell", st),
            _cell(m.get('tip', ''), "cell", st),
            _cell(f"{borc:,.2f}" if borc else "—", "cell_r", st),
            _cell(f"{alacak:,.2f}" if alacak else "—", "cell_r", st),
            _cell(f"{net:+,.2f}", "cell_r", st),
        ])

    tbl = Table(header + rows, colWidths=col_widths, repeatRows=1)
    style = _table_style()

    for idx, m in enumerate(bakiyeler):
        r = idx + 1
        borc   = float(m.get('toplam_borc', 0))
        alacak = float(m.get('toplam_alacak', 0))
        net    = borc - alacak
        if net > 0:
            style.add("BACKGROUND", (0, r), (-1, r), C_RED)
        elif net < 0:
            style.add("BACKGROUND", (0, r), (-1, r), C_GREEN)

    tbl.setStyle(style)
    story.append(tbl)

    gen_net = gen_borc - gen_alacak
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Genel Toplam  —  Borc: {gen_borc:,.2f} TL  |  "
        f"Alacak: {gen_alacak:,.2f} TL  |  Net: {gen_net:+,.2f} TL</b>",
        st["bold"]
    ))

    doc.build(story)
    _open_pdf(path)


# ══════════════════════════════════════════════════════════
#  4. EKSTRe (CARİ DETAY) PDF
# ══════════════════════════════════════════════════════════
def pdf_ekstre(hareketler: list, unvan: str, vergi_no: str = "", parent=None):
    safe_name = unvan.replace(" ", "_").replace("/", "-")[:30]
    path = _save_dialog(parent, f"ekstre_{safe_name}.pdf")
    if not path:
        return

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    st = _styles()
    story = _header_table(
        "Cari Hesap Ekstresi",
        unvan + (f"  |  Vergi/TC: {vergi_no}" if vergi_no else "")
    )

    # 18 cm kullanılabilir alan
    col_widths = [0.7*cm, 2.3*cm, 2.5*cm, 7.5*cm, 2*cm, 2*cm, 2*cm]
    header = [[
        _hdr_cell("#", st), _hdr_cell("Tarih", st),
        _hdr_cell("Fis No", st), _hdr_cell("Aciklama", st),
        _hdr_cell("Borc (TL)", st), _hdr_cell("Alacak (TL)", st),
        _hdr_cell("Bakiye (TL)", st),
    ]]

    rows = []
    running = tb = ta = 0.0
    for i, h in enumerate(hareketler, 1):
        borc   = float(h.get('borc', 0))
        alacak = float(h.get('alacak', 0))
        running += borc - alacak
        tb += borc
        ta += alacak
        rows.append([
            _cell(str(i), "cell", st),
            _cell(str(h.get('tarih', ''))[:10], "cell", st),
            _cell(h.get('fisno', '') or '—', "cell", st),
            _cell(h.get('aciklama', '') or '—', "cell", st),
            _cell(f"{borc:,.2f}" if borc else "—", "cell_r", st),
            _cell(f"{alacak:,.2f}" if alacak else "—", "cell_r", st),
            _cell(f"{running:+,.2f}", "cell_r", st),
        ])

    tbl = Table(header + rows, colWidths=col_widths, repeatRows=1)
    style = _table_style()

    for idx, h in enumerate(hareketler):
        r = idx + 1
        borc   = float(h.get('borc', 0))
        alacak = float(h.get('alacak', 0))
        if borc > 0:
            style.add("BACKGROUND", (0, r), (-1, r), C_RED)
        elif alacak > 0:
            style.add("BACKGROUND", (0, r), (-1, r), C_GREEN)

    tbl.setStyle(style)
    story.append(tbl)

    net = tb - ta
    story.append(Spacer(1, 8))
    if net > 0:
        net_lbl = f"Alacagimiz (Borclu): {net:,.2f} TL"
    elif net < 0:
        net_lbl = f"Borcumuz (Alacakli): {abs(net):,.2f} TL"
    else:
        net_lbl = "Bakiye: 0,00 TL (Sifir)"

    story.append(Paragraph(
        f"<b>Toplam Borc: {tb:,.2f} TL  |  Toplam Alacak: {ta:,.2f} TL  |  {net_lbl}</b>",
        st["bold"]
    ))

    doc.build(story)
    _open_pdf(path)
