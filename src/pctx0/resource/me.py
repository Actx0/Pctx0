# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

from pctx0.resource.base import Resource
from pctx0.types import AccessKeyPrincipal
from pctx0.utils import _GET, parse_me_principal


class Me(Resource):
    """Key introspection API client."""

    _prefix = "/api/v1/me"

    def get(self) -> AccessKeyPrincipal:
        data = self._request(_GET, self._prefix)
        return parse_me_principal(data)
