import cloudinary
import cloudinary.uploader
from fastapi import HTTPException

cloudinary.config(
  cloud_name="dws8lpmua",
  api_key="595136529363616",
  api_secret="VwJl7HXcox_1U9qeeN0fVmoL_VY",
  secure=True
)

def upload_to_cloudinary(file, folder_name):
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder_name,
            resource_type="auto"  # auto = detect image, video, document automatically
        )
        return {
            "secure_url": result["secure_url"],   # This is the URL you use in frontend or save in DB
            "public_id": result["public_id"],     # Important if you later want to delete/update the file
            "resource_type": result["resource_type"]  # Whether it was image, video, raw etc
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

