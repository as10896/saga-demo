from typing import Any

from fastapi import Request


def url_for(request: Request, name: str, **path_params: Any) -> str:
    """
    The default `url_for` function from Starlette causes HTTPS-hosted pages to request stylesheets using the HTTP scheme,
    which will be blocked because content must also be served over HTTPS.
    To resolve this issue, remove the URI scheme (i.e., use "//" instead of "http://" or "https://").

    Refs:
    - https://stackoverflow.com/questions/70521784/fastapi-links-created-by-url-for-in-jinja2-template-use-http-instead-of-https
    - https://github.com/fastapi/fastapi/discussions/6073
    """

    http_url: str = request.url_for(name, **path_params)._url

    return http_url.replace("http:", "")
