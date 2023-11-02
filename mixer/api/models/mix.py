from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from mixer.api.database import Base


class Mix(Base):
    __tablename__ = "mix"

    id = Column(String, primary_key=True, index=True)

    tracks = relationship("Track", back_populates="mix")
