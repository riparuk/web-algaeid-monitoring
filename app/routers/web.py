from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from typing import Optional

from requests import Session
from app.db import crud
from datetime import date

from app.dependencies import get_db

router = APIRouter(
    tags=["web"],
    responses={404: {"description": "Not found"}},
)

# Initialize Jinja2Templates
templates = Jinja2Templates(directory="app/templates")

# Endpoint untuk menampilkan dashboard
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Menampilkan list items di dashboard.
    """
    # Ambil semua items dari database
    items = crud.get_items(db)
    
    # Render template dashboard dengan data items
    return templates.TemplateResponse("index.html", {"request": request, "items": items})

# Endpoint untuk menampilkan halaman form tambah item
@router.get("/add", response_class=HTMLResponse)
async def add_item_form(request: Request):
    """
    Menampilkan form untuk menambahkan item baru.
    """
    return templates.TemplateResponse("add.html", {"request": request})

@router.get("/lamp/{item_id}", response_class=HTMLResponse)
async def sensor_dashboard(item_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Menampilkan halaman dashboard sensor untuk mengambil data berdasarkan item_id dan tanggal.
    """
    # Fetch data items dari database jika diperlukan
    item = crud.get_item(db=db, item_id=item_id)

    # Kirim items ke template jika perlu
    return templates.TemplateResponse("lamp.html", {"request": request, "item": item})

@router.get("/visualize/{item_id}/{day_date}", response_class=HTMLResponse)
async def visualize(item_id: str, day_date: str, request: Request):
    """
    Serve the visualization page with data for a specific item ID on a specific date.
    """
    try:
        date_obj = date.fromisoformat(day_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    try:
        data_dict = crud.get_sensor_data_for_date(item_id=item_id, date=date_obj)
        return templates.TemplateResponse("visualize.html", {"request": request, "data": data_dict})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))