import typing

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

__all__ = ["HTTPConnection"]


class HTTPConnection:
    def __init__(
        self, headers: typing.Dict[str, str], retries_total: int, backoff_factor_seconds: int
    ) -> None:
        self.headers = headers
        self.retries_total = retries_total
        self.backoff_factor_seconds = backoff_factor_seconds

    def make_request(self, url: str) -> typing.Optional[requests.Response]:
        retries = Retry(
            total=self.retries_total,
            backoff_factor=self.backoff_factor_seconds,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)

        session = requests.Session()
        session.mount("https://", adapter)

        try:
            response = session.get(url, allow_redirects=True, headers=self.headers)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error: {e}")
            return None
