"""Send confirmation emails via SMTP (Brevo) with PDF attachment."""

import smtplib
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from app.config import settings

logger = logging.getLogger(__name__)

BCC_ALEX = "alex@finanz-surfer.de"

EMAIL_SIGNATURE = """
<div style="margin-top: 24px; font-family: sans-serif; font-size: 13px; color: #1F3B4D; line-height: 1.5;">
  <div style="border-top: 1px solid #8D5F4E; margin-bottom: 16px; width: 180px;"></div>
  <div style="font-family: 'Libre Baskerville', Georgia, serif; font-size: 20px; color: #8D5F4E; margin-bottom: 12px;">
    <span style="color: #C4956A;">Finanz</span><em>surfer</em>
  </div>
  <p style="margin: 0 0 2px;"><strong>T:</strong> +49 151 52531347</p>
  <p style="margin: 0 0 2px;"><strong>M:</strong> <a href="mailto:alex@finanz-surfer.de" style="color: #8D5F4E;">alex@finanz-surfer.de</a></p>
  <p style="margin: 0 0 12px;"><strong>W:</strong> <a href="https://www.finanz-surfer.de" style="color: #8D5F4E;">www.finanz-surfer.de</a></p>
  <p style="margin: 0 0 2px;"><strong>Finance Flow | Alexander Schack</strong></p>
  <p style="margin: 0 0 2px;">Weidengrund 76</p>
  <p style="margin: 0 0 16px;">18059 Rostock</p>
  <div style="font-size: 10px; color: #999; line-height: 1.4;">
    <p style="margin: 0 0 6px;">Diese E-Mail enth&auml;lt vertrauliche und/oder rechtlich gesch&uuml;tzte Informationen. Wenn Sie nicht der richtige Adressat sind oder dieses E-Mail irrt&uuml;mlich erhalten haben, informieren Sie bitte sofort den Absender und vernichten Sie diese Mail. Das unerlaubte Kopieren sowie die unbefugte Weitergabe dieser Mail sind nicht gestattet.</p>
    <p style="margin: 0;">This e-mail may contain confidential and/or privileged information. If you are not the intended recipient (or have received this e-mail in error) please notify the sender immediately and destroy this e-mail. Any unauthorized copying, disclosure or distribution of the material in this e-mail is strictly forbidden.</p>
  </div>
</div>
"""


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
        <p>Liebe Gr&uuml;&szlig;e<br>Alex</p>
    </div>
    """ % contract.vorname

    _send_email(contract.email, client_subject, client_body,
                pdf_bytes=pdf_bytes, pdf_filename=pdf_filename)


def _send_email(to, subject, html_body, pdf_bytes=None, pdf_filename=None):
    """Send a single email via SMTP, optionally with PDF attachment.

    Always BCC alex@finanz-surfer.de so Alex gets a copy of every outgoing mail.
    Appends Alex's email signature to all outgoing HTML emails.
    """
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to

        # HTML body with signature
        full_html = html_body + EMAIL_SIGNATURE
        html_part = MIMEMultipart("alternative")
        html_part.attach(MIMEText(full_html, "html", "utf-8"))
        msg.attach(html_part)

        # PDF attachment
        if pdf_bytes and pdf_filename:
            pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
            pdf_part.add_header(
                "Content-Disposition", "attachment",
                filename=pdf_filename,
            )
            msg.attach(pdf_part)

        # Always send to recipient + BCC Alex
        recipients = [to]
        if to != BCC_ALEX:
            recipients.append(BCC_ALEX)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, recipients, msg.as_string())

        logger.info("E-Mail gesendet an %s (BCC: %s): %s", to, BCC_ALEX, subject)
    except Exception as e:
        logger.error("E-Mail-Fehler an %s: %s", to, str(e))
