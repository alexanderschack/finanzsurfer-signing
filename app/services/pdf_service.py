"""Generate A4 PDF from signed contract using headless Chromium."""

import os
import re
import tempfile
import subprocess
import logging
from app.services.contract_service import (
    format_datum, format_betrag,
    zahlungsblock_raten, zahlungsblock_einmal,
    MONATE_DE, TEMPLATE_PATH,
)

logger = logging.getLogger(__name__)

STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "static"
)

# Find chromium binary
CHROMIUM = None
for path in ["/usr/bin/google-chrome-stable", "/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]:
    if os.path.exists(path):
        CHROMIUM = path
        break


def generate_signed_pdf(contract) -> bytes:
    """Generate a signed A4 PDF using headless Chromium.

    Uses the original print-optimized template with proper @page CSS.
    Chromium renders it exactly like a browser Cmd+P.
    """
    if not CHROMIUM:
        logger.error("Chromium nicht gefunden. PDF wird nicht generiert.")
        return None

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Payment block
    if contract.raten > 0 and contract.rate > 0:
        zahlungs_block = zahlungsblock_raten(
            contract.raten, contract.rate, contract.startdatum
        )
    else:
        zahlungs_block = zahlungsblock_einmal()

    # Bonus line
    bonus_zeile = ""
    if contract.bonus:
        bonus_zeile = "<li>%s</li>" % contract.bonus

    # Replace placeholders
    replacements = {
        "{{VORNAME}}": contract.vorname,
        "{{NACHNAME}}": contract.nachname,
        "{{STRASSE}}": contract.strasse,
        "{{PLZ_ORT}}": contract.plz_ort,
        "{{EMAIL}}": contract.email,
        "{{MOBIL}}": contract.mobil,
        "{{BETRAG_GESAMT}}": format_betrag(contract.betrag_gesamt),
        "{{ZAHLUNGS_BLOCK}}": zahlungs_block,
        "{{STARTDATUM}}": format_datum(contract.startdatum),
        "{{WOCHEN}}": str(contract.wochen),
        "{{BONUS_ZEILE}}": bonus_zeile,
    }

    for key, value in replacements.items():
        html = html.replace(key, value)

    # Rewrite image paths to absolute file paths
    assets_dir = os.path.join(STATIC_DIR, "assets")
    html = html.replace('src="assets/', 'src="file://%s/' % assets_dir)

    # Replace physical signature block with digital signature
    signed_date = contract.signed_at[:10] if contract.signed_at else ""
    try:
        signed_date_formatted = format_datum(signed_date)
    except (ValueError, IndexError):
        signed_date_formatted = signed_date

    signatur_path = os.path.join(assets_dir, "signatur-alex.png")

    signed_block = """
    <div style="margin-top: 8mm;">
      <div style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 12pt; color: #1F3B4D; margin-bottom: 4mm;">
        Digital unterschrieben
      </div>
      <div style="background: #d4edda; border-radius: 4px; padding: 5mm 6mm; margin-bottom: 4mm;">
        <p style="margin-bottom: 2mm; font-size: 10pt;"><strong>Unterschrieben als:</strong> %s</p>
        <p style="margin-bottom: 2mm; font-size: 10pt;"><strong>Datum:</strong> %s</p>
        <p style="margin-bottom: 0; font-size: 10pt;"><strong>IP-Adresse:</strong> %s</p>
      </div>
      <div style="margin-top: 6mm;">
        <div style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 12pt; color: #1F3B4D; margin-bottom: 2mm;">
          Gegengezeichnet
        </div>
        <img src="file://%s" style="height: 15mm; width: auto; display: block; margin-bottom: 2mm;" alt="Unterschrift Alexander Schack">
        <p style="font-size: 10pt; margin-bottom: 0;">Finance Flow | Alexander Schack</p>
      </div>
      <div style="font-size: 8pt; color: #8D5F4E; margin-top: 4mm;">
        Dieser Vertrag wurde gemäß § 126b BGB in Textform digital geschlossen.
      </div>
    </div>
    """ % (contract.signed_name, signed_date_formatted, contract.signed_ip or "—", signatur_path)

    # Replace CTA + signature block + closing
    html = re.sub(
        r'<div class="cta">.*?</div>\s*'
        r'<div class="signature-block">.*?</div>\s*</div>\s*'
        r'<div class="closing">.*?</div>',
        signed_block,
        html,
        flags=re.DOTALL,
    )

    # Write HTML to temp file
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    pdf_path = html_path.replace(".html", ".pdf")

    try:
        result = subprocess.run(
            [
                CHROMIUM,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--print-to-pdf=%s" % pdf_path,
                "--no-pdf-header-footer",
                "file://%s" % html_path,
            ],
            capture_output=True,
            timeout=30,
        )

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            logger.info(
                "PDF generiert fuer %s %s (%d bytes)",
                contract.vorname, contract.nachname, len(pdf_bytes)
            )
            return pdf_bytes
        else:
            logger.error("PDF nicht erstellt. Chromium stderr: %s", result.stderr.decode())
            return None
    except subprocess.TimeoutExpired:
        logger.error("Chromium timeout bei PDF-Generierung")
        return None
    except Exception as e:
        logger.error("PDF-Fehler: %s", str(e))
        return None
    finally:
        # Cleanup temp files
        for p in [html_path, pdf_path]:
            try:
                os.unlink(p)
            except OSError:
                pass
