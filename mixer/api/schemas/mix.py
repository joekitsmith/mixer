from typing import Optional

from pydantic import BaseModel

from mixer.api.schemas.track import Track


class MixBase(BaseModel):
    pass


class Mix(BaseModel):
    id: str
    tracks: Optional[list[Track]]

    class Config:
        orm_mode = True


class MixDelete(BaseModel):
    message: str
