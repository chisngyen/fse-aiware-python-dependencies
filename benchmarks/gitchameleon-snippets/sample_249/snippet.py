from falcon import Response
import falcon


def custom_link(resp: Response, link_rel: str, link_href: str) -> falcon.Response:
    resp.
append_link(link_href, link_rel)
    return resp

# --- test ---
link_rel = "next"
link_href = "http://example.com/next"
resp = Response()

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    custom_resp = custom_link(resp,link_rel,link_href)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expected_link = f'<{link_href}>;'
link_header = custom_resp.get_header("Link") or ""
assert expected_link in link_header
