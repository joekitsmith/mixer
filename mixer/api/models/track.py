from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from mixer.api.database import Base


class Track(Base):
    __tablename__ = "track"

    id = Column(String, primary_key=True, index=True)
    mix_id = Column(String, ForeignKey("mix.id"))
    bucket_id = Column(String)
    filename = Column(String)
    content_type = Column(String)

    mix = relationship("Mix", back_populates="tracks")
