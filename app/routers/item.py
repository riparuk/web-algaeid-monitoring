from datetime import date, datetime, time, timedelta
import os
import shutil
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from gtts import gTTS
import pandas as pd
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import crud, models, schemas
from app.dependencies import get_db

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Item not found"}},
)

# Skema untuk nilai sensor
class Value(BaseModel):
    timestamps: Optional[List[int]] = None
    CO2: Optional[List[int]] = None
    DO: Optional[List[int]] = None
    PM2dot5: Optional[List[int]] = None
    Temp: Optional[List[int]] = None
    Humidity: Optional[List[int]] = None
    Turbidity: Optional[List[int]] = None

# Tambahkan CRUD endpoints
@router.post("/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    """
    Create a new item in the database.
    """
    return crud.create_item(db=db, item=item)

@router.get("/{item_id}", response_model=schemas.Item)
def read_item(item_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a single item by its ID.
    """
    db_item = crud.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@router.get("/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Retrieve a list of items with pagination.
    """
    return crud.get_items(db=db, skip=skip, limit=limit)

@router.put("/{item_id}", response_model=schemas.Item)
def update_item(item_id: str, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    """
    Update an existing item by its ID.
    """
    db_item = crud.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.update_item(db=db, item_id=item_id, item=item)

@router.delete("/{item_id}", response_model=schemas.Item)
def delete_item(item_id: str, db: Session = Depends(get_db)):
    """
    Delete an item by its ID.
    """
    db_item = crud.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.delete_item(db=db, item_id=item_id)

@router.put("/{item_id}/activate")
def activate_item(item_id: str, db: Session = Depends(get_db)):
    """
    Activate an item by setting its isActive status to True.
    """
    db_item = crud.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.isActive = True
    db.commit()
    return {"message": "Item activated successfully"}

@router.put("/{item_id}/deactivate")
def deactivate_item(item_id: str, db: Session = Depends(get_db)):
    """
    Deactivate an item by setting its isActive status to False.
    """
    db_item = crud.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.isActive = False
    db.commit()
    return {"message": "Item deactivated successfully"}

def save_to_csv(item_id: str, sensor_data: dict):
    """
    Save sensor data to a CSV file organized by item_id and date.
    If the CSV file already exists, append the new data.
    """
    # Ensure the directory exists
    folder_path = f"data/{item_id}/"
    os.makedirs(folder_path, exist_ok=True)
    
    # Get the current date
    today = datetime.now().date().isoformat()
    file_path = os.path.join(folder_path, f"{today}.csv")
    
    # Prepare data for DataFrame
    data_to_save = {
        "timestamp": sensor_data.get("timestamp", []),
        "CO2": sensor_data.get("CO2", []),
        "DO": sensor_data.get("DO", []),
        "PM2dot5": sensor_data.get("PM2dot5", []),
        "Temp": sensor_data.get("Temp", []),
        "Humidity": sensor_data.get("Humidity", []),
        "Turbidity": sensor_data.get("Turbidity", [])
    }
    
    # Create DataFrame
    df = pd.DataFrame(data_to_save)
    
    # Append to the CSV file if it exists, otherwise create a new file
    if os.path.isfile(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, mode='w', header=True, index=False)

# Endpoint untuk input data sensor berdasarkan item_id dan simpan ke CSV
@router.post("/{item_id}/sensor-data", response_model=Value)
async def add_sensor_data(item_id: str, sensor_data: Value, db: Session = Depends(get_db)):
    """
    Input sensor data for a specific item ID and append it to a CSV file organized by item_id and date.
    """
    # Cari item berdasarkan item_id
    db_item = crud.get_item(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Generate timestamps as UNIX timestamps (integer)
    now = datetime.utcnow() + timedelta(hours=7)  # Adjust to UTC+7
    num_data_points = len(sensor_data.CO2 or [])

    # Calculate the start time in minutes
    start_time = now - timedelta(minutes=num_data_points - 1)

    # Generate timestamps in minutes
    timestamps = [int((start_time + timedelta(minutes=i)).timestamp()) for i in range(num_data_points)]

    # Combine sensor data with timestamps
    data_with_timestamps = {
        "timestamp": timestamps,
        "CO2": sensor_data.CO2,
        "DO": sensor_data.DO,
        "PM2dot5": sensor_data.PM2dot5,
        "Temp": sensor_data.Temp,
        "Humidity": sensor_data.Humidity,
        "Turbidity": sensor_data.Turbidity
    }

    # Save to CSV
    save_to_csv(item_id, data_with_timestamps)
    # Update the `updated_at` timestamp in the database
    db_item.updated_at = datetime.utcnow() + timedelta(hours=7)  # Adjust to UTC+7
    db.commit()

    return sensor_data

# Endpoint untuk mengambil data sensor berdasarkan item_id dan tanggal
@router.get("/sensor-data/{item_id}/date/{day_date}", response_model=Value)
async def get_sensor_data_by_date(item_id: str, day_date: str, interval: str):
    """
    Retrieve sensor data for a specific item ID on a specific date from CSV files.
    """
    try:
        date_obj = date.fromisoformat(day_date)  # Convert the date from string to date object
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    # Retrieve data from the CSV file
    data = crud.get_sensor_data_for_date(item_id=item_id, date=date_obj, interval=interval)
    
    if data is None:
        return Value(
            timestamps=[],
            CO2=[],
            DO=[],
            PM2dot5=[],
            Temp=[],
            Humidity=[],
            Turbidity=[]
        )
    else:
        return Value(
            timestamps=data.get("timestamps", []),
            CO2=data.get("CO2", []),
            DO=data.get("DO", []),
            PM2dot5=data.get("PM2dot5", []),
            Temp=data.get("Temp", []),
            Humidity=data.get("Humidity", []),
            Turbidity=data.get("Turbidity", [])
        )
    
@router.post("/{item_id}/text-to-speech")
async def text_to_speech(item_id: str, text: str):
    """
    Convert text to speech audio and save it as an MP3 file.
    """
    # Generate the speech audio
    tts = gTTS(text)
    audio_file = NamedTemporaryFile(suffix=".mp3", delete=False)
    tts.save(audio_file.name)
    
    # Save the audio file to the appropriate location
    folder_path = f"data/{item_id}/audio/"
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{item_id}.mp3")
    shutil.move(audio_file.name, file_path)
    
    return {"message": "Text converted to speech audio successfully"}

@router.get("/{item_id}/text-to-speech")
async def get_text_to_speech(item_id: str):
    """
    Retrieve the text to speech audio file.
    """
    file_path = f"data/{item_id}/audio/{item_id}.mp3"
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return StreamingResponse(open(file_path, "rb"), media_type="audio/mpeg")
