from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from .database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    isActive = Column(Boolean, default=False)
    isCO2 = Column(Boolean, default=False)
    isDO = Column(Boolean, default=False)
    isPM2dot5 = Column(Boolean, default=False)
    isTemp = Column(Boolean, default=False)
    isHumidity = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Track last update time