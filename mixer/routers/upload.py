import io
import os

from fastapi import APIRouter, HTTPException, UploadFile
from minio import Minio
from minio.error import S3Error

upload_router = APIRouter(prefix="/upload")

MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"]
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]
MINIO_BUCKET = "my-bucket"

# Create a MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,  # Change to True if your MinIO uses HTTPS
)

# Ensure the bucket exists
if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)


@upload_router.post("/")
async def upload_track(file: UploadFile):
    # Validate file format
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
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "etag": result.etag,
        }
    except S3Error as exc:
        raise HTTPException(
            status_code=500, detail=f"Error saving to MinIO: {exc}"
        ) from exc
