"""Cashu protocol and Clear operator models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProtocolModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class BlindedMessage(ProtocolModel):
    amount: int = Field(gt=0)
    id: str
    blinded_secret: str = Field(alias="B_")


class BlindSignature(ProtocolModel):
    amount: int
    id: str
    blind_signature: str = Field(alias="C_")


class Proof(ProtocolModel):
    amount: int = Field(gt=0)
    id: str
    secret: str = Field(min_length=1)
    signature: str = Field(alias="C")


class MintQuoteRequest(BaseModel):
    amount: int = Field(gt=0)
    unit: str
    memo: str | None = Field(default=None, max_length=280)


class MintRequest(BaseModel):
    quote: str
    outputs: list[BlindedMessage] = Field(min_length=1, max_length=128)


class SwapRequest(BaseModel):
    inputs: list[Proof] = Field(min_length=1, max_length=128)
    outputs: list[BlindedMessage] = Field(min_length=1, max_length=128)


class CheckStateRequest(BaseModel):
    Ys: list[str] = Field(min_length=1, max_length=256)


class RetireRequest(BaseModel):
    inputs: list[Proof] = Field(min_length=1, max_length=128)
    memo: str | None = Field(default=None, max_length=280)
