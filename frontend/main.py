import streamlit as st
import requests
from datetime import datetime
import json
import hashlib
from pathlib import Path
import secrets

# Configure page
st.set_page_config(
    page_title="Solana Wallet Manager",
    page_icon="💰",
    layout="wide"
)

# Backend API URL
API_URL = "http://localhost:8000"


def generate_private_key():
    """Generate a random private key"""
    return secrets.token_hex(32)


def hash_private_key(private_key):
    """Hash private key for storage"""
    return hashlib.sha256(private_key.encode()).hexdigest()


def format_address(address: str, length: int = 8) -> str:
    """Format address to show beginning and end with ellipsis"""
    if len(address) <= length * 2:
        return address
    return f"{address[:length]}...{address[-length:]}"


def format_timestamp(timestamp: str) -> str:
    """Format timestamp to readable date"""
    dt = datetime.fromisoformat(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_private_key' not in st.session_state:
        st.session_state.current_private_key = None
    if 'my_wallets' not in st.session_state:
        st.session_state.my_wallets = {}
    if 'show_private_key' not in st.session_state:
        st.session_state.show_private_key = False
    if 'new_wallet_data' not in st.session_state:
        st.session_state.new_wallet_data = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Wallets"


def get_storage_path():
    """Get storage path for wallet data"""
    storage_dir = Path("wallet_data")
    storage_dir.mkdir(exist_ok=True)
    return storage_dir / "wallets.json"


def load_stored_data():
    """Load stored wallet data"""
    storage_path = get_storage_path()
    try:
        if storage_path.exists():
            with open(storage_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return {}


def save_data(data):
    """Save wallet data"""
    storage_path = get_storage_path()
    try:
        with open(storage_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")


def verify_private_key(private_key):
    """Verify private key and load associated wallet"""
    if not private_key:
        return False

    hashed_key = hash_private_key(private_key)
    all_wallets = load_stored_data()

    if hashed_key in all_wallets:
        st.session_state.authenticated = True
        st.session_state.current_private_key = private_key
        st.session_state.my_wallets = {
            all_wallets[hashed_key]["name"]: all_wallets[hashed_key]
        }
        return True
    return False


def get_wallet_balance(public_key):
    """Fetch wallet balance"""
    try:
        response = requests.get(f"{API_URL}/wallets/{public_key}/balance")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching balance: {str(e)}")
        return None


def get_wallet_transactions(public_key, limit=10, before=None):
    """Fetch wallet transactions"""
    try:
        params = {"limit": limit}
        if before:
            params["before"] = before
        response = requests.get(
            f"{API_URL}/wallets/{public_key}/transactions",
            params=params
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching transactions: {str(e)}")
        return []


def get_trending_tokens():
    """Fetch trending tokens"""
    try:
        response = requests.get(f"{API_URL}/tokens/trending")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching tokens: {str(e)}")
        return []


def add_token_to_wallet(wallet_public_key, token_address):
    """Add token to wallet"""
    try:
        response = requests.post(
            f"{API_URL}/wallets/{wallet_public_key}/tokens",
            params={"token_address": token_address}
        )
        if response.status_code == 200:
            st.success("Token added successfully!")
            return response.json()
        else:
            st.error(f"Error adding token: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def create_custom_token(name, symbol, decimals, total_supply):
    """Create custom token"""
    try:
        response = requests.post(
            f"{API_URL}/tokens/custom",
            json={
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply
            }
        )
        if response.status_code == 200:
            st.success("Custom token created successfully!")
            return response.json()
        else:
            st.error(f"Error creating token: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def create_wallet(name):
    """Create a new wallet"""
    try:
        response = requests.post(
            f"{API_URL}/wallets/wallet",
            json={"name": name}
        )
        if response.status_code == 200:
            data = response.json()

            # Generate private key
            private_key = generate_private_key()
            hashed_key = hash_private_key(private_key)

            wallet_data = {
                "name": data["name"],
                "public_key": data["public_key"],
                "hashed_private_key": hashed_key
            }

            # Store the wallet data
            all_wallets = load_stored_data()
            all_wallets[hashed_key] = wallet_data
            save_data(all_wallets)

            # Set the session state to show private key
            st.session_state.authenticated = True
            st.session_state.current_private_key = private_key
            st.session_state.my_wallets = {name: wallet_data}
            st.session_state.show_private_key = True
            st.session_state.new_wallet_data = {
                "wallet": wallet_data,
                "private_key": private_key
            }

            st.success("Wallet created successfully!")
            return wallet_data
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def render_login():
    """Render login page"""
    col1, col2 = st.columns(2)

    with col1:
        st.title("Access Your Wallet")
        with st.form("login_form"):
            private_key = st.text_input("Enter Private Key", type="password")
            submitted = st.form_submit_button("Access Wallet")

            if submitted:
                if private_key:
                    if verify_private_key(private_key):
                        st.success("Access granted!")
                        st.rerun()
                    else:
                        st.error("Invalid private key")
                else:
                    st.error("Please enter your private key")

    with col2:
        st.title("Create New Wallet")
        with st.form("create_wallet_form"):
            wallet_name = st.text_input("Wallet Name")
            submitted = st.form_submit_button("Create Wallet")

            if submitted:
                if wallet_name:
                    result = create_wallet(wallet_name)
                    if result:
                        st.rerun()
                else:
                    st.warning("Please enter a wallet name")


def show_new_wallet_notice():
    """Show one-time private key notice"""
    if st.session_state.show_private_key and st.session_state.new_wallet_data:
        st.warning("""
        ⚠️ IMPORTANT: Save your private key now! It will only be shown once!
        You will need this private key to access your wallet in the future.
        """)

        with st.expander("View Private Key", expanded=True):
            st.code(st.session_state.new_wallet_data["private_key"])
            st.info("Copy this private key and store it safely. You'll need it to access your wallet.")
            if st.button("I have saved my private key"):
                st.session_state.show_private_key = False
                st.session_state.new_wallet_data = None
                st.rerun()


def render_wallet_overview():
    """Render wallet overview page"""
    wallet = list(st.session_state.my_wallets.values())[0]
    st.header(f"Wallet: {wallet['name']}")

    # Display wallet information
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Public Key**")
        st.code(wallet['public_key'])

    # Get and display balance
    balance = get_wallet_balance(wallet['public_key'])
    if balance:
        with col2:
            st.metric("SOL Balance", f"{balance['sol_balance']:.4f} SOL")
            if balance['usd_value']:
                st.metric("USD Value", f"${balance['usd_value']:.2f}")

        if balance['tokens']:
            st.subheader("Token Balances")
            for token in balance['tokens']:
                st.metric(
                    token['symbol'],
                    f"{token['balance']:.4f}",
                    f"${token['usd_value']:.2f}" if token['usd_value'] else None
                )


def render_transactions():
    """Render transactions page"""
    wallet = list(st.session_state.my_wallets.values())[0]
    st.header("Transaction History")

    transaction_limit = st.slider("Number of transactions", 5, 50, 10)
    transactions = get_wallet_transactions(wallet['public_key'], limit=transaction_limit)

    if transactions:
        for tx in transactions:
            with st.expander(f"Transaction: {format_address(tx['signature'])}"):
                cols = st.columns([2, 1, 1])
                with cols[0]:
                    st.markdown("**Type**")
                    st.write(tx['type'].title())
                    st.markdown("**Time**")
                    st.write(format_timestamp(tx['timestamp']))

                with cols[1]:
                    st.markdown("**Amount**")
                    amount_color = "green" if tx['type'] == "receive" else "red"
                    st.markdown(
                        f"<span style='color: {amount_color}'>{tx['amount']} "
                        f"{tx['token_symbol']}</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown("**Status**")
                    status_color = "green" if tx['status'] == "confirmed" else "orange"
                    st.markdown(
                        f"<span style='color: {status_color}'>{tx['status'].title()}</span>",
                        unsafe_allow_html=True
                    )

                with cols[2]:
                    st.markdown("**From**")
                    st.code(format_address(tx['from_address']))
                    st.markdown("**To**")
                    st.code(format_address(tx['to_address']))
    else:
        st.info("No transactions found")


def render_tokens():
    """Render tokens page"""
    wallet = list(st.session_state.my_wallets.values())[0]
    st.header("Manage Tokens")

    # Display trending tokens
    st.subheader("Trending Tokens")
    tokens = get_trending_tokens()

    if tokens:
        for token in tokens:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{token['name']} ({token['symbol']})**")
                st.code(token['address'], language="text")
            with col2:
                st.write("Price")
                st.write(f"${token['price']:.2f}")
            with col3:
                if st.button("Add Token", key=token['address']):
                    add_token_to_wallet(wallet['public_key'], token['address'])
    else:
        st.info("No trending tokens available")


def render_create_token():
    """Render create token page"""
    st.header("Create Custom Token")

    with st.form("create_token_form"):
        token_name = st.text_input("Token Name")
        token_symbol = st.text_input("Token Symbol")
        decimals = st.number_input("Decimals", min_value=0, max_value=9, value=9)
        total_supply = st.number_input("Total Supply", min_value=1, value=1000000)

        if st.form_submit_button("Create Token"):
            if token_name and token_symbol:
                create_custom_token(token_name, token_symbol, decimals, total_supply)
            else:
                st.warning("Please fill in all fields")


def main():
    init_session_state()

    if not st.session_state.authenticated:
        render_login()
    else:
        st.title("Solana Wallet Manager")

        # Show private key notice if needed
        show_new_wallet_notice()

        # Sidebar navigation
        st.sidebar.title("Navigation")
        st.session_state.current_page = st.sidebar.radio(
            "Choose a page",
            ["Wallet Overview", "Transactions", "Tokens", "Create Custom Token"]
        )

        # Logout button
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.current_private_key = None
            st.session_state.my_wallets = {}
            st.rerun()

        # Render selected page
        if st.session_state.current_page == "Wallet Overview":
            render_wallet_overview()
        elif st.session_state.current_page == "Transactions":
            render_transactions()
        elif st.session_state.current_page == "Tokens":
            render_tokens()
        elif st.session_state.current_page == "Create Custom Token":
            render_create_token()


if __name__ == "__main__":
    main()