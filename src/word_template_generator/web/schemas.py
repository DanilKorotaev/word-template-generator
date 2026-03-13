from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


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


class ActFieldPayload(BaseModel):
    value: Any = ""
    type: Literal["text", "multiline", "date", "reference", "number"] = "text"
    format: str | None = None


class ActNumberPayload(BaseModel):
    prefix: str = ""
    value: int | str | None = None


class ActEditorDataPayload(BaseModel):
    template: str | None = None
    output_name: str | None = None
    number: ActNumberPayload | None = None
    fields: dict[str, ActFieldPayload] = Field(default_factory=dict)


class SaveActPayload(BaseModel):
    workspace: str
    filename: str
    is_new: bool = False
    data: ActEditorDataPayload


class DeleteActPayload(BaseModel):
    workspace: str
    filename: str
