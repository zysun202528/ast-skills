import requests
import pandas as pd
from datetime import datetime
import json
import time

class TencentDataLoader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://gu.qq.com/'
        }

    def _get_symbol_prefix(self, symbol):
        """
        Identify if the symbol is SH (Shanghai) or SZ (Shenzhen).
        Tencent API format: sh600519, sz000001
        """
        if symbol.startswith('6') or symbol.startswith('9') or symbol.startswith('sh'):
            return f"sh{symbol[-6:]}"
        else:
            return f"sz{symbol[-6:]}"

    def get_stock_history(self, symbol, days=365):
        """
        Get daily historical k-line data from Tencent.
        symbol: e.g. '600519' or 'sh600519'
        """
        ts_code = self._get_symbol_prefix(symbol)
        
        # Tencent API for daily k-line: http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,day,,,320,qfq
        # param format: code,k_type,start_date,end_date,num_points,adjust_type
        # qfq = forward adjusted price
        url = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {
            'param': f"{ts_code},day,,,{days},qfq"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Parse response: data['data'][ts_code]['day'] or ['qfqday']
                if 'data' in data and ts_code in data['data']:
                    stock_data = data['data'][ts_code]
                    
                    # Prefer 'qfqday' (forward adjusted) if available, else 'day'
                    raw_data = stock_data.get('qfqday', stock_data.get('day', []))
                    
                    if not raw_data:
                        return None
                        
                    # Tencent data format: [date, open, close, high, low, volume, ...]
                    # The number of columns might vary (e.g., 6 or 7 or more).
                    # We only need the first 6 columns.
                    try:
                        df = pd.DataFrame(raw_data)
                        # Ensure we have at least 6 columns
                        if df.shape[1] < 6:
                            return None
                            
                        # Select first 6 columns
                        df = df.iloc[:, :6]
                        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume']
                    except Exception as e:
                        print(f"Error processing data frame for {symbol}: {e}")
                        return None
                    
                    # Clean data
                    df['date'] = pd.to_datetime(df['date'])
                    for col in ['open', 'close', 'high', 'low', 'volume']:
                        df[col] = pd.to_numeric(df[col])
                        
                    return df
            return None
        except Exception as e:
            print(f"Error fetching history for {symbol}: {e}")
            return None

    def get_realtime_snapshot(self, symbols):
        """
        Get realtime snapshot for a list of symbols.
        symbols: list of stock codes ['600519', '000001']
        """
        if isinstance(symbols, str):
            symbols = [symbols]
            
        ts_codes = [self._get_symbol_prefix(s) for s in symbols]
        codes_str = ",".join(ts_codes)
        
        # Tencent realtime API: http://qt.gtimg.cn/q=sh600519,sz000001
        url = f"http://qt.gtimg.cn/q={codes_str}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                # Response format: v_sh600519="1~贵州茅台~600519~1700.00~...";
                results = {}
                lines = response.text.split(';')
                
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.split('="')
                    if len(parts) < 2:
                        continue
                        
                    code = parts[0].split('_')[-1] # sh600519
                    data_str = parts[1].strip('"')
                    data = data_str.split('~')
                    
                    if len(data) > 30:
                        results[code] = {
                            'name': data[1],
                            'code': data[2],
                            'price': float(data[3]),
                            'prev_close': float(data[4]),
                            'open': float(data[5]),
                            'volume': float(data[6]), # in hands (100 shares)
                            'amount': float(data[37]) * 10000, # turnover amount
                            'change_pct': float(data[32]),
                            'high': float(data[33]),
                            'low': float(data[34]),
                            'market_value': float(data[45]) if len(data) > 45 else 0, # total market cap
                            'pe': float(data[39]) if len(data) > 39 else 0
                        }
                return results
            return None
        except Exception as e:
            print(f"Error fetching realtime data: {e}")
            return None

    def get_index_data(self):
        """
        Get major A-share indices data (Snapshot + Brief History)
        Indices: SH Composite (sh000001), SZ Component (sz399001), ChiNext (sz399006)
        """
        indices = ['sh000001', 'sz399001', 'sz399006']
        return self.get_realtime_snapshot(indices)

    def get_index_history(self, index_code, days=365):
        """
        Get historical data for an index.
        index_code: e.g. 'sh000001'
        """
        return self.get_stock_history(index_code, days)

    def get_realtime_quote(self, symbol):
        """
        Get real-time quote for a single stock.
        Useful for checking opening price at 9:25 or real-time monitoring.
        symbol: e.g. '600519'
        """
        # Add prefix
        if symbol.startswith('6'):
            code = f"sh{symbol}"
        elif symbol.startswith('0') or symbol.startswith('3'):
            code = f"sz{symbol}"
        else:
            code = f"sh{symbol}" # Default fallback
            
        url = f"http://qt.gtimg.cn/q={code}"
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                # Format: v_sh600519="1~贵州茅台~600519~1514.00~..."
                content = response.text
                if not content:
                    return None
                    
                parts = content.split('~')
                if len(parts) > 30:
                    data = {
                        'name': parts[1],
                        'code': parts[2],
                        'price': float(parts[3]),
                        'prev_close': float(parts[4]),
                        'open': float(parts[5]),
                        'volume': float(parts[6]),
                        'bid1': float(parts[9]),
                        'ask1': float(parts[19]),
                        'high': float(parts[33]),
                        'low': float(parts[34]),
                        'amount': float(parts[37]),
                        'turnover_rate': float(parts[38]) if parts[38] else 0,
                        'pe': float(parts[39]) if parts[39] else 0,
                        'market_cap': float(parts[45]) if parts[45] else 0, # Total Market Cap
                    }
                    return data
        except Exception as e:
            print(f"Error fetching realtime quote for {symbol}: {e}")
            
        return None

    def get_market_breadth(self):
        """
        Get market breadth data: Up/Down counts.
        Since getting full market breadth is heavy, we use a sample of 
        ~20 key constituents from various sectors (Key Stock Breadth).
        """
        # Representative stocks (Top weighted in indices)
        # 600519(茅台), 300750(宁德), 601318(平安), 600036(招行), 002594(比亚迪)
        # 000858(五粮液), 601888(中免), 300059(东财), 600030(中信), 601012(隆基)
        # 000333(美的), 600276(恒瑞), 603288(海天), 002415(海康), 601138(工业富联)
        # 000001(平安银行), 600900(长江电力), 601398(工行), 000651(格力), 601088(神华)
        sample_symbols = [
            '600519', '300750', '601318', '600036', '002594',
            '000858', '601888', '300059', '600030', '601012',
            '000333', '600276', '603288', '002415', '601138',
            '000001', '600900', '601398', '000651', '601088'
        ]
        
        # Add Northbound Fund Flow as well
        breadth_data = {'north_net_inflow': 0, 'up': 0, 'down': 0, 'flat': 0}
        
        # 1. Get Northbound
        url_north = "http://qt.gtimg.cn/q=ff_north_cney,ff_north_hkhy"
        try:
            resp = requests.get(url_north, headers=self.headers, timeout=5)
            if resp.status_code == 200:
                parts = resp.text.split(';')
                for part in parts:
                    if "ff_north_cney" in part:
                        vals = part.split('~')
                        if len(vals) > 4:
                            breadth_data['north_net_inflow'] = float(vals[3]) 
        except Exception:
            pass

        # 2. Get Sampled Breadth
        snapshots = self.get_realtime_snapshot(sample_symbols)
        if snapshots:
            for code, data in snapshots.items():
                if data['change_pct'] > 0:
                    breadth_data['up'] += 1
                elif data['change_pct'] < 0:
                    breadth_data['down'] += 1
                else:
                    breadth_data['flat'] += 1
                    
        return breadth_data

    def get_sector_map(self):
        return {
            'sh512880': '证券 (Securities)',
            'sh512480': '半导体 (Semiconductor)',
            'sh516160': '新能源 (New Energy)',
            'sh512010': '医药 (Healthcare)',
            'sh510150': '消费 (Consumer)',
            'sh512800': '银行 (Bank)',
            'sh512660': '军工 (Military)',
            'sh512690': '酒 (Liquor)',
            'sh561560': '电力 (Power)',
            'sh515070': '人工智能 (AI)',
            'sh515050': '通信 (Communication/CPO)',
            'sh512980': '传媒 (Media)',
            'sh512200': '房地产 (Real Estate)',
            'sh515220': '煤炭 (Coal)',
            'sz159995': '芯片 (Chips)',
            'sz159939': '信息技术 (IT)'
        }

    def get_sector_etf_performance(self):
        """
        Get performance of key sector ETFs to identify leading sectors.
        Returns a list of dicts with sector info.
        """
        # Key Sector ETFs (Top Liquid & Representative)
        sectors = self.get_sector_map()
        
        # Let's construct URL manually to be safe with ETF codes
        codes_str = ",".join(sectors.keys())
        url = f"http://qt.gtimg.cn/q={codes_str}"
        
        results = []
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                lines = response.text.split(';')
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.split('="')
                    if len(parts) < 2:
                        continue
                        
                    code = parts[0].split('_')[-1] # sh512880
                    data_str = parts[1].strip('"')
                    data = data_str.split('~')
                    
                    if len(data) > 30 and code in sectors:
                        # Change % is at index 31 (e.g. 1.25)
                        # Or calculate (price - prev_close) / prev_close
                        price = float(data[3])
                        prev_close = float(data[4])
                        change_pct = float(data[32])
                        
                        results.append({
                            'name': sectors[code],
                            'code': code,
                            'price': price,
                            'change_pct': change_pct
                        })
                        
            # Sort by change_pct descending (Strongest first)
            results.sort(key=lambda x: x['change_pct'], reverse=True)
            return results
            
        except Exception as e:
            print(f"Error fetching sector ETFs: {e}")
            return []

if __name__ == "__main__":
    loader = TencentDataLoader()
    
    print("--- Testing History Fetch (Moutai 600519) ---")
    df = loader.get_stock_history("600519", days=10)
    if df is not None:
        print(df.tail())
    else:
        print("Failed to fetch history.")

    print("\n--- Testing Realtime Fetch (Indices) ---")
    indices = loader.get_index_data()
    if indices:
        for code, data in indices.items():
            print(f"{data['name']} ({code}): {data['price']} ({data['change_pct']}%)")
    else:
        print("Failed to fetch indices.")

    print("\n--- Testing Index History Fetch (SH000001) ---")
    idx_df = loader.get_index_history("sh000001", days=100)
    if idx_df is not None:
        print(idx_df.tail())
    else:
        print("Failed to fetch index history.")
