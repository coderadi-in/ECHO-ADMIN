# ==================================================
# SETUP
# ==================================================

# ? IMPORTS
import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

# ? LOAD VIRTUAL ENVIRONMENT
load_dotenv('.venv/vars.env')


# ==================================================
# REQUEST ENGINE
# ==================================================

class RequestEngine:
    """
    Thin wrapper around ``requests.Session`` that automatically injects the
    admin authentication headers required by the ECHO admin API.
    """

    def __init__(self) -> None:
        admin_id = os.getenv('ADMIN_ID')
        admin_key = os.getenv('ADMIN_KEY')

        if (not admin_id) or (not admin_key):
            raise EnvironmentError(
                "ADMIN_ID and ADMIN_KEY must be set in the environment "
                "(expected in '.venv/vars.env')."
            )

        self.headers = {
            'admin-id': admin_id,
            'admin-key': admin_key,
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    # --------------------------------------------------
    # CORE VERBS
    # --------------------------------------------------

    def get(self, url: str, **url_args) -> requests.Response:
        return self.session.get(url, params=url_args)

    def post(self, url: str, json: dict, **url_args) -> requests.Response:
        return self.session.post(url, json=json, params=url_args)

    def patch(self, url: str, json: dict, **url_args) -> requests.Response:
        return self.session.patch(url, json=json, params=url_args)

    def delete(self, url: str, **url_args) -> requests.Response:
        return self.session.delete(url, params=url_args)

    # --------------------------------------------------
    # FILE DOWNLOAD
    # --------------------------------------------------

    def download(
        self,
        url: str,
        destination: Path | str,
        **url_args,
    ) -> requests.Response:
        """
        Stream a file from ``url`` and persist it to ``destination``.

        Returns the underlying ``requests.Response`` so callers can inspect
        the status code even when the transfer failed.
        """
        destination = Path(destination)
        with self.session.get(url, params=url_args, stream=True) as response:
            if response.status_code == 200:
                with destination.open('wb') as fh:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            fh.write(chunk)
            return response