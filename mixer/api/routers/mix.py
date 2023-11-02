import tempfile

import soundfile as sf
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from mixer.api import schemas
from mixer.api.crud import crud_mix
from mixer.api.database import get_db
from mixer.api.minio_client import minio_client
from mixer.processors.sync import get_track_groups, mix_track_group
from mixer.processors.track import SAMPLE_RATE, TrackProcessor

mix_router = APIRouter(prefix="/mix", tags=["Mix"])


@mix_router.post("/", response_model=schemas.Mix)
def create_mix(response: Response, db: Session = Depends(get_db)):
    """
    Create a mix and attach the ID to a cookie.

    Returns
    -------
    mix : schemas.Mix
        Mix created in DB
    """
    mix = crud_mix.create_mix(db)
    response.set_cookie(key="mix_id", value=mix.id)
    return mix


@mix_router.get("/", response_model=schemas.Mix)
def get_current_mix(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    """
    Get the mix that is associated with the ID stored in the request cookie if it exists.

    Returns
    -------
    mix : schemas.Mix
        Mix created in database

    Raises
    ------
    HTTPException
        If the mix ID request cookie is not present, a 400 error is raised
    HTTPException
        If a mix could not be retrieved from the database using the ID, a 404 error is raised
    """
    mix_id = request.cookies.get("mix_id")
    if not mix_id:
        raise HTTPException(
            status_code=400, detail="A mix could not be found in the current session"
        )
    mix = crud_mix.get_mix(db, mix_id)
    if not mix:
        raise HTTPException(
            status_code=404,
            detail="A mix with ID {mix_id} could not be found in the database",
        )
    return mix


@mix_router.get("/{mix_id}", response_model=schemas.Mix)
def get_mix_by_id(mix_id: str, db: Session = Depends(get_db)):
    """
    Get a mix by its ID if it exists.

    Parameters
    ----------
    mix_id : str
        ID of mix in database

    Returns
    -------
    mix : schemas.Mix
        Mix created in database

    Raises
    ------
    HTTPException
        If a mix could not be retrieved from the database using the ID, a 404 error is raised
    """
    mix = crud_mix.get_mix(db, mix_id)
    if not mix:
        raise HTTPException(
            status_code=404, detail=f"A mix could not be found with ID {mix.id}"
        )
    return mix


@mix_router.delete("/", response_model=schemas.MixDelete)
def discard_mix(request: Request, response: Response):
    """
    Remove the mix ID request cookie if it exists.

    Returns
    -------
    mix : schemas.MixDelete
        message describing discard action taken, if any
    """
    mix_id = request.cookies.get("mix_id")
    if not mix_id:
        return {"message": "No mix found in session"}
    response.delete_cookie("mix_id")
    return {"message": f"Mix {mix_id} removed from session"}


@mix_router.post("/process")
def process_mix(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> FileResponse:
    """
    Trigger processing of the mix using uploaded tracks and designated cue points.

    Parameters
    ----------


    Returns
    -------
    mix : schemas.MixProcess
        message describing mix processing status
    """
    mix = get_current_mix(request, response, db)

    tracklist = []
    for track in mix.tracks:
        audio = minio_client.get_object(track.bucket_id, track.filename)
        with tempfile.NamedTemporaryFile(delete=True) as temp:
            for a in audio.stream():
                temp.write(a)
            temp.flush()

            track_proc = TrackProcessor(temp.name)
            track_proc.load()
            track_proc.calculate_bpm()
            track_proc.calculate_downbeats()
            tracklist.append(track_proc)

    track_groups = get_track_groups(tracklist)
    track_group = max(track_groups, key=lambda x: len(x.tracks))
    combined_audio = mix_track_group(track_group)

    output_path = f"{mix.id}.mp3"
    sf.write(output_path, combined_audio, int(SAMPLE_RATE))

    return FileResponse(output_path)
