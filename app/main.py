from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
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


@app.get("/")
async def root():
    return RedirectResponse(url="/admin/contracts", status_code=302)
