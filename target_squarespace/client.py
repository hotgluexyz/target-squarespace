import json
from datetime import datetime

import backoff
import requests
from hotglue_singer_sdk.exceptions import FatalAPIError, RetriableAPIError
from hotglue_singer_sdk.target_sdk.auth import ApiAuthenticator
from hotglue_singer_sdk.target_sdk.client import HotglueSink


class SquarespaceSink(HotglueSink):

    base_url = "https://api.squarespace.com/1.0/commerce"

    def _log_and_raise(self, exception_class, response):
        self.logger.info(f"Response code: {response.status_code}, info: {response.text}")
        error_message = response.text
        try:
            error = response.json()
        except ValueError:
            error = None
        if isinstance(error, dict) and "contextId" in error:
            error.pop("contextId")
            error_message = json.dumps(error)
        raise exception_class(error_message)

    def validate_response(self, response: requests.Response) -> None:
        """Log client errors and exclude context IDs from the saved error."""
        if 400 <= response.status_code < 500 and response.status_code != 429:
            self._log_and_raise(FatalAPIError, response)
        super().validate_response(response)

    @property
    def authenticator(self):
        if not hasattr(self, "_authenticator"):
            if self.config.get("client_id"):
                authenticator, auth_endpoint = self._target.access_token_support(self._target)
                self._authenticator = authenticator(self._target, auth_endpoint=auth_endpoint)
            else:
                self._authenticator = ApiAuthenticator(
                    self._target,
                    header_name="Authorization",
                    header_value_prefix="Bearer ",
                    config_key="api_key",
                )
        return self._authenticator

    @backoff.on_exception(
        backoff.expo,
        (RetriableAPIError, requests.exceptions.ReadTimeout),
        max_tries=5,
        factor=2,
    )
    def _request(
        self, http_method, endpoint, params=None, request_data=None, headers=None, verify=True
    ) -> requests.PreparedRequest:
        """Prepare a request object."""
        url = self.url(endpoint)
        merged_headers = {**self.default_headers, **(headers or {})}

        response = requests.request(
            method=http_method,
            url=url,
            params=params,
            headers=merged_headers,
            json=request_data,
            verify=verify,
        )
        self.validate_response(response)
        return response


    def validate_input(self, record: dict):
        return self.unified_schema(**record).dict()

    def convert_datetime(self, date: datetime):
        # convert datetime.datetime into str
        if isinstance(date, datetime):
            # This is the format -> "2022-08-15T19:16:35Z"
            return date.strftime("%Y-%m-%dT%H:%M:%SZ")
        return date
