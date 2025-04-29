from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, UploadFile
import pytest
from services.upload_service import validate_and_upload, ALLOWED_EXTENSIONS

class TestUploadService(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_file = Mock(spec=UploadFile)
        self.mock_file.filename = "test_image.jpg"

    @patch('services.upload_service.generate_secure_filename')
    @patch('services.upload_service.upload_file_to_supabase')
    async def test_validate_and_upload_success(
        self,
        mock_upload_to_supabase,
        mock_generate_filename
    ):
        expected_url = "https://example.com/uploads/image.jpg"
        mock_generate_filename.return_value = "secure_filename.jpg"
        mock_upload_to_supabase.return_value = expected_url
        
        result = await validate_and_upload(self.mock_file)
        
        mock_generate_filename.assert_called_once_with(self.mock_file.filename, ".jpg")
        mock_upload_to_supabase.assert_called_once_with(
            self.mock_file,
            "secure_filename.jpg",
            section="chat"
        )
        self.assertEqual(result, expected_url)

    async def test_validate_and_upload_invalid_extension(self):
        self.mock_file.filename = "test.xyz"
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_and_upload(self.mock_file)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Unsupported file type"

    def test_allowed_extensions(self):
        expected_extensions = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}
        self.assertEqual(ALLOWED_EXTENSIONS, expected_extensions)