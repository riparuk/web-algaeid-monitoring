from datetime import date, timedelta, datetime
import io
import os
from typing import Dict, List, Optional
from matplotlib import pyplot as plt
import pandas as pd
from sqlalchemy.orm import Session
from . import models, schemas
import plotly.graph_objects as go


# Create (Insert) a new item
def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(
        id=item.id,  # Convert UUID to string before storing in SQLite
        name=item.name,
        isActive=item.isActive,
        isCO2=item.isCO2,
        isDO=item.isDO,
        isPM2dot5=item.isPM2dot5,
        isTemp=item.isTemp,
        isHumidity=item.isHumidity,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Read (Retrieve) an item by ID
def get_item(db: Session, item_id: str):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

# Read (Retrieve) all items
def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

# Update an existing item by ID
def update_item(db: Session, item_id: str, item: schemas.ItemCreate):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        db_item.name = item.name
        db_item.isActive = item.isActive
        db_item.isCO2 = item.isCO2
        db_item.isDO = item.isDO
        db_item.isPM2dot5 = item.isPM2dot5
        db_item.isTemp = item.isTemp
        db_item.isHumidity = item.isHumidity
        db.commit()
        db.refresh(db_item)
    return db_item

# Delete an item by ID
def delete_item(db: Session, item_id: str):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item

def get_sensor_data_for_date(item_id: str, date: date, interval: str = 'minute') -> Optional[Dict[str, Optional[List[Optional[float]]]]]:
    """
    Retrieve sensor data for a specific item ID on a specific date from CSV files,
    and include timestamps for each data point. Data can be aggregated by 'second', 'minute', or 'hour'.
    """
    # Prepare to collect all data
    all_data = {
        "timestamps": [],
        "CO2": [],
        "DO": [],
        "PM2dot5": [],
        "Temp": [],
        "Humidity": []
    }

    # Format the date to match the CSV file naming convention
    date_str = date.isoformat()  # YYYY-MM-DD
    folder_path = f"data/{item_id}/"
    
    try:
        # Read the CSV file for the specific date
        file_path = os.path.join(folder_path, f"{date_str}.csv")
        if not os.path.isfile(file_path):
            return None
        
        df = pd.read_csv(file_path)

        # Convert the timestamp column to datetime if available
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

        # Determine the frequency for resampling based on the interval
        if interval == 'minute':
            resample_freq = 'T'  # minute-level resampling
        elif interval == 'hour':
            resample_freq = 'H'  # hour-level resampling
        else:
            resample_freq = 'S'  # second-level (default)

        # Resample data based on the selected interval
        df_resampled = df.set_index('timestamp').resample(resample_freq).mean()

        # Convert the index (timestamps) to a list of UNIX timestamps
        all_data['timestamps'] = df_resampled.index.astype('int64') // 10**9  # Convert back to UNIX timestamps
        all_data['timestamps'] = all_data['timestamps'].tolist()  # Ensure it's a list for serialization

        # Fill sensor data with the resampled data, and convert to integers
        all_data['CO2'] = [int(value) for value in df_resampled['CO2'].tolist() if pd.notna(value)]
        all_data['DO'] = [int(value) for value in df_resampled['DO'].tolist() if pd.notna(value)]
        all_data['PM2dot5'] = [int(value) for value in df_resampled['PM2dot5'].tolist() if pd.notna(value)]
        all_data['Temp'] = [int(value) for value in df_resampled['Temp'].tolist() if pd.notna(value)]
        all_data['Humidity'] = [int(value) for value in df_resampled['Humidity'].tolist() if pd.notna(value)]


    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    return all_data

def plot_interactive_sensor_data(item_id: str, date: date, sensors: List[str]) -> io.BytesIO:
    """
    Plot selected sensor data for a specific item ID on a specific date and return the plot as a BytesIO object.
    """
    # Format the date to match the CSV file naming convention
    date_str = date.isoformat()  # YYYY-MM-DD
    folder_path = f"data/{item_id}/"
    
    # Create a BytesIO object to save the plot
    buffer = io.BytesIO()
    
    try:
        # Read the CSV file for the specific date
        file_path = os.path.join(folder_path, f"{date_str}.csv")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"No data file found for date {date_str}.")
        
        df = pd.read_csv(file_path)
        
        # Plotting
        fig = go.Figure()
        for sensor in sensors:
            if sensor in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df[sensor], mode='lines', name=sensor))
        
        fig.update_layout(
            title=f'Sensor Data for {item_id} on {date_str}',
            xaxis_title='Time (Seconds)',
            yaxis_title='Sensor Values'
        )
        
        # Save plot to BytesIO object
        fig.write_image(buffer, format='png')
        buffer.seek(0)
        
        return buffer
        
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for {date_str}.")
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")
    