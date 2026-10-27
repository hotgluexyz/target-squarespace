import json

import requests
from hotglue_etl_exceptions import InvalidCredentialsError
from hotglue_singer_sdk.helpers._util import utc_now
from hotglue_singer_sdk.target_sdk.auth import OAuthAuthenticator


TOKEN_URL = "https://login.squarespace.com/api/1/login/oauth/provider/tokens"


class SquarespaceOAuthAuthenticator(OAuthAuthenticator):
    """OAuth 2.0 authenticator for Squarespace using refresh token flow.

    Squarespace requires Basic auth (client_id:client_secret) on the token
    endpoint and returns an absolute expiry timestamp (access_token_expires_at)
    instead of the relative expires_in used by most OAuth providers.
    """

    @property
    def oauth_request_body(self) -> dict:
        return {
            "grant_type": "refresh_token",
            "refresh_token": self._config["refresh_token"],
        }

    def _update_access_token_locally(self) -> None:
        client_id = self._config["client_id"]
        client_secret = self._config["client_secret"]

        request_time = utc_now()
        self.logger.info("Refreshing Squarespace OAuth access token")
        token_response = requests.post(
            self._auth_endpoint,
            json=self.oauth_request_body,
            auth=(client_id, client_secret),
            timeout=300,
        )

        try:
            token_response.raise_for_status()
            self.logger.info("OAuth token refresh successful.")
        except Exception as ex:
            try:
                error_body = token_response.json()
            except Exception:
                error_body = token_response.text
            self.state.update({"auth_error_response": error_body})
            raise InvalidCredentialsError(
                f"Failed OAuth login, response was '{error_body}'. {ex}"
            ) from ex

        token_json = token_response.json()

        self.access_token = token_json["access_token"]
        self._config["access_token"] = token_json["access_token"]
        self._config["refresh_token"] = token_json["refresh_token"]
        # access_token_expires_at is an absolute Unix timestamp — store directly
        # so that the parent's is_token_valid() comparison (expires_in - now < 120) works correctly
        self.expires_in = int(token_json["access_token_expires_at"])
        self._config["expires_in"] = self.expires_in
        self.last_refreshed = request_time

        if self._config_file_path is not None:
            with open(self._config_file_path, "w") as outfile:
                json.dump(self._config, outfile, indent=4)
