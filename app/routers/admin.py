import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.contract import Contract
from app.services.contract_service import render_contract_html
from app.templates_instance import templates

router = APIRouter(prefix="/admin")


@router.get("/", include_in_schema=False)
async def admin_root(user: User = Depends(get_current_user)):
    return RedirectResponse(url="/admin/contracts", status_code=302)


@router.get("/contracts", response_class=HTMLResponse)
async def contract_list(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contracts = db.query(Contract).order_by(Contract.id.desc()).all()
    return templates.TemplateResponse("admin/list.html", {
        "request": request,
        "user": user,
        "contracts": contracts,
    })


@router.get("/contracts/new", response_class=HTMLResponse)
async def contract_form(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse("admin/create.html", {
        "request": request,
        "user": user,
    })


@router.post("/contracts")
async def contract_create(
    request: Request,
    vorname: str = Form(...),
    nachname: str = Form(...),
    strasse: str = Form(...),
    plz_ort: str = Form(...),
    email: str = Form(...),
    mobil: str = Form(...),
    betrag_gesamt: int = Form(...),
    raten: int = Form(0),
    rate: int = Form(0),
    startdatum: str = Form(...),
    wochen: int = Form(14),
    bonus: str = Form(""),
    gueltig_tage: int = Form(14),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Render contract HTML
    contract_html = render_contract_html(
        vorname=vorname, nachname=nachname, strasse=strasse,
        plz_ort=plz_ort, email=email, mobil=mobil,
        betrag_gesamt=betrag_gesamt, raten=raten, rate=rate,
        startdatum=startdatum, wochen=wochen, bonus=bonus or None,
    )

    now = datetime.now()
    contract = Contract(
        token=secrets.token_urlsafe(32),
        vorname=vorname,
        nachname=nachname,
        strasse=strasse,
        plz_ort=plz_ort,
        email=email,
        mobil=mobil,
        betrag_gesamt=betrag_gesamt,
        raten=raten,
        rate=rate,
        startdatum=startdatum,
        wochen=wochen,
        bonus=bonus or None,
        contract_html=contract_html,
        status="pending",
        created_at=now.isoformat(),
        expires_at=(now + timedelta(days=gueltig_tage)).isoformat(),
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    return RedirectResponse(
        url="/admin/contracts/%d" % contract.id,
        status_code=302,
    )


@router.get("/contracts/{contract_id}", response_class=HTMLResponse)
async def contract_detail(
    contract_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        return RedirectResponse(url="/admin/contracts", status_code=302)

    base_url = str(request.base_url).rstrip("/")
    sign_url = "%s/v/%s" % (base_url, contract.token)

    return templates.TemplateResponse("admin/detail.html", {
        "request": request,
        "user": user,
        "contract": contract,
        "sign_url": sign_url,
    })
