# data/barcode_scanner.py — THRESHOLD · Scanner code-barres
# ─────────────────────────────────────────────────────────────────────────────
# Scan code-barres EAN13/EAN8 → lookup Open Food Facts → dict aliment.
#
# Sur Android  : WebView avec BarcodeDetector API (natif Android WebView).
# Sur desktop  : pyzbar + OpenCV (développement/test).
#
# API publique :
#   scan_and_lookup(page, app_state, on_result)
#     → appelle on_result(food_dict) si trouvé, on_result(None) si annulé/erreur
#
#   lookup_barcode(barcode: str) -> dict | None
#     → requête Open Food Facts, retourne dict compatible _open_food_modal
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import json
import threading
import urllib.request
import urllib.error
from typing import Callable

import flet as ft

from data.logger import log_exc, log

# ── OFF API ───────────────────────────────────────────────────────────────────
_OFF_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
_OFF_FIELDS = (
    "product_name,product_name_fr,"
    "nutriments,"
    "categories_tags,"
    "quantity"
)
_UA = "THRESHOLD-App/1.0 (+contact@threshold.app)"


def lookup_barcode(barcode: str) -> dict | None:
    """Interroge Open Food Facts et retourne un dict compatible _open_food_modal.

    Retourne None si le produit est introuvable ou en cas d'erreur réseau.
    """
    barcode = barcode.strip()
    if not barcode:
        return None
    try:
        url = (_OFF_URL.format(barcode=barcode)
               + "?fields=" + urllib.request.quote(_OFF_FIELDS))
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") != 1:
            log.info("barcode %s introuvable sur OFF", barcode)
            return None

        p   = data.get("product", {})
        nut = p.get("nutriments", {})

        # Nom : français en priorité
        nom = (p.get("product_name_fr") or p.get("product_name") or "").strip()
        if not nom:
            return None

        # Catégorie OFF → catégorie THRESHOLD
        cats_off = p.get("categories_tags", [])
        categorie = _map_off_category(cats_off)

        return {
            "nom":        nom,
            "categorie":  categorie,
            "kcal":       round(float(nut.get("energy-kcal_100g", 0) or 0), 1),
            "proteines":  round(float(nut.get("proteins_100g",    0) or 0), 1),
            "glucides":   round(float(nut.get("carbohydrates_100g",0) or 0), 1),
            "lipides":    round(float(nut.get("fat_100g",          0) or 0), 1),
            "fibres":     round(float(nut.get("fiber_100g",        0) or 0), 1),
            "portion_ref": 100,
            "notes":      f"Code-barres : {barcode}",
        }
    except Exception:
        log_exc(f"lookup_barcode({barcode})")
        return None


def _map_off_category(tags: list) -> str:
    """Mappe les tags catégorie OFF vers les catégories THRESHOLD."""
    tags_str = " ".join(tags).lower()
    if any(k in tags_str for k in ("viande","poulet","dinde","boeuf","porc","poisson","saumon","thon")):
        return "Protéines animales"
    if any(k in tags_str for k in ("tofu","legumineuse","lentille","pois","haricot","soja")):
        return "Protéines végétales"
    if any(k in tags_str for k in ("lait","yaourt","fromage","oeuf","dairy","laitage")):
        return "Œufs & laitiers"
    if any(k in tags_str for k in ("supplement","whey","proteine","creatine","complement")):
        return "Suppléments"
    if any(k in tags_str for k in ("riz","pate","pain","cereale","farine","glucide","pomme-de-terre","patate")):
        return "Glucides"
    if any(k in tags_str for k in ("fruit","pomme","banane","orange","fraise","fruits")):
        return "Fruits"
    if any(k in tags_str for k in ("legume","brocoli","epinard","carotte","courgette","salade")):
        return "Légumes"
    if any(k in tags_str for k in ("huile","avocat","amande","noix","beurre","graisse","lipide")):
        return "Lipides"
    return "Divers"


# ── HTML/JS de la page scanner (BarcodeDetector API) ─────────────────────────
_SCANNER_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#111; display:flex; flex-direction:column;
         align-items:center; justify-content:center; height:100vh; }
  #video { width:100%; max-width:480px; border-radius:12px; }
  #overlay { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
             width:220px; height:220px; border:3px solid #22c55e; border-radius:12px;
             pointer-events:none; }
  #status { color:#fff; margin-top:12px; font-family:sans-serif; font-size:14px; text-align:center; }
  #cancel { margin-top:16px; padding:10px 28px; background:#ef4444; color:#fff;
            border:none; border-radius:8px; font-size:15px; cursor:pointer; }
</style>
</head>
<body>
<div style="position:relative;display:inline-block">
  <video id="video" autoplay playsinline></video>
  <div id="overlay"></div>
</div>
<div id="status">Pointez la caméra vers le code-barres...</div>
<button id="cancel" onclick="cancelScan()">Annuler</button>
<script>
let stream = null;
let scanning = true;

async function startScan() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: {ideal:1280}, height: {ideal:720} }
    });
    document.getElementById('video').srcObject = stream;
    await document.getElementById('video').play();
    detectLoop();
  } catch(e) {
    document.getElementById('status').textContent = 'Erreur caméra : ' + e.message;
    sendResult('ERROR:' + e.message);
  }
}

async function detectLoop() {
  if (!scanning) return;
  const video = document.getElementById('video');
  if (video.readyState < 2) { setTimeout(detectLoop, 100); return; }

  if ('BarcodeDetector' in window) {
    const detector = new BarcodeDetector({formats:['ean_13','ean_8','upc_a','upc_e','code_128','code_39']});
    try {
      const barcodes = await detector.detect(video);
      if (barcodes.length > 0) {
        scanning = false;
        stopStream();
        sendResult('OK:' + barcodes[0].rawValue);
        return;
      }
    } catch(e) {}
  } else {
    document.getElementById('status').textContent = 'BarcodeDetector non supporté';
    sendResult('ERROR:BarcodeDetector non disponible');
    return;
  }
  setTimeout(detectLoop, 300);
}

function stopStream() {
  if (stream) stream.getTracks().forEach(t => t.stop());
}

function cancelScan() {
  scanning = false;
  stopStream();
  sendResult('CANCEL');
}

function sendResult(value) {
  // Communication vers Flet via le titre de la page (polling)
  document.title = 'SCAN:' + value;
  // Fallback : lien cliquable automatique (intercepté par Flet WebView)
  window.location.hash = encodeURIComponent(value);
}

startScan();
</script>
</body>
</html>"""


# ── Fonction principale ───────────────────────────────────────────────────────

def scan_and_lookup(
    page: ft.Page,
    app_state,
    on_result: Callable[[dict | None], None],
) -> None:
    """Point d'entrée unique du scanner.

    Sur Android  : ouvre une WebView avec BarcodeDetector.
    Sur desktop  : tente pyzbar/OpenCV, sinon propose saisie manuelle.
    Dans les deux cas, appelle on_result(food_dict) ou on_result(None).
    """
    is_android = str(getattr(page, "platform", "")).upper() == "ANDROID"

    if is_android:
        _scan_webview(page, on_result)
    else:
        _scan_desktop(page, on_result)


def _scan_webview(page: ft.Page, on_result: Callable) -> None:
    """Scan via WebView Android (BarcodeDetector API)."""
    from ui.snackbar import snack

    scanned = {"done": False}

    def _on_title_change(e):
        """Flet WebView expose page_title via on_page_ended / on_page_started."""
        pass  # voir polling ci-dessous

    def _close_and_call(result_code: str):
        if scanned["done"]:
            return
        scanned["done"] = True
        # Fermer le dialog
        try:
            dlg.open = False
            page.update()
        except Exception:
            pass

        if result_code.startswith("OK:"):
            barcode = result_code[3:].strip()
            snack(page, f"Code détecté : {barcode}", "info")
            # Lookup OFF en background
            def _lookup():
                food = lookup_barcode(barcode)
                if food:
                    page.run_task(_deliver, food)
                else:
                    snack(page, "Produit introuvable sur Open Food Facts.", "warning")
                    page.run_task(_deliver, None)
            async def _deliver(food):
                on_result(food)
            threading.Thread(target=_lookup, daemon=True).start()

        elif result_code == "CANCEL":
            on_result(None)
        else:
            snack(page, f"Erreur scanner : {result_code}", "error")
            on_result(None)

    # WebView avec polling du hash
    wv = ft.WebView(
        expand=True,
        on_page_started=lambda e: None,
        on_page_ended=lambda e: None,
    )

    # Injection HTML via data URI
    import base64
    html_b64 = base64.b64encode(_SCANNER_HTML.encode()).decode()
    wv.url = f"data:text/html;base64,{html_b64}"

    # Polling toutes les 500 ms via un timer Flet pour lire le hash
    _poll_count = {"n": 0}

    async def _poll(e=None):
        _poll_count["n"] += 1
        if _poll_count["n"] > 120 or scanned["done"]:  # timeout 60s
            _close_and_call("CANCEL")
            return
        # Exécute JS pour récupérer le hash
        try:
            result = await wv.run_javascript_async(
                "window.location.hash.slice(1) || ''"
            )
            if result:
                import urllib.parse
                _close_and_call(urllib.parse.unquote(result))
        except Exception:
            pass

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("📷 Scanner un code-barres", color="#22c55e"),
        content=ft.Container(content=wv, width=380, height=460),
        actions=[ft.TextButton("Annuler", on_click=lambda e: _close_and_call("CANCEL"))],
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()

    # Lancer le polling
    page.run_task(_start_polling, _poll)


async def _start_polling(poll_fn):
    import asyncio
    for _ in range(120):
        await asyncio.sleep(0.5)
        await poll_fn()


def _scan_desktop(page: ft.Page, on_result: Callable) -> None:
    """Scan desktop via pyzbar + OpenCV (fallback dev)."""
    from ui.snackbar import snack

    def _try_pyzbar():
        try:
            import cv2
            from pyzbar.pyzbar import decode as pyz_decode

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("Webcam inaccessible")

            found = None
            for _ in range(200):  # ~10 s max
                ret, frame = cap.read()
                if not ret:
                    break
                codes = pyz_decode(frame)
                if codes:
                    found = codes[0].data.decode("utf-8")
                    break
            cap.release()

            if found:
                snack(page, f"Code détecté : {found}", "info")
                food = lookup_barcode(found)
                on_result(food)
            else:
                snack(page, "Aucun code détecté.", "warning")
                on_result(None)

        except ImportError:
            # pyzbar/cv2 non installé → saisie manuelle
            _manual_barcode_input(page, on_result)
        except Exception:
            log_exc("_scan_desktop")
            _manual_barcode_input(page, on_result)

    threading.Thread(target=_try_pyzbar, daemon=True).start()


def _manual_barcode_input(page: ft.Page, on_result: Callable) -> None:
    """Fallback desktop : saisie manuelle du code-barres."""
    from ui.snackbar import snack

    field = ft.TextField(
        label="Code-barres EAN",
        hint_text="Ex: 3017620422003",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        width=280,
    )

    def _submit(e=None):
        code = (field.value or "").strip()
        dlg.open = False
        page.update()
        if not code:
            on_result(None)
            return
        snack(page, "Recherche sur Open Food Facts...", "info")

        def _lookup():
            food = lookup_barcode(code)
            if food:
                on_result(food)
            else:
                snack(page, "Produit introuvable.", "warning")
                on_result(None)
        threading.Thread(target=_lookup, daemon=True).start()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("🔢 Saisir un code-barres"),
        content=field,
        actions=[
            ft.TextButton("Rechercher", on_click=_submit),
            ft.TextButton("Annuler", on_click=lambda e: (setattr(dlg, "open", False), page.update(), on_result(None))),
        ],
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()
