import unittest
import mock
import tempfile

from km3db import DBManager
from km3db.core import on_whitelisted_host, SESSION_COOKIES, AuthenticationError


class TestKM3DB(unittest.TestCase):
    def test_init(self):
        DBManager()

    def test_whitelisted_hosts(self):
        for host, cookie in SESSION_COOKIES.items():
            if on_whitelisted_host(host):
                assert DBManager().session_cookie == cookie

    def test_get(self):
        db = DBManager()
        result = db.get("streamds/detectors.txt")
        assert result.startswith(
            "OID\tSERIALNUMBER\tLOCATIONID\tCITY\tFIRSTRUN\tLASTRUN\nD_DU1CPPM\t2\tA00070004\tMarseille"
        )

    @mock.patch("os.path.exists")
    @mock.patch("os.getenv")
    @mock.patch("urllib.request.urlopen")
    def test_request_session_cookie_from_env_with_credentials(
        self, urlopen_mock, getenv_mock, exists_mock
    ):
        class StreamMock:
            def read(self):
                return b"foo"

        def getenv_mock_side_effect(key):
            if key == "KM3NET_DB_USERNAME":
                return "username"
            if key == "KM3NET_DB_PASSWORD":
                return "password"
            return None

        urlopen_mock.return_value = StreamMock()
        exists_mock.return_value = False
        getenv_mock.side_effect = getenv_mock_side_effect

        db = DBManager()
        with self.assertRaises(AuthenticationError):
            cookie = db.request_session_cookie()

        getenv_mock.assert_has_calls(
            [
                mock.call("KM3NET_DB_USERNAME"),
                mock.call("KM3NET_DB_PASSWORD"),
            ]
        )

        urlopen_mock.assert_called_with(
            "https://km3netdbweb.in2p3.fr/home.htm?usr=username&pwd=password&persist=y"
        )

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
