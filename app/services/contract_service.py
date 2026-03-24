"""Render contract HTML from template with placeholder replacement."""

import os
import re
from datetime import datetime

MONATE_DE = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]

# Path to the contract template (bundled with the app)
TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates", "contract_template.html"
)


def format_datum(iso_str):
    """2026-04-09 -> 09. April 2026"""
    d = datetime.strptime(iso_str, "%Y-%m-%d")
    return "%02d. %s %d" % (d.day, MONATE_DE[d.month], d.year)


def format_betrag(betrag):
    """3600 -> 3.600"""
    return "{:,.0f}".format(betrag).replace(",", ".")


def zahlungsblock_einmal():
    return (
        '<p>Der Gesamtbetrag ist nach Rechnungsstellung fällig. '
        'Zahlungsziel: 14 Tage.</p>'
    )


def zahlungsblock_raten(raten, rate, start_iso):
    d = datetime.strptime(start_iso, "%Y-%m-%d")
    start_monat = d.month
    start_jahr = d.year

    monate = []
    for i in range(raten):
        m = (start_monat - 1 + i) % 12 + 1
        j = start_jahr + (start_monat - 1 + i) // 12
        monate.append((MONATE_DE[m], j))

    erster = "%s %s" % (monate[0][0], monate[0][1])

    if raten > 2:
        rest = "%s – %s %s" % (monate[1][0], monate[-1][0], monate[-1][1])
    elif raten > 1:
        rest = "%s %s" % (monate[1][0], monate[-1][1])
    else:
        rest = ""

    return (
        '<p>Die Zahlung erfolgt in <span class="highlight">%d monatlichen '
        'Raten à %s EUR brutto</span> (inkl. gesetzl. USt.). '
        'Die erste Rate wird im <span class="highlight">%s</span> in '
        'Rechnung gestellt, die weiteren Raten jeweils im Folgemonat '
        '(%s). Zahlungsziel: jeweils '
        '<span class="highlight">14 Tage</span> nach Rechnungsstellung.</p>'
    ) % (raten, format_betrag(rate), erster, rest)


def render_contract_html(
    vorname, nachname, strasse, plz_ort, email, mobil,
    betrag_gesamt, raten, rate, startdatum, wochen, bonus
):
    """Render the full contract HTML with all placeholders replaced."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Payment block
    if raten > 0 and rate > 0:
        zahlungs_block = zahlungsblock_raten(raten, rate, startdatum)
    else:
        zahlungs_block = zahlungsblock_einmal()

    # Bonus line
    bonus_zeile = ""
    if bonus:
        bonus_zeile = "<li>%s</li>" % bonus

    # Replace placeholders
    replacements = {
        "{{VORNAME}}": vorname,
        "{{NACHNAME}}": nachname,
        "{{STRASSE}}": strasse,
        "{{PLZ_ORT}}": plz_ort,
        "{{EMAIL}}": email,
        "{{MOBIL}}": mobil,
        "{{BETRAG_GESAMT}}": format_betrag(betrag_gesamt),
        "{{ZAHLUNGS_BLOCK}}": zahlungs_block,
        "{{STARTDATUM}}": format_datum(startdatum),
        "{{WOCHEN}}": str(wochen),
        "{{BONUS_ZEILE}}": bonus_zeile,
    }

    for key, value in replacements.items():
        html = html.replace(key, value)

    # Rewrite image paths for web serving
    html = html.replace('src="assets/', 'src="/static/assets/')

    # Adapt print CSS for web display
    css_replacements = {
        # Page layout: A4 fixed -> flowing web
        "width: 210mm;": "max-width: 800px;",
        "padding: 25mm;": "padding: 40px 30px;",
        "page-break-after: always;": "",
        "@page {\n    size: A4;\n    margin: 0;\n  }": "",
        "-webkit-print-color-adjust: exact;\n    print-color-adjust: exact;": "",
        # Cover
        "padding-top: 60mm;": "padding-top: 80px; padding-bottom: 60px;",
        "height: 297mm;": "min-height: 400px;",
        # Logo
        "top: 25mm;": "top: 20px;",
        "left: 30mm;": "left: 20px;",
        "height: 28mm;": "height: 50px;",
        # Section logo
        "height: 14mm;": "height: 36px;",
        "margin-bottom: 4mm;": "margin-bottom: 8px;",
        # Cover footer
        "bottom: 25mm;": "bottom: 20px;",
        # mm units to px
        "margin-bottom: 15mm;": "margin-bottom: 30px;",
        "margin-bottom: 20mm;": "margin-bottom: 30px;",
        "margin-top: 15mm;": "margin-top: 25px;",
        "margin-bottom: 5mm;": "margin-bottom: 10px;",
        "margin-bottom: 8mm;": "margin-bottom: 16px;",
        "margin-bottom: 6mm;": "margin-bottom: 12px;",
        "margin: 6mm 0;": "margin: 12px 0;",
        "margin-top: 2mm;": "margin-top: 4px;",
        "margin: 4mm 0;": "margin: 8px 0;",
        "margin: 3mm 0 3mm 6mm;": "margin: 6px 0 6px 12px;",
        "margin-bottom: 1.5mm;": "margin-bottom: 3px;",
        "left: -2mm;": "left: -8px;",
        "padding-left: 4mm;": "padding-left: 12px;",
        "margin-top: 8mm;": "margin-top: 16px;",
        "margin-bottom: 4mm;": "margin-bottom: 8px;",
        "margin-bottom: 3mm;": "margin-bottom: 6px;",
        "margin-bottom: 2mm;": "margin-bottom: 4px;",
        "margin-top: 1mm;": "margin-top: 2px;",
        "margin-top: 10mm;": "margin-top: 16px;",
        "gap: 20mm;": "gap: 40px;",
        "height: 15mm;": "height: 30px;",
        'style="margin-top: 10mm;"': 'style="margin-top: 20px;"',
        # Media queries: flatten for web
        "@media print {\n    body { background: #EDE6DE; }\n    .page { margin: 0; box-shadow: none; }\n  }\n  @media screen {\n    .page {\n      margin: 10mm auto;\n      box-shadow: 0 2px 20px rgba(0,0,0,0.1);\n    }\n  }": ".page { margin: 20px auto; }",
    }

    for old, new in css_replacements.items():
        html = html.replace(old, new)

    # Remove the physical signature block (signing is digital)
    html = re.sub(
        r'<div class="cta">.*?</div>\s*<div class="signature-block">.*?</div>\s*</div>\s*<div class="closing">.*?</div>',
        '',
        html,
        flags=re.DOTALL,
    )

    # Remove page numbers from web view (only needed in PDF)
    html = re.sub(
        r'<div class="page-number">.*?</div>',
        '',
        html,
    )

    # Show more of the cover image in web view
    html = html.replace('height: 55%;', 'height: 70%;')

    return html
