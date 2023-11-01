from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mixer.api.database import Base, engine
from mixer.api.routers.mix import mix_router
from mixer.api.routers.track import track_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(track_router)
app.include_router(mix_router)


@app.get("/health", tags=["health_check"])
def health_check():
    """Health check"""
    return {"message": "Server is healthy"}
