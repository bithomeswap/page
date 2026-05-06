"""
模拟盘 / 测试网 API 密钥配置（不涉及真实资金）。

安全说明：
    - 此文件为本地私密配置，已写入 .gitignore，请勿提交 GitHub
    - 公开仓库请使用 clients/api_keys_demo.example.py 作为模板
    - 实盘 Key 在 clients/api_keys_live.py（同样勿提交）

测试网地址：
    - Binance: https://testnet.binancefuture.com
    - OKX: Demo Trading（同主网地址，靠 x-simulated-trading:1 区分）
    - Gate: https://api-testnet.gateapi.io
    - Bitget: Demo Trading（同主网地址，靠 paptrading:1 区分）
"""

# ─── Binance 期货测试网 ────────────────────────────────────────────────────────
BINANCE_TESTNET_API_KEY    = "FwG5JD7QTKlJHL3OWp254O53gy6KgZ9xi9DKNSU0d7otn3bGkEwsCyW3cTY3PcMn"
BINANCE_TESTNET_SECRET_KEY = "bXPAdlGWcJ3Fj90CL1HHa3nL78RmRDrY24Kj9FxdtBQHGNfbeBbH4qFX6ZpfGuZm"

# ─── OKX Demo Trading ─────────────────────────────────────────────────────────
OKX_DEMO_API_KEY    = "ac18355e-5b45-4a1d-b5e0-3c582d3a329e"
OKX_DEMO_SECRET_KEY = "6D825ECC50C2758B9B7578DF299F26B2"
OKX_DEMO_PASSPHRASE = "Lrx059218@"

# ─── Gate.io 测试网 ────────────────────────────────────────────────────────────
GATE_TESTNET_API_KEY    = "7e29321b91653ffded777df1f33c77c2"
GATE_TESTNET_SECRET_KEY = "cf224302129cf9823725ac8ff21a1688f57dfd5e241a623d461e8f0aa6c59c05"

# ─── Bitget Demo Trading ───────────────────────────────────────────────────────
BITGET_DEMO_API_KEY    = "bg_0e0ea60d31b540181c6818ec6c85f825"
BITGET_DEMO_SECRET_KEY = "05d3a5dd4afa1f46fd7be62f3b924ab71807f6a72b278176305c08b9cdce94a8"
BITGET_DEMO_PASSPHRASE = "Lrc059218"


def get_demo_keys(exchange: str) -> dict:
    """返回指定交易所的模拟盘 API Key 字典。"""
    return {
        "binance": {"key": BINANCE_TESTNET_API_KEY, "secret": BINANCE_TESTNET_SECRET_KEY},
        "okx":     {"key": OKX_DEMO_API_KEY, "secret": OKX_DEMO_SECRET_KEY, "passphrase": OKX_DEMO_PASSPHRASE},
        "gate":    {"key": GATE_TESTNET_API_KEY, "secret": GATE_TESTNET_SECRET_KEY},
        "bitget":  {"key": BITGET_DEMO_API_KEY, "secret": BITGET_DEMO_SECRET_KEY, "passphrase": BITGET_DEMO_PASSPHRASE},
    }.get(exchange, {})


def check_demo_keys() -> dict[str, bool]:
    """检查各交易所模拟盘 Key 是否已配置（非空）。"""
    return {
        "binance": bool(BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_SECRET_KEY),
        "okx":     bool(OKX_DEMO_API_KEY and OKX_DEMO_SECRET_KEY and OKX_DEMO_PASSPHRASE),
        "gate":    bool(GATE_TESTNET_API_KEY and GATE_TESTNET_SECRET_KEY),
        "bitget":  bool(BITGET_DEMO_API_KEY and BITGET_DEMO_SECRET_KEY and BITGET_DEMO_PASSPHRASE),
    }
