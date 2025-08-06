from typing import Any

from fastapi import Request
from jinja2 import pass_context
from starlette.datastructures import URL


@pass_context
def url_for(
    context: dict[str, Any],
    name: str,
    /,
    **path_params: Any,
) -> URL:
    """
    The default `url_for` function from Starlette causes HTTPS-hosted pages to request stylesheets using the HTTP scheme,
    which will be blocked because content must also be served over HTTPS.
    To resolve this issue, remove the URI scheme (i.e., use "//" instead of "http://" or "https://").

    Refs:
    - https://github.com/encode/starlette/blob/fa5355442753f794965ae1af0f87f9fec1b9a3de/starlette/templating.py#L120
    - https://stackoverflow.com/questions/70521784/fastapi-links-created-by-url-for-in-jinja2-template-use-http-instead-of-https
    - https://github.com/fastapi/fastapi/discussions/6073
    """
    request: Request = context["request"]
    http_url: URL = request.url_for(name, **path_params)
    http_url: URL = http_url.replace(scheme="")
    return http_url
