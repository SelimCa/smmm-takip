"""
Zirve Net DÖKÜMANLAR/BEYANNAME klasörlerini tarar.
Her mükellef için bulunan PDF'leri:
  1. DB'deki beyanname kaydıyla eşleştirir
  2. Beyanname verildi olarak işaretler (yoksa oluşturur)
  3. PDF verisini DB'ye kaydeder (BLOB)

Dosya adı formatı:
  TÜR_BAŞ_AY_YIL_SON_AY_YIL_KISIM_VERGİNO_VDK_Beyanname.pdf
  Örnek: KDV1_01_2026_01_2026_NİRVANA CAM İNŞ_6311926833_051260_Beyanname.pdf
         KGECICI_01_2024_03_2024_..._Beyanname.pdf
"""

import os
import re
import unicodedata

from db import db

# Zirve TÜR -> bizim TÜR eşleştirmesi
ZİRVE_TUR_MAP = {
    'KDV1':      'KDV1',
    'KDV2':      'KDV2',
    'MUHSGK':    'MUHSGK',
    'KGECICI':   'GECİCİ VERGİ',
    'GECICI':    'GECİCİ VERGİ',
    'KURUMLAR':  'KURUMLAR VERGİSİ',
    'GELIR':     'GELİR VERGİSİ',
    'GELİR':     'GELİR VERGİSİ',
    'DAMGA':     'DAMGA VERGİSİ',
    'MUHTASAR3': 'MUHTASAR 3 AYLIK',
    'GVK67':     'GVK 67',
}

# Üç aylık dönem: başlangıç ayı → dönem no
UC_AYLIK_DONEM = {1: 1, 4: 2, 7: 3, 10: 4}

# Yıllık türler
YILLIK_TURLER = {'KURUMLAR VERGİSİ', 'GELİR VERGİSİ'}

VERGI_NO_RE = re.compile(r'\b(\d{10,11})\b')


def _norm_text(value: str) -> str:
    """Türkçe/özel karakterleri sadeleştirip karşılaştırma için normalize eder."""
    v = unicodedata.normalize('NFKD', value or '')
    v = ''.join(ch for ch in v if not unicodedata.combining(ch))
    return v.upper().replace(' ', '').replace('-', '')


def _map_tur(tur_raw: str):
    """Zirve dosya adındaki türü esnek şekilde bizim türe map eder."""
    t = _norm_text(tur_raw)

    # Önce doğrudan map dene
    direct = ZİRVE_TUR_MAP.get(t)
    if direct:
        return direct

    # Esnek eşleşmeler
    if 'GECICI' in t:
        return 'GECİCİ VERGİ'
    if 'MUHSGK' in t:
        return 'MUHSGK'
    if 'MUHTASAR3' in t or ('MUHTASAR' in t and '3' in t):
        return 'MUHTASAR 3 AYLIK'
    if 'KURUMLAR' in t:
        return 'KURUMLAR VERGİSİ'
    if 'GELIR' in t:
        return 'GELİR VERGİSİ'
    if 'DAMGA' in t:
        return 'DAMGA VERGİSİ'
    if 'GVK67' in t:
        return 'GVK 67'
    if t.startswith('KDV1'):
        return 'KDV1'
    if t.startswith('KDV2'):
        return 'KDV2'

    return None


def _uc_aylik_donem_from_month(ay: int):
    """Ay numarasından 3 aylık dönem no döner (1..4)."""
    if ay in (1, 2, 3):
        return 1
    if ay in (4, 5, 6):
        return 2
    if ay in (7, 8, 9):
        return 3
    if ay in (10, 11, 12):
        return 4
    return None


def _parse_pdf_adi(dosya_adi):
    """
    Dosya adından (tur, yil, donem) çıkarır.
    Başarısızsa None döner.
    """
    # Uzantıyı kaldır
    ad = dosya_adi
    if ad.lower().endswith('.pdf'):
        ad = ad[:-4]

    parts = ad.split('_')
    if len(parts) < 5:
        return None

    tur_zirve = parts[0]
    tur = _map_tur(tur_zirve)
    if tur is None:
        return None

    try:
        bas_ay  = int(parts[1])
        bas_yil = int(parts[2])
        son_ay  = int(parts[3])
        son_yil = int(parts[4])
    except (ValueError, IndexError):
        return None

    # Vergi no/TC no: 10 veya 11 haneli sayıyı dosya adında ara
    vergi_no = None
    for p in parts:
        m = VERGI_NO_RE.fullmatch(p.strip())
        if m:
            vergi_no = m.group(1)
            break

    # Dönem hesapla
    if tur in YILLIK_TURLER:
        # KURUMLAR_01_2025_12_2025 -> beyan yılı = bas_yil
        donem = 1
        yil   = bas_yil
    elif tur == 'GECİCİ VERGİ':
        # Başlangıç/bitiş ayı bazlı dönem tespiti (farklı dosya adlarına toleranslı)
        donem = _uc_aylik_donem_from_month(bas_ay) or _uc_aylik_donem_from_month(son_ay)
        if donem is None:
            return None
        yil = son_yil if donem == 4 and son_ay in (1, 2) else bas_yil
    elif tur == 'MUHTASAR 3 AYLIK':
        donem = _uc_aylik_donem_from_month(bas_ay) or _uc_aylik_donem_from_month(son_ay)
        if donem is None:
            return None
        yil = son_yil if donem == 4 and son_ay in (1, 2) else bas_yil
    else:
        # Aylık türler: dönem = ay numarası
        donem = bas_ay
        yil   = bas_yil

    return {'tur': tur, 'yil': yil, 'donem': donem, 'vergi_no': vergi_no}


def _zirve_klasoru(zirve_yolu, unvan_klasor):
    """Mükellef klasöründeki BEYANNAME dizinini döner."""
    return os.path.join(zirve_yolu, unvan_klasor, 'DÖKÜMANLAR', 'BEYANNAME')


def tara_ve_aktar(progress_cb=None):
    """
    Tüm mükellef klasörlerini tarar.
    progress_cb(mesaj: str) — ilerleme bildirimi (isteğe bağlı)

    Döner: {'eklenen': int, 'guncellenen': int, 'verildi_isaret': int, 'hatalar': list}
    """
    zirve_yolu = db.get_zirve_yolu()
    if not os.path.isdir(zirve_yolu):
        return {'eklenen': 0, 'guncellenen': 0, 'verildi_isaret': 0,
                'hatalar': [f"Zirve klasörü bulunamadı: {zirve_yolu}"]}

    # Mükellef listesini vergi no ile indeksle
    mukellefler = db.get_mukellefler(sadece_aktif=False)
    vno_map = {m['vergi_no']: m for m in mukellefler if m.get('vergi_no')}

    # Mevcut PDF kayıtları
    mevcut_pdfler = db.get_tum_pdf_keyler()

    eklenen   = 0
    guncellenen = 0
    verildi_isaret = 0
    hatalar   = []

    # Zirve klasöründeki tüm alt dizinleri tara
    try:
        klasorler = os.listdir(zirve_yolu)
    except PermissionError as e:
        return {'eklenen': 0, 'guncellenen': 0, 'verildi_isaret': 0, 'hatalar': [str(e)]}

    for klasor_adi in sorted(klasorler):
        beyan_klasor = _zirve_klasoru(zirve_yolu, klasor_adi)
        if not os.path.isdir(beyan_klasor):
            continue

        if progress_cb:
            progress_cb(f"Taranan: {klasor_adi}")

        try:
            pdf_dosyalar = [f for f in os.listdir(beyan_klasor)
                            if f.lower().endswith('.pdf')]
        except PermissionError:
            continue

        for dosya_adi in sorted(pdf_dosyalar):
            parsed = _parse_pdf_adi(dosya_adi)
            if not parsed:
                continue

            vergi_no = parsed.get('vergi_no')
            if not vergi_no:
                # Vergi no bulunamadı — klasör adından eşleştir
                # Klasör adındaki alt çizgileri boşluğa çevir
                klasor_temiz = klasor_adi.replace('_', ' ').strip()
                mukellef = next(
                    (m for m in mukellefler
                     if m['unvan'].upper() == klasor_temiz.upper()),
                    None
                )
            else:
                mukellef = vno_map.get(vergi_no)

            if mukellef is None:
                # DB'de kayıtlı değil, atla
                continue

            mid   = mukellef['id']
            tur   = parsed['tur']
            yil   = parsed['yil']
            donem = parsed['donem']
            anahtar = (mid, tur, yil, donem)

            # PDF dosyasını oku
            dosya_tam = os.path.join(beyan_klasor, dosya_adi)
            try:
                with open(dosya_tam, 'rb') as f:
                    pdf_bytes = f.read()
            except Exception as e:
                hatalar.append(f"{dosya_adi}: {e}")
                continue

            # DB'ye kaydet
            if anahtar in mevcut_pdfler:
                guncellenen += 1
            else:
                eklenen += 1
                mevcut_pdfler.add(anahtar)

            db.save_beyanname_pdf(mid, tur, yil, donem, dosya_adi, pdf_bytes)

            # Beyanname kaydını verildi olarak işaretle
            mevcut = db.get_beyanname(mid, tur, yil, donem)
            if mevcut is None:
                # Kayıt yoksa oluştur
                from db import beyanname_son_gun
                son_gun = beyanname_son_gun(tur, yil, donem)
                db.upsert_beyanname(mid, tur, yil, donem, {
                    'verildi':        1,
                    'verilme_tarihi': None,
                    'son_gun':        son_gun,
                    'odendi':         0,
                    'odeme_tipi':     None,
                    'odeme_tarihi':   None,
                    'tutar':          0.0,
                    'aciklama':       'Zirve taramasından',
                    'atlandi':        0,
                })
                verildi_isaret += 1
            elif not mevcut.get('verildi'):
                db.upsert_beyanname(mid, tur, yil, donem, {
                    **mevcut,
                    'verildi':        1,
                    'verilme_tarihi': mevcut.get('verilme_tarihi'),
                    'aciklama':       mevcut.get('aciklama') or 'Zirve taramasından',
                })
                verildi_isaret += 1

    return {
        'eklenen':        eklenen,
        'guncellenen':    guncellenen,
        'verildi_isaret': verildi_isaret,
        'hatalar':        hatalar,
    }
