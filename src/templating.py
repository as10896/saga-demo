"""
The default `url_for` function from Starlette builds absolute URLs from the incoming request, which breaks behind a proxy:

1. The scheme is taken from the request, so HTTPS-hosted pages request stylesheets using the HTTP scheme,
   which will be blocked because content must also be served over HTTPS.
2. The host is taken from the `Host` header. On Koyeb, the request that wakes a sleeping instance carries
   an internal host (e.g. `<uuid>:8000`), so the generated links point to an unreachable address.

To resolve both issues, return a root-relative URL (i.e. "/static/..." without scheme or host),
so that the browser resolves it against the current page.

Refs:
- https://github.com/encode/starlette/blob/fa5355442753f794965ae1af0f87f9fec1b9a3de/starlette/templating.py#L120
- https://stackoverflow.com/questions/70521784/fastapi-links-created-by-url-for-in-jinja2-template-use-http-instead-of-https
- https://github.com/fastapi/fastapi/discussions/6073
"""

from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context


@pass_context
def url_for(
    context: dict[str, Any],
    name: str,
    /,
    **path_params: Any,
) -> str:
    request: Request = context["request"]
    # `.path` keeps the `root_path` prefix (if any) but drops the scheme and host
    return request.url_for(name, **path_params).path


templates = Jinja2Templates(directory="src/templates")
templates.env.globals["url_for"] = url_for
