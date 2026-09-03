# ArbitrageEngine

A lightweight cross-exchange arbitrage scanner written in Python.

## Features
- Pulls public spot tickers through `ccxt`
- Compares bid/ask spreads across configured exchanges
- Estimates net edge after configurable fees
- Dry-run only: no order placement or private API keys required
- JSON output option for automation

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python arbitrage_engine.py
```

This project is a research/monitoring tool. It does not guarantee profitable trades and does not place orders.
