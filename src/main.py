import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from data_loader import TencentDataLoader

class MarketAnalyzer:
    def __init__(self):
        self.loader = TencentDataLoader()

    def calculate_rsi(self, series, period=6):
        """
        Calculate RSI (Relative Strength Index)
        Using Wilders Smoothing (Standard) or Simple Moving Average?
        Standard RSI uses Wilders Smoothing. But for simplicity and speed, SMA is often used in simple scripts.
        Let's use a simple EMA-like approach or just simple gain/loss avg.
        """
        delta = series.diff()
        
        # Make a copy to avoid SettingWithCopy warning
        up = delta.copy()
        down = delta.copy()
        
        up[up < 0] = 0
        down[down > 0] = 0
        
        # Calculate the EMA
        roll_up = up.ewm(span=period, adjust=False).mean()
        roll_down = down.abs().ewm(span=period, adjust=False).mean()
        
        rs = roll_up / roll_down
        return 100.0 - (100.0 / (1.0 + rs))

    def analyze_index_trend(self, index_code, name):
        """
        Analyze index trend using MA20 and MA60.
        Returns: Trend status (BULL/BEAR/SIDEWAYS) and details
        """
        df = self.loader.get_index_history(index_code, days=365)
        if df is None or len(df) < 60:
            return {"status": "UNKNOWN", "ma20": 0, "ma60": 0, "current": 0}
            
        # Calculate MAs
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()
        df['MA5_VOL'] = df['volume'].rolling(window=5).mean()
        
        latest = df.iloc[-1]
        
        # Determine Trend
        trend = "SIDEWAYS"
        if latest['close'] > latest['MA20'] and latest['MA20'] > latest['MA60']:
            trend = "BULL (Uptrend)"
        elif latest['close'] < latest['MA20'] and latest['MA20'] < latest['MA60']:
            trend = "BEAR (Downtrend)"
            
        # Volume Check
        volume_signal = "NORMAL"
        if latest['volume'] > latest['MA5_VOL']:
            volume_signal = "HIGH_VOLUME"
        elif latest['volume'] < latest['MA5_VOL'] * 0.6:
            volume_signal = "LOW_VOLUME"
            
        return {
            "name": name,
            "date": latest['date'].strftime("%Y-%m-%d"),
            "price": latest['close'],
            "ma20": latest['MA20'],
            "ma60": latest['MA60'],
            "trend": trend,
            "volume_signal": volume_signal
        }

    def get_market_traffic_light(self):
        """
        Layer 1: Macro Market Timing (Traffic Light System)
        """
        indices = {
            'sh000001': 'Shanghai Composite',
            'sz399001': 'Shenzhen Component',
            'sz399006': 'ChiNext Index'
        }
        
        results = []
        bull_count = 0
        
        print("\n=== Layer 1: Macro Trend Analysis ===")
        for code, name in indices.items():
            res = self.analyze_index_trend(code, name)
            results.append(res)
            
            print(f"[{name}] Price: {res['price']:.2f} | MA20: {res['ma20']:.2f} | Trend: {res['trend']}")
            
            if "BULL" in res['trend']:
                bull_count += 1
        
        # Traffic Light Logic
        traffic_light = "RED"
        action = "STOP (Empty Portfolio)"
        
        if bull_count >= 2:
            traffic_light = "GREEN"
            action = "GO (Aggressive)"
        elif bull_count == 1:
            traffic_light = "YELLOW"
            action = "CAUTION (Defensive)"
            
        print(f"\n>>> MARKET SIGNAL: {traffic_light} <<<")
        print(f">>> SUGGESTED ACTION: {action} <<<")
        
        return traffic_light

    def get_market_sentiment(self):
        """
        Layer 2: Market Sentiment (The "Mood")
        Factors:
        1. Northbound Funds (Smart Money)
        2. Major Index Performance (Average Daily Change %)
        3. Volume Analysis (Today vs MA5 Volume)
        """
        print("\n=== Layer 2: Market Sentiment ===")
        sentiment_score = 50  # Start neutral

        # Factor 1: Northbound Funds
        breadth = self.loader.get_market_breadth()
        north_flow = breadth.get('north_net_inflow', 0)
        print(f"[Factor 1] Northbound Funds: {north_flow:.2f} 亿")
        
        if north_flow > 50:
            sentiment_score += 20
        elif north_flow > 10:
            sentiment_score += 10
        elif north_flow < -50:
            sentiment_score -= 20
        elif north_flow < -10:
            sentiment_score -= 10

        # Factor 2 & 3: Index Performance & Volume
        indices = ['sh000001', 'sz399001', 'sz399006']
        total_change_pct = 0
        volume_status = 0 # -1: Shrink, 0: Normal, 1: Expand
        
        valid_indices = 0
        for code in indices:
            df = self.loader.get_index_history(code, days=10)
            if df is not None and len(df) >= 6:
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Daily Change
                change_pct = (latest['close'] - prev['close']) / prev['close'] * 100
                total_change_pct += change_pct
                
                # Volume Analysis
                ma5_vol = df['volume'].rolling(window=5).mean().iloc[-1]
                if latest['volume'] > ma5_vol * 1.2:
                    volume_status += 1
                elif latest['volume'] < ma5_vol * 0.8:
                    volume_status -= 1
                    
                valid_indices += 1
        
        avg_change = 0
        if valid_indices > 0:
            avg_change = total_change_pct / valid_indices
            
        print(f"[Factor 2] Avg Index Change: {avg_change:.2f}%")
        
        if avg_change > 1.0:
            sentiment_score += 20
        elif avg_change > 0.3:
            sentiment_score += 10
        elif avg_change < -1.0:
            sentiment_score -= 20
        elif avg_change < -0.3:
            sentiment_score -= 10
            
        # Volume impact
        print(f"[Factor 3] Volume Trend: ", end="")
        if volume_status > 0:
            print("Expanding (Active)")
            sentiment_score += 10
        elif volume_status < 0:
            print("Shrinking (Inactive)")
            sentiment_score -= 10
        else:
            print("Normal")
            
        # Factor 4: Market Breadth (Sampled)
        up_count = breadth.get('up', 0)
        down_count = breadth.get('down', 0)
        total_sample = up_count + down_count + breadth.get('flat', 0)
        
        print(f"[Factor 4] Key Stock Breadth: Up {up_count} vs Down {down_count} (Sample: {total_sample})")
        
        if total_sample > 0:
            up_ratio = up_count / total_sample
            if up_ratio >= 0.7: # Strong Bull
                sentiment_score += 15
            elif up_ratio >= 0.55: # Mild Bull
                sentiment_score += 5
            elif up_ratio <= 0.3: # Strong Bear
                sentiment_score -= 15
            elif up_ratio <= 0.45: # Mild Bear
                sentiment_score -= 5

        # Factor 5: Sector Performance (Leading Sectors)
        print(f"\n[Factor 5] Leading Sectors (Hotspots)")
        sector_etfs = self.loader.get_sector_etf_performance()
        
        # Display top 3 sectors
        top_sectors = sector_etfs[:3]
        avg_top3_change = 0
        
        if top_sectors:
            print("Top Leading Sectors:")
            for s in top_sectors:
                print(f"  - {s['name']}: {s['change_pct']:.2f}%")
                avg_top3_change += s['change_pct']
            
            avg_top3_change /= len(top_sectors)
            
            # Impact on Sentiment
            if avg_top3_change > 2.0:
                sentiment_score += 15
                print(">> Sector Heat: High (Broad Rally)")
            elif avg_top3_change > 0.5:
                sentiment_score += 5
                print(">> Sector Heat: Moderate")
            elif avg_top3_change < -1.0:
                sentiment_score -= 10
                print(">> Sector Heat: Cold (Broad Decline)")
        else:
             print("No sector data available.")

        # Factor 6: Technical Indicators (RSI)
        # Use Shanghai Composite as the benchmark
        sh_df = self.loader.get_index_history('sh000001', days=60)
        if sh_df is not None and len(sh_df) > 14:
            rsi_6 = self.calculate_rsi(sh_df['close'], period=6).iloc[-1]
            print(f"\n[Factor 6] Technicals (Shanghai Index)")
            print(f"RSI (6-day): {rsi_6:.2f}")
            
            if rsi_6 > 80:
                sentiment_score += 10
                print(">> RSI Signal: Overbought (Extreme Greed)")
            elif rsi_6 > 50:
                sentiment_score += 5
                print(">> RSI Signal: Strong")
            elif rsi_6 < 20:
                sentiment_score -= 10
                print(">> RSI Signal: Oversold (Extreme Fear)")
            elif rsi_6 < 40:
                sentiment_score -= 5
                print(">> RSI Signal: Weak")
            else:
                print(">> RSI Signal: Neutral")

        # Determine Mood
        mood = "中性 (Neutral)"
        if sentiment_score >= 80:
            mood = "极度贪婪 / 过热 (Extremely Greedy)"
        elif sentiment_score >= 65:
            mood = "贪婪 / 乐观 (Greedy)"
        elif sentiment_score <= 20:
            mood = "极度恐慌 / 冰点 (Extremely Fearful)"
        elif sentiment_score <= 35:
            mood = "恐慌 / 悲观 (Fearful)"
            
        print(f"Sentiment Score: {sentiment_score}/100")
        print(f"Market Mood: {mood}")
        
        return sentiment_score, mood

    def analyze_sector(self, sector_name, market_status="GREEN", sentiment_score=50):
        """
        Analyze a specific sector using its ETF as proxy.
        """
        print(f"\n=== Sector Analysis: {sector_name} ===")
        # 1. Map sector name to ETF code
        sector_map = self.loader.get_sector_map()
        
        target_code = None
        target_name = ""
        # Try direct match
        for code, name in sector_map.items():
            if sector_name in name or sector_name in code:
                target_code = code
                target_name = name
                print(f"Matched Sector ETF: {name} ({code})")
                break
        
        if not target_code:
            print(f"Sector '{sector_name}' not found in monitored list.")
            print("Available sectors:", ", ".join([v.split(' ')[0] for v in sector_map.values()]))
            return

        # 2. Analyze the ETF
        # Treat it like a stock analysis
        # Strip prefix for compatibility if needed, but loader handles it.
        # However, analyze_stock_strategy might expect just the number for display? 
        # It passes to loader, which handles it.
        # But for display "Layer 3: ... ({symbol})", it's fine.
        
        self.analyze_stock_strategy(target_code, 100000, market_status=market_status, sentiment_score=sentiment_score)

    def analyze_stock_strategy(self, symbol, capital, risk_per_trade=0.01, market_status="GREEN", sentiment_score=50):
        """
        Layer 3: Individual Stock Strategy & Risk Control
        symbol: Stock code (e.g., '600519')
        capital: Total account capital
        risk_per_trade: Risk % per trade (default 1%)
        market_status: Macro trend status (RED/YELLOW/GREEN)
        sentiment_score: Market sentiment score (0-100)
        """
        print(f"\n=== Layer 3: Strategy & Risk Control ({symbol}) ===")
        
        # Adjust Risk based on Market Context (Layer 1 & 2 Integration)
        adjusted_risk = risk_per_trade
        risk_note = "Standard Risk"
        
        if market_status == "RED":
            adjusted_risk = 0.0
            risk_note = "Market RED (No New Positions)"
        elif market_status == "YELLOW":
            adjusted_risk = risk_per_trade * 0.5
            risk_note = "Market YELLOW (Half Risk)"
        
        if sentiment_score < 35: # Fearful
            adjusted_risk *= 0.8
            risk_note += " + Sentiment Fearful (Reduced)"
        elif sentiment_score > 80: # Overheated
            adjusted_risk *= 0.8
            risk_note += " + Sentiment Overheated (Reduced)"
            
        print(f"[System Integration] Market: {market_status} | Sentiment: {sentiment_score}")
        print(f"[Risk Adjustment] {risk_note} -> Effective Risk: {adjusted_risk*100:.2f}%")
        
        # Get Realtime Quote
        quote = self.loader.get_realtime_quote(symbol)
        if quote:
            print(f"Name: {quote['name']}")
            print(f"Current Price: {quote['price']:.2f}")
            change_pct = (quote['price'] - quote['prev_close']) / quote['prev_close'] * 100
            print(f"Change: {change_pct:.2f}%")
            if quote['price'] == quote['open'] and quote['volume'] > 0:
                 print("Info: Using Open Price (possibly Call Auction data)")
        
        df = self.loader.get_stock_history(symbol, days=365)
        if df is None or len(df) < 60:
            print("Error: Insufficient data for analysis.")
            return

        # Update latest price with realtime quote if available and market is open
        if quote and quote['price'] > 0:
            # Check if the last row is today's date
            today = datetime.now().strftime('%Y-%m-%d')
            if not df.empty:
                last_date = df.iloc[-1]['date'].strftime('%Y-%m-%d')
                
                if last_date == today:
                    # Update existing row
                    # Use integer location for safer assignment
                    idx = df.index[-1]
                    df.at[idx, 'close'] = quote['price']
                    df.at[idx, 'high'] = max(df.at[idx, 'high'], quote['high'])
                    df.at[idx, 'low'] = min(df.at[idx, 'low'], quote['low'])
                    df.at[idx, 'volume'] = quote['volume']
                    print(f"Info: Updated today's candle with Real-time Price: {quote['price']}")
                else:
                    # Append new row for today
                    # Create a DataFrame for the new row
                    new_row = pd.DataFrame([{
                        'date': pd.Timestamp(today),
                        'open': quote['open'],
                        'close': quote['price'],
                        'high': quote['high'],
                        'low': quote['low'],
                        'volume': quote['volume']
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    print(f"Info: Appended new candle for today with Real-time Price: {quote['price']}")
        
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()
        
        # ATR Calculation
        df['TR'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=20).mean()
        
        latest = df.iloc[-1]
        
        # 3. Trend Analysis
        trend = "震荡/无趋势 (SIDEWAYS)"
        if latest['close'] > latest['MA20'] and latest['MA20'] > latest['MA60']:
            trend = "上涨趋势/买入区 (UPTREND)"
        elif latest['close'] < latest['MA20'] and latest['MA20'] < latest['MA60']:
            trend = "下跌趋势/卖出区 (DOWNTREND)"
            
        # 4. Risk Control (Position Sizing)
        atr = latest['ATR']
        stop_loss_width = 2.0 * atr  # Stop loss at 2 ATRs
        stop_loss_price = latest['close'] - stop_loss_width
        
        # Risk Amount = Capital * Risk%
        risk_amount = capital * adjusted_risk
        
        # Position Size = Risk Amount / Risk Per Share (Stop Loss Width)
        if stop_loss_width > 0:
            position_size = int(risk_amount / stop_loss_width)
            # Round down to nearest 100 (A-share board lot)
            position_size = (position_size // 100) * 100
        else:
            position_size = 0
            
        total_cost = position_size * latest['close']
        
        # Output Results
        print(f"Date: {latest['date'].strftime('%Y-%m-%d')}")
        print(f"Price: {latest['close']:.2f}")
        print(f"Trend: {trend}")
        print(f"Volatility (ATR): {atr:.2f}")
        print("-" * 30)
        print(f"Stop Loss Price: {stop_loss_price:.2f} (Width: {stop_loss_width:.2f})")
        print(f"Max Risk Amount: {risk_amount:.2f} ({adjusted_risk*100:.2f}% of Capital)")
        print(f"Suggested Position: {position_size} shares")
        print(f"Estimated Cost: {total_cost:.2f}")
        
        if trend == "上涨趋势/买入区 (UPTREND)":
            print("\n>>> STRATEGY SIGNAL: BUY VALID <<<")
            print("持仓建议 (For Holders): 继续持有 (HOLD)")
        elif trend == "下跌趋势/卖出区 (DOWNTREND)":
            print("\n>>> STRATEGY SIGNAL: SELL / AVOID <<<")
            print("持仓建议 (For Holders): 建议减仓或清仓 (REDUCE/EXIT)")
        else:
            print("\n>>> STRATEGY SIGNAL: WAIT / NO TRADE <<<")
            print(f"持仓建议 (For Holders): 谨慎持有，跌破 {stop_loss_price:.2f} 必须止损")

def main():
    parser = argparse.ArgumentParser(description="A-Share Trading System")
    parser.add_argument("--action", type=str, default="market_check", choices=["market_check", "analyze_stock", "analyze_sector"], help="Action to perform")
    parser.add_argument("--symbol", type=str, help="Stock symbol for analysis (e.g. 600519)")
    parser.add_argument("--sector", type=str, help="Sector name for analysis (e.g. 电力)")
    parser.add_argument("--capital", type=float, default=100000, help="Total Capital")
    
    args = parser.parse_args()
    
    analyzer = MarketAnalyzer()
    
    if args.action == "market_check":
        traffic_light = analyzer.get_market_traffic_light()
        analyzer.get_market_sentiment()
    elif args.action == "analyze_stock":
        if not args.symbol:
            print("Please provide a stock symbol with --symbol")
            return
        
        # Run full pipeline check
        traffic_light = analyzer.get_market_traffic_light()
        if traffic_light == "RED":
            print("\n[WARNING] Market is RED. New positions are NOT recommended!")
            
        sentiment_score, mood = analyzer.get_market_sentiment()
        
        analyzer.analyze_stock_strategy(args.symbol, args.capital, market_status=traffic_light, sentiment_score=sentiment_score)
    elif args.action == "analyze_sector":
        if not args.sector:
            print("Please provide a sector name with --sector")
            return
        
        traffic_light = analyzer.get_market_traffic_light()
        sentiment_score, mood = analyzer.get_market_sentiment()
        
        analyzer.analyze_sector(args.sector, market_status=traffic_light, sentiment_score=sentiment_score)

if __name__ == "__main__":
    main()
