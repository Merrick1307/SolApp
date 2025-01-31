import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID

from ..models import (
    WalletCreate, Transaction, WalletBalance,
    TokenBalance, WalletResponse
)
from .tokens import client, logger

# Empty dict for in-memory wallet storage
wallets = {}

# Initialize API Router
router = APIRouter()


@router.post("/wallet", response_model=WalletResponse)
async def create_wallet(wallet_data: WalletCreate):
    """Create a new Solana wallet"""
    try:
        # Generate new keypair
        seed_bytes = os.urandom(32)
        keypair = Keypair.from_seed(seed_bytes)
        public_key = str(keypair.pubkey())
        # Store the seed bytes as private key
        private_key = seed_bytes.hex()

        # Store wallet info
        wallet = {
            "public_key": public_key,
            "private_key": private_key,
            "name": wallet_data.name
        }
        wallets[public_key] = wallet

        return WalletResponse(
            public_key=wallet["public_key"],
            name=wallet["name"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[WalletResponse])
async def get_wallets():
    """Get all wallets"""
    return list(wallets.values())


@router.get("/{public_key}", response_model=WalletResponse)
async def get_wallet(public_key: str):
    """Get specific wallet details"""
    if public_key not in wallets:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallets[public_key]


@router.post("/{public_key}/tokens")
async def add_token_to_wallet(public_key: str, token_address: str):
    """Add token to wallet"""
    if public_key not in wallets:
        raise HTTPException(status_code=404, detail="Wallet not found")

    try:
        # Reconstruct keypair from stored private key
        seed_bytes = bytes.fromhex(wallets[public_key]["private_key"])
        wallet_keypair = Keypair.from_seed(seed_bytes)
        token = Token(
            client, Pubkey.from_string(token_address),
            TOKEN_PROGRAM_ID, wallet_keypair
        )

        # Get or create associated token account
        associated_token_account = token.create_associated_token_account(
            wallet_keypair.pubkey()
        )

        return {
            "message": "Token added successfully",
            "associated_token_account": str(associated_token_account)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{public_key}/balance", response_model=WalletBalance)
async def get_wallet_balance(public_key: str):
    """Get wallet SOL and token balances"""
    try:
        wallet_pubkey = Pubkey.from_string(public_key)
        # Get SOL balance
        response = client.get_balance(wallet_pubkey)

        if response.value is None:
            raise HTTPException(status_code=500, detail="Failed to fetch SOL balance")

        sol_balance = response.value / 1e9  # Convert lamports to SOL
        # Get token accounts with proper request formatting
        request_data = {
            "method": "getTokenAccountsByOwner",
            "jsonrpc": "2.0",
            "params": [
                str(wallet_pubkey),
                {
                    "programId": str(TOKEN_PROGRAM_ID)
                },
                {
                    "encoding": "jsonParsed"
                }
            ],
            "id": 1
        }

        # Request
        token_response = client._provider.session.post(
            client._provider.endpoint_uri,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )

        token_response_data = token_response.json()
        token_balances = []

        if (
                'result' in token_response_data and
                'value' in token_response_data['result']
        ):
            for account in token_response_data['result']['value']:
                try:
                    parsed_data = account['account']['data']['parsed']['info']
                    mint_address = parsed_data['mint']
                    token_amount = parsed_data['tokenAmount']

                    token_balances.append(TokenBalance(
                        address=mint_address,
                        balance=token_amount['uiAmount'],
                        usd_value=None
                    ))
                except (KeyError, TypeError) as e:
                    logger.error(f"Error parsing token account: {str(e)}")
                    continue

        return WalletBalance(
            sol_balance=sol_balance,
            usd_value=None,
            tokens=token_balances
        )
    except Exception as e:
        logger.exception("Error fetching wallet balance")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{public_key}/transactions",response_model=List[Transaction]
)
async def get_wallet_transactions(
        public_key: str,
        limit: int = 10,
        before: Optional[str] = None
):
    """Get wallet transaction history"""
    if public_key not in wallets:
        raise HTTPException(
            status_code=404, detail="Wallet not found"
        )

    try:
        # Get transaction signatures
        response = client.get_signatures_for_address(
            Pubkey.from_string(public_key),
            limit=limit,
            before=before
        )

        transactions = []
        for signature_info in response.value:
            # Get transaction details
            tx_response = client.get_transaction(signature_info.signature)

            if tx_response.value:
                tx = tx_response.value
                # Parse transaction type and amounts
                tx_type = \
                    "receive" if tx.transaction.message.is_to_wallet(public_key) \
                        else "send"
                amount = tx.transaction.message.instructions[0].data.amount / 1e9
                # Update the transactions list
                transactions.append(Transaction(
                    signature=str(signature_info.signature),
                    timestamp=datetime.fromtimestamp(signature_info.block_time),
                    type=tx_type,
                    amount=amount,
                    token_symbol="SOL",
                    from_address=str(tx.transaction.message.account_keys[0]),
                    to_address=str(tx.transaction.message.account_keys[1]),
                    status="confirmed" if signature_info.confirmed else "pending"
                ))

        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))