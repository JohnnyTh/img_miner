import pathlib
import typing

import pydantic

__all__ = ["ArtefactInfo", "ProgressTracker"]


class ArtefactInfo(pydantic.BaseModel):
    local_p: typing.Optional[pathlib.Path] = None
    url_primary: str
    url_hosting: typing.Optional[str] = None
    index_download: int
    success_download: bool

    @pydantic.field_validator("local_p", mode="before")
    def convert_to_path(cls, value: typing.Union[str, pathlib.Path]) -> pathlib.Path:
        if isinstance(value, str):
            return pathlib.Path(value)
        return value


class ProgressTracker(pydantic.BaseModel):
    batch_id: int = 0
    n_processed: int = 0
    n_successful: int = 0
    generator_type: str = "undefined"
    random_seed: typing.Optional[int] = None
