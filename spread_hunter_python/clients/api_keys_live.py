"""
实盘 API 密钥（主网 - 涉及真实资金）。

⚠️  安全提示：
    - 此文件已加入 .gitignore，不会提交到 Git
    - 服务器上建议设置 600 权限：chmod 600 clients/api_keys_live.py
    - 发现泄露立即到交易所撤销并重新生成 API Key

IP 绑定：45.76.202.248（学生服务器地址）
Gate 资金密码：090204（提现时需要）
"""

# ─── Binance 主网 ──────────────────────────────────────────────────────────────
# 权限：期货交易 + 账户查询；如需划转提现还需开启"通用划转"
BINANCE_API_KEY    = "0jmNVvNZusoXKGkwnGLBghPh8Kmc0klh096VxNS9kn8P0nkAEslVUlsuOcRoGrtm"
BINANCE_SECRET_KEY = "PbSWkno1meUckhmkLyz8jQ2RRG7KgmZyAWhIF0qPdCJrmDSFxoxGdMG5gZeYYCgy"

# ─── OKX 主网 ─────────────────────────────────────────────────────────────────
OKX_API_KEY    = "8635667b-0702-4034-ab65-ff58275a0556"
OKX_SECRET_KEY = "5A133B8EDFA08199FD4733DD4338D712"
OKX_PASSPHRASE = "wthWTH00."

# ─── Gate 主网 ────────────────────────────────────────────────────────────────
GATE_API_KEY    = "ca2acb5938c32509605a1534f1af71a8"
GATE_SECRET_KEY = "100115d19a15fcc9d881f9b127ca7a1fbbadba92ee23f909a7db3d5ee82f8ecc"

# ─── Bitget 主网 ──────────────────────────────────────────────────────────────
BITGET_API_KEY    = "bg_5e69f9e32e87c9bb8087f97cc6adb910"
BITGET_SECRET_KEY = "b0682a6e4a0e0c50493a4be19b4f56de4fa81f07d6e7d010a71e1971a7c3bbb4"
BITGET_PASSPHRASE = "wthWTH00"


def get_live_keys(exchange: str) -> dict:
    """返回指定交易所的实盘 API Key 字典。"""
    return {
        "binance": {"key": BINANCE_API_KEY, "secret": BINANCE_SECRET_KEY},
        "okx":     {"key": OKX_API_KEY, "secret": OKX_SECRET_KEY, "passphrase": OKX_PASSPHRASE},
        "gate":    {"key": GATE_API_KEY, "secret": GATE_SECRET_KEY},
        "bitget":  {"key": BITGET_API_KEY, "secret": BITGET_SECRET_KEY, "passphrase": BITGET_PASSPHRASE},
    }.get(exchange, {})


def check_live_keys() -> dict[str, bool]:
    """检查各交易所实盘 Key 是否已配置（非空）。"""
    return {
        "binance": bool(BINANCE_API_KEY and BINANCE_SECRET_KEY),
        "okx":     bool(OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE),
        "gate":    bool(GATE_API_KEY and GATE_SECRET_KEY),
        "bitget":  bool(BITGET_API_KEY and BITGET_SECRET_KEY and BITGET_PASSPHRASE),
    }
