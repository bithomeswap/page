# account_query.py
"""
账户金额查询 - 支持理财、现货、合约账户
签名实现与 exchange_client.py 保持一致
"""

import base64
import hashlib
import hmac
import json
import time
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from clients.api_keys_live import get_live_keys


@dataclass
class AccountSummary:
    """账户总览"""
    exchange: str
    spot_usdt: float = 0.0          # 现货/资金账户 USDT
    contract_usdt: float = 0.0      # 合约账户 USDT（可用余额）
    contract_total_usdt: float = 0.0 # 合约总权益（含保证金+未实现盈亏）
    earn_usdt: float = 0.0          # 活期理财 USDT
    total_usdt: float = 0.0         # 总计
    
    def calculate_total(self):
        self.total_usdt = self.spot_usdt + self.contract_usdt + self.earn_usdt


class AccountQuery:
    """账户金额查询"""
    
    @staticmethod
    def _request(url: str, headers: Dict, body: str = None, method: str = "GET") -> Dict:
        """发送HTTP请求"""
        try:
            data = body.encode() if body else None
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            return {"error": f"HTTP {e.code}: {error_body}"}
        except Exception as e:
            return {"error": str(e)}
    
    # ========== Binance 查询 ==========
    def query_binance(self, api_key: str, secret_key: str) -> AccountSummary:
        """查询币安账户 - 现货、合约、理财"""
        summary = AccountSummary(exchange="Binance")
        
        timestamp = int(time.time() * 1000)
        
        def sign(params: str) -> str:
            return hmac.new(secret_key.encode(), params.encode(), hashlib.sha256).hexdigest()
        
        headers = {"X-MBX-APIKEY": api_key}
        
        # 1. 查询现货余额
        params = f"timestamp={timestamp}"
        signature = sign(params)
        url = f"https://api.binance.com/sapi/v1/capital/config/getall?{params}&signature={signature}"
        
        data = self._request(url, headers)
        if isinstance(data, list):
            for item in data:
                if item.get("coin") == "USDT":
                    summary.spot_usdt = float(item.get("free", 0))
                    break
        
        # 2. 查询合约账户
        params = f"timestamp={timestamp}"
        signature = sign(params)
        url = f"https://fapi.binance.com/fapi/v2/balance?{params}&signature={signature}"
        
        data = self._request(url, headers)
        if isinstance(data, list):
            for item in data:
                if item.get("asset") == "USDT":
                    summary.contract_usdt = float(item.get("availableBalance", 0))
                    summary.contract_total_usdt = float(item.get("balance", 0))
                    break
        
        # 3. 查询理财余额（Simple Earn 灵活理财）
        params = f"timestamp={timestamp}&size=100"
        signature = sign(params)
        url = f"https://api.binance.com/sapi/v1/simple-earn/flexible/position?{params}&signature={signature}"
        
        data = self._request(url, headers)
        if "error" not in data and "rows" in data:
            for item in data["rows"]:
                if item.get("asset") == "USDT":
                    summary.earn_usdt += float(item.get("totalAmount", 0))
        
        summary.calculate_total()
        return summary
    
    # ========== OKX 查询（修正版） ==========
    def query_okx(self, api_key: str, secret_key: str, passphrase: str) -> AccountSummary:
        """查询OKX账户 - 资金账户、交易账户、理财"""
        summary = AccountSummary(exchange="OKX")
        
        def sign(method: str, path: str, body: str = "") -> tuple:
            # 完全复制 exchange_client.py 中的实现
            ts = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
            message = ts + method.upper() + path + body
            
            signature = base64.b64encode(
                hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
            
            return ts, signature
        
        def get_headers(method: str, path: str, body: str = "") -> Dict:
            timestamp, signature = sign(method, path, body)
            headers = {
                "OK-ACCESS-KEY": api_key,
                "OK-ACCESS-SIGN": signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": passphrase,
                "Content-Type": "application/json"
            }
            # 注意：实盘不添加 x-simulated-trading header
            return headers
        
        # 1. 查询资金账户（现货）
        path = "/api/v5/asset/balances"
        # 注意：GET 请求的参数应该放在 path 中，而不是 body
        url = f"https://www.okx.com{path}?ccy=USDT"
        data = self._request(url, get_headers("GET", path))
        
        if data.get("code") == "0":
            for item in (data.get("data") or []):
                if item.get("ccy") == "USDT":
                    summary.spot_usdt = float(item.get("availBal", 0))
                    break
        else:
            print(f"  OKX资金账户查询失败: {data}")
        
        # 2. 查询交易账户（合约）
        path = "/api/v5/account/balance"
        url = f"https://www.okx.com{path}?ccy=USDT"
        data = self._request(url, get_headers("GET", path))
        
        if data.get("code") == "0":
            for detail in (data.get("data") or [{}])[0].get("details", []):
                if detail.get("ccy") == "USDT":
                    summary.contract_usdt = float(detail.get("availBal", 0))
                    summary.contract_total_usdt = float(detail.get("eq", 0))
                    break
        else:
            print(f"  OKX交易账户查询失败: {data}")
        
        # 3. 查询活期理财（余币宝）
        path = "/api/v5/finance/savings/balance"
        url = f"https://www.okx.com{path}?ccy=USDT"
        data = self._request(url, get_headers("GET", path))
        
        if data.get("code") == "0":
            for item in (data.get("data") or []):
                if item.get("ccy") == "USDT":
                    summary.earn_usdt = float(item.get("amt", 0))
                    break
        elif data.get("code") != "51000":  # 51000 表示未开通
            print(f"  OKX理财查询: {data.get('msg', '未知')}")
        
        summary.calculate_total()
        return summary

    # ========== Gate 查询 ==========
    def query_gate(self, api_key: str, secret_key: str) -> AccountSummary:
        """查询Gate账户 - 现货、合约、理财"""
        summary = AccountSummary(exchange="Gate")
        
        def sign(method: str, path: str, body: str = "", query: str = "") -> tuple:
            # 与 exchange_client.py 中 GateClient._sign 保持一致
            timestamp = str(int(time.time()))
            body_hash = hashlib.sha512(body.encode() if body else b"").hexdigest()
            message = f"{method.upper()}\n{path}\n{query}\n{body_hash}\n{timestamp}"
            
            signature = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            return timestamp, signature
        
        def get_headers(method: str, path: str, body: str = "", query: str = "") -> Dict:
            timestamp, signature = sign(method, path, body, query)
            return {
                "KEY": api_key,
                "SIGN": signature,
                "Timestamp": timestamp,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        
        # 1. 查询现货账户
        path = "/api/v4/spot/accounts"
        url = f"https://api.gateio.ws{path}"
        data = self._request(url, get_headers("GET", path))
        
        if isinstance(data, list):
            for item in data:
                if item.get("currency") == "USDT":
                    summary.spot_usdt = float(item.get("available", 0))
                    break
        
        # 2. 查询合约账户
        path = "/api/v4/futures/usdt/accounts"
        url = f"https://api.gateio.ws{path}"
        data = self._request(url, get_headers("GET", path))
        
        if isinstance(data, dict):
            summary.contract_usdt = float(data.get("available", 0))
            summary.contract_total_usdt = float(data.get("total", 0))
        
        # 3. 查询理财宝持仓 - 使用正确的 API 端点
        # Gate V4 理财 API: GET /api/v4/earn/uni/lends （统一理财计划）
        endpoints = [
            ("/api/v4/earn/uni/lends", "lends"),           # 理财宝借贷记录
            ("/api/v4/earn/uni/interest", "interest"),     # 理财宝收益记录
            ("/api/v4/wallet/records", "records"),         # 钱包记录
        ]
        for path, name in endpoints:
            url = f"https://api.gateio.ws{path}"
            data = self._request(url, get_headers("GET", path))
            if isinstance(data, list) and data:
                print(f"  Gate {name} API 返回: {len(data)} 条记录")
                for item in data:
                    if item.get("currency") == "USDT":
                        amount = float(item.get("amount", item.get("principal", 0)))
                        if amount > 0:
                            summary.earn_usdt += amount
        # 如果以上都为空，尝试查询活期理财
        if summary.earn_usdt == 0:
            # Gate 活期理财可能通过 wallet/records 查询
            path = "/api/v4/wallet/records"
            query = "currency=USDT&type=lend"
            url = f"https://api.gateio.ws{path}?{query}"
            headers = get_headers("GET", path, query=query)
            data = self._request(url, headers)
            if isinstance(data, list):
                for item in data:
                    if item.get("type") == "lend" and item.get("change") > 0:
                        summary.earn_usdt += float(item.get("balance", 0))
        
        summary.calculate_total()
        return summary
    
    # ========== Bitget 查询 ==========
    def query_bitget(self, api_key: str, secret_key: str, passphrase: str) -> AccountSummary:
        """查询Bitget账户 - 现货、合约、理财"""
        summary = AccountSummary(exchange="Bitget")
        
        def sign(timestamp: str, method: str, path: str, body: str = "") -> str:
            # 与 exchange_client.py 中 BitgetClient._sign 保持一致
            message = timestamp + method.upper() + path + body
            return base64.b64encode(
                hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
        
        def get_headers(method: str, path: str, body: str = "") -> Dict:
            timestamp = str(int(time.time() * 1000))
            signature = sign(timestamp, method, path, body)
            return {
                "ACCESS-KEY": api_key,
                "ACCESS-SIGN": signature,
                "ACCESS-TIMESTAMP": timestamp,
                "ACCESS-PASSPHRASE": passphrase,
                "Content-Type": "application/json"
            }
        
        # 1. 查询现货账户
        path = "/api/v2/spot/account/assets?coin=USDT"
        url = f"https://api.bitget.com{path}"
        data = self._request(url, get_headers("GET", path))
        
        if data.get("code") == "00000":
            for item in (data.get("data") or []):
                if item.get("coin") == "USDT":
                    summary.spot_usdt = float(item.get("available", 0))
                    break
        
        # 2. 查询合约账户
        path = "/api/v2/mix/account/accounts?productType=USDT-FUTURES"
        url = f"https://api.bitget.com{path}"
        data = self._request(url, get_headers("GET", path))
        
        if data.get("code") == "00000":
            for item in (data.get("data") or []):
                if item.get("marginCoin") == "USDT":
                    summary.contract_usdt = float(item.get("available", 0))
                    # Bitget 需要计算总权益
                    locked = float(item.get("locked", 0))
                    summary.contract_total_usdt = summary.contract_usdt + locked
                    break
        
        # 3. 查询活期理财
        path = "/api/v2/earn/savings/assets?coin=USDT"
        url = f"https://api.bitget.com{path}"
        data = self._request(url, get_headers("GET", path))
        
        if data.get("code") == "00000":
            raw = data.get("data") or {}
            items = raw.get("resultList") or []
            for item in items:
                summary.earn_usdt += float(item.get("holdAmount", 0))
        
        summary.calculate_total()
        return summary


def format_amount(amount: float) -> str:
    """格式化金额显示"""
    if amount >= 1000:
        return f"${amount:,.2f}"
    elif amount >= 1:
        return f"${amount:,.4f}"
    else:
        return f"${amount:.6f}"


def main():
    print("=" * 80)
    print("📊 账户总览 - 现货 | 合约 | 理财")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    query = AccountQuery()
    total_assets = 0.0
    results = []
    
    # 查询币安
    print("\n🏦 BINANCE")
    print("-" * 50)
    try:
        keys = get_live_keys("binance")
        if keys and keys.get("key"):
            summary = query.query_binance(keys["key"], keys["secret"])
            results.append(summary)
            print(f"  现货余额:     {format_amount(summary.spot_usdt)}")
            print(f"  合约可用:     {format_amount(summary.contract_usdt)}")
            print(f"  合约权益:     {format_amount(summary.contract_total_usdt)}")
            print(f"  活期理财:     {format_amount(summary.earn_usdt)}")
            print(f"  ────────────────────────────────────────")
            print(f"  总计:         {format_amount(summary.total_usdt)}")
            total_assets += summary.total_usdt
        else:
            print("  ❌ API Key 未配置")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    # 查询 OKX
    print("\n🏦 OKX")
    print("-" * 50)
    try:
        keys = get_live_keys("okx")
        if keys and keys.get("key"):
            summary = query.query_okx(keys["key"], keys["secret"], keys["passphrase"])
            results.append(summary)
            print(f"  资金账户:     {format_amount(summary.spot_usdt)}")
            print(f"  交易可用:     {format_amount(summary.contract_usdt)}")
            print(f"  交易权益:     {format_amount(summary.contract_total_usdt)}")
            print(f"  余币宝:       {format_amount(summary.earn_usdt)}")
            print(f"  ────────────────────────────────────────")
            print(f"  总计:         {format_amount(summary.total_usdt)}")
            total_assets += summary.total_usdt
        else:
            print("  ❌ API Key 未配置")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    # 查询 Gate
    print("\n🏦 GATE")
    print("-" * 50)
    try:
        keys = get_live_keys("gate")
        if keys and keys.get("key"):
            summary = query.query_gate(keys["key"], keys["secret"])
            results.append(summary)
            print(f"  现货余额:     {format_amount(summary.spot_usdt)}")
            print(f"  合约可用:     {format_amount(summary.contract_usdt)}")
            print(f"  合约权益:     {format_amount(summary.contract_total_usdt)}")
            print(f"  理财宝:       {format_amount(summary.earn_usdt)}")
            print(f"  ────────────────────────────────────────")
            print(f"  总计:         {format_amount(summary.total_usdt)}")
            total_assets += summary.total_usdt
        else:
            print("  ❌ API Key 未配置")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    # 查询 Bitget
    print("\n🏦 BITGET")
    print("-" * 50)
    try:
        keys = get_live_keys("bitget")
        if keys and keys.get("key"):
            summary = query.query_bitget(keys["key"], keys["secret"], keys["passphrase"])
            results.append(summary)
            print(f"  现货余额:     {format_amount(summary.spot_usdt)}")
            print(f"  合约可用:     {format_amount(summary.contract_usdt)}")
            print(f"  合约权益:     {format_amount(summary.contract_total_usdt)}")
            print(f"  活期理财:     {format_amount(summary.earn_usdt)}")
            print(f"  ────────────────────────────────────────")
            print(f"  总计:         {format_amount(summary.total_usdt)}")
            total_assets += summary.total_usdt
        else:
            print("  ❌ API Key 未配置")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    # 总计
    print("\n" + "=" * 80)
    print(f"💰 跨交易所总资产: {format_amount(total_assets)}")
    print("=" * 80)
    
    # 按账户类型汇总
    print("\n📈 按账户类型汇总:")
    print("-" * 50)
    total_spot = sum(r.spot_usdt for r in results)
    total_contract = sum(r.contract_usdt for r in results)
    total_contract_equity = sum(r.contract_total_usdt for r in results)
    total_earn = sum(r.earn_usdt for r in results)
    
    print(f"  现货总额:     {format_amount(total_spot)}")
    print(f"  合约可用:     {format_amount(total_contract)}")
    print(f"  合约权益:     {format_amount(total_contract_equity)}")
    print(f"  理财总额:     {format_amount(total_earn)}")
    
    print("\n" + "=" * 80)
    print("🔧 签名算法（与 exchange_client.py 一致）:")
    print("   - Binance: HMAC-SHA256 + hex")
    print("   - OKX: HMAC-SHA256 + Base64，时间戳 ISO 8601")
    print("   - Gate: HMAC-SHA512 + hex，含 body_hash")
    print("   - Bitget: HMAC-SHA256 + Base64，时间戳毫秒")
    print("=" * 80)


if __name__ == "__main__":
    main()