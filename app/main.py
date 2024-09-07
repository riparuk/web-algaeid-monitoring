from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.db import models
from app.db.database import engine
from app.routers import web, item

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(item.router)
app.include_router(web.router)