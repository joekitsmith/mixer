from typing import Optional

from pydantic import BaseModel


class TrackBase(BaseModel):
    bucket_id: str
    filename: str
    content_type: str


class TrackCreate(TrackBase):
    pass


class Track(TrackBase):
    id: str
    mix_id: str

    class Config:
        orm_mode = True


class TrackAnalysis(BaseModel):
    track_id: str
    bpm: float
    downbeats: Optional[list[float]]
