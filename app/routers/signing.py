from datetime import datetime
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contract import Contract
from app.services.email_service import send_signing_confirmation
from app.services.pdf_service import generate_signed_pdf
from app.templates_instance import templates

router = APIRouter()


def _get_contract_or_none(db: Session, token: str):
    return db.query(Contract).filter(Contract.token == token).first()


@router.get("/v/{token}", response_class=HTMLResponse)
async def view_contract(token: str, request: Request, db: Session = Depends(get_db)):
    contract = _get_contract_or_none(db, token)

    if not contract:
        return templates.TemplateResponse("public/expired.html", {
            "request": request,
            "reason": "not_found",
        })

    if contract.status == "signed":
        return templates.TemplateResponse("public/contract.html", {
            "request": request,
            "contract": contract,
            "signed": True,
        })

    if contract.is_expired:
        return templates.TemplateResponse("public/expired.html", {
            "request": request,
            "reason": "expired",
        })

    return templates.TemplateResponse("public/contract.html", {
        "request": request,
        "contract": contract,
        "signed": False,
    })


@router.post("/v/{token}/sign")
async def sign_contract(
    token: str,
    request: Request,
    signed_name: str = Form(...),
    zustimmung: str = Form(...),
    db: Session = Depends(get_db),
):
    contract = _get_contract_or_none(db, token)

    if not contract or contract.status == "signed" or contract.is_expired:
        return RedirectResponse(url="/v/%s" % token, status_code=302)

    # Save signature
    contract.signed_name = signed_name.strip()
    contract.signed_at = datetime.now().isoformat()
    contract.signed_ip = request.client.host if request.client else "unknown"
    contract.signed_user_agent = request.headers.get("user-agent", "unknown")
    contract.status = "signed"
    db.commit()

    # Generate PDF and send confirmation emails (non-blocking on failure)
    base_url = str(request.base_url).rstrip("/")
    try:
        pdf_bytes = generate_signed_pdf(contract)
    except Exception:
        pdf_bytes = None

    try:
        send_signing_confirmation(contract, base_url, pdf_bytes=pdf_bytes)
    except Exception:
        pass  # Email failure should not break the signing flow

    return RedirectResponse(url="/v/%s/bestaetigung" % token, status_code=302)


@router.get("/v/{token}/bestaetigung", response_class=HTMLResponse)
async def confirmation(token: str, request: Request, db: Session = Depends(get_db)):
    contract = _get_contract_or_none(db, token)

    if not contract or contract.status != "signed":
        return RedirectResponse(url="/v/%s" % token, status_code=302)

    return templates.TemplateResponse("public/confirmed.html", {
        "request": request,
        "contract": contract,
    })
