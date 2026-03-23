"""Send confirmation emails via SMTP (Brevo) with PDF attachment."""

import smtplib
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from app.config import settings

logger = logging.getLogger(__name__)


def send_signing_confirmation(contract, base_url="https://sign.finanz-surfer.de", pdf_bytes=None):
    """Send confirmation email to both Alex and the client, with PDF attached."""
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP nicht konfiguriert — E-Mails werden nicht gesendet.")
        return

    pdf_filename = "Mentoring-Vertrag_%s_%s.pdf" % (contract.vorname, contract.nachname)

    # Email to Alex
    alex_subject = "Vertrag unterschrieben: %s %s" % (contract.vorname, contract.nachname)
    alex_body = """
    <div style="font-family: sans-serif; color: #1F3B4D;">
        <h2>Vertrag digital unterschrieben</h2>
        <p><strong>Name:</strong> %s</p>
        <p><strong>Unterschrieben als:</strong> %s</p>
        <p><strong>Datum:</strong> %s</p>
        <p><strong>IP:</strong> %s</p>
        <p>Der unterschriebene Vertrag ist als PDF angehängt.</p>
    </div>
    """ % (contract.full_name, contract.signed_name, contract.signed_at,
           contract.signed_ip)

    _send_email("alex@finanz-surfer.de", alex_subject, alex_body,
                pdf_bytes=pdf_bytes, pdf_filename=pdf_filename)

    # Email to client
    client_subject = "Dein Mentoring-Vertrag — unterschrieben"
    client_body = """
    <div style="font-family: sans-serif; color: #1F3B4D;">
        <p>Liebe %s,</p>
        <p>vielen Dank! Dein Mentoring-Vertrag wurde erfolgreich unterschrieben.</p>
        <p>Den unterschriebenen Vertrag findest du als PDF im Anhang dieser E-Mail.</p>
        <p>Ich freue mich auf unsere Zusammenarbeit!</p>
        <p>Liebe Grüße,<br>Alex</p>
    </div>
    """ % contract.vorname

    _send_email(contract.email, client_subject, client_body,
                pdf_bytes=pdf_bytes, pdf_filename=pdf_filename)


def _send_email(to, subject, html_body, pdf_bytes=None, pdf_filename=None):
    """Send a single email via SMTP, optionally with PDF attachment."""
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to

        # HTML body
        html_part = MIMEMultipart("alternative")
        html_part.attach(MIMEText(html_body, "html"))
        msg.attach(html_part)

        # PDF attachment
        if pdf_bytes and pdf_filename:
            pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
            pdf_part.add_header(
                "Content-Disposition", "attachment",
                filename=pdf_filename,
            )
            msg.attach(pdf_part)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, to, msg.as_string())

        logger.info("E-Mail gesendet an %s: %s", to, subject)
    except Exception as e:
        logger.error("E-Mail-Fehler an %s: %s", to, str(e))
