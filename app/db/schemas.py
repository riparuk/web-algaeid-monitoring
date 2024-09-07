from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

class ItemBase(BaseModel):
    id: str
    name: str
    isActive: bool
    isCO2: bool
    isDO: bool
    isPM2dot5: bool
    isTemp: bool
    isHumidity: bool

class ItemCreate(ItemBase):
    # Pastikan id dan name tidak boleh kosong
    id: str = Field(..., min_length=1, description="ID cannot be empty")
    name: str = Field(..., min_length=1, description="Name cannot be empty")

class Item(ItemBase):
    updated_at: datetime  # Add this line to include the updated_at field

    class Config:
        from_attributes = True