from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
import pytest
import jwt
from services.AuthHandler import AuthHandler

class TestAuthHandler(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.username = "testuser"
        self.email = "test@example.com"
        self.password = "testpassword"
        self.otp = "123456"

    def test_get_user_by_username_or_email_success(self):
        mock_user = Mock()
        self.mock_db.query().filter().first.return_value = mock_user
        
        result = AuthHandler._get_user_by_username_or_email(
            self.mock_db,
            self.username
        )
        
        self.assertEqual(result, mock_user)

    def test_get_user_by_username_or_email_not_found(self):
        self.mock_db.query().filter().first.return_value = None
        
        result = AuthHandler._get_user_by_username_or_email(
            self.mock_db,
            self.username
        )
        
        self.assertIsNone(result)

    def test_check_otp_validity_success(self):
        mock_user = Mock(
            otp=self.otp,
            otp_expiry=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        
        # Should not raise an exception
        AuthHandler._check_otp_validity(mock_user, self.otp)

    def test_check_otp_validity_invalid_otp(self):
        mock_user = Mock(
            otp=self.otp,
            otp_expiry=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthHandler._check_otp_validity(mock_user, "wrong_otp")
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid OTP"

    def test_check_otp_validity_expired(self):
        mock_user = Mock(
            otp=self.otp,
            otp_expiry=datetime.now(timezone.utc) - timedelta(minutes=10)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthHandler._check_otp_validity(mock_user, self.otp)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "OTP expired"

    @patch('services.AuthHandler.hash_password')
    @patch('services.AuthHandler.generate_otp')
    @patch('services.AuthHandler.store_otp')
    async def test_create_user_success(
        self,
        mock_store_otp,
        mock_generate_otp,
        mock_hash_password
    ):
        self.mock_db.query().filter().first.return_value = None
        mock_hash_password.return_value = "hashed_password"
        mock_generate_otp.return_value = self.otp
        
        with patch.object(AuthHandler, '_send_otp_email') as mock_send_email:
            result = await AuthHandler.create_user(
                self.mock_db,
                self.username,
                self.email,
                self.password
            )
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        mock_store_otp.assert_called_once()
        mock_send_email.assert_called_once()
        self.assertEqual(
            result["message"],
            "User created successfully. Please verify your email."
        )

    @patch('services.AuthHandler.verify_password')
    @patch('services.AuthHandler.create_access_token')
    async def test_authenticate_user_success(
        self,
        mock_create_token,
        mock_verify_password
    ):
        mock_user = Mock(
            username=self.username,
            is_verified=True
        )
        self.mock_db.query().filter().first.return_value = mock_user
        mock_verify_password.return_value = True
        mock_create_token.return_value = "access_token"
        
        result = await AuthHandler.authenticate_user(
            self.mock_db,
            self.username,
            self.password
        )
        
        self.assertEqual(result["access_token"], "access_token")
        self.assertEqual(result["token_type"], "bearer")

    @patch('services.AuthHandler.verify_password')
    async def test_authenticate_user_invalid_credentials(self, mock_verify_password):
        mock_verify_password.return_value = False
        self.mock_db.query().filter().first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await AuthHandler.authenticate_user(
                self.mock_db,
                self.username,
                self.password
            )
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid credentials"

    @patch('jwt.decode')
    def test_get_current_user_success(self, mock_jwt_decode):
        mock_user = Mock(username=self.username)
        mock_jwt_decode.return_value = {"sub": self.username}
        self.mock_db.query().filter().first.return_value = mock_user
        
        result = AuthHandler.get_current_user(self.mock_db, "valid_token")
        
        self.assertEqual(result, mock_user)

    @patch('jwt.decode')
    def test_get_current_user_invalid_token(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = jwt.PyJWTError()
        
        with pytest.raises(HTTPException) as exc_info:
            AuthHandler.get_current_user(self.mock_db, "invalid_token")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"