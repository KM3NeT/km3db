import unittest
import mock

from km3db import DBManager
from km3db.core import on_whitelisted_host, SESSION_COOKIES, AuthenticationError
import km3db.compat


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
    @mock.patch("km3db.compat.urlopen")
    def test_request_session_cookie_from_env(
        self, urlopen_mock, getenv_mock, exists_mock
    ):
        class StreamMock:
            def read(self):
                return b"foo"

        urlopen_mock.return_value = StreamMock()
        exists_mock.return_value = False
        getenv_mock.side_effect = ["username", "password"]

        db = DBManager()
        with self.assertRaises(AuthenticationError):
            cookie = db._request_session_cookie()

        getenv_mock.assert_has_calls(
            [mock.call("KM3NET_DB_USERNAME"), mock.call("KM3NET_DB_PASSWORD")]
        )

        urlopen_mock.assert_called_with(
            "https://km3netdbweb.in2p3.fr/home.htm?usr=username&pwd=password&persist=y"
        )
