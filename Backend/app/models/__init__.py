from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class WalletCreate(BaseModel):
    name: str


class TokenX(BaseModel):
    symbol: str
    name: str
    address: str
    price: Optional[float]


class CustomToken(BaseModel):
    name: str
    symbol: str
    decimals: int
    total_supply: int


class Transaction(BaseModel):
    signature: str
    timestamp: datetime
    type: str  # 'send' or 'receive'
    amount: float
    token_symbol: str
    from_address: str
    to_address: str
    status: str


class TokenBalance(BaseModel):
    symbol: str
    balance: float
    usd_value: Optional[float]


class WalletBalance(BaseModel):
    sol_balance: float
    usd_value: Optional[float]
    tokens: List[TokenBalance]


class WalletResponse(BaseModel):
    """Response model for general wallet queries"""
    private_key: str
    public_key: str
    name: str