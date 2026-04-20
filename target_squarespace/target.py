"""Squarespace target class."""

from singer_sdk.target_base import Target
from singer_sdk import typing as th

from target_squarespace.sinks import (
    ContactsSink,
    OrdersSink,
)
from target_hotglue.target import TargetHotglue
from typing import List, Optional, Union
from pathlib import PurePath


class TargetSquarespace(TargetHotglue):
    """Sample target for Squarespace."""

    def __init__(
        self,
        config: Optional[Union[dict, PurePath, str, List[Union[PurePath, str]]]] = None,
        parse_env_config: bool = False,
        validate_config: bool = True,
        state: str = None
    ) -> None:
        self.config_file = config[0]
        super().__init__(config, parse_env_config, validate_config)


    SINK_TYPES = [OrdersSink, ContactsSink]
    MAX_PARALLELISM = 10
    name = "target-squarespace"


if __name__ == "__main__":
    TargetSquarespace.cli()