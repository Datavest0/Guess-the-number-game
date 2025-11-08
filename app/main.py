from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Tuple
from sqlalchemy.orm import Session
from random import choice
from . import models
from .database import engine, sessionlocal, get_db

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='templates')

# --- initialize computer_number at app startup (optional) ---
# --- initialize computer_number at module import (minimal change) ---
computer_number: int = None

def init_computer_number(db: Session) -> int:
    last = db.query(models.Guess).order_by(models.Guess.id.desc()).first()
    return last.computer_number if last and last.computer_number is not None else choice(range(1, 101))

# MAKE SURE TABLES EXIST BEFORE QUERYING
# <-- ADD THIS LINE -->
models.Base.metadata.create_all(bind=engine)

# call this once at module import (keeps your original behavior)
_db = sessionlocal()
try:
    computer_number = init_computer_number(_db)
finally:
    _db.close()

# route (direct sync DB usage)
@app.api_route("/", methods=["GET", "POST"], response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    if request.method == "POST":
        form_data = await request.form()
        guess = int(form_data.get("number_guess"))
        result = check_number_show_message(guess, computer_number)

        # insert with SQLAlchemy
        new_row = models.Guess(guess=guess, result=result, computer_number=computer_number)
        db.add(new_row)
        db.commit()

    # fetch guesses (as list of tuples (guess, result))
    rows: List[Tuple] = db.query(models.Guess.guess, models.Guess.result).order_by(models.Guess.id.asc()).all()
    guesses = list(reversed(rows))
    return templates.TemplateResponse("ai.html", {"request": request, "guesses": guesses})


@app.get("/reset", response_class=HTMLResponse)
def reset(request: Request, db: Session = Depends(get_db)):
    global computer_number
    computer_number = choice(range(1, 101))
    # delete all rows
    db.query(models.Guess).delete()
    db.commit()
    return templates.TemplateResponse("ai.html", {"request": request, "guesses": []})


def check_number_show_message(guessed_number, computer_number):
    if guessed_number == computer_number:
        return f'{guessed_number} is correct'
    elif guessed_number < computer_number:
        return f'{guessed_number} is too low'
    else:
        return f'{guessed_number} is too high'