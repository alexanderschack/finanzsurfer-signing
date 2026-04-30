from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from app.database import Base, engine
from app.routers import auth, admin, signing

app = FastAPI(title="Finanzsurfer Signing", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(signing.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(contracts)")).fetchall()]
        if "raten_plan" not in cols:
            conn.execute(text("ALTER TABLE contracts ADD COLUMN raten_plan VARCHAR(200)"))
            conn.commit()


@app.get("/")
async def root():
    return RedirectResponse(url="/admin/contracts", status_code=302)
