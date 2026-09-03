from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Iterable

import ccxt
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Opportunity:
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    gross_edge_pct: float
    estimated_net_edge_pct: float


def csv_env(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


def load_tickers(exchange_ids: Iterable[str], symbol: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for exchange_id in exchange_ids:
        exchange_cls = getattr(ccxt, exchange_id, None)
        if exchange_cls is None:
            continue
        exchange = exchange_cls({"enableRateLimit": True, "timeout": 15000})
        try:
            ticker = exchange.fetch_ticker(symbol)
            bid = float(ticker.get("bid") or 0)
            ask = float(ticker.get("ask") or 0)
            if bid > 0 and ask > 0:
                out[exchange_id] = {"bid": bid, "ask": ask}
        except Exception as exc:
            print(f"warning: {exchange_id}: {exc}")
        finally:
            close = getattr(exchange, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
    return out


def find_opportunities(symbol: str, tickers: dict[str, dict], fee_pct: float, min_net_pct: float) -> list[Opportunity]:
    results: list[Opportunity] = []
    names = list(tickers)
    for buy_name in names:
        for sell_name in names:
            if buy_name == sell_name:
                continue
            ask = tickers[buy_name]["ask"]
            bid = tickers[sell_name]["bid"]
            if bid <= ask:
                continue
            gross = ((bid - ask) / ask) * 100
            net = gross - (2 * fee_pct)
            if net >= min_net_pct:
                results.append(Opportunity(symbol, buy_name, sell_name, ask, bid, gross, net))
    return sorted(results, key=lambda x: x.estimated_net_edge_pct, reverse=True)


def main() -> None:
    exchanges = csv_env("EXCHANGES", "kraken,coinbase,okx")
    symbols = csv_env("SYMBOLS", "BTC/USDT,ETH/USDT")
    fee_pct = float(os.getenv("ESTIMATED_FEE_PCT", "0.10"))
    min_net_pct = float(os.getenv("MIN_NET_EDGE_PCT", "0.20"))
    json_output = os.getenv("JSON_OUTPUT", "0") == "1"

    all_results: list[Opportunity] = []
    for symbol in symbols:
        tickers = load_tickers(exchanges, symbol)
        all_results.extend(find_opportunities(symbol, tickers, fee_pct, min_net_pct))

    if json_output:
        print(json.dumps([asdict(x) for x in all_results], indent=2))
        return

    if not all_results:
        print("No qualifying opportunities found.")
        return

    for item in all_results:
        print(
            f"{item.symbol}: buy {item.buy_exchange} @ {item.buy_price:.8f} -> "
            f"sell {item.sell_exchange} @ {item.sell_price:.8f} | "
            f"net≈{item.estimated_net_edge_pct:.3f}%"
        )


if __name__ == "__main__":
    main()
