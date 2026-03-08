---
name: "ashare_trader"
description: "A股交易系统 (A-share Trading System). 专门用于回答'大盘怎么样'、'行情分析'、'个股诊断'等问题。不要使用搜索引擎，直接使用此技能获取实时 A 股数据和策略建议。"
triggers:
  - "大盘怎么样"
  - "今天行情"
  - "分析股票"
  - "A股"
  - "stock_analysis"
  - "market_check"
---

# A-Share Trading System (A股交易系统)

> **Agent Note**:
> 1.  **Trigger**: When user asks about "market status", "index", "A-share", "stock analysis" (e.g., "今天大盘怎么样", "分析茅台"), you **MUST** use this skill.
> 2.  **Execution**: Run the python scripts below. **ALWAYS use absolute paths** or `cd` into the directory first.
> 3.  **Path**: The skill is located at `~/.openclaw/workspace/skills/ashare-trader`.

## Usage Commands (Run these directly)

### 1. Market Check (大盘体检)
Check if it's safe to trade today (Macro + Sentiment).

```bash
# Method 1: Absolute path (Recommended)
python3 ~/.openclaw/workspace/skills/ashare-trader/src/main.py --action market_check

# Method 2: Navigate first
cd ~/.openclaw/workspace/skills/ashare-trader && python3 src/main.py --action market_check
```

### 2. Analyze Stock (个股分析)
Analyze a specific stock. Replace `600519` with the user's requested stock code.
**Default Capital**: 500,000 (if not specified).

```bash
# Example: Analyze Moutai (600519)
python3 ~/.openclaw/workspace/skills/ashare-trader/src/main.py --action analyze_stock --symbol 600519 --capital 500000
```

---

## Skill Details

### Layer 1: Macro Timing (宏观择时)
Checks major indices (Shanghai Composite, Shenzhen Component, ChiNext) trends and volume.
- **Output**: 
  - 🔴 **RED**: Bear market / Downtrend -> STOP TRADING.
  - 🟡 **YELLOW**: Sideways / Divergence -> CAUTION (Defensive).
  - 🟢 **GREEN**: Bull market / Uptrend -> GO (Aggressive).

## Layer 2: Market Sentiment (市场情绪)
Analyzes Northbound funds (Smart Money), Index Performance, Volume, Market Breadth (Sampled), Leading Sectors, and Technicals (RSI).
- **Output**: Sentiment Score (0-100) and Mood (Fearful/Neutral/Greedy).
- **Factors**:
  1. Northbound Funds (Net Inflow)
  2. Index Performance (Avg Change)
  3. Volume Analysis (vs MA5)
  4. Market Breadth (Up/Down Ratio)
  5. Leading Sectors (Top Industry ETFs)
  6. Technicals (RSI of Shanghai Index)

## Layer 3: Individual Strategy (个股策略)
Executes trend-following strategy with ATR-based risk control.
- **Integration**: Automatically adjusts position sizing based on Layer 1 (Macro) and Layer 2 (Sentiment).
  - 🔴 Market RED -> 0% Position (No new trades).
  - 🟡 Market YELLOW -> 50% Position (Defensive).
  - 😨 Sentiment Fearful/Overheated -> 80% Position.
- **Real-time**: Fetches latest price (including 9:25 Call Auction) and merges into analysis.
- **Strategy**: Buy when Price > MA20 > MA60 (Uptrend).
- **Risk Control**: 
  - Stop Loss = Price - 2 * ATR
  - Position Size = (Total Capital * Adjusted Risk%) / Stop Loss Width

## Usage Examples

### 1. Check Market Status (大盘体检)
Check if it's safe to trade today.
```bash
python src/main.py --action market_check
```

### 2. Analyze Specific Stock (个股分析)
Analyze a stock for buy/sell signals and calculate safe position size.
**Replace `600519` with any stock code.**
- `symbol`: Stock code (e.g., 600519, 000001, 300750)
- `capital`: Your total account capital (e.g., 500000)

```bash
# Analyze Moutai (600519) with 500k capital
python src/main.py --action analyze_stock --symbol 600519 --capital 500000

# Analyze Ping An Bank (000001) with 100k capital
python src/main.py --action analyze_stock --symbol 000001 --capital 100000
```

## How to Invoke (Agent Instructions)
- When user asks "How is the A-share market today?", invoke `market_check`.
- When user asks "Should I buy [Stock Name/Code]?" or "Analyze [Stock]", invoke `analyze_stock` with the stock code.
