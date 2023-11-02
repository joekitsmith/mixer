import uuid

from sqlalchemy.orm import Session

from mixer.api import models


def get_mix(db: Session, mix_id: str):
    return db.query(models.Mix).filter(models.Mix.id == mix_id).first()


def create_mix(db: Session):
    db_mix = models.Mix(id=str(uuid.uuid4()))
    db.add(db_mix)
    db.commit()
    db.refresh(db_mix)
    return db_mix
