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

# Static assets directory for weasyprint to resolve images
STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "static"
)


def generate_signed_pdf(contract) -> bytes:
    """Generate a signed A4 PDF from the contract data.

    Uses the original print-optimized template (not the web version),
    replaces the signature block with digital signature info.
    Returns PDF as bytes.
    """
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

    # Replace everything from CTA through closing (including signature block)
    html = re.sub(
        r'<div class="cta">.*?</div>\s*'
        r'<div class="signature-block">.*?</div>\s*</div>\s*'
        r'<div class="closing">.*?</div>',
        signed_block,
        html,
        flags=re.DOTALL,
    )

    # Fix CSS for weasyprint PDF rendering:
    # 1. Remove cover-bg mask-image (not supported by weasyprint) — use simple opacity
    html = html.replace(
        '-webkit-mask-image: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.3) 30%, rgba(0,0,0,0.6) 100%);\n'
        '    mask-image: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.3) 30%, rgba(0,0,0,0.6) 100%);',
        ''
    )
    # Reduce opacity further for cleaner look in PDF
    html = html.replace(
        'opacity: 0.3;',
        'opacity: 0.15;'
    )

    # 2. Ensure each .page is exactly one A4 page with proper breaks
    weasyprint_css = """
    <style>
      @page { size: A4; margin: 0; }
      .page {
        width: 210mm !important;
        height: 297mm !important;
        min-height: 297mm !important;
        max-height: 297mm !important;
        overflow: hidden !important;
        page-break-after: always !important;
        page-break-inside: avoid !important;
        position: relative !important;
      }
      .page:last-child {
        page-break-after: auto !important;
      }
      .page-number {
        position: absolute !important;
        bottom: 20mm !important;
        right: 30mm !important;
      }
      .page-logo {
        position: absolute !important;
        top: 20mm !important;
        left: 30mm !important;
        height: 20mm !important;
        width: auto !important;
      }
      /* Screen media query should not apply */
      @media screen { .page { margin: 0 !important; box-shadow: none !important; } }
    </style>
    """
    html = html.replace('</head>', weasyprint_css + '</head>')

    # Generate PDF (lazy import — weasyprint needs system libs)
    try:
        from weasyprint import HTML
    except OSError:
        logger.error("weasyprint nicht verfügbar (fehlende System-Libraries). PDF wird nicht generiert.")
        return None
    pdf_bytes = HTML(string=html).write_pdf()
    logger.info(
        "PDF generiert fuer %s %s (%d bytes)",
        contract.vorname, contract.nachname, len(pdf_bytes)
    )
    return pdf_bytes
