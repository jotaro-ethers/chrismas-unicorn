import os
import json
import time
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import boto3
from dotenv import load_dotenv
import aiofiles

# Application-specific imports (keep existing app structure)
from app.config import get_settings
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.routers import health, webhook, transactions

# Load .env (if used)
load_dotenv()

# Settings
settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
    )

    # Register CORS middleware
    # Include CloudFront/S3 origins explicitly for proper CORS support
    explicit_origins = [
        "https://ourxmas.pics",
        "https://www.ourxmas.pics",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=explicit_origins,
        # allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    from fastapi.exceptions import RequestValidationError
    from fastapi import HTTPException

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Register routers (existing modules)
    try:
        app.include_router(health.router)
        app.include_router(webhook.router)
        app.include_router(transactions.router)
    except Exception:
        # If those routers are not present in some setups, don't fail here.
        pass

    return app


app = create_app()

# --- Static files (admin UI + preview) ---
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
# Ensure the public and preview directories exist
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
(PUBLIC_DIR / "preview").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

# --- AWS / S3 client setup (use env fallback) ---
S3_BUCKET = os.getenv("S3_BUCKET_NAME") or getattr(settings, "S3_BUCKET_NAME", None)
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL") or getattr(settings, "S3_PUBLIC_URL", None)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") or getattr(
    settings, "AWS_ACCESS_KEY_ID", None
)
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or getattr(
    settings, "AWS_SECRET_ACCESS_KEY", None
)
AWS_REGION = os.getenv("AWS_REGION") or getattr(settings, "AWS_REGION", "us-east-1")
PORT = int(os.getenv("PORT", getattr(settings, "PORT", 3000)))
DOMAIN = os.getenv("DOMAIN") or getattr(settings, "DOMAIN", "ourxmas.pics")

# Create boto3 client only if credentials or role exist
s3_client = None
try:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
except Exception:
    s3_client = None


def generate_html(config: dict, image_count: int) -> str:
    """Generate HTML for the Christmas experience using chosen tree template."""
    image_paths = [f"./image{i+1}.jpeg" for i in range(image_count)]
    image_list_js = ", ".join([json.dumps(p) for p in image_paths])

    template_path = PUBLIC_DIR / f"{config.get('treeType', 'tree1')}.html"
    if not template_path.exists():
        template_path = PUBLIC_DIR / "tree1.html"

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    html_content = template.replace(
        "LOVE_TEXT", json.dumps(config.get("loveText", ""))
    ).replace("IMAGE_LIST", image_list_js)
    html_content = html_content.replace("PHOTO_COUNT", json.dumps(image_count))
    # Optionally replace foliage count and colors if templates use these tokens
    html_content = html_content.replace(
        "FOLIAGE_COUNT", json.dumps(config.get("foliageCount", 15000))
    )
    html_content = html_content.replace(
        "MAIN_TITLE", json.dumps(config.get("mainTitle", "MERRY CHRISTMAS"))
    )
    html_content = html_content.replace(
        "TREE_COLOR", json.dumps(config.get("treeColor", "#004225"))
    )
    html_content = html_content.replace(
        "ACCENT_COLOR", json.dumps(config.get("accentColor", "#FFD700"))
    )
    return html_content


async def upload_to_s3(project_id: str, folder: str, files_dict: dict) -> str:
    """Upload files (bytes + content_type) to S3 and return public URL (prefers S3_PUBLIC_URL)."""
    if not s3_client:
        raise RuntimeError("S3 client not configured")

    bucket = S3_BUCKET
    if not bucket:
        raise RuntimeError("S3 bucket not configured (S3_BUCKET_NAME)")

    base_key = f"{project_id}"
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=4)

    # HTML
    html_content = files_dict["html"]
    await loop.run_in_executor(
        executor,
        lambda: s3_client.put_object(
            Bucket=bucket,
            Key=f"{base_key}/index.html",
            Body=html_content.encode("utf-8"),
            ContentType="text/html",
        ),
    )

    # Body images (all converted to JPEG)
    for idx, img in enumerate(files_dict["bodyImages"]):
        fname = f"image{idx+1}.jpeg"
        key = f"{base_key}/{fname}"
        data = img["data"]
        content_type = img.get("content_type", "image/jpeg")
        await loop.run_in_executor(
            executor,
            lambda _key=key, _data=data, _ct=content_type: s3_client.put_object(
                Bucket=bucket, Key=_key, Body=_data, ContentType=_ct
            ),
        )

    # Music - use user uploaded or default audio.mp3 from public folder
    music = files_dict.get("music")
    if music:
        # User uploaded custom music
        key = f"{base_key}/audio.mp3"
        data = music["data"]
        content_type = music.get("content_type", "audio/mpeg")
        await loop.run_in_executor(
            executor,
            lambda _key=key, _data=data, _ct=content_type: s3_client.put_object(
                Bucket=bucket, Key=_key, Body=_data, ContentType=_ct
            ),
        )
    else:
        # Use default audio.mp3 from public folder
        default_audio_path = PUBLIC_DIR / "audio.mp3"
        if default_audio_path.exists():
            with open(default_audio_path, "rb") as f:
                audio_data = f.read()
            key = f"{base_key}/audio.mp3"
            await loop.run_in_executor(
                executor,
                lambda _key=key, _data=audio_data: s3_client.put_object(
                    Bucket=bucket, Key=_key, Body=_data, ContentType="audio/mpeg"
                ),
            )

    # Build public URL
    return f"https://{project_id}.{DOMAIN}"


async def save_locally(project_id: str, files_dict: dict) -> str:
    """Save files locally for preview (preserve filenames/extensions)"""
    preview_dir = Path(f"public/preview/{project_id}")
    preview_dir.mkdir(parents=True, exist_ok=True)

    # HTML
    async with aiofiles.open(preview_dir / "index.html", "w", encoding="utf-8") as f:
        await f.write(files_dict["html"])

    for idx, img in enumerate(files_dict["bodyImages"]):
        fname = img.get("filename", f"image{idx+1}.jpeg")
        async with aiofiles.open(preview_dir / fname, "wb") as f:
            await f.write(img["data"])

    music = files_dict.get("music")
    if music:
        fname = music.get("filename", "audio.mp3")
        async with aiofiles.open(preview_dir / fname, "wb") as f:
            await f.write(music["data"])

    return f"http://localhost:{PORT}/preview/{project_id}/index.html"


# --- Endpoints (admin UI, generate, preview) ---


@app.get("/")
async def root():
    return FileResponse(str(PUBLIC_DIR / "admin.html"))


@app.get("/admin")
async def admin():
    return FileResponse(str(PUBLIC_DIR / "admin.html"))


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": time.time(),
        "service": "Christmas Experience Generator",
    }


@app.post("/api/validate")
async def validate_request(request: Request):
    """Validate form data before payment - returns validation result without generating."""
    from app.validators import validate_generate_request, ValidationError

    form = await request.form()

    try:
        await validate_generate_request(form)
        return {"valid": True}
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"valid": False, "error": "Validation failed", "errors": e.errors},
        )


@app.post("/api/generate")
async def generate(request: Request):
    """Generate and deploy Christmas experience (handles arbitrary file fields)"""
    from app.validators import validate_generate_request, ValidationError

    start_time = time.time()
    form = await request.form()

    # Validate request using validator
    try:
        validated_data = await validate_generate_request(form)
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Validation failed",
                "errors": e.errors,
            },
        )

    # Extract validated data
    projectName = validated_data["projectName"]
    treeType = validated_data["treeType"]
    mainTitle = validated_data["mainTitle"]
    loveText = validated_data["loveText"]
    treeColor = validated_data["treeColor"]
    accentColor = validated_data["accentColor"]
    foliageCount = validated_data["foliageCount"]
    deployTo = validated_data["deployTo"]
    s3Folder = validated_data["s3Folder"]
    body_images = validated_data["bodyImages"]
    music_file = validated_data["music"]

    # Verify payment before generating
    MIN_PAYMENT_AMOUNT = 29000
    try:
        from app.database import SessionLocal
        from app.models.transaction import Transaction

        if SessionLocal is None:
            logger.error("Database not configured for payment verification")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Database not configured"},
            )

        db = SessionLocal()
        try:
            # Check for valid payment with matching content and sufficient amount
            transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.content.ilike(f"%{projectName}%"),
                    Transaction.amount >= MIN_PAYMENT_AMOUNT,
                )
                .order_by(Transaction.created_at.desc())
                .first()
            )

            if not transaction:
                logger.warning(f"Payment not found for project: {projectName}")
                return JSONResponse(
                    status_code=402,
                    content={
                        "success": False,
                        "error": "Payment not verified. Please complete payment first.",
                    },
                )

            # Check if already generated (has URL)
            if transaction.url:
                logger.info(f"Project already generated: {projectName}, URL: {transaction.url}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "This project has already been generated.",
                        "existingUrl": transaction.url,
                    },
                )

            logger.info(
                f"Payment verified for project: {projectName}, "
                f"amount: {transaction.amount}, transaction_id: {transaction.id}"
            )
        finally:
            db.close()
    except Exception as e:
        logger.exception(f"Error verifying payment: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Payment verification failed: {str(e)}"},
        )

    # Build config & HTML
    config = {
        "projectName": projectName,
        "treeType": treeType,
        "mainTitle": mainTitle,
        "loveText": loveText,
        "treeColor": treeColor,
        "accentColor": accentColor,
        "foliageCount": (
            int(foliageCount) if foliageCount and str(foliageCount).isdigit() else 15000
        ),
    }
    html_content = generate_html(config, len(body_images))

    # Prepare files dict
    files_dict = {"html": html_content, "bodyImages": body_images}
    if music_file:
        files_dict["music"] = music_file

    # Deploy
    try:
        project_id = projectName
        if deployTo == "s3":
            if not s3_client or not S3_BUCKET:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "S3 not configured (AWS credentials / S3_BUCKET_NAME)",
                    },
                )
            public_url = await upload_to_s3(
                project_id=project_id, folder=s3Folder, files_dict=files_dict
            )
        else:
            public_url = await save_locally(
                project_id=project_id, files_dict=files_dict
            )

        # Save URL to transaction record
        try:
            from app.database import SessionLocal
            from app.models.transaction import Transaction

            if SessionLocal:
                db = SessionLocal()
                try:
                    transaction = (
                        db.query(Transaction)
                        .filter(Transaction.content.ilike(f"%{projectName}%"))
                        .order_by(Transaction.created_at.desc())
                        .first()
                    )
                    if transaction:
                        transaction.url = public_url
                        db.commit()
                        logger.info(
                            f"Updated transaction {transaction.id} with URL: {public_url}"
                        )
                finally:
                    db.close()
        except Exception as db_err:
            logger.warning(f"Failed to save URL to transaction: {db_err}")

        generation_time = int((time.time() - start_time) * 1000)
        return {
            "success": True,
            "projectId": project_id,
            "publicUrl": public_url,
            "generationTime": generation_time,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/preview/{project_id}/index.html")
async def preview(project_id: str):
    preview_file = Path(f"public/preview/{project_id}/index.html")
    if preview_file.exists():
        return FileResponse(preview_file)
    return JSONResponse(status_code=404, content={"error": "Preview not found"})


@app.get("/preview/{project_id}/{file_path}")
async def preview_file(project_id: str, file_path: str):
    file_full_path = PUBLIC_DIR / "preview" / project_id / file_path
    if file_full_path.exists():
        return FileResponse(file_full_path)
    return JSONResponse(status_code=404, content={"error": "File not found"})


@app.get("/api/payment/verify/{project_name}")
async def verify_payment(project_name: str, min_amount: int = 29000):
    """Check if payment with matching content and amount exists in database."""
    try:
        from app.database import SessionLocal
        from app.models.transaction import Transaction

        if SessionLocal is None:
            logger.error("Database not configured")
            return JSONResponse(
                status_code=500,
                content={"error": "Database not configured", "verified": False},
            )

        db = SessionLocal()
        try:
            # Query transactions for content containing project_name and amount >= min_amount
            logger.info(
                f"Verifying payment for project: {project_name}, min_amount: {min_amount}"
            )

            query = (
                db.query(Transaction)
                .filter(
                    Transaction.content.ilike(f"%{project_name}%"),
                    Transaction.amount >= min_amount,
                )
                .order_by(Transaction.created_at.desc())
            )

            # Log the query for debugging
            logger.info(
                f"Query: content ILIKE '%{project_name}%' AND amount >= {min_amount}"
            )

            transaction = query.first()

            if transaction:
                logger.info(
                    f"Found matching transaction: id={transaction.id}, "
                    f"content={transaction.content}, amount={transaction.amount}"
                )
                return {
                    "verified": True,
                    "transaction": {
                        "id": transaction.id,
                        "content": transaction.content,
                        "amount": transaction.amount,
                        "transaction_date": str(transaction.transaction_date),
                        "reference_code": transaction.reference_code,
                        "url": transaction.url,
                    },
                }

            logger.info(f"No matching transaction found for project: {project_name}")
            return {"verified": False}
        finally:
            db.close()
    except Exception as e:
        logger.exception(f"Error verifying payment: {e}")
        return JSONResponse(
            status_code=500, content={"error": str(e), "verified": False}
        )


@app.get("/api/project/check/{project_name}")
async def check_project_exists(project_name: str):
    """Check if project name already exists in transactions (to prevent duplicates)."""
    try:
        from app.database import SessionLocal
        from app.models.transaction import Transaction

        if SessionLocal is None:
            logger.error("Database not configured")
            return JSONResponse(
                status_code=500, content={"error": "Database not configured"}
            )

        db = SessionLocal()
        try:
            logger.info(f"Checking if project exists: {project_name}")

            # Check if any transaction with this content already has a URL (already generated)
            existing = (
                db.query(Transaction)
                .filter(
                    Transaction.content.ilike(f"%{project_name}%"),
                    Transaction.url.isnot(None),
                )
                .first()
            )

            if existing:
                logger.info(f"Project already exists with URL: {existing.url}")
                return {
                    "exists": True,
                    "url": existing.url,
                    "message": "This project has already been generated",
                }

            return {"exists": False}
        finally:
            db.close()
    except Exception as e:
        logger.exception(f"Error checking project: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn

    # When running locally, run the app object from this module
    uvicorn.run("app.main:app", port=PORT, reload=True)
