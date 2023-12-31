import io
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from minio.error import S3Error
from sqlalchemy.orm import Session

from mixer.api import schemas
from mixer.api.crud import crud_track
from mixer.api.database import get_db
from mixer.api.minio_client import MINIO_BUCKET, minio_client
from mixer.processors.track import TrackProcessor

track_router = APIRouter(prefix="/track", tags=["Track"])


@track_router.post("/", response_model=schemas.Track)
async def add_track(request: Request, file: UploadFile, db: Session = Depends(get_db)):
    """
    Upload a track to the minio bucket and add it to the current mix.

    Parameters
    ----------
    file : UploadFile
        audio file

    Returns
    -------
    track : schemas.Track
        track added to database with minio metadata

    Raises
    ------
    HTTPException
        If the mix ID request cookie is not present, a 400 error is raised
    HTTPException
        If the audio file does not have a filename or content type, a 400 error is raised
    HTTPException
        If the audio file is not the correct format, a 400 error is raised
    HTTPException
        If the audio file could not be saved to minio, a 500 error is raised
    """
    mix_id = request.cookies.get("mix_id")
    if not mix_id:
        raise HTTPException(
            status_code=400,
            detail="Mix not found. Create a mix then add the track again.",
        )

    # Validate file format
    if file.filename is None or file.content_type is None:
        raise HTTPException(status_code=400, detail="Invalid file")
    if not file.filename.endswith((".mp3", ".wav")):
        raise HTTPException(status_code=400, detail="Invalid file format")

    try:
        # Save the file to MinIO
        file_data = file.file.read()
        file_data_stream = io.BytesIO(file_data)

        result = minio_client.put_object(
            MINIO_BUCKET,
            file.filename,
            data=file_data_stream,
            length=len(file_data),
            content_type=file.content_type,
        )
        track = schemas.TrackCreate(
            bucket_id=result.bucket_name,
            filename=file.filename,
            content_type=file.content_type,
        )
        db_track = crud_track.create_track(db, track, mix_id)
        return db_track

    except S3Error as exc:
        raise HTTPException(
            status_code=500, detail=f"Error saving to MinIO: {exc}"
        ) from exc


@track_router.get("/{track_id}", response_model=schemas.Track)
def get_track_by_id(track_id: str, db: Session = Depends(get_db)):
    """
    Get a track's metadata using its ID, if it exists.

    Parameters
    ----------
    track_id : str
        ID of track in database

    Returns
    -------
    track : schemas.Track
        track metadata

    Raises
    ------
    HTTPException
        If the track could not be found, a 404 error is raised
    """
    track = crud_track.get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found.")
    return track


@track_router.get("/{track_id}/analysis", response_model=schemas.TrackAnalysis)
def get_track_analysis(
    track_id: str, downbeats: bool = True, db: Session = Depends(get_db)
):
    """
    Get the time points of a track's downbeats.

    Parameters
    ----------
    track_id : str
        ID of track in database
    downbeats : bool
        If downbeats should be calculated for track

    Returns
    -------
    track_analysis : schemas.TrackAnalysis
        analysis of track including tempo and downbeats

    Raises
    ------
    HTTPException
        If tempo could not be calculated for a track, a 500 error is raised
    HTTPException
        If the track could not be found, a 404 error is raised
    """
    track = crud_track.get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found.")

    audio = minio_client.get_object(track.bucket_id, track.filename)

    with tempfile.NamedTemporaryFile(delete=True) as temp:
        for a in audio.stream():
            temp.write(a)
        temp.flush()

        track_processor = TrackProcessor(temp.name, name=track.filename)
        track_processor.load()
        track_processor.calculate_bpm()
        if track_processor.bpm is None:
            raise HTTPException(
                status_code=500,
                detail=f"Tempo could not be calculated for {track.filename}",
            )

        track_analysis = schemas.TrackAnalysis(
            track_id=track.id, bpm=track_processor.bpm, downbeats=None
        )
        if downbeats:
            track_processor.calculate_downbeats()
            track_analysis.downbeats = track_processor.downbeats.tolist()

    return track_analysis
