"""
SMMM TAKİP — Lisans Yönetimi

Hız garantisi:
  • Önbellekte geçerli kayıt varsa  : < 5 ms  (yerel dosya okuma)
  • İlk çalıştırma / önbellek yok   : < 4 sn  (GitHub CDN'den)
  • Ağ hatası + önbellek mevcutsa   : < 5 ms  (önbellek kullanılır)

Lisans kayıt dosyası  : GitHub repo kökünde  licenses.json
Yerel önbellek        : %APPDATA%\\SMMM Takip\\license_cache.json
Kullanıcı adı config  : %APPDATA%\\SMMM Takip\\config.ini
"""

import os
import json
import threading
import configparser
import urllib.request
from datetime import date

from version import GITHUB_REPO

# ─── Dosya yolları ────────────────────────────────────────────
_APPDATA  = os.environ.get('APPDATA', os.path.expanduser('~'))
_DATA_DIR = os.path.join(_APPDATA, 'SMMM Takip')
_CONFIG   = os.path.join(_DATA_DIR, 'config.ini')
_CACHE    = os.path.join(_DATA_DIR, 'license_cache.json')
_RAW_URL  = (
    f"https://raw.githubusercontent.com/{GITHUB_REPO}/master/licenses.json"
    "?_={{}}"  # önbellek kırıcı
)


# ─── Kullanıcı adı ────────────────────────────────────────────

def get_username() -> str:
    cfg = configparser.ConfigParser()
    try:
        cfg.read(_CONFIG, encoding='utf-8')
        return cfg.get('Uygulama', 'kullanici_adi', fallback='').strip()
    except Exception:
        return ''


def save_username(username: str):
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_CONFIG, 'w', encoding='utf-8') as f:
        f.write(f"[Uygulama]\nkullanici_adi={username}\n")


# ─── Önbellek ─────────────────────────────────────────────────

def _read_cache() -> dict:
    try:
        with open(_CACHE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _write_cache(data: dict):
    os.makedirs(_DATA_DIR, exist_ok=True)
    try:
        with open(_CACHE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ─── GitHub'dan çek ───────────────────────────────────────────

def _fetch(timeout: int = 4) -> dict | None:
    """GitHub raw URL'den licenses.json indir. None → başarısız."""
    if not GITHUB_REPO or 'GITHUB_KULLANICISI' in GITHUB_REPO:
        return None
    try:
        import time
        url = _RAW_URL.format(int(time.time()))
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'SMMM-Takip-License',
                'Cache-Control': 'no-cache',
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception:
        return None


# ─── Lisans değerlendirme ─────────────────────────────────────

def _evaluate(username: str, data: dict) -> tuple:
    """
    Döner: (True, isim)  → geçerli
            (False, mesaj) → geçersiz
    """
    lisanslar = data.get('licenses', {})
    bilgi = lisanslar.get(username)
    if bilgi is None:
        return False, (
            f"'{username}' kullanıcısı için lisans bulunamadı.\n"
            "Yöneticinizle iletişime geçin."
        )
    if not bilgi.get('active', False):
        return False, (
            f"'{username}' lisansı devre dışı bırakılmış.\n"
            "Yöneticinizle iletişime geçin."
        )
    expires = bilgi.get('expires')
    if expires:
        try:
            if date.today() > date.fromisoformat(expires):
                return False, (
                    f"'{username}' lisansının süresi dolmuş ({expires}).\n"
                    "Yöneticinizle iletişime geçin."
                )
        except Exception:
            pass
    return True, bilgi.get('name', username)


# ─── Ana fonksiyon ────────────────────────────────────────────

def verify(show_progress_cb=None) -> tuple:
    """
    Lisans doğrula. main() tarafından uygulama açılmadan önce çağrılır.

    Döner:
      (None,  'dev')     → GITHUB_REPO ayarsız, geliştirici modu — geç
      (True,  isim)      → Lisans geçerli
      (False, hata_msg)  → Lisans geçersiz — uygulamayı açma
    """
    # ── Geliştirici modu ──────────────────────────────────────
    if not GITHUB_REPO or 'GITHUB_KULLANICISI' in GITHUB_REPO:
        return None, 'dev'

    username = get_username()
    if not username:
        return False, (
            "Kullanıcı adı tanımlanmamış.\n"
            "Lütfen uygulamayı yeniden kurun veya yöneticinizle iletişime geçin."
        )

    # ── 1) Önbellekten hızlı kontrol ─────────────────────────
    cache = _read_cache()
    if cache:
        ok, msg = _evaluate(username, cache)
        if ok:
            # Geçerli → arka planda önbelleği tazele, hemen devam et
            threading.Thread(target=_refresh_cache, daemon=True).start()
            return True, msg
        # Geçersiz önbellekte — yine de canlı kontrol dene
        # (Yönetici lisansı yeniden aktif etmiş olabilir)

    # ── 2) GitHub'dan canlı kontrol ───────────────────────────
    if show_progress_cb:
        show_progress_cb("Lisans doğrulanıyor...")

    data = _fetch(timeout=4)
    if data:
        _write_cache(data)
        return _evaluate(username, data)

    # ── 3) Ağ hatası — önbellek varsa kullan ─────────────────
    if cache:
        return _evaluate(username, cache)

    return False, (
        "Lisans sunucusuna ulaşılamadı.\n"
        "İnternet bağlantınızı kontrol edip tekrar deneyin."
    )


def _refresh_cache():
    """Arka planda sessizce önbelleği günceller."""
    data = _fetch(timeout=8)
    if data:
        _write_cache(data)
