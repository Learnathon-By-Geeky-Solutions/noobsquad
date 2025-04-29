from supabase import create_client
from io import BytesIO
from fastapi import HTTPException
import os
from dotenv import load_dotenv
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Supabase setup

supabase = create_client(supabase_url, supabase_key)

# Mapping of section types to folders
SECTION_FOLDER_MAP = {
    "upload_documents": "upload_documents/",
    "research_papers": "research_papers/",
    "chat": "chat/"
}

BUCKET_NAME = "noobsquad"  # your supabase bucket name

# Upload Function
async def upload_file_to_supabase(file_obj, filename: str, section: str):
    try:
        if section not in SECTION_FOLDER_MAP:
            raise HTTPException(status_code=400, detail="Invalid document section.")

        folder = SECTION_FOLDER_MAP[section]
        destination_path = f"{folder}{filename}"

        file_content = await file_obj.read()

        # Auto-detect MIME type based on extension
        ext = filename.split(".")[-1].lower()
        ext_to_content_type = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "txt": "text/plain",
            "jpg": "image/jpg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        content_type = ext_to_content_type.get(ext, "application/octet-stream")

        upload_response = supabase.storage.from_(BUCKET_NAME).upload(
            destination_path,
            file_content,
            {
                "content-type": content_type  # Force correct content type
            }
        )

        # Get the public URL for the uploaded file
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(destination_path)
        return file_url

    except Exception as e:
        print(f"Error uploading file to Supabase: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document to Supabase.")