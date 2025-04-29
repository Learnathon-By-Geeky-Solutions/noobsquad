from unittest import TestCase
from unittest.mock import Mock, patch, mock_open
import os
import pytest
from fastapi import HTTPException, UploadFile
from services.FileHandler import (
    _get_file_extension,
    validate_file_extension,
    save_upload_file,
    generate_secure_filename,
    remove_old_file_if_exists
)

class TestFileHandler(TestCase):
    def setUp(self):
        self.user_id = 1
        self.allowed_extensions = {".pdf", ".doc", ".docx"}
        self.test_filename = "test_document.pdf"

    def test_get_file_extension(self):
        filename = "test.PDF"
        result = _get_file_extension(filename)
        self.assertEqual(result, ".pdf")

    def test_validate_file_extension_success(self):
        result = validate_file_extension(self.test_filename, self.allowed_extensions)
        self.assertEqual(result, ".pdf")

    def test_validate_file_extension_invalid(self):
        invalid_filename = "test.xyz"
        with pytest.raises(HTTPException) as exc_info:
            validate_file_extension(invalid_filename, self.allowed_extensions)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid file format."

    # @patch("services.FileHandler.shutil")
    # def test_save_upload_file(self, mock_shutil):
    #     mock_upload_file = Mock(spec=UploadFile)
    #     destination_dir = "test_dir"
    #     filename = "test.pdf"
        
    #     with patch("builtins.open", mock_open()) as mock_file:
    #         result = save_upload_file(mock_upload_file, destination_dir, filename)
        
    #     expected_path = os.path.join(destination_dir, filename)
    #     self.assertEqual(result, expected_path)
    #     mock_shutil.copyfileobj.assert_called_once()

    # def test_generate_secure_filename(self):
    #     file_ext = ".pdf"
    #     result = generate_secure_filename(file_ext)
        
    #     # Check format: user_id_randomhex.ext
    #     parts = result.split("_")
    #     self.assertEqual(len(parts), 2)
    #     self.assertEqual(parts[0], str(self.user_id))
        
    #     name_ext = parts[1]
    #     self.assertTrue(name_ext.endswith(file_ext))
    #     # Check that we have an 8-byte (16 char) hex string before the extension
    #     hex_part = name_ext[:-len(file_ext)]
    #     self.assertEqual(len(hex_part), 16)
    #     # Verify it's actually hex
    #     int(hex_part, 16)  # This will raise ValueError if not hex

    # @patch("services.FileHandler.os.path")
    # @patch("services.FileHandler.os")
    # def test_remove_old_file_if_exists(self, mock_os, mock_path):
    #     file_path = "test.pdf"
    #     mock_path.exists.return_value = True
        
    #     remove_old_file_if_exists(file_path)
        
    #     mock_path.exists.assert_called_once_with(file_path)
    #     mock_os.remove.assert_called_once_with(file_path)

    # @patch("services.FileHandler.os.path")
    # @patch("services.FileHandler.os")
    # def test_remove_old_file_if_not_exists(self, mock_os, mock_path):
    #     file_path = "test.pdf"
    #     mock_path.exists.return_value = False
        
    #     remove_old_file_if_exists(file_path)
        
