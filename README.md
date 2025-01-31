# SolApp
Solana Wallet (Testnet integration)

# Solana Wallet Manager

A full-stack application for managing Solana wallets and tokens, built with FastAPI and Streamlit. This application 
allows users to create and manage Solana wallets, track balances, create custom tokens, and monitor transactions on 
the Solana testnet.

## Features

- 🏦 Wallet Management
  - Create new Solana wallets
  - View wallet balances (SOL and tokens)
  - Track transaction history
  - Monitor wallet activities

- 💰 Token Features
  - View trending tokens
  - Create custom tokens
  - Add tokens to wallets
  - Track token balances

- 📊 Transaction Tracking
  - View detailed transaction history
  - Filter transactions
  - Real-time status updates

## Architecture

### Backend (FastAPI)

The backend is built with FastAPI and provides the following components:

- **API Routes**
  - `/wallets`: Wallet management endpoints
  - `/tokens`: Token management endpoints

- **Core Components**
  - Solana client integration
  - Token program integration
  - RPC communication handling

- **Models**
  - `WalletCreate`: Wallet creation schema
  - `TokenX`: Token information schema
  - `CustomToken`: Custom token creation schema
  - `Transaction`: Transaction information schema
  - `WalletBalance`: Balance information schema

### Frontend (Streamlit)

The frontend is built with Streamlit and provides:

- Intuitive user interface for wallet management
- Real-time balance updates
- Transaction history visualization
- Token management interface

## Setup

### Prerequisites

- Python 3.8+
- pip
- Solana CLI tools

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd solana-wallet-manager
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the core package:
```env
SOLANA_ENDPOINT="https://api.testnet.solana.com"
```

### Running the Application

1. Start the Backend:
```bash
cd Backend
uvicorn app.main:app --reload
```

2. Start the Frontend:
```bash
cd Frontend
streamlit run app.py
```

The application will be available at:
- Backend API: `http://localhost:8000`
- Frontend UI: `http://localhost:8501`

## API Documentation

### Wallet Endpoints

- `POST /wallets/wallet`: Create a new wallet
- `GET /wallets`: List all wallets
- `GET /wallets/{public_key}`: Get wallet details
- `GET /wallets/{public_key}/balance`: Get wallet balance
- `GET /wallets/{public_key}/transactions`: Get wallet transactions
- `POST /wallets/{public_key}/tokens`: Add token to wallet

### Token Endpoints

- `GET /tokens/trending`: Get trending tokens
- `POST /tokens/custom`: Create custom token

## Frontend Pages

1. **Wallets**
   - Create new wallets
   - View existing wallets
   - Manage wallet information

2. **Wallet Details**
   - View detailed wallet information
   - Check balances
   - View transaction history

3. **Tokens**
   - View trending tokens
   - Add tokens to wallets
   - Track token balances

4. **Create Custom Token**
   - Create new custom tokens
   - Set token parameters
   - Deploy to Solana testnet

## Development

### Backend Structure

```
Backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── tokens.py
│   │   └── wallets.py
│   ├── core/
│   │   └── config.py
│   ├── models.py
│   └── main.py
```

### Frontend Structure

```
Frontend/
└── __init__.py
```

## Error Handling

The application includes comprehensive error handling:
- Backend API error responses
- Frontend user notifications
- Solana RPC error handling
- Transaction failure handling

## Security Considerations ()

- Private keys are stored in-memory only
- No sensitive data persistence
- Secure RPC communication
- Input validation and sanitization

## Future Improvements (# TODO)

1. Add mainnet support
2. Implement token price feeds
3. Add wallet backup/restore functionality
4. Enhance transaction filtering
5. Add multi-signature wallet support


## License

This project is licensed under the MIT License - see the LICENSE file for details.
