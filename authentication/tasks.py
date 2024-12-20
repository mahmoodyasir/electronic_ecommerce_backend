import boto3
from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage
import mimetypes

@shared_task
def upload_user_image_to_s3_task(temp_file_path, file_name):
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        # Construct the destination file path in S3
        s3_file_path = f"users/{file_name}"

        # Upload the file from the temporary location to S3
        with default_storage.open(temp_file_path, 'rb') as file_data:
            s3_client.upload_fileobj(
                file_data,
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_file_path,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': mimetypes.guess_type(file_name)[0] or 'application/octet-stream',
                    'ContentDisposition': 'inline'
                }
            )
            
        image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_file_path}"

        default_storage.delete(temp_file_path)

        return image_url

    except Exception as e:
        return str(e)