import asyncio
import logging
import os
from typing import List, Optional

from fastapi import HTTPException, APIRouter
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.rpc.responses import RpcPerfSample
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID

from SolAppT import SOLANA_API_ENDPOINT
from SolAppT import CustomToken, TokenX


logger = logging.getLogger(__name__)
# Initialize Solana Testnet client
client = Client(SOLANA_API_ENDPOINT, timeout=120)

# Initialize Router
router = APIRouter()


async def get_token_metadata(token_address: Pubkey) -> Optional[dict]:
    """Helper function to get token metadata from on-chain data"""
    try:
        # Create a temporary keypair for reading
        seed_bytes = os.urandom(32)
        temp_keypair = Keypair.from_seed(seed_bytes)

        # Get token account info
        token = Token(
            client,
            token_address,
            TOKEN_PROGRAM_ID,
            temp_keypair
        )

        # Get mint info
        mint_account = client.get_account_info(token_address)
        if not mint_account.value:
            return None

        # Get token supply
        mint_info = token.get_mint_info()
        if not mint_info:
            return None

        return {
            "address": str(token_address),
            "supply": mint_info.supply,
            "decimals": mint_info.decimals
        }
    except Exception:
        return None


@router.get("/trending", response_model=List[TokenX])
async def get_trending_tokens(limit: int = 10):
    """Get list of trending tokens based on recent transaction volume"""
    try:
        # Fetch recent performance samples
        recent_blocks = client.get_recent_performance_samples(limit=5)
        performance_samples: List[RpcPerfSample] = recent_blocks.value

        if not performance_samples:
            logger.error("No recent performance samples found.")
            raise HTTPException(status_code=500, detail="Failed to fetch recent blocks")

        # Extract slot numbers
        slots = [sample.slot for sample in performance_samples[:5]]
        token_transactions = {}

        for slot in slots:
            block_info = client.get_block(slot)
            if not hasattr(block_info, "value") or not block_info.value:
                logger.warning(f"Skipping block {slot} due to missing transaction data")
                continue

            for tx in block_info.value.transactions:
                if str(TOKEN_PROGRAM_ID) in [str(key) for key in tx.transaction.message.account_keys]:
                    for account in tx.transaction.message.account_keys:
                        token_info = await get_token_metadata(account)
                        if not token_info:
                            continue

                        if str(account) not in token_transactions:
                            token_transactions[str(account)] = {
                                "count": 0,
                                "metadata": token_info,
                            }
                        token_transactions[str(account)]["count"] += 1

        # Sort tokens by transaction count
        sorted_tokens = sorted(
            token_transactions.items(), key=lambda x: x[1]["count"], reverse=True
        )[:limit]

        tokens = [
            TokenX(symbol="Unknown", name="Unknown", address=address, price=0.0)
            for address, data in sorted_tokens
        ]

        return tokens
    except Exception as e:
        logger.exception("Error fetching trending tokens")
        raise HTTPException(status_code=500, detail=str(e))


async def request_airdrop(
        client, wallet_address: str, lamports: int = 1000000000
):
    try:
        # Convert string address to Pubkey
        pubkey = Pubkey.from_string(wallet_address)

        # Request airdrop with proper parameters
        opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)

        # Make the airdrop request
        response = await client.request_airdrop(
            pubkey,
            lamports,
            # opts=opts
        )

        if not response.value:
            raise HTTPException(
                status_code=500,
                detail="Airdrop request failed - no transaction signature returned"
            )

        # Wait for transaction confirmation
        await client.confirm_transaction(
            response.value,
            commitment=Confirmed
        )

        return response.value

    except Exception as e:
        logger.error(f"Airdrop request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to request airdrop: {str(e)}"
        )



@router.post("/custom")
async def create_custom_token(token_data: CustomToken) -> TokenX:
    try:
        # Create mint authority keypair
        seed_bytes = os.urandom(32)
        mint_authority = Keypair.from_seed(seed_bytes)

        # Check balance before airdrop
        balance_before = client.get_balance(mint_authority.pubkey())
        logger.info(f"Balance before airdrop: {balance_before.value} lamports")

        # Request airdrop
        airdrop_sig = await request_airdrop(client, str(mint_authority.pubkey()))
        logger.info(f"Airdrop requested with signature: {airdrop_sig}")

        # Wait for confirmation
        await asyncio.sleep(30)  # Use asyncio.sleep instead of time.sleep in async function

        # Confirm transaction
        confirmation = client.confirm_transaction(airdrop_sig)
        if not confirmation:
            raise HTTPException(status_code=500, detail="Failed to confirm airdrop transaction")

        # Check balance after airdrop
        balance_after = client.get_balance(mint_authority.pubkey())
        logger.info(f"Balance after airdrop: {balance_after.value} lamports")

        # Create the token
        token = Token.create_mint(
            client,
            mint_authority,
            mint_authority.pubkey(),
            token_data.decimals,
            TOKEN_PROGRAM_ID
        )

        logger.info(f"Created token at address {token.pubkey}")

        return TokenX(
            symbol=token_data.symbol,
            name=token_data.name,
            address=str(token.pubkey),
            price=None
        )

    except Exception as e:
        logger.exception("Error creating custom token")
        raise HTTPException(status_code=500, detail=str(e))
