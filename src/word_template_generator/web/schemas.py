from __future__ import annotations

from pydantic import BaseModel


class WorkspacePayload(BaseModel):
    workspace: str


class BuildOnePayload(BaseModel):
    workspace: str
    act: str

