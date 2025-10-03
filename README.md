# 🚀 Bitzapp - AI-Powered Bitcoin Wallet in WhatsApp

> **Hackathon-Ready MVP** - A decentralized Bitcoin wallet that works entirely within WhatsApp, powered by AI and real Nigerian payment APIs.

## 🌟 Features

### 💰 **Bitcoin Wallet Management**
- **Non-Custodial Wallets**: Full control of your private keys
- **Custodial Wallets**: Easy-to-use managed wallets
- **Send/Receive Bitcoin**: Direct peer-to-peer transactions
- **Real-time Balance**: Check your Bitcoin balance anytime

### 💱 **Nigerian Integration**
- **Naira Deposits**: Convert Naira to Bitcoin via Bitnob API
- **Naira Withdrawals**: Convert Bitcoin to Naira bank transfers
- **Bill Payments**: Pay Nigerian bills using Bitcoin
- **Real Exchange Rates**: Live BTC/NGN rates from Bitnob

### 🤖 **AI-Powered Assistant**
- **Bitcoin Education**: Learn about Bitcoin and blockchain
- **Transaction Help**: Get assistance with wallet operations
- **Market Insights**: Ask about Bitcoin prices and trends
- **Powered by Gemini AI**: Advanced conversational AI

### 📱 **WhatsApp-First Experience**
- **No App Download**: Works entirely within WhatsApp
- **Simple Commands**: Easy-to-use text commands
- **Secure Messaging**: End-to-end encrypted communication
- **Multi-language Support**: English and local languages

## 🛠️ Tech Stack

- **Backend**: Django + Django REST Framework
- **Database**: SQLite (hackathon), PostgreSQL (production)
- **APIs**: Bitnob, MavaPay, Gemini AI, WhatsApp Business
- **Blockchain**: Bitcoin (Testnet/Mainnet)
- **Deployment**: Ready for Heroku, Railway, or AWS

## 🚀 Quick Start

### 1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd bitzapp
```

### 2. **Set Up Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. **Configure Environment Variables**
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 4. **Run Database Migrations**
```bash
python manage.py migrate
python manage.py setup_sample_data
```

### 5. **Start the Server**
```bash
python manage.py runserver
```

## 🔑 API Configuration

### **Required API Keys:**
- **Bitnob**: BTC/NGN exchange, deposits, withdrawals
- **MavaPay**: Bill payments (Airtel, MTN, DSTV, etc.)
- **Gemini AI**: AI chatbot responses
- **WhatsApp Business**: Message handling

### **Demo Mode:**
The app works in demo mode without API keys - perfect for hackathon demos!

## 📱 WhatsApp Commands

### **Wallet Management**
- `/create` - Create non-custodial wallet
- `/import` - Import existing wallet with seed phrase
- `/wallet` - Show wallet information
- `/balance` - Check Bitcoin balance

### **Bitcoin Operations**
- `/send <amount> <address>` - Send Bitcoin
- `/receive` - Get your Bitcoin address
- `/deposit <amount>` - Deposit Naira to get Bitcoin
- `/withdraw <amount> <bank_details>` - Withdraw Bitcoin to Naira

### **Bill Payments**
- `/paybill <provider> <amount> <account>` - Pay bills with Bitcoin
- `/bills` - List available bill providers

### **AI Assistant**
- `/ask <question>` - Ask the AI about Bitcoin
- `/help` - Show all available commands

## 🏗️ Project Structure

```
bitzapp/
├── core/                    # Core models and views
│   ├── models.py           # User, Wallet, Transaction models
│   ├── views.py            # WhatsApp webhook handler
│   └── command_handlers.py # Command processing logic
├── wallet/                 # Bitcoin wallet services
│   ├── models.py           # Wallet-specific models
│   └── services.py         # Bitcoin operations
├── payments/               # Payment processing
│   ├── models.py           # Payment models
│   └── services.py         # Bitnob/MavaPay integration
├── chatbot/                # AI chatbot
│   ├── models.py           # Chat models
│   └── services.py         # Gemini AI integration
└── tests/                  # Test scripts
```

## 🧪 Testing

### **Run All Tests**
```bash
python test_complete_flow.py
```

### **Test Specific Features**
```bash
# Test custodial wallet
python test_commands.py

# Test non-custodial wallet
python test_non_custodial.py

# Test fresh user flow
python test_fresh_user.py

# Test API integrations
python test_real_apis.py
```

## 🔒 Security Features

- **Non-Custodial Wallets**: Users control their private keys
- **Seed Phrase Security**: BIP39 mnemonic phrases
- **Encrypted Storage**: Private keys encrypted at rest
- **CSRF Protection**: Django CSRF middleware
- **Input Validation**: Comprehensive input sanitization
- **Rate Limiting**: API rate limiting protection

## 🌍 Decentralization

- **No Central Authority**: Users own their Bitcoin
- **Open Source**: Fully transparent codebase
- **Permissionless**: No KYC required for basic usage
- **Censorship Resistant**: Cannot be shut down by authorities
- **Self-Sovereign**: Users control their funds

## 📊 Hackathon Demo

### **Demo Script:**
1. **Create Wallet**: `/create` - Show seed phrase generation
2. **Check Balance**: `/balance` - Show wallet status
3. **Deposit Naira**: `/deposit 50000` - Show Naira to Bitcoin conversion
4. **Pay Bills**: `/paybill airtel 1000 08012345678` - Show bill payment
5. **AI Chat**: `/ask What is Bitcoin?` - Show AI responses
6. **Send Bitcoin**: `/send 0.001 bc1...` - Show peer-to-peer transfer

### **Key Demo Points:**
- ✅ **Real API Integration**: Bitnob, MavaPay, Gemini
- ✅ **Non-Custodial**: Users control private keys
- ✅ **WhatsApp Native**: No app download required
- ✅ **Nigerian Focus**: Local payment methods
- ✅ **AI Powered**: Intelligent assistance

## 🚀 Deployment

### **Heroku (Recommended)**
```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn bitzapp.wsgi" > Procfile

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### **Railway**
```bash
# Connect GitHub repository
# Set environment variables
# Deploy automatically
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Hackathon Submission

**Project**: Bitzapp - AI-Powered Bitcoin Wallet in WhatsApp
**Track**: FinTech / Blockchain
**Team**: [Your Team Name]
**Demo**: [Your Demo URL]

### **Problem Solved:**
- **Accessibility**: Bitcoin for the unbanked in Nigeria
- **Education**: AI-powered Bitcoin learning
- **Integration**: Local payment methods
- **Decentralization**: Non-custodial wallet control

### **Technical Innovation:**
- **WhatsApp Integration**: No app download barrier
- **Real API Integration**: Production-ready code
- **Non-Custodial Design**: True decentralization
- **AI Assistant**: Educational and helpful

---

**Built with ❤️ for the Nigerian Bitcoin community**