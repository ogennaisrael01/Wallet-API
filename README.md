# Wallet API

## Overview

A fintech-inspired backend system that simulates a digital wallet, enabling users to securely manage funds, perform transactions, and track balances through RESTful APIs.

## Features

* User authentication and authorization(JWT)
* Wallet creation and balance management
* Deposit and withdrawal operations
* Secure fund transfers between users
* Transaction validation and error handling

## Tech Stack

* Python
* Django
* Django REST Framework
* SQLite

## API Endpoints (Sample)

* POST /api/auth/register/
* POST /api/auth/login/
* GET /api/wallet/
* POST /api/deposit/
* POST /api/transfer/

## Key Engineering Decisions

* Implemented validation logic to prevent invalid transactions (e.g., insufficient balance)
* Structured project using DRF serializers and views for scalability
* Designed modular architecture for maintainability and future expansion

## Setup Instructions

1. Clone the repository:
   git clone https://github.com/ogennaisrael01/Wallet-API.git

2. Navigate into the project:
   cd Wallet-API

3. Create a virtual environment:
   uv venv

4. Activate environment:
   source venv/bin/activate  (Linux/macOS)
   venv\Scripts\activate     (Windows)

5. Install dependencies:
   uv sync

6. Run migrations:
   uv run manage.py migrate

7. Start server:
   uv run manage.py runserver 0.0.0.0:8000

## Future Improvements

* Implement transaction history tracking
* Add unit tests for core functionality
* Dockerize the application
