"""
Zirve Net veri klasoeründen mükellef listesini ve beyanname türlerini okur.

Her mükellef klasörü altındaki SirketBilgileri.ini dosyasından:
  - Ünvan, vergi/TC no, mükellef tipi
  - Beyanname türleri (kdv1eh, kdv2eh, gmuhgeh, geceh, kureh, geveh)
"""

import os
import re
from db import db

YIL_RE = re.compile(r'^\d{4}$')

# SirketBilgileri.ini -> uygulama alanı eşleştirmesi
# Sıralı liste: ilk bulunan kullanılır
BEYAN_KEY_MAP = {
    'kdv1':             ('kdv1eh',),
    # kdv2 Zirve'den otomatik aktarılmaz — kullanıcı manuel seçer
    'muhsgk':           ('gmuhgeh', 'muheh'),
    'gecici_vergi':     ('geceh',),
    'kurumlar_vergisi': ('kureh',),
    'gelir_vergisi':    ('geveh',),
    # Yeni türler
    'damga_vergisi':    ('dmpeh', 'damgaeh'),          # Damga Vergisi
    'muhtasar_3aylik':  ('muh3eh', 'muhtasar3eh'),     # 3 Aylık Muhtasar
    'gvk_67':           ('g67eh', 'gvk67eh'),          # GVK Geçici 67
}


def _parse_ini_ilk_bolum(dosya_yolu):
    """
    SirketBilgileri.ini okur. Aynı anahtar birden fazla bölümde
    tekrarlanabilir; yalnızca ilk geçen değeri alır.
    """
    sonuc = {}
    if not os.path.isfile(dosya_yolu):
        return sonuc
    for enc in ('utf-8', 'windows-1254', 'cp1252', 'latin-1'):
        try:
            with open(dosya_yolu, 'r', encoding=enc, errors='strict') as f:
                icerik = f.read()
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        return sonuc

    for satir in icerik.splitlines():
        satir = satir.strip()
        if satir.startswith('[') or not satir or '=' not in satir:
            continue
        anahtar, _, deger = satir.partition('=')
        anahtar = anahtar.strip().lower()
        if anahtar not in sonuc:
            sonuc[anahtar] = deger.strip()
    return sonuc


def _e_mi(deger):
    return str(deger).upper() in ('E', 'EVET', '1', 'TRUE', '-1')


def _is_mukellef_folder(klasor_yolu):
    try:
        icerik = os.listdir(klasor_yolu)
    except PermissionError:
        return False
    for item in icerik:
        if YIL_RE.match(item):
            return True
        if item.upper() == 'GENEL.MDF':
            return True
        if item.lower() == 'sirketbilgileri.ini':
            return True
    return False


def _klasor_adi_temizle(ad):
    ad = ad.replace('_', ' ').strip()
    ad = re.sub(r'\s+', ' ', ad).strip(' -')
    return ad


def _vergi_no(ini):
    for anahtar in ('vergino', 'vatno', 'edit3'):
        v = ini.get(anahtar, '').strip()
        v_temiz = re.sub(r'\D', '', v)
        if len(v_temiz) >= 10:
            return v_temiz
    return ''


def _mukellef_tipi(ini):
    tur = ini.get('mukellefturu', ini.get('mukellefluru', '0')).strip()
    return 'gercek' if tur == '0' else 'tuzel'


def _telefon(ini):
    alan = re.sub(r'\D', '', ini.get('alankodu', ''))
    tel  = re.sub(r'\D', '', ini.get('tel', ''))
    if alan and tel:
        return f"0{alan}{tel}"
    if tel:
        return tel
    return ''


def _ek_bilgiler(ini):
    """Zirve'den çekilebilen ek firma bilgilerini döner."""
    return {
        'email':         ini.get('email', '').strip(),
        'adres':         ini.get('adres', '').strip(),
        'sehir':         ini.get('sehir', '').strip(),
        'vergi_dairesi': ini.get('vergidairesi', '').strip(),
        'yetkili':       ini.get('yetkili', '').strip(),
        'yetkili_tc':    re.sub(r'\D', '', ini.get('tcno', '')),
        'mersis_no':     re.sub(r'\D', '', ini.get('mersisno', '')),
        'ssk_sicil':     ini.get('sssn', '').strip(),
        'faaliyet_kodu': ini.get('fakod', '').strip(),
    }


def _beyanname_turleri(ini):
    sonuc = {}
    for alan, anahtarlar in BEYAN_KEY_MAP.items():
        for a in anahtarlar:
            deger = ini.get(a.lower())
            if deger is not None:
                sonuc[alan] = int(_e_mi(deger))
                break
        else:
            sonuc[alan] = 0
    return sonuc


def zirve_mukellef_listesi(yol=None):
    """
    Zirve data klasöründeki mükellef klasörlerini tarar.
    Her mükellef için SirketBilgileri.ini okunur.
    """
    if yol is None:
        yol = db.get_zirve_yolu()
    if not os.path.isdir(yol):
        return []
    try:
        icerik = os.listdir(yol)
    except PermissionError:
        return []

    sonuc = []
    for item in icerik:
        tam_yol = os.path.join(yol, item)
        if not os.path.isdir(tam_yol):
            continue
        if not _is_mukellef_folder(tam_yol):
            continue

        ini_yolu = os.path.join(tam_yol, 'SirketBilgileri.ini')
        ini = _parse_ini_ilk_bolum(ini_yolu)

        unvan = _klasor_adi_temizle(item)
        beyanlar = _beyanname_turleri(ini)
        ekler = _ek_bilgiler(ini)

        sonuc.append({
            'unvan':        unvan,
            'klasor_adi':   item,
            'tam_yol':      tam_yol,
            'vergi_no':     _vergi_no(ini),
            'tip':          _mukellef_tipi(ini),
            'telefon':      _telefon(ini),
            **ekler,
            **beyanlar,
        })

    return sorted(sonuc, key=lambda x: x['unvan'])


def zirve_iceri_aktar(yol=None):
    """
    Zirve'den okunan mükellefleri veritabanına ekler/günceller.
    Vergi no + beyanname türleri ini'den otomatik doldurulur.
    """
    mukellefler = zirve_mukellef_listesi(yol)

    tum_db = db.get_mukellefler(sadece_aktif=False)
    mevcut_vno = {m['vergi_no']: m for m in tum_db if m.get('vergi_no')}
    mevcut_unvan = {m['unvan'].upper(): m for m in tum_db}

    eklenen = 0
    guncellenen = 0
    hatalar = []

    for m in mukellefler:
        vergi_no = m['vergi_no']
        if not vergi_no:
            vergi_no = str(abs(hash(m['klasor_adi'])) % 10_000_000_000).zfill(10)

        kayit = mevcut_vno.get(vergi_no) or mevcut_unvan.get(m['unvan'].upper())

        veri = {
            'vergi_no':          vergi_no,
            'unvan':             m['unvan'],
            'tip':               m['tip'],
            'telefon':           m.get('telefon', ''),
            'email':             m.get('email', ''),
            'adres':             m.get('adres', ''),
            'sehir':             m.get('sehir', ''),
            'vergi_dairesi':     m.get('vergi_dairesi', ''),
            'yetkili':           m.get('yetkili', ''),
            'yetkili_tc':        m.get('yetkili_tc', ''),
            'mersis_no':         m.get('mersis_no', ''),
            'ssk_sicil':         m.get('ssk_sicil', ''),
            'faaliyet_kodu':     m.get('faaliyet_kodu', ''),
            'kdv1':              m['kdv1'],
            'kdv2':              kayit.get('kdv2', 0) if kayit else 0,  # manuel seçilir, Zirve'den aktarılmaz
            'muhsgk':            m['muhsgk'],
            'gecici_vergi':      m['gecici_vergi'],
            'kurumlar_vergisi':  m['kurumlar_vergisi'],
            'gelir_vergisi':     m['gelir_vergisi'],
            'muhtasar_3aylik':   m.get('muhtasar_3aylik', 0),
            'damga_vergisi':     m.get('damga_vergisi', 0),
            'gvk_67':            m.get('gvk_67', 0),
            'aylik_ucret':       kayit.get('aylik_ucret', 0.0) if kayit else 0.0,
            'yillik_ucret':      kayit.get('yillik_ucret', 0.0) if kayit else 0.0,
        }

        try:
            if kayit:
                db.update_mukellef(kayit['id'], {**kayit, **veri})
                guncellenen += 1
            else:
                db.add_mukellef(veri)
                eklenen += 1
        except Exception as e:
            hatalar.append(f"{m['unvan']}: {e}")

    return {
        'eklenen':     eklenen,
        'guncellenen': guncellenen,
        'hatalar':     hatalar,
    }
