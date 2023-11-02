import os

from minio import Minio

MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"]
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]
MINIO_BUCKET = "my-bucket"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,  # Change to True if your MinIO uses HTTPS
)

if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)
