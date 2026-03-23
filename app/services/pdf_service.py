"""Generate A4 PDF from signed contract using weasyprint."""

import os
import re
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


def generate_signed_pdf(contract) -> bytes:
    """Generate a signed A4 PDF from the contract data."""
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

    # Rewrite image paths to absolute file paths for weasyprint
    assets_dir = os.path.join(STATIC_DIR, "assets")
    html = html.replace('src="assets/', 'src="file://%s/' % assets_dir)

    # Replace physical signature block with digital signature
    signed_date = contract.signed_at[:10] if contract.signed_at else ""
    try:
        signed_date_formatted = format_datum(signed_date)
    except (ValueError, IndexError):
        signed_date_formatted = signed_date

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
      <div style="font-size: 8pt; color: #8D5F4E;">
        Dieser Vertrag wurde gemäß § 126b BGB in Textform digital geschlossen.
      </div>
    </div>
    """ % (contract.signed_name, signed_date_formatted, contract.signed_ip or "—")

    # Replace CTA + signature block + closing
    html = re.sub(
        r'<div class="cta">.*?</div>\s*'
        r'<div class="signature-block">.*?</div>\s*</div>\s*'
        r'<div class="closing">.*?</div>',
        signed_block,
        html,
        flags=re.DOTALL,
    )

    # Remove the cover background image entirely (mask-image not supported in weasyprint)
    html = re.sub(
        r'<img class="cover-bg"[^>]*>',
        '',
        html,
    )

    # Remove all existing <style> and rebuild clean CSS for weasyprint
    html = re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL)

    # Remove @media blocks and screen-only styles
    # Remove box-shadow references

    weasyprint_css = """<style>
    @page { size: A4; margin: 0; }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Montserrat', sans-serif;
      font-size: 11pt;
      line-height: 1.6;
      color: #1F3B4D;
      background: #EDE6DE;
    }

    .page {
      width: 210mm;
      padding: 45mm 30mm 35mm 30mm;
      background: #EDE6DE;
      position: relative;
      page-break-before: always;
      page-break-inside: avoid;
    }
    .page:first-child { page-break-before: auto; }

    .page-cover {
      display: block;
      text-align: center;
      padding-top: 80mm;
      min-height: 297mm;
    }

    .logo {
      position: absolute;
      top: 25mm;
      left: 30mm;
      height: 28mm;
      width: auto;
    }

    .cover-title {
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: 42pt;
      color: #1F3B4D;
      text-transform: uppercase;
      letter-spacing: 1px;
      line-height: 1.15;
      margin-bottom: 15mm;
    }

    .cover-subtitle {
      font-family: 'Libre Baskerville', serif;
      font-size: 14pt;
      font-weight: 400;
      color: #1F3B4D;
      margin-bottom: 5mm;
    }

    .cover-tagline {
      font-family: 'Montserrat', sans-serif;
      font-size: 11pt;
      color: #8D5F4E;
      margin-bottom: 20mm;
    }

    .cover-welcome {
      font-family: 'Libre Baskerville', serif;
      font-size: 16pt;
      color: #1F3B4D;
      margin-top: 15mm;
    }
    .cover-welcome .name { color: #1F3B4D; font-weight: 400; }

    .cover-footer {
      position: absolute;
      bottom: 25mm;
      left: 30mm;
      font-size: 9pt;
      color: #8D5F4E;
    }
    .cover-footer a { color: #8D5F4E; text-decoration: none; }

    h1 {
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: 18pt;
      text-transform: uppercase;
      color: #1F3B4D;
      letter-spacing: 1.5px;
      margin-bottom: 8mm;
    }

    h2 {
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: 13pt;
      text-transform: uppercase;
      color: #1F3B4D;
      letter-spacing: 1px;
      margin-top: 8mm;
      margin-bottom: 4mm;
    }

    p {
      margin-bottom: 3mm;
      text-align: justify;
    }

    .parties { margin: 6mm 0; }
    .party { margin-bottom: 5mm; }
    .party-name { font-weight: 700; font-size: 12pt; }
    .party-role { font-style: italic; color: #8D5F4E; margin-top: 2mm; }
    .party-und { text-align: center; margin: 4mm 0; color: #8D5F4E; }

    .highlight { font-weight: 700; }

    ul { margin: 3mm 0 3mm 6mm; list-style: none; }
    ul li { padding-left: 4mm; position: relative; margin-bottom: 1.5mm; }
    ul li::before { content: "–"; position: absolute; left: -2mm; color: #8D5F4E; }

    .cta {
      text-align: left;
      margin-top: 10mm;
      margin-bottom: 2mm;
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: 12pt;
      color: #1F3B4D;
    }

    .separator {
      border: none;
      border-top: 0.5pt solid #8D5F4E;
      margin: 4mm 0;
      opacity: 0.4;
    }

    .page-number {
      position: absolute;
      bottom: 20mm;
      right: 30mm;
      font-size: 9pt;
      color: #8D5F4E;
    }

    .page-logo {
      position: absolute;
      top: 20mm;
      left: 30mm;
      height: 20mm;
      width: auto;
    }

    .anlage-header {
      font-family: 'Montserrat', sans-serif;
      font-size: 9pt;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #8D5F4E;
      margin-bottom: 6mm;
    }

    .anlage-stand {
      font-size: 10pt;
      color: #8D5F4E;
      margin-bottom: 5mm;
    }
    </style>"""

    html = html.replace('</head>', weasyprint_css + '\n</head>')

    # Generate PDF
    try:
        from weasyprint import HTML
    except OSError:
        logger.error("weasyprint nicht verfügbar. PDF wird nicht generiert.")
        return None

    pdf_bytes = HTML(string=html).write_pdf()
    logger.info(
        "PDF generiert fuer %s %s (%d bytes)",
        contract.vorname, contract.nachname, len(pdf_bytes)
    )
    return pdf_bytes
