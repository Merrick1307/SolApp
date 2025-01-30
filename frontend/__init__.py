from datetime import datetime

import streamlit as st
import requests

# Configure page
st.set_page_config(
    page_title="Solana Wallet Manager",
    page_icon="💰",
    layout="wide"
)

# Backend API URL
API_URL = "http://localhost:8000"


def format_address(address: str, length: int = 8) -> str:
    """Format address to show beginning and end with ellipsis"""
    if len(address) <= length * 2:
        return address
    return f"{address[:length]}...{address[-length:]}"

def format_timestamp(timestamp: str) -> str:
    """Format timestamp to readable date"""
    dt = datetime.fromisoformat(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_wallet(name):
    """Create a new wallet"""
    try:
        response = requests.post(
            f"{API_URL}/wallets/wallet",
            json={"name": name}
        )
        if response.status_code == 200:
            st.success("Wallet created successfully!")
            return response.json()
        else:
            st.error(f"Error creating wallet: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def get_wallets():
    """Fetch all wallets"""
    try:
        response = requests.get(f"{API_URL}/wallets")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching wallets: {str(e)}")
        return []


def get_wallet_details(public_key):
    """Fetch specific wallet details"""
    try:
        response = requests.get(f"{API_URL}/wallets/{public_key}")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.error("Wallet not found")
        else:
            st.error(f"Error fetching wallet details: {response.text}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


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
            json={"token_address": token_address}
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


def get_wallet_balance(public_key):
    """Fetch wallet balance from backend"""
    try:
        response = requests.get(
            f"{API_URL}/wallets/{public_key}/balance"
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching balance: {str(e)}")
        return None

def get_wallet_transactions(public_key, limit=10, before=None):
    """Fetch wallet transactions from backend"""
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


# Main app
def main():
    st.title("Solana Wallet Manager")

    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page",
        ["Wallets", "Wallet Details", "Tokens", "Create Custom Token"]
    )

    if page == "Wallets":
        st.header("Manage Wallets")

        # Create new wallet
        with st.expander("Create New Wallet"):
            wallet_name = st.text_input("Wallet Name")
            if st.button("Create Wallet"):
                if wallet_name:
                    create_wallet(wallet_name)
                else:
                    st.warning("Please enter a wallet name")

        # Display wallets
        st.subheader("Your Wallets")
        wallets = get_wallets()

        if wallets:
            for wallet in wallets:
                with st.expander(f"Wallet: {wallet['name']}"):
                    st.code(f"Public Key: {wallet['public_key']}")
        else:
            st.info("No wallets found. Create one to get started!")

    elif page == "Wallet Details":
        st.header("Wallet Details")

        # Input for wallet public key
        col1, col2 = st.columns([3, 1])
        with col1:
            public_key = st.text_input("Enter Wallet Public Key")
        with col2:
            search_button = st.button("Search Wallet")

        # Option to select from existing wallets
        st.subheader("Or select from existing wallets")
        wallets = get_wallets()
        if wallets:
            selected_wallet = st.selectbox(
                "Select a wallet",
                options=wallets,
                format_func=lambda x: f"{x['name']} ({x['public_key'][:8]}...)"
            )
            if selected_wallet:
                public_key = selected_wallet['public_key']

        # Display wallet details
        if public_key and (search_button or selected_wallet):
            wallet_details = get_wallet_details(public_key)
            if wallet_details:
                st.success("Wallet found!")

                # Display wallet information in a clean format
                st.subheader("Wallet Information")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Wallet Name**")
                    st.code(wallet_details['name'])

                    st.markdown("**Public Key**")
                    st.code(wallet_details['public_key'])


            # Display balance information
            st.subheader("Wallet Balance")
            balance = get_wallet_balance(public_key)
            if balance:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("SOL Balance", f"{balance['sol_balance']:.4f} SOL")
                    if balance['usd_value']:
                        st.metric("USD Value", f"${balance['usd_value']:.2f}")

                with col2:
                    st.subheader("Token Balances")
                    if balance['tokens']:
                        for token in balance['tokens']:
                            st.metric(
                                token['symbol'],
                                f"{token['balance']:.4f}",
                                f"${token['usd_value']:.2f}" if token['usd_value'] else None
                            )
                    else:
                        st.info("No token balances found")

            st.subheader("Transaction History")

            # Add transaction filters
            col1, col2 = st.columns([2, 1])
            with col1:
                transaction_limit = st.slider("Number of transactions", 5, 50, 10)

            # Fetch and display transactions
            transactions = get_wallet_transactions(public_key, limit=transaction_limit)

            if transactions:
                # Create a clean table view of transactions
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
                                f"<span style='color: "
                                f"{amount_color}'>{tx['amount']} {tx['token_symbol']}</span>",
                                unsafe_allow_html=True
                            )

                            st.markdown("**Status**")
                            status_color = "green" if tx['status'] == "confirmed" else "orange"
                            st.markdown(f"<span style='color: "
                                        f"{status_color}'>{tx['status'].title()}</span>",
                                        unsafe_allow_html=True
                                        )

                        with cols[2]:
                            st.markdown("**From**")
                            st.code(format_address(tx['from_address']))

                            st.markdown("**To**")
                            st.code(format_address(tx['to_address']))
            else:
                st.info("No transactions found for this wallet")


    elif page == "Tokens":
        st.header("Manage Tokens")

        # Get wallets for selection
        wallets = get_wallets()
        if not wallets:
            st.warning("Please create a wallet first")
            return

        selected_wallet = st.selectbox(
            "Select Wallet",
            options=wallets,
            format_func=lambda x: f"{x['name']} ({x['public_key'][:8]}...)"
        )

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
                        add_token_to_wallet(selected_wallet['public_key'], token['address'])
        else:
            st.info("No trending tokens available")

    elif page == "Create Custom Token":
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


if __name__ == "__main__":
    main()