import uuid

from sqlalchemy.orm import Session

from mixer.api import models, schemas


def get_track(db: Session, track_id: str):
    return db.query(models.Track).filter(models.Track.id == track_id).first()


def create_track(db: Session, track: schemas.TrackCreate, mix_id: str):
    db_track = models.Track(
        id=str(uuid.uuid4()),
        mix_id=mix_id,
        bucket_id=track.bucket_id,
        filename=track.filename,
        content_type=track.content_type,
    )
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track
