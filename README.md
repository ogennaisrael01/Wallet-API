# Project Name
Wallet-API: A Digital Wallet Backend System

## Overview
Wallet-API is a comprehensive backend service that simulates a digital wallet platform, enabling users to securely manage their funds through RESTful APIs. The system allows users to register accounts, deposit money using payment gateways, transfer funds between users, withdraw to bank accounts, and track all transactions. It's designed for fintech applications that need reliable fund management with built-in security measures like transaction pins and idempotency keys.

This system serves developers building mobile or web applications that require payment processing and wallet functionality. It solves the problem of complex payment integration by providing a clean API layer over payment processors while maintaining transaction integrity and user security.

## Tech Stack
- **Python**: Core programming language for the backend logic
- **Django**: Web framework providing ORM, admin interface, and project structure
- **Django REST Framework (DRF)**: For building REST APIs with serialization and authentication
- **Django REST Framework Simple JWT**: Handles JSON Web Token authentication with refresh tokens
- **Paystack**: Payment gateway integration for deposits, transfers, and withdrawals
- **SQLite**: Database for development and testing (easily replaceable with PostgreSQL for production)
- **bcrypt**: Password hashing for secure credential storage
- **django-environ**: Environment variable management for configuration
- **DRF-YASG**: API documentation generation with Swagger/OpenAPI
- **Gunicorn**: Production WSGI server
- **WhiteNoise**: Static file serving for Django
- **Validators**: Input validation utilities

## System Architecture
The project follows Django's modular app architecture with clear separation of concerns:

- **base_config/**: Core Django configuration including settings, JWT configuration, and URL routing
- **api/users/**: User management module handling registration, authentication, and profile management
- **api/wallet/**: Core wallet functionality including transactions, payments, and transfers
- **staticfiles/**: Static assets for Django admin and API documentation

The wallet app contains:
- **models.py**: Database schemas for users, wallets, transactions, and payment records
- **views.py**: API endpoints for wallet operations
- **serializers.py**: Data validation and transformation
- **services/**: Business logic layer with wallet operations and payment processing
- **permissions.py**: Access control for wallet resources

## Core Features
1. **User Registration & Authentication**
   - Email-based registration with password validation
   - JWT token authentication with refresh capability
   - Profile management and avatar support
   - Automatic wallet creation upon user registration

2. **Wallet Management**
   - Automatic account number generation (10-digit format starting with 58)
   - Balance tracking with previous balance history
   - Currency support (default NGN)
   - Secure account number hashing for privacy

3. **Deposit Operations**
   - Paystack payment initialization
   - Transaction verification and wallet crediting
   - Idempotency key support to prevent duplicate transactions
   - Minimum deposit amount validation (₦100)

4. **Fund Transfers**
   - Peer-to-peer transfers between users
   - Transaction PIN verification for security
   - Account number validation
   - Insufficient balance checks
   - Transfer status tracking (Processing, Pending, Success, Failed)

5. **Withdrawal Operations**
   - Bank account withdrawal requests
   - Admin approval workflow for security
   - Bank details validation
   - Transaction PIN requirement

6. **Transaction Security**
   - 4-digit transaction PIN setup and verification
   - Idempotency keys for duplicate prevention
   - Transaction status tracking
   - Comprehensive validation and error handling

## API Overview
The API is organized around authentication and wallet operations:

**Authentication Endpoints:**
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login with JWT tokens
- `GET /api/auth/profile/me/` - User profile retrieval and updates

**Wallet Endpoints:**
- `GET /api/wallet/` - Wallet details and balance
- `POST /api/wallet/deposit/` - Initialize deposit via Paystack
- `POST /api/wallet/verify_deposit/` - Verify and complete deposit
- `POST /api/wallet/set_transaction_pin/` - Set 4-digit transaction PIN
- `POST /api/wallet/transfer/` - Initialize fund transfer
- `POST /api/wallet/verify_transfer/` - Complete transfer verification
- `POST /api/wallet/withdraw/` - Request withdrawal to bank account
- `POST /api/wallet/approve/` - Admin approval for withdrawals

**Documentation:**
- `/api/schema/swagger-ui/` - Interactive API documentation
- `/api/schema/redoc/` - Alternative documentation format

## Authentication & Security
The system uses JWT (JSON Web Tokens) for authentication with the following security measures:

- **Token Management**: Access tokens (50 minutes default) and refresh tokens (7 days default)
- **Token Blacklisting**: Prevents reuse of compromised refresh tokens
- **Role-Based Access**: Admin approval required for withdrawals
- **Transaction PINs**: 4-digit PIN required for transfers and withdrawals
- **Idempotency Keys**: Prevents duplicate transaction processing
- **Input Validation**: Comprehensive validation for amounts, account numbers, and references
- **Rate Limiting**: 100 requests/hour for anonymous users, 1000/hour for authenticated users
- **CORS Configuration**: Restricted to localhost origins for development

## Payment Flow
The system integrates with Paystack for payment processing:

1. **Deposit Flow**:
   - User initiates deposit with amount and idempotency key
   - System creates transaction record and initializes Paystack payment
   - User completes payment on Paystack
   - System verifies payment and credits wallet
   - Transaction marked as successful

2. **Transfer Flow**:
   - User provides recipient account number, amount, and PIN
   - System validates account, balance, and PIN
   - Creates transfer and transaction records
   - Processes internal transfer (debit sender, credit receiver)
   - Updates transaction status

3. **Withdrawal Flow**:
   - User submits bank details, amount, and PIN
   - Admin reviews and approves withdrawal
   - System debits wallet and marks transaction complete
   - External payout to bank account (implementation noted for future)

**Error Handling**: Failed payments update transaction status, successful ones credit/debit wallets atomically using database transactions.

## Database Design
The system uses the following core models:

- **CustomUser**: Extended Django user with UUID primary key, email/username/avatar
- **AccountNumber**: Unique 10-digit account numbers with hashed storage for privacy
- **UserWallet**: One-to-one with user, stores balance, previous balance, currency
- **TransferPin**: Hashed 4-digit PIN for transaction security
- **Transfer**: Records between wallets with status tracking
- **Withdraw**: Bank withdrawal requests with account details
- **WalletTransaction**: Comprehensive transaction log with idempotency keys

**Key Relationships**:
- User → Wallet (1:1)
- Wallet → AccountNumber (1:1)
- User → TransferPin (1:1)
- Wallet → Transactions (1:many)
- Transfer → Sender/Receiver Wallets (many:1)

**Constraints**: Unique constraints prevent duplicate wallets per user, hashed fields ensure data privacy.

## Getting Started
1. **Prerequisites**:
   - Python 3.13+
   - uv package manager (recommended) or pip
   - Paystack account with API keys

2. **Installation**:
   - Clone: `git clone https://github.com/ogennaisrael01/Wallet-API.git`
   - Navigate: `cd Wallet-API`
   - Install: `uv sync` (or `pip install -r requirements.txt`)

3. **Environment Setup**:
   Create `.env` file with:
   ```
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   PAYSTACK_SECRET_KEY=your-paystack-secret
   PAYSTACK_INITIALIZE_URL=https://api.paystack.co/transaction/initialize
   PAYSTACK_VERIFY_PAYMENT=https://api.paystack.co/transaction/verify/
   JWT_ACCESS_TOKEN_LIFETIME=50
   JWT_REFRESH_TOKEN_LIFETIME=7
   PAGINATION_PAGE_SIZE=20
   ```

4. **Database Setup**:
   - Run migrations: `uv run manage.py migrate`
   - Create superuser: `uv run manage.py createsuperuser`

5. **Run Development Server**:
   - Start: `uv run manage.py runserver 0.0.0.0:8000`
   - Access admin: `http://localhost:8000/admin/`
   - API docs: `http://localhost:8000/api/schema/swagger-ui/`

6. **Testing**:
   - Use `test_client.http` file in VS Code REST Client extension
   - Register user, login, set PIN, deposit funds, test transfers

The system is production-ready with proper error handling, logging, and security measures. For production deployment, configure PostgreSQL, set DEBUG=False, and use Gunicorn with proper environment variables.