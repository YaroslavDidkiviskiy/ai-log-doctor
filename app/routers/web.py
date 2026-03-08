from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.upload import Upload
from app.models.incident import Incident
from app.services.file_storage import save_upload, validate_extension
from app.tasks.process_upload import process_upload

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    recent = db.query(Upload).order_by(Upload.created_at.desc()).limit(10).all()
    return templates.TemplateResponse(request, "index.html", {"uploads": recent})


@router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not file.filename or not validate_extension(file.filename):
        recent = db.query(Upload).order_by(Upload.created_at.desc()).limit(10).all()
        return templates.TemplateResponse(
            request, "index.html",
            {"uploads": recent, "error": "Only .log and .txt files are allowed"},
        )

    try:
        stored_name, stored_path = await save_upload(file)
    except ValueError as e:
        recent = db.query(Upload).order_by(Upload.created_at.desc()).limit(10).all()
        return templates.TemplateResponse(
            request, "index.html", {"uploads": recent, "error": str(e)},
        )

    upload = Upload(filename=file.filename, stored_path=stored_path, status="uploaded")
    db.add(upload)
    db.commit()
    db.refresh(upload)

    background_tasks.add_task(process_upload, upload.id)
    return RedirectResponse(f"/uploads/{upload.id}", status_code=303)


@router.get("/uploads", response_class=HTMLResponse)
def uploads_list(request: Request, db: Session = Depends(get_db)):
    all_uploads = db.query(Upload).order_by(Upload.created_at.desc()).all()
    return templates.TemplateResponse(request, "uploads.html", {"uploads": all_uploads})


@router.get("/uploads/{upload_id}", response_class=HTMLResponse)
def upload_detail(request: Request, upload_id: int, db: Session = Depends(get_db)):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(404, "Upload not found")
    incidents = (
        db.query(Incident)
        .filter(Incident.upload_id == upload_id)
        .order_by(Incident.count.desc())
        .all()
    )
    return templates.TemplateResponse(
        request, "upload_detail.html", {"upload": upload, "incidents": incidents},
    )


@router.get("/uploads/{upload_id}/status", response_class=HTMLResponse)
def upload_status_fragment(
    request: Request, upload_id: int, db: Session = Depends(get_db)
):
    """HTMX endpoint: returns just the status badge for polling."""
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(404)
    return templates.TemplateResponse(
        request, "fragments/upload_status.html", {"upload": upload},
    )


@router.get("/incidents/{incident_id}", response_class=HTMLResponse)
def incident_detail(
    request: Request, incident_id: int, db: Session = Depends(get_db)
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return templates.TemplateResponse(
        request, "incident_detail.html", {"incident": incident},
    )
