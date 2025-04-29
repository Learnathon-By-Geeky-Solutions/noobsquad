from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, UploadFile
from services.file_service import (
    save_uploaded_research_paper,
    get_file_response,
    ALLOWED_DOCS
)

class TestFileService(IsolatedAsyncioTestCase):
    def setUp(self):
        self.user_id = 1
        self.mock_file = Mock(spec=UploadFile)
        self.mock_file.filename = "test_paper.pdf"

    @patch('services.file_service.validate_file_extension')
    @patch('services.file_service.secure_filename')
    @patch('services.file_service.generate_secure_filename')
    @patch('services.file_service.upload_file_to_supabase')
    async def test_save_uploaded_research_paper(
        self,
        mock_upload_to_supabase,
        mock_generate_filename,
        mock_secure_filename,
        mock_validate_extension
    ):
        # Setup mocks
        mock_validate_extension.return_value = ".pdf"
        mock_generate_filename.return_value = "generated_name.pdf"
        mock_secure_filename.return_value = "secure_name.pdf"
        mock_upload_to_supabase.return_value = "https://example.com/papers/secure_name.pdf"

        # Call function
        result = await save_uploaded_research_paper(self.mock_file, self.user_id)

        # Verify
        mock_validate_extension.assert_called_once_with(self.mock_file.filename, ALLOWED_DOCS)
        mock_generate_filename.assert_called_once_with(self.user_id, ".pdf")
        mock_secure_filename.assert_called_once_with("generated_name.pdf")
        mock_upload_to_supabase.assert_called_once_with(
            self.mock_file,
            "secure_name.pdf",
            section="research_papers"
        )
        self.assertEqual(result, "https://example.com/papers/secure_name.pdf")

# class TestFileServiceSync(TestCase):
#     @patch('services.file_service.validate_file_existence')
#     @patch('services.file_service.FileResponse')
    # def test_get_file_response(self, mock_file_response, mock_validate_existence):
    #     filepath = "path/to/file.pdf"
    #     filename = "file.pdf"
    #     mock_response = Mock()
    #     mock_file_response.return_value = mock_response

    #     result = get_file_response(filepath, filename)

    #     mock_validate_existence.assert_called_once_with(filepath)
    #     mock_file_response.assert_called_once_with(
    #         path=filepath,
    #         filename=filename,
    #         media_type="application/pdf"
    #     )
    #     self.assertEqual(result, mock_response)