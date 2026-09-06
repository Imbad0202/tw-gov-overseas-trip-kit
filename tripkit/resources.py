"""Read bundled data after a wheel install, with a source-checkout fallback."""
from importlib.resources import files
from pathlib import Path


def resource_text(group: str, name: str) -> str:
    try:
        return files(f"tripkit.{group}").joinpath(name).read_text(encoding="utf-8")
    except ModuleNotFoundError:
        directory = {"schemas": "schema", "examples": "examples"}[group]
        return (Path(__file__).resolve().parent.parent / directory / name).read_text(encoding="utf-8")
