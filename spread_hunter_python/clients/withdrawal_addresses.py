"""
各交易所 USDT 充值地址（用于资金再平衡提现目标）。

格式：ADDRESSES[exchange][network] = address
网络名称与各交易所 API 的 chain/network 参数对应：
  - SOL  → Solana
  - BSC  → BNB Smart Chain (BEP20)
  - TRX  → Tron (TRC20)
  - ETH  → Ethereum (ERC20)

注意：BSC/ETH/ARB/POL 通常共用同一个 EVM 地址。
"""

ADDRESSES: dict[str, dict[str, str]] = {
    "binance": {
        "SOL": "DRwv5ApPFC41zHokT7xYdUWEArjJ1i4qwRoCQ8NJchzV",
        "TRX": "TLYcXKe687V2VcN7qqohjtkaPgq7KTVxZE",
        "ETH": "0x67ad4b57089952ada7f8004d0262d2d5e5eeda7d",
        "BSC": "0x67ad4b57089952ada7f8004d0262d2d5e5eeda7d",
        "POL": "0x67ad4b57089952ada7f8004d0262d2d5e5eeda7d",
    },
    "okx": {
        "SOL": "8CXPtieZ52MCZkrtDeACiD5R9wuVUqR7JDEjqjiWBRic",
        "TRX": "TEhsrZgCrra6BwQn6feDPcBNbabqSDaxg8",
        "ETH": "0x8c7b7aef3ead4134b802e337c05752946098ed38",
        "BSC": "0x8c7b7aef3ead4134b802e337c05752946098ed38",
        "ARB": "0x8c7b7aef3ead4134b802e337c05752946098ed38",
        "AVAX": "0x8c7b7aef3ead4134b802e337c05752946098ed38",
    },
    "gate": {
        "SOL":  "3BSURcEHkGa2PRLLt2p173qAHYfDucPe5i4xa6TwWogr",
        "TRX":  "TUALrGrLd7Wx5iKuQBLfXzVxHFRWLTbrsB",
        "ETH":  "0xc78d642D463c8B244A88C991B681A369Cf045e4A",
        "BSC":  "0xc78d642D463c8B244A88C991B681A369Cf045e4A",
        "ARB":  "0xc78d642D463c8B244A88C991B681A369Cf045e4A",
        "AVAX": "0xc78d642D463c8B244A88C991B681A369Cf045e4A",
    },
    "bitget": {
        "SOL": "CrgYHVKVj2iHEBXsd4SZP3ZamnJxcFmVnxTsa89dDPR1",
        "TRX": "TXPNJdv2Qwf9PJYZedMEJSHmXB7ysMiQhp",
        "ETH": "0x77f024e482ab6547f77444113a9237f8fe0492bb",
        "BSC": "0x77f024e482ab6547f77444113a9237f8fe0492bb",
        "ARB": "0x77f024e482ab6547f77444113a9237f8fe0492bb",
    },
    "htx": {
        "SOL": "5EaZT9En6Hks8VhZYkGiVysCyr1X9Sy3JCgUnJrUXD4Y",
        "TRX": "TPtd2TzkBNuUbNJAN9ZXx2pkP6ZY3FSpuJ",
        "ETH": "0x866955a009dd67a1c08f99312fda17690d0e0cad",
        "BSC": "0x866955a009dd67a1c08f99312fda17690d0e0cad",
        "ARB": "0x866955a009dd67a1c08f99312fda17690d0e0cad",
    },
}

# 各交易所 API 使用的网络名称映射（内部统一名 → 各所参数值）
NETWORK_NAMES: dict[str, dict[str, str]] = {
    "binance": {"SOL": "SOL", "BSC": "BSC", "TRX": "TRX", "ETH": "ETH"},
    "okx":     {"SOL": "Solana", "BSC": "BSC", "TRX": "TRC20", "ETH": "ERC20", "ARB": "Arbitrum One"},
    "gate":    {"SOL": "SOL", "BSC": "BSC", "TRX": "TRX", "ETH": "ETH", "ARB": "ARB"},
    "bitget":  {"SOL": "SOL", "BSC": "BEP20", "TRX": "TRC20", "ETH": "ERC20", "ARB": "ARB"},
}

# 优先尝试的网络列表（按手续费从低到高的经验排序）
PREFERRED_NETWORKS = ["SOL", "BSC", "ARB", "TRX", "ETH"]


def get_deposit_address(exchange: str, network: str) -> str:
    """获取指定交易所指定网络的 USDT 充值地址。"""
    return ADDRESSES.get(exchange, {}).get(network, "")


def get_api_network_name(exchange: str, network: str) -> str:
    """将内部统一网络名转换为指定交易所 API 使用的网络名称参数。"""
    return NETWORK_NAMES.get(exchange, {}).get(network, network)


def get_supported_networks(source: str, target: str) -> list[str]:
    """
    返回 source 和 target 交易所都支持的网络列表（按优先级排序）。
    即：source 能提现、target 有对应充值地址。
    """
    src_nets = set(ADDRESSES.get(source, {}).keys())
    tgt_nets = set(ADDRESSES.get(target, {}).keys())
    common   = src_nets & tgt_nets
    return [n for n in PREFERRED_NETWORKS if n in common]
