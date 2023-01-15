from datetime import date, datetime
from pydantic import BaseModel


class PrivKey(BaseModel):
    path: str
    key_type: str | None = None


class PubKey(BaseModel):
    path: str
    key_type: str


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
    signer: PrivKey | None = None
    expires: datetime | date | str | None = None
    readme: str | None = None
    keys: dict[str, PubKey]
    steps: list[Step]
    inspect: list[Inspection]
