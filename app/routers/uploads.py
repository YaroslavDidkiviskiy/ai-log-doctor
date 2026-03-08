from fastapi import APIRouter, Depends, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.upload import Upload
from app.models.incident import Incident
from app.schemas.upload import UploadOut
from app.schemas.incident import IncidentOut
from app.services.file_storage import save_upload, validate_extension
from app.tasks.process_upload import process_upload

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("", response_model=UploadOut, status_code=201)
async def create_upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Upload:
    if not file.filename or not validate_extension(file.filename):
        raise HTTPException(400, "Only .log and .txt files are allowed")

    try:
        stored_name, stored_path = await save_upload(file)
    except ValueError as e:
        raise HTTPException(413, str(e))

    upload = Upload(
        filename=file.filename,
        stored_path=stored_path,
        status="uploaded",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    background_tasks.add_task(process_upload, upload.id)

    return upload


@router.get("", response_model=list[UploadOut])
def list_uploads(db: Session = Depends(get_db)) -> list[Upload]:
    return (
        db.query(Upload).order_by(Upload.created_at.desc()).all()
    )


@router.get("/{upload_id}", response_model=UploadOut)
def get_upload(upload_id: int, db: Session = Depends(get_db)) -> Upload:
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(404, "Upload not found")
    return upload


@router.post("/{upload_id}/process", response_model=UploadOut)
def reprocess_upload(
    upload_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Upload:
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(404, "Upload not found")
    if upload.status == "processing":
        raise HTTPException(409, "Upload is already being processed")

    upload.status = "uploaded"
    db.commit()
    db.refresh(upload)

    background_tasks.add_task(process_upload, upload.id)
    return upload


@router.get("/{upload_id}/incidents", response_model=list[IncidentOut])
def get_upload_incidents(
    upload_id: int, db: Session = Depends(get_db)
) -> list[Incident]:
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(404, "Upload not found")
    return (
        db.query(Incident)
        .filter(Incident.upload_id == upload_id)
        .order_by(Incident.severity.desc(), Incident.count.desc())
        .all()
    )
