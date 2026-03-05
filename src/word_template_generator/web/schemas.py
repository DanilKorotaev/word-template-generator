from __future__ import annotations

from pydantic import BaseModel


class WorkspacePayload(BaseModel):
    workspace: str
    template: str | None = None
    output_dir: str | None = None


class BuildOnePayload(BaseModel):
    workspace: str
    act: str
    template: str | None = None
    output_dir: str | None = None


class OpenFilePayload(BaseModel):
    path: str

