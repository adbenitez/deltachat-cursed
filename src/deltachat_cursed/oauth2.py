import webbrowser
import wsgiref.simple_server
from itertools import count
from typing import Optional
from urllib.parse import parse_qs, urlparse

from deltachat import Account
from deltachat.capi import ffi


def is_oauth2(ac: Account, addr: str) -> bool:
    return get_oauth2_url(ac, addr, "") is not None


def get_oauth2_url(ac: Account, addr: str, redirect_uri: str) -> Optional[str]:
    buf = ffi.dlopen(None).dc_get_oauth2_url(
        ac._dc_context, addr.encode("utf-8"), redirect_uri.encode("utf-8")  # noqa
    )

    if buf == ffi.NULL:
        return None

    chars = []
    for i in count():
        if buf[i] == b"\x00":
            break
        chars.append(ord(buf[i]))

    return bytes(chars).decode("utf-8")


# borrowed from google-auth-library-python-oauthlib
def get_authz_code(
    ac: Account,
    addr: str,
    port: int,
    authorization_prompt_message: str = None,
    success_message: str = None,
    open_browser: bool = True,
) -> str:
    """Run a local server for receiving the authorization code and return it"""

    if authorization_prompt_message is None:
        authorization_prompt_message = (
            "Please visit this URL to authorize this application: {url}"
        )

    if success_message is None:
        success_message = (
            "The authorization code was received. You may close this window."
        )

    auth_url = get_oauth2_url(ac, addr, f"http://127.0.0.1:{port}/")
    assert auth_url

    wsgi_app = _RedirectWSGIApp(success_message)
    local_server = wsgiref.simple_server.make_server("127.0.0.1", port, wsgi_app)

    if open_browser:
        webbrowser.open(auth_url, new=1, autoraise=True)

    print(authorization_prompt_message.format(url=auth_url))

    local_server.handle_request()

    authorization_response = wsgi_app.last_request_uri

    res_params = parse_qs(urlparse(authorization_response).query)  # type: ignore
    assert (
        "code" in res_params and res_params["code"]
    ), "authorization code not found in url"

    return res_params["code"][0]  # type: ignore


class _RedirectWSGIApp:
    """WSGI app to handle the authorization redirect.
    Stores the request URI and displays the given success message.
    """

    def __init__(self, success_message: str) -> None:
        """
        Args:
            success_message (str): The message to display in the web browser
                the authorization flow is complete.
        """
        self.last_request_uri: Optional[str] = None
        self._success_message = success_message

    def __call__(self, environ, start_response) -> list:
        """WSGI Callable.
        Args:
            environ (Mapping[str, Any]): The WSGI environment.
            start_response (Callable[str, list]): The WSGI start_response
                callable.
        Returns:
            Iterable[bytes]: The response body.
        """
        start_response("200 OK", [("Content-type", "text/plain")])
        self.last_request_uri = wsgiref.util.request_uri(environ)
        return [self._success_message.encode("utf-8")]
