import unittest
import mock
import tempfile

from km3db import DBManager
from km3db.core import AuthenticationError


class TestKM3DB(unittest.TestCase):
    def test_init(self):
        DBManager()

    def test_get(self):
        db = DBManager()
        result = db.get("streamds/detectors.txt")
        assert result.startswith(
            "OID\tSERIALNUMBER\tLOCATIONID\tCITY\tFIRSTRUN\tLASTRUN\nD_DU1CPPM\t2\tA00070004\tMarseille"
        )

    @mock.patch("os.getenv")
    @mock.patch("km3db.core.urllib.request.build_opener")
    def test_request_session_cookie_from_env_with_credentials(
        self, build_opener_mock, getenv_mock
    ):
        credentials = {
            "KM3NET_DB_USERNAME": "username",
            "KM3NET_DB_PASSWORD": "password",
            "KM3NET_DB_TOTP": "",
        }
        getenv_mock.side_effect = credentials.get

        open_mock = build_opener_mock.return_value.open
        response_mock = open_mock.return_value.__enter__.return_value
        response_mock.read.return_value = b"foo"

        db = DBManager()
        with self.assertRaises(AuthenticationError):
            db.request_session_cookie()

        getenv_mock.assert_has_calls(
            [
                mock.call("KM3NET_DB_USERNAME"),
                mock.call("KM3NET_DB_PASSWORD"),
                mock.call("KM3NET_DB_TOTP"),
            ]
        )

        open_mock.assert_called_once_with(
            "https://km3netdbweb.in2p3.fr/home.htm"
            "?usr=username&pwd=password&totp=&persist=y",
            timeout=30,
        )

    @mock.patch("os.getenv")
    @mock.patch("km3db.core.urllib.request.build_opener")
    def test_request_session_cookie_with_invalid_totp(
        self, build_opener_mock, getenv_mock
    ):
        from urllib.error import HTTPError

        credentials = {
            "KM3NET_DB_USERNAME": "username",
            "KM3NET_DB_PASSWORD": "password",
            "KM3NET_DB_TOTP": "123456",
        }
        getenv_mock.side_effect = credentials.get

        login_response = mock.MagicMock()
        login_response.__enter__.return_value.read.return_value = (
            b'<script>const id = "abc123";</script>'
        )
        open_mock = build_opener_mock.return_value.open
        open_mock.side_effect = [
            login_response,
            HTTPError(
                "https://km3netdbweb.in2p3.fr/2fa", 417, "Expectation Failed", {}, None
            ),
        ]

        db = DBManager()
        with self.assertRaisesRegex(AuthenticationError, "Invalid TOTP"):
            db.request_session_cookie()

    @mock.patch("os.path.exists")
    @mock.patch("os.getenv")
    def test_request_session_cookie_from_env_with_cookie(
        self, getenv_mock, exists_mock
    ):
        class StreamMock:
            def read(self):
                return b"foo"

        the_cookie = "namnam"

        def getenv_mock_side_effect(key):
            if key == "KM3NET_DB_COOKIE":
                return the_cookie
            return None

        exists_mock.return_value = False
        getenv_mock.side_effect = getenv_mock_side_effect

        db = DBManager()

        cookie = db._request_session_cookie()

        getenv_mock.assert_has_calls(
            [
                mock.call("KM3NET_DB_COOKIE"),
            ]
        )

        assert the_cookie == cookie

    @mock.patch("os.path.exists")
    @mock.patch("os.getenv")
    def test_request_session_cookie_from_env_with_cookie_file(
        self, getenv_mock, exists_mock
    ):
        class StreamMock:
            def read(self):
                return b"foo"

        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(b"ignoredstring namnam")
        f.close()

        def getenv_mock_side_effect(key):
            if key == "KM3NET_DB_COOKIE_FILE":
                return f.name
            return None

        exists_mock.return_value = False
        getenv_mock.side_effect = getenv_mock_side_effect

        db = DBManager()

        cookie = db._request_session_cookie()

        getenv_mock.assert_has_calls(
            [
                mock.call("KM3NET_DB_COOKIE_FILE"),
            ]
        )

        assert "namnam" == cookie
