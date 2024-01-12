import json
import pathlib
import typing

__all__ = ["read_json", "write_json"]


def read_json(path: pathlib.Path) -> typing.Dict[typing.Any, typing.Any]:
    with open(path, "r") as file:
        data = json.load(file)
    return data


def write_json(json_: typing.Dict[typing.Any, typing.Any], path: pathlib.Path) -> None:
    with open(path, "w") as file:
        json.dump(json_, file)
