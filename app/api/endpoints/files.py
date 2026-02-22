import os
import uuid
import boto3
import botocore
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.api import deps
from app.db import models, database
from app.schemas import file as file_schema
from app.core.config import settings

router = APIRouter()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION_NAME
)

@router.post("/upload", response_model=file_schema.FileResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(database.get_db),
    current_user_id: int = Depends(deps.get_current_user)
):
    """
    Upload a new file.
    """
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    s3_key = unique_filename
    
    # Calculate file size before passing the stream to boto3
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    try:
        s3_client.upload_fileobj(
            file.file,
            settings.AWS_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": file.content_type}
        )
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == 'NoSuchBucket':
            try:
                # Attempt to create the bucket
                if settings.AWS_REGION_NAME == "us-east-1" or not settings.AWS_REGION_NAME:
                    s3_client.create_bucket(Bucket=settings.AWS_BUCKET_NAME)
                else:
                    s3_client.create_bucket(
                        Bucket=settings.AWS_BUCKET_NAME,
                        CreateBucketConfiguration={
                            'LocationConstraint': settings.AWS_REGION_NAME
                        }
                    )
                
                # Retry the upload
                file.file.seek(0)
                s3_client.upload_fileobj(
                    file.file,
                    settings.AWS_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={"ContentType": file.content_type}
                )
            except Exception as create_upload_e:
                raise HTTPException(status_code=500, detail=f"Bucket did not exist. Tried creating it, but failed: {str(create_upload_e)}")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file to S3: {str(e)}")
    
    db_file = models.FileRecord(
        user_id=current_user_id,
        sys_filename=unique_filename,
        original_filename=file.filename,
        content_type=file.content_type,
        file_path=s3_key,
        size=file_size
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file

@router.get("/", response_model=List[file_schema.FileResponse])
def list_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user_id: int = Depends(deps.get_current_user)
):
    """
    List uploaded files for the current user.
    """
    files = db.query(models.FileRecord).filter(models.FileRecord.user_id == current_user_id).offset(skip).limit(limit).all()
    return files

@router.get("/{file_id}", response_model=file_schema.FileResponse)
def get_file_info(
    file_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: int = Depends(deps.get_current_user)
):
    """
    Get file metadata.
    """
    file_record = db.query(models.FileRecord).filter(models.FileRecord.id == file_id, models.FileRecord.user_id == current_user_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    return file_record

@router.get("/{file_id}/show")
def show_file(
    file_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: int = Depends(deps.get_current_user)
):
    """
    Show file inline in the browser.
    """
    file_record = db.query(models.FileRecord).filter(models.FileRecord.id == file_id, models.FileRecord.user_id == current_user_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_BUCKET_NAME,
                'Key': file_record.file_path,
                'ResponseContentDisposition': f'inline; filename="{file_record.original_filename}"',
                'ResponseContentType': file_record.content_type
            },
            ExpiresIn=3600
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not generate URL")

@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: int = Depends(deps.get_current_user)
):
    """
    Download the file.
    """
    file_record = db.query(models.FileRecord).filter(models.FileRecord.id == file_id, models.FileRecord.user_id == current_user_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_BUCKET_NAME,
                'Key': file_record.file_path,
                'ResponseContentDisposition': f'attachment; filename="{file_record.original_filename}"'
            },
            ExpiresIn=3600
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not generate URL")
