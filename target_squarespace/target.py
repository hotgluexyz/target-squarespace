"""Squarespace target class."""

from hotglue_singer_sdk import typing as th
from hotglue_singer_sdk.helpers.capabilities import AlertingLevel
from hotglue_singer_sdk.target_sdk.target import TargetHotglue

from target_squarespace.auth import TOKEN_URL, SquarespaceOAuthAuthenticator
from target_squarespace.sinks import (
    ContactsSink,
    OrdersSink,
)


class TargetSquarespace(TargetHotglue):
    """Sample target for Squarespace."""

    SINK_TYPES = [OrdersSink, ContactsSink]
    MAX_PARALLELISM = 10
    name = "target-squarespace"
    alerting_level = AlertingLevel.ERROR

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_key",
            th.StringType,
            description="Squarespace API key. Not required when using OAuth.",
        ),
        th.Property(
            "client_id",
            th.StringType,
            description="OAuth application client ID. When present, OAuth is used instead of the API key.",
        ),
        th.Property(
            "client_secret",
            th.StringType,
            description="OAuth application client secret.",
        ),
        th.Property(
            "refresh_token",
            th.StringType,
            description="OAuth refresh token.",
        ),
        th.Property(
            "access_token",
            th.StringType,
            description="Current OAuth access token. Written back to the config file after each refresh.",
        ),
    ).to_dict()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # The SDK's --access-token flow reads `config_file`; TargetHotglue only sets `_config_file_path`.
        self.config_file = self._config_file_path

    @classmethod
    def access_token_support(cls, connector=None):
        """Return authenticator class and auth endpoint for token refresh."""
        return SquarespaceOAuthAuthenticator, TOKEN_URL


if __name__ == "__main__":
    TargetSquarespace.cli()
