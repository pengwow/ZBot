import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

host = "0.0.0.0"
port = 18000


@fastapi_app.get("/")
async def root():
    return {"message": "Hello World"}


uvicorn.run(fastapi_app, host=host, port=port, log_level="info")