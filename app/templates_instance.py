from fastapi.templating import Jinja2Templates
from datetime import date as _date

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["enumerate"] = enumerate
templates.env.globals["now"] = _date.today()
