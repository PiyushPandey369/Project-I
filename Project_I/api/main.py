from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.route import router

app = FastAPI(title="AQI Prediction API")

app.mount("/static", StaticFiles(directory="api/static"), name="static")

app.include_router(router)