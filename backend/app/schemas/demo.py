from typing import Literal

from pydantic import BaseModel

DemoRole = Literal["user", "admin"]


class DemoAccount(BaseModel):
    role: DemoRole
    email: str


class DemoAccountsResponse(BaseModel):
    """The demo accounts on offer. Only served while demo mode is on."""

    accounts: list[DemoAccount]


class DemoLoginRequest(BaseModel):
    role: DemoRole
