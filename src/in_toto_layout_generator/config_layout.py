from datetime import datetime
from pydantic import BaseModel


class PrivKey(BaseModel):
    uri: str
    backend: str | None = None
    scheme: str | None = None


class PubKey(BaseModel):
    uri: str
    backend: str | None = None
    scheme: str | None = None


class Step(BaseModel):
    name: str
    threshold: int = 1
    expected_materials: list[str] = []
    expected_products: list[str] = []
    pubkeys: list[str]
    expected_command: str = ''


class Inspection(BaseModel):
    name: str
    expected_materials: list[str] = []
    expected_products: list[str] = []
    run: str


class Config(BaseModel):
    signing_key: PrivKey | None = None
    expires: datetime | str | None = None
    readme: str | None = None
    keys: dict[str, PubKey]
    steps: list[Step]
    inspect: list[Inspection]
