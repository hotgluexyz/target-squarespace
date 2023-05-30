from target_hotglue.client import HotglueSink
from datetime import datetime
import backoff
import requests
from singer_sdk.exceptions import RetriableAPIError

class SquarespaceSink(HotglueSink):

    base_url = "https://api.squarespace.com/1.0/commerce"

    @property
    def http_headers(self):
        token = self.config.get("api_key")
        auth_credentials = {
            "Authorization": f"Bearer {token}"
        }
        return auth_credentials


    @backoff.on_exception(
        backoff.expo,
        (RetriableAPIError, requests.exceptions.ReadTimeout),
        max_tries=5,
        factor=2,
    )
    def _request(
        self, http_method, endpoint, params=None, request_data=None, headers=None
    ) -> requests.PreparedRequest:
        """Prepare a request object."""
        url = self.url(endpoint)
        headers = self.http_headers

        response = requests.request(
            method=http_method,
            url=url,
            params=params,
            headers=headers,
            json=request_data,
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
    
    