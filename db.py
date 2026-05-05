import sqlite3
import os
import shutil
import calendar
from datetime import date, datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Exe olarak paketlendiyse (PyInstaller) veriler AppData\Roaming\SMMM Takip içine yazılır,
# geliştirme ortamında proje klasörü altındaki data/ kullanılır.
import sys as _sys
if getattr(_sys, 'frozen', False):
    # Kurulu uygulama — kullanıcının AppData klasörüne yaz
    _APPDATA = os.environ.get('APPDATA', os.path.expanduser('~'))
    DATA_DIR = os.path.join(_APPDATA, 'SMMM Takip', 'data')
else:
    # Geliştirme — proje klasörü
    DATA_DIR = os.path.join(APP_DIR, 'data')

DB_FILE = os.path.join(DATA_DIR, 'smmm_data.db')
LEGACY_DB_FILE = os.path.join(APP_DIR, 'smmm_data.db')

AYLAR = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


# Aylık beyan türleri
AYLIK_TURLER = ('KDV1', 'KDV2', 'MUHSGK', 'DAMGA VERGİSİ', 'GVK 67')
# 3 aylık dönem türleri
UC_AYLIK_TURLER = ('GECİCİ VERGİ', 'MUHTASAR 3 AYLIK')
# Yıllık türler
YILLIK_TURLER = ('KURUMLAR VERGİSİ', 'GELİR VERGİSİ')

UC_AYLIK_DONEM_LABEL = {
    1: '1.Dönem (Oca-Mar)',
    2: '2.Dönem (Nis-Haz)',
    3: '3.Dönem (Tem-Eyl)',
    4: '4.Dönem (Eki-Ara)',
}


def _son_gun(yil, ay, gun):
    """Verilen yıl/ay/gün için son günü döner. Gün o ayda yoksa ay sonu alınır."""
    max_gun = calendar.monthrange(yil, ay)[1]
    return date(yil, ay, min(gun, max_gun)).isoformat()


def _ay_son_gunu(yil, ay):
    return date(yil, ay, calendar.monthrange(yil, ay)[1]).isoformat()


def beyanname_son_gun(tur, b_yil, b_donem):
    """
    Beyanname türüne ve döneme göre son verilme/ödeme gününü hesaplar.

    Kaynaklar (verginet.net):
      KDV1           → izleyen ay 28
      KDV2           → izleyen ay 25
      MUHSGK         → izleyen ay 26
      DAMGA VERGİSİ  → izleyen ay 26
      GVK 67         → izleyen ay 26
      GECİCİ VERGİ   → dönem sonunu izleyen 2. ayın 17'si
                       (Q1→17 Mayıs, Q2→17 Ağustos, Q3→17 Kasım, Q4→17 Şubat+1)
      MUHTASAR 3AY   → 26 Nisan / 26 Temmuz / 26 Ekim / 26 Ocak
      KURUMLAR       → Nisan ayı son günü (beyan yılı)
      GELİR VERGİSİ  → Mart ayı son günü (beyan yılı)
    """
    try:
        if tur == 'KDV1':
            # b_donem = ay numarası, b_yil = yıl
            # izleyen ay
            if b_donem == 12:
                return _son_gun(b_yil + 1, 1, 28)
            return _son_gun(b_yil, b_donem + 1, 28)

        elif tur == 'KDV2':
            if b_donem == 12:
                return _son_gun(b_yil + 1, 1, 25)
            return _son_gun(b_yil, b_donem + 1, 25)

        elif tur in ('MUHSGK', 'DAMGA VERGİSİ', 'GVK 67'):
            if b_donem == 12:
                return _son_gun(b_yil + 1, 1, 26)
            return _son_gun(b_yil, b_donem + 1, 26)

        elif tur == 'GECİCİ VERGİ':
            # b_donem: 1=Q1(Oca-Mar), 2=Q2(Nis-Haz), 3=Q3(Tem-Eyl), 4=Q4(Eki-Ara)
            if b_donem == 1:   return _son_gun(b_yil, 5, 17)       # 17 Mayıs
            elif b_donem == 2: return _son_gun(b_yil, 8, 17)       # 17 Ağustos
            elif b_donem == 3: return _son_gun(b_yil, 11, 17)      # 17 Kasım
            elif b_donem == 4: return _son_gun(b_yil + 1, 2, 17)   # 17 Şubat sonraki yıl

        elif tur == 'MUHTASAR 3 AYLIK':
            if b_donem == 1:   return _son_gun(b_yil, 4, 26)       # 26 Nisan
            elif b_donem == 2: return _son_gun(b_yil, 7, 26)       # 26 Temmuz
            elif b_donem == 3: return _son_gun(b_yil, 10, 26)      # 26 Ekim
            elif b_donem == 4: return _son_gun(b_yil + 1, 1, 26)   # 26 Ocak sonraki yıl

        elif tur == 'KURUMLAR VERGİSİ':
            # b_yil = vergilendirme yılı, beyan bir sonraki yıl Nisan'da
            return _ay_son_gunu(b_yil + 1, 4)  # Nisan sonu

        elif tur == 'GELİR VERGİSİ':
            return _ay_son_gunu(b_yil + 1, 3)  # Mart sonu

    except Exception:
        pass

    # Özel beyanname türü olabilir — DB'den kontrol et
    return _ozel_tur_son_gun(tur, b_yil, b_donem)


def _ozel_tur_son_gun(tur_ad, b_yil, b_donem):
    """Özel beyanname türü için son günü DB'den okuyarak hesaplar."""
    try:
        row = db._conn.execute(
            "SELECT periyot, son_gun_gunu FROM ozel_beyanname_turleri WHERE ad=?",
            (tur_ad,)).fetchone()
        if not row:
            return None
        periyot, gun = row[0], int(row[1])
        if periyot == 'aylik':
            if b_donem == 12:
                return _son_gun(b_yil + 1, 1, gun)
            return _son_gun(b_yil, b_donem + 1, gun)
        elif periyot == '3aylik':
            ay_map = {1: 4, 2: 7, 3: 10, 4: 1}
            yil_map = {1: b_yil, 2: b_yil, 3: b_yil, 4: b_yil + 1}
            return _son_gun(yil_map.get(b_donem, b_yil), ay_map.get(b_donem, 4), gun)
        elif periyot == 'yillik':
            return _ay_son_gunu(b_yil + 1, gun)  # gun = ay numarası burada
    except Exception:
        pass
    return None


def donem_label(tur, yil, donem):
    if tur in AYLIK_TURLER:
        return f"{AYLAR[donem]} {yil}"
    elif tur in UC_AYLIK_TURLER:
        return f"{UC_AYLIK_DONEM_LABEL.get(donem, str(donem))} {yil}"
    else:
        return str(yil)


def _prepare_db_path(path):
    """DB klasörünü hazırlar, eski konumdaki db'yi yeni konuma taşır."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if path == DB_FILE and not os.path.exists(path) and os.path.exists(LEGACY_DB_FILE):
        try:
            os.replace(LEGACY_DB_FILE, path)
        except Exception:
            # Taşıma başarısızsa kopyalayarak devam et.
            shutil.copy2(LEGACY_DB_FILE, path)

    # Eski kök klasördeki dosyayı temizle (artık data klasörü kullanılıyor)
    if path == DB_FILE and os.path.exists(LEGACY_DB_FILE):
        try:
            os.remove(LEGACY_DB_FILE)
        except Exception:
            pass  # Uygulama açıksa kilitlidir, sonraki açılışta silinir


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    def connect(self, db_file=None):
        path = db_file or DB_FILE
        _prepare_db_path(path)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._create_tables()
        return True, "Bağlantı başarılı"

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS ayarlar (
                anahtar TEXT PRIMARY KEY,
                deger   TEXT
            );

            CREATE TABLE IF NOT EXISTS mukellefler (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                vergi_no        TEXT UNIQUE NOT NULL,
                unvan           TEXT NOT NULL,
                tip             TEXT NOT NULL DEFAULT 'gercek',
                telefon         TEXT DEFAULT '',
                email           TEXT DEFAULT '',
                adres           TEXT DEFAULT '',
                sehir               TEXT DEFAULT '',
                vergi_dairesi       TEXT DEFAULT '',
                yetkili             TEXT DEFAULT '',
                yetkili_tc          TEXT DEFAULT '',
                mersis_no           TEXT DEFAULT '',
                ssk_sicil           TEXT DEFAULT '',
                faaliyet_kodu       TEXT DEFAULT '',
                kdv1                INTEGER DEFAULT 0,
                kdv2                INTEGER DEFAULT 0,
                muhsgk              INTEGER DEFAULT 0,
                gecici_vergi        INTEGER DEFAULT 0,
                kurumlar_vergisi    INTEGER DEFAULT 0,
                gelir_vergisi       INTEGER DEFAULT 0,
                muhtasar_3aylik     INTEGER DEFAULT 0,
                damga_vergisi       INTEGER DEFAULT 0,
                gvk_67              INTEGER DEFAULT 0,
                aylik_ucret         REAL DEFAULT 0,
                yillik_ucret        REAL DEFAULT 0,
                aktif               INTEGER DEFAULT 1,
                kayit_tarihi        TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS beyannameler (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                mukellef_id     INTEGER NOT NULL,
                tur             TEXT NOT NULL,
                yil             INTEGER NOT NULL,
                donem           INTEGER NOT NULL,
                verildi         INTEGER DEFAULT 0,
                verilme_tarihi  TEXT,
                son_gun         TEXT,
                odendi          INTEGER DEFAULT 0,
                odeme_tarihi    TEXT,
                odeme_tipi      TEXT DEFAULT NULL,
                tutar           REAL DEFAULT 0.0,
                aciklama        TEXT DEFAULT '',
                atlandi         INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now')),
                UNIQUE (mukellef_id, tur, yil, donem),
                FOREIGN KEY (mukellef_id) REFERENCES mukellefler(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cari_hareketler (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                mukellef_id INTEGER NOT NULL,
                tarih       TEXT NOT NULL,
                aciklama    TEXT NOT NULL,
                borc        REAL DEFAULT 0.0,
                alacak      REAL DEFAULT 0.0,
                fisno       TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (mukellef_id) REFERENCES mukellefler(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS beyanname_pdfler (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                mukellef_id     INTEGER NOT NULL,
                tur             TEXT NOT NULL,
                yil             INTEGER NOT NULL,
                donem           INTEGER NOT NULL,
                dosya_adi       TEXT NOT NULL,
                pdf_data        BLOB NOT NULL,
                kaydedilme      TEXT DEFAULT (datetime('now')),
                UNIQUE(mukellef_id, tur, yil, donem),
                FOREIGN KEY (mukellef_id) REFERENCES mukellefler(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ozel_beyanname_turleri (
                ad          TEXT PRIMARY KEY,
                periyot     TEXT NOT NULL DEFAULT 'aylik',
                son_gun_gunu INTEGER NOT NULL DEFAULT 26
            );

            CREATE TABLE IF NOT EXISTS mukellef_ozel_beyanlar (
                mukellef_id INTEGER NOT NULL,
                tur_ad      TEXT NOT NULL,
                PRIMARY KEY (mukellef_id, tur_ad),
                FOREIGN KEY (mukellef_id) REFERENCES mukellefler(id) ON DELETE CASCADE
            );
        """)
        self._conn.commit()
        self._migrate()

    def _migrate(self):
        """Mevcut veritabanına yeni sütunlar ekler (idempotent)."""
        yeni_kolonlar = [
            ('mukellefler', 'muhtasar_3aylik',  'INTEGER DEFAULT 0'),
            ('mukellefler', 'damga_vergisi',    'INTEGER DEFAULT 0'),
            ('mukellefler', 'gvk_67',           'INTEGER DEFAULT 0'),
            ('mukellefler', 'aylik_ucret',      'REAL DEFAULT 0'),
            ('mukellefler', 'yillik_ucret',     'REAL DEFAULT 0'),
            ('mukellefler', 'sehir',            "TEXT DEFAULT ''"),
            ('mukellefler', 'vergi_dairesi',    "TEXT DEFAULT ''"),
            ('mukellefler', 'yetkili',          "TEXT DEFAULT ''"),
            ('mukellefler', 'yetkili_tc',       "TEXT DEFAULT ''"),
            ('mukellefler', 'mersis_no',        "TEXT DEFAULT ''"),
            ('mukellefler', 'ssk_sicil',        "TEXT DEFAULT ''"),
            ('mukellefler', 'faaliyet_kodu',    "TEXT DEFAULT ''"),
            ('beyannameler', 'odeme_tipi',      'TEXT DEFAULT NULL'),
            ('beyannameler', 'atlandi',         'INTEGER DEFAULT 0'),
        ]
        for tablo, kolon, tip in yeni_kolonlar:
            try:
                self._conn.execute(f'ALTER TABLE {tablo} ADD COLUMN {kolon} {tip}')
                self._conn.commit()
            except Exception:
                pass  # Kolon zaten var

    def _rows(self, cursor):
        return [dict(r) for r in cursor.fetchall()]

    def _row(self, cursor):
        r = cursor.fetchone()
        return dict(r) if r else None

    # ══════════════ AYARLAR ══════════════

    ZIRVE_YOLU_KEY = "zirve_veri_yolu"
    ZIRVE_YOLU_DEFAULT = r"C:\zirvenetfinansman\zirvedata"

    def get_ayar(self, anahtar, varsayilan=""):
        r = self._row(self._conn.execute(
            "SELECT deger FROM ayarlar WHERE anahtar=?", (anahtar,)))
        return r['deger'] if r else varsayilan

    def set_ayar(self, anahtar, deger):
        self._conn.execute(
            "INSERT INTO ayarlar(anahtar,deger) VALUES(?,?) "
            "ON CONFLICT(anahtar) DO UPDATE SET deger=excluded.deger",
            (anahtar, str(deger)))
        self._conn.commit()

    def get_zirve_yolu(self):
        return self.get_ayar(self.ZIRVE_YOLU_KEY, self.ZIRVE_YOLU_DEFAULT)

    def set_zirve_yolu(self, yol):
        self.set_ayar(self.ZIRVE_YOLU_KEY, yol)

    # ══════════════ MÜKELLEF ══════════════

    def get_mukellefler(self, sadece_aktif=True):
        q = "SELECT * FROM mukellefler"
        if sadece_aktif:
            q += " WHERE aktif=1"
        q += " ORDER BY unvan COLLATE NOCASE"
        return self._rows(self._conn.execute(q))

    def get_mukellef(self, mid):
        return self._row(self._conn.execute("SELECT * FROM mukellefler WHERE id=?", (mid,)))

    def add_mukellef(self, d):
        c = self._conn.execute(
            """INSERT INTO mukellefler
               (vergi_no,unvan,tip,telefon,email,adres,sehir,vergi_dairesi,
                yetkili,yetkili_tc,mersis_no,ssk_sicil,faaliyet_kodu,
                kdv1,kdv2,muhsgk,gecici_vergi,kurumlar_vergisi,gelir_vergisi,
                muhtasar_3aylik,damga_vergisi,gvk_67,aylik_ucret,yillik_ucret)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d['vergi_no'], d['unvan'], d.get('tip', 'gercek'),
             d.get('telefon', ''), d.get('email', ''), d.get('adres', ''),
             d.get('sehir', ''), d.get('vergi_dairesi', ''),
             d.get('yetkili', ''), d.get('yetkili_tc', ''),
             d.get('mersis_no', ''), d.get('ssk_sicil', ''), d.get('faaliyet_kodu', ''),
             int(d.get('kdv1', 0)), int(d.get('kdv2', 0)), int(d.get('muhsgk', 0)),
             int(d.get('gecici_vergi', 0)), int(d.get('kurumlar_vergisi', 0)),
             int(d.get('gelir_vergisi', 0)),
             int(d.get('muhtasar_3aylik', 0)), int(d.get('damga_vergisi', 0)),
             int(d.get('gvk_67', 0)),
             float(d.get('aylik_ucret', 0)), float(d.get('yillik_ucret', 0))))
        self._conn.commit()
        return c.lastrowid

    def update_mukellef(self, mid, d):
        self._conn.execute(
            """UPDATE mukellefler SET
               vergi_no=?,unvan=?,tip=?,telefon=?,email=?,adres=?,sehir=?,vergi_dairesi=?,
               yetkili=?,yetkili_tc=?,mersis_no=?,ssk_sicil=?,faaliyet_kodu=?,
               kdv1=?,kdv2=?,muhsgk=?,gecici_vergi=?,kurumlar_vergisi=?,gelir_vergisi=?,
               muhtasar_3aylik=?,damga_vergisi=?,gvk_67=?,aylik_ucret=?,yillik_ucret=?,
               kayit_tarihi=COALESCE(?, kayit_tarihi)
               WHERE id=?""",
            (d['vergi_no'], d['unvan'], d.get('tip', 'gercek'),
             d.get('telefon', ''), d.get('email', ''), d.get('adres', ''),
             d.get('sehir', ''), d.get('vergi_dairesi', ''),
             d.get('yetkili', ''), d.get('yetkili_tc', ''),
             d.get('mersis_no', ''), d.get('ssk_sicil', ''), d.get('faaliyet_kodu', ''),
             int(d.get('kdv1', 0)), int(d.get('kdv2', 0)), int(d.get('muhsgk', 0)),
             int(d.get('gecici_vergi', 0)), int(d.get('kurumlar_vergisi', 0)),
             int(d.get('gelir_vergisi', 0)),
             int(d.get('muhtasar_3aylik', 0)), int(d.get('damga_vergisi', 0)),
             int(d.get('gvk_67', 0)),
             float(d.get('aylik_ucret', 0)), float(d.get('yillik_ucret', 0)),
             d.get('kayit_tarihi') or None,
             mid))
        self._conn.commit()

    def set_mukellef_aktif(self, mid, aktif):
        self._conn.execute("UPDATE mukellefler SET aktif=? WHERE id=?", (int(aktif), mid))
        self._conn.commit()

    # ══════════════ BEYANNAME ══════════════

    def get_beyanname(self, mukellef_id, tur, yil, donem):
        return self._row(self._conn.execute(
            "SELECT * FROM beyannameler WHERE mukellef_id=? AND tur=? AND yil=? AND donem=?",
            (mukellef_id, tur, yil, donem)))

    def upsert_beyanname(self, mukellef_id, tur, yil, donem, data):
        self._conn.execute(
            """INSERT INTO beyannameler
               (mukellef_id,tur,yil,donem,verildi,verilme_tarihi,
                son_gun,odendi,odeme_tarihi,odeme_tipi,tutar,aciklama,atlandi)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(mukellef_id,tur,yil,donem) DO UPDATE SET
               verildi=excluded.verildi,
               verilme_tarihi=excluded.verilme_tarihi,
               son_gun=excluded.son_gun,
               odendi=excluded.odendi,
               odeme_tarihi=excluded.odeme_tarihi,
               odeme_tipi=excluded.odeme_tipi,
               tutar=excluded.tutar,
               aciklama=excluded.aciklama,
               atlandi=excluded.atlandi""",
            (mukellef_id, tur, yil, donem,
             int(data.get('verildi', 0)),
             data.get('verilme_tarihi') or None,
             data.get('son_gun') or None,
             int(data.get('odendi', 0)),
             data.get('odeme_tarihi') or None,
             data.get('odeme_tipi') or None,
             float(data.get('tutar', 0)),
             data.get('aciklama', ''),
             int(data.get('atlandi', 0))))
        self._conn.commit()

    def _declarations_for_month(self, m, yil, ay):
        """Verilen mükellefi için o ayda beklenen beyanname listesi → [(tur, yil, donem)]"""
        res = []
        # ── Aylık beyannameler ──
        if m.get('kdv1'):           res.append(('KDV1', yil, ay))
        if m.get('kdv2'):           res.append(('KDV2', yil, ay))
        if m.get('muhsgk'):         res.append(('MUHSGK', yil, ay))
        if m.get('damga_vergisi'):  res.append(('DAMGA VERGİSİ', yil, ay))
        if m.get('gvk_67'):         res.append(('GVK 67', yil, ay))

        # ── Geçici Vergi: 4 dönem (2025'ten itibaren) ──
        # Son gün: 17 Mayıs / 17 Ağustos / 17 Kasım / 17 Şubat
        if m.get('gecici_vergi'):
            if ay == 5:   res.append(('GECİCİ VERGİ', yil, 1))
            elif ay == 8: res.append(('GECİCİ VERGİ', yil, 2))
            elif ay == 11:res.append(('GECİCİ VERGİ', yil, 3))
            elif ay == 2: res.append(('GECİCİ VERGİ', yil - 1, 4))  # 4. dönem = önceki yıl Q4

        # ── 3 Aylık Muhtasar: 4 dönem ──
        # Son gün: 26 Nisan / 26 Temmuz / 26 Ekim / 26 Ocak
        if m.get('muhtasar_3aylik'):
            if ay == 4:   res.append(('MUHTASAR 3 AYLIK', yil, 1))
            elif ay == 7: res.append(('MUHTASAR 3 AYLIK', yil, 2))
            elif ay == 10:res.append(('MUHTASAR 3 AYLIK', yil, 3))
            elif ay == 1: res.append(('MUHTASAR 3 AYLIK', yil - 1, 4))  # önceki yıl Q4

        # ── Yıllık beyannameler ──
        # Kurumlar Vergisi → Nisan(4), bir önceki yıl için
        if m.get('kurumlar_vergisi') and ay == 4:
            res.append(('KURUMLAR VERGİSİ', yil - 1, 12))
        # Gelir Vergisi → Mart(3), bir önceki yıl için
        if m.get('gelir_vergisi') and ay == 3:
            res.append(('GELİR VERGİSİ', yil - 1, 12))

        # ── Özel beyanname türleri ──
        ozel = self.get_mukellef_ozel_beyanlar(m['id'])
        for ot in ozel:
            tur_ad  = ot['tur_ad']
            periyot = ot['periyot']
            if periyot == 'aylik':
                res.append((tur_ad, yil, ay))
            elif periyot == '3aylik':
                if ay == 4:   res.append((tur_ad, yil, 1))
                elif ay == 7: res.append((tur_ad, yil, 2))
                elif ay == 10:res.append((tur_ad, yil, 3))
                elif ay == 1: res.append((tur_ad, yil - 1, 4))
            elif periyot == 'yillik':
                if ay == 4:
                    res.append((tur_ad, yil - 1, 12))

        return res

    def get_ay_beyannameleri(self, yil, ay):
        """Belirtilen ay için tüm aktif mükelleflerin beklenen beyannameleri"""
        mukellefler = self.get_mukellefler()
        result = []
        for m in mukellefler:
            for tur, b_yil, b_donem in self._declarations_for_month(m, yil, ay):
                existing = self.get_beyanname(m['id'], tur, b_yil, b_donem)
                if existing:
                    row = dict(existing)
                    # son_gun boşsa otomatik hesapla
                    if not row.get('son_gun'):
                        row['son_gun'] = beyanname_son_gun(tur, b_yil, b_donem)
                else:
                    sg = beyanname_son_gun(tur, b_yil, b_donem)
                    row = {
                        'id': None,
                        'mukellef_id': m['id'],
                        'tur': tur,
                        'yil': b_yil,
                        'donem': b_donem,
                        'verildi': 0,
                        'verilme_tarihi': None,
                        'son_gun': sg,
                        'odendi': 0,
                        'odeme_tarihi': None,
                        'odeme_tipi': None,
                        'tutar': 0.0,
                        'aciklama': '',
                        'atlandi': 0,
                    }
                row['unvan'] = m['unvan']
                row['vergi_no'] = m['vergi_no']
                result.append(row)
        return result

    def get_dashboard_stats(self, yil, ay):
        # Aktif mükellef sayısı
        c = self._conn.execute("SELECT COUNT(*) FROM mukellefler WHERE aktif=1")
        mukellef_sayisi = c.fetchone()[0]

        beyanlar = self.get_ay_beyannameleri(yil, ay)
        toplam = len(beyanlar)
        verildi = sum(1 for b in beyanlar if b['verildi'])

        # Bakiye toplamları
        c = self._conn.execute(
            "SELECT COALESCE(SUM(borc),0), COALESCE(SUM(alacak),0) FROM cari_hareketler")
        r = c.fetchone()
        return {
            'mukellef_sayisi': mukellef_sayisi,
            'beyan_toplam': toplam,
            'beyan_verildi': verildi,
            'beyan_verilmedi': toplam - verildi,
            'toplam_borc': float(r[0]),
            'toplam_alacak': float(r[1]),
        }

    # ══════════════ CARİ HESAP ══════════════

    def get_cari(self, mukellef_id):
        return self._rows(self._conn.execute(
            "SELECT * FROM cari_hareketler WHERE mukellef_id=? ORDER BY tarih ASC, id ASC",
            (mukellef_id,)))

    def add_cari(self, mukellef_id, tarih, aciklama, borc, alacak, fisno=''):
        self._conn.execute(
            """INSERT INTO cari_hareketler
               (mukellef_id,tarih,aciklama,borc,alacak,fisno)
               VALUES(?,?,?,?,?,?)""",
            (mukellef_id, tarih, aciklama, float(borc), float(alacak), fisno))
        self._conn.commit()

    def muhasebe_cariye_aktar(self, mukellef_id, yil, baslangic_ay=1):
        """Mükellef için belirtilen yılda aylık muhasebe bedeli fişleri oluşturur (idempotent).
        Döner: (eklenen_adet, atlanan_adet)
        """
        m = self.get_mukellef(mukellef_id)
        if not m:
            return 0, 0
        aylik = float(m.get('aylik_ucret') or 0)
        if aylik <= 0:
            return 0, 0
        eklenen = 0
        atlanan = 0
        for ay in range(baslangic_ay, 13):
            fisno = f"MUHSB-{mukellef_id}-{yil}-{ay:02d}"
            mevcut = self._row(self._conn.execute(
                "SELECT id FROM cari_hareketler WHERE mukellef_id=? AND fisno=?",
                (mukellef_id, fisno)))
            if mevcut:
                atlanan += 1
                continue
            tarih = f"{yil}-{ay:02d}-01"
            aciklama = f"{AYLAR[ay]} {yil} muhasebe bedeli"
            self.add_cari(mukellef_id, tarih, aciklama, aylik, 0.0, fisno)
            eklenen += 1
        return eklenen, atlanan

    def count_muhasebe_fisler(self, mukellef_id, yil):
        """Belirtilen yıl için kaç aylık muhasebe fişi zaten mevcut."""
        c = self._conn.execute(
            "SELECT COUNT(*) FROM cari_hareketler WHERE mukellef_id=? AND fisno LIKE ?",
            (mukellef_id, f"MUHSB-{mukellef_id}-{yil}-%"))
        return c.fetchone()[0]

    def yeni_yil_ac(self, mevcut_yil, yeni_yil):
        """Her aktif mükellef için mevcut yılın net bakiyesini yeni yıla devir fişi olarak ekler.
        Döner: eklenen_adet
        """
        mukellefler = self.get_mukellefler()
        eklenen = 0
        for m in mukellefler:
            fisno = f"DEVIR-{m['id']}-{yeni_yil}"
            mevcut = self._row(self._conn.execute(
                "SELECT id FROM cari_hareketler WHERE mukellef_id=? AND fisno=?",
                (m['id'], fisno)))
            if mevcut:
                continue
            bakiye = self.get_bakiye(m['id'])
            if bakiye == 0:
                continue
            tarih = f"{yeni_yil}-01-01"
            aciklama = f"{mevcut_yil}'dan devir"
            if bakiye > 0:  # borç bakiyesi → devir borç
                self.add_cari(m['id'], tarih, aciklama, bakiye, 0.0, fisno)
            else:  # alacak bakiyesi → devir alacak
                self.add_cari(m['id'], tarih, aciklama, 0.0, abs(bakiye), fisno)
            eklenen += 1
        return eklenen

    def delete_cari(self, hareket_id):
        self._conn.execute("DELETE FROM cari_hareketler WHERE id=?", (hareket_id,))
        self._conn.commit()

    def delete_cari_by_fisno(self, mukellef_id, fisno):
        """Belirli bir fişno ile eşleşen cari kaydı siler."""
        self._conn.execute(
            "DELETE FROM cari_hareketler WHERE mukellef_id=? AND fisno=?",
            (mukellef_id, fisno))
        self._conn.commit()

    def get_bakiye(self, mukellef_id):
        c = self._conn.execute(
            "SELECT COALESCE(SUM(borc),0)-COALESCE(SUM(alacak),0) FROM cari_hareketler WHERE mukellef_id=?",
            (mukellef_id,))
        r = c.fetchone()[0]
        return float(r) if r else 0.0

    def get_tum_bakiyeler(self):
        return self._rows(self._conn.execute("""
            SELECT m.id, m.unvan, m.vergi_no,
                   COALESCE(SUM(ch.borc),0)   AS toplam_borc,
                   COALESCE(SUM(ch.alacak),0) AS toplam_alacak,
                   COALESCE(SUM(ch.borc),0)-COALESCE(SUM(ch.alacak),0) AS bakiye
            FROM mukellefler m
            LEFT JOIN cari_hareketler ch ON m.id = ch.mukellef_id
            WHERE m.aktif=1
            GROUP BY m.id, m.unvan, m.vergi_no
            ORDER BY m.unvan COLLATE NOCASE
        """))

    # ══════════════ BEYANNAME PDF ══════════════

    def save_beyanname_pdf(self, mukellef_id, tur, yil, donem, dosya_adi, pdf_bytes):
        """PDF verisini DB'ye kaydeder (varsa üzerine yazar)."""
        self._conn.execute(
            """INSERT INTO beyanname_pdfler(mukellef_id, tur, yil, donem, dosya_adi, pdf_data)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(mukellef_id, tur, yil, donem) DO UPDATE SET
               dosya_adi=excluded.dosya_adi,
               pdf_data=excluded.pdf_data,
               kaydedilme=datetime('now')""",
            (mukellef_id, tur, yil, donem, dosya_adi, sqlite3.Binary(pdf_bytes)))
        self._conn.commit()

    def get_beyanname_pdf(self, mukellef_id, tur, yil, donem):
        """PDF verisini döner. Yoksa None."""
        r = self._row(self._conn.execute(
            "SELECT pdf_data, dosya_adi FROM beyanname_pdfler "
            "WHERE mukellef_id=? AND tur=? AND yil=? AND donem=?",
            (mukellef_id, tur, yil, donem)))
        return r  # {'pdf_data': bytes, 'dosya_adi': str} veya None

    def has_beyanname_pdf(self, mukellef_id, tur, yil, donem):
        r = self._conn.execute(
            "SELECT 1 FROM beyanname_pdfler "
            "WHERE mukellef_id=? AND tur=? AND yil=? AND donem=?",
            (mukellef_id, tur, yil, donem)).fetchone()
        return r is not None

    def get_tum_pdf_keyler(self):
        """Tüm kayıtlı PDF'lerin (mukellef_id, tur, yil, donem) setini döner."""
        rows = self._conn.execute(
            "SELECT mukellef_id, tur, yil, donem FROM beyanname_pdfler").fetchall()
        return {(r[0], r[1], r[2], r[3]) for r in rows}

    # ══════════════ ÖZEL BEYANNAME TÜRLERİ ══════════════

    def get_ozel_turler(self):
        """Tüm özel beyanname türlerini döner: [{ad, periyot, son_gun_gunu}]"""
        return self._rows(self._conn.execute(
            "SELECT ad, periyot, son_gun_gunu FROM ozel_beyanname_turleri ORDER BY ad"))

    def add_ozel_tur(self, ad, periyot, son_gun_gunu):
        ad = ad.strip().upper()
        self._conn.execute(
            "INSERT OR REPLACE INTO ozel_beyanname_turleri(ad, periyot, son_gun_gunu) "
            "VALUES(?,?,?)", (ad, periyot, int(son_gun_gunu)))
        self._conn.commit()

    def delete_ozel_tur(self, ad):
        self._conn.execute(
            "DELETE FROM ozel_beyanname_turleri WHERE ad=?", (ad,))
        self._conn.execute(
            "DELETE FROM mukellef_ozel_beyanlar WHERE tur_ad=?", (ad,))
        self._conn.commit()

    def get_mukellef_ozel_beyanlar(self, mukellef_id):
        """Mükellefi için atanmış özel türleri periyot bilgisiyle döner."""
        return self._rows(self._conn.execute(
            """SELECT mob.tur_ad, COALESCE(obt.periyot,'aylik') AS periyot
               FROM mukellef_ozel_beyanlar mob
               LEFT JOIN ozel_beyanname_turleri obt ON mob.tur_ad = obt.ad
               WHERE mob.mukellef_id=?""", (mukellef_id,)))

    def set_mukellef_ozel_beyanlar(self, mukellef_id, tur_listesi):
        """Mükellefin özel beyanlarını günceller (tur_listesi: ad listesi)."""
        self._conn.execute(
            "DELETE FROM mukellef_ozel_beyanlar WHERE mukellef_id=?", (mukellef_id,))
        for ad in tur_listesi:
            self._conn.execute(
                "INSERT OR IGNORE INTO mukellef_ozel_beyanlar(mukellef_id, tur_ad) VALUES(?,?)",
                (mukellef_id, ad))
        self._conn.commit()


db = Database()
