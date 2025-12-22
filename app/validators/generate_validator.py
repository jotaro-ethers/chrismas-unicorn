"""Validator for /api/generate endpoint."""

import re
import io
from typing import Dict, List, Any, Tuple
from PIL import Image

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB for images
MIN_IMAGES = 5
MAX_IMAGES = 15
MAX_NAME_LEN = 63
PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9]+$")

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_IMAGE_MIMETYPES = {"image/png", "image/jpeg"}

# YouTube URL patterns
YOUTUBE_URL_PATTERNS = [
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})"),
]


class ValidationError(Exception):
    """Custom validation error with field-specific errors."""

    def __init__(self, errors: Dict[str, str]):
        self.errors = errors
        super().__init__(str(errors))


def get_file_extension(filename: str) -> str:
    """Extract lowercase file extension from filename."""
    if not filename or "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def validate_project_name(name: str) -> Tuple[bool, str]:
    """Validate project name - only alphanumeric characters allowed."""
    if not name or not name.strip():
        return False, "Project name is required"

    name = name.strip()

    if not PROJECT_NAME_PATTERN.match(name):
        return (
            False,
            "Project name can only contain letters (A-Z, a-z) and numbers (0-9)",
        )

    if len(name) > MAX_NAME_LEN:
        return False, f"Project name must be {MAX_NAME_LEN} characters or less"

    return True, ""


def validate_image_file(
    filename: str, content_type: str, size: int
) -> Tuple[bool, str]:
    """Validate a single image file."""
    ext = get_file_extension(filename)

    if (
        ext not in ALLOWED_IMAGE_EXTENSIONS
        and content_type not in ALLOWED_IMAGE_MIMETYPES
    ):
        return (
            False,
            f"Invalid image type: {filename}. Allowed formats: PNG, JPG, JPEG",
        )

    if size > MAX_FILE_SIZE:
        return False, f"Image '{filename}' exceeds 5 MB limit"

    return True, ""


def extract_youtube_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    if not url or not url.strip():
        return ""

    url = url.strip()

    for pattern in YOUTUBE_URL_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)

    return ""


def validate_youtube_url(url: str) -> Tuple[bool, str, str]:
    """
    Validate YouTube URL and extract video ID.
    Returns (is_valid, error_message, video_id).
    """
    if not url or not url.strip():
        # YouTube URL is optional
        return True, "", ""

    video_id = extract_youtube_video_id(url)

    if not video_id:
        return False, "Invalid YouTube URL. Please provide a valid YouTube video link.", ""

    return True, "", video_id


def convert_image_to_jpeg(image_data: bytes, filename: str) -> Tuple[bytes, str, str]:
    """
    Convert image to JPEG format.
    Returns (converted_data, new_filename, content_type).
    """
    ext = get_file_extension(filename)

    # If already JPEG, return as-is
    if ext in {".jpg", ".jpeg"}:
        return image_data, filename, "image/jpeg"

    try:
        # Open image with PIL
        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ("RGBA", "LA", "P"):
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Save as JPEG
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=90)
        jpeg_data = output.getvalue()

        # Generate new filename with .jpeg extension
        base_name = filename.rsplit(".", 1)[0] if "." in filename else filename
        new_filename = f"{base_name}.jpeg"

        return jpeg_data, new_filename, "image/jpeg"
    except Exception as e:
        # If conversion fails, return original
        print(f"Warning: Failed to convert {filename} to JPEG: {e}")
        return image_data, filename, "image/png"


async def validate_generate_request(form) -> Dict[str, Any]:
    """
    Validate the generate request form data.

    Returns validated data dict if valid.
    Raises ValidationError with field-specific errors if invalid.
    """
    errors: Dict[str, str] = {}

    # Validate project name
    project_name = form.get("projectName", "")
    if isinstance(project_name, str):
        project_name = project_name.strip().lower()
    else:
        project_name = ""

    valid, error = validate_project_name(project_name)
    if not valid:
        errors["projectName"] = error

    # Validate YouTube URL (optional)
    youtube_url = form.get("youtubeUrl", "")
    if isinstance(youtube_url, str):
        youtube_url = youtube_url.strip()
    else:
        youtube_url = ""

    youtube_video_id = ""
    if youtube_url:
        valid, error, youtube_video_id = validate_youtube_url(youtube_url)
        if not valid:
            errors["youtubeUrl"] = error

    # Collect and validate files
    body_images: List[Dict[str, Any]] = []
    seen_filenames = set()

    for key in form.keys():
        values = form.getlist(key)
        for val in values:
            filename = getattr(val, "filename", None)
            content_type = getattr(val, "content_type", None)

            if not filename:
                continue

            # Skip duplicates
            if filename in seen_filenames:
                continue
            seen_filenames.add(filename)

            # Read file content
            content = await val.read()
            file_size = len(content)

            entry = {
                "field": key,
                "filename": filename,
                "content_type": content_type or "application/octet-stream",
                "data": content,
                "size": file_size,
            }

            # Categorize and validate
            if key.startswith("bodyImage") or key == "bodyImages":
                valid, error = validate_image_file(
                    filename, content_type or "", file_size
                )
                if not valid:
                    if "bodyImages" not in errors:
                        errors["bodyImages"] = error
                else:
                    # Convert image to JPEG before adding
                    converted_data, new_filename, new_content_type = (
                        convert_image_to_jpeg(content, filename)
                    )
                    entry["data"] = converted_data
                    entry["filename"] = new_filename
                    entry["content_type"] = new_content_type
                    entry["size"] = len(converted_data)
                    body_images.append(entry)

    # Validate image count
    if len(body_images) < MIN_IMAGES:
        errors["bodyImages"] = (
            f"Please upload at least {MIN_IMAGES} images (currently: {len(body_images)})"
        )
    elif len(body_images) > MAX_IMAGES:
        errors["bodyImages"] = (
            f"Maximum {MAX_IMAGES} images allowed (currently: {len(body_images)})"
        )

    # If any errors, raise ValidationError
    if errors:
        raise ValidationError(errors)

    # Return validated data
    return {
        "projectName": project_name,
        "treeType": form.get("treeType", "tree1"),
        "mainTitle": form.get("mainTitle", "MERRY CHRISTMAS"),
        "loveText": form.get("loveText", "I LOVE YOU ❤️"),
        "treeColor": form.get("treeColor", "#004225"),
        "accentColor": form.get("accentColor", "#FFD700"),
        "foliageCount": form.get("foliageCount", "15000"),
        "deployTo": form.get("deployTo", "s3"),
        "s3Folder": form.get("s3Folder", "christmas-experience-bucket"),
        "bodyImages": body_images,
        "youtubeVideoId": youtube_video_id,
    }
