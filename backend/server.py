from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Models
class WatchlistItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    name: str
    instrument_type: str  # stock, etf, bond, fund
    isin: Optional[str] = None
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WatchlistItemCreate(BaseModel):
    symbol: str
    name: str
    instrument_type: str
    isin: Optional[str] = None

class SearchResult(BaseModel):
    symbol: str
    name: str
    instrument_type: str
    exchange: Optional[str] = None
    currency: Optional[str] = None

class QuoteData(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    currency: str = "USD"

class HistoricalData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

# Sample financial data for demo (fallback when API is rate limited)
SAMPLE_INSTRUMENTS = {
    "AAPL": {"name": "Apple Inc.", "type": "stock", "sector": "Technology", "currency": "USD", "isin": "US0378331005", "exchange": "NASDAQ"},
    "MSFT": {"name": "Microsoft Corporation", "type": "stock", "sector": "Technology", "currency": "USD", "isin": "US5949181045", "exchange": "NASDAQ"},
    "GOOGL": {"name": "Alphabet Inc.", "type": "stock", "sector": "Technology", "currency": "USD", "isin": "US02079K3059", "exchange": "NASDAQ"},
    "AMZN": {"name": "Amazon.com Inc.", "type": "stock", "sector": "Consumer Cyclical", "currency": "USD", "isin": "US0231351067", "exchange": "NASDAQ"},
    "TSLA": {"name": "Tesla Inc.", "type": "stock", "sector": "Consumer Cyclical", "currency": "USD", "isin": "US88160R1014", "exchange": "NASDAQ"},
    "META": {"name": "Meta Platforms Inc.", "type": "stock", "sector": "Technology", "currency": "USD", "isin": "US30303M1027", "exchange": "NASDAQ"},
    "NVDA": {"name": "NVIDIA Corporation", "type": "stock", "sector": "Technology", "currency": "USD", "isin": "US67066G1040", "exchange": "NASDAQ"},
    "JPM": {"name": "JPMorgan Chase & Co.", "type": "stock", "sector": "Financial Services", "currency": "USD", "isin": "US46625H1005", "exchange": "NYSE"},
    "V": {"name": "Visa Inc.", "type": "stock", "sector": "Financial Services", "currency": "USD", "isin": "US92826C8394", "exchange": "NYSE"},
    "JNJ": {"name": "Johnson & Johnson", "type": "stock", "sector": "Healthcare", "currency": "USD", "isin": "US4781601046", "exchange": "NYSE"},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "type": "etf", "sector": "Broad Market", "currency": "USD", "isin": "US78462F1030", "exchange": "NYSE"},
    "QQQ": {"name": "Invesco QQQ Trust", "type": "etf", "sector": "Technology", "currency": "USD", "isin": "US46090E1038", "exchange": "NASDAQ"},
    "VTI": {"name": "Vanguard Total Stock Market ETF", "type": "etf", "sector": "Broad Market", "currency": "USD", "isin": "US9229087690", "exchange": "NYSE"},
    "IWM": {"name": "iShares Russell 2000 ETF", "type": "etf", "sector": "Small Cap", "currency": "USD", "isin": "US4642876555", "exchange": "NYSE"},
    "EFA": {"name": "iShares MSCI EAFE ETF", "type": "etf", "sector": "International", "currency": "USD", "isin": "US4642874659", "exchange": "NYSE"},
    "BND": {"name": "Vanguard Total Bond Market ETF", "type": "bond", "sector": "Bonds", "currency": "USD", "isin": "US9219378356", "exchange": "NYSE"},
    "AGG": {"name": "iShares Core U.S. Aggregate Bond ETF", "type": "bond", "sector": "Bonds", "currency": "USD", "isin": "US4642872265", "exchange": "NYSE"},
    "TLT": {"name": "iShares 20+ Year Treasury Bond ETF", "type": "bond", "sector": "Government Bonds", "currency": "USD", "isin": "US4642874329", "exchange": "NYSE"},
    "VFIAX": {"name": "Vanguard 500 Index Fund Admiral", "type": "fund", "sector": "Large Blend", "currency": "USD", "isin": "US9229083632", "exchange": "MUTUAL"},
    "FXAIX": {"name": "Fidelity 500 Index Fund", "type": "fund", "sector": "Large Blend", "currency": "USD", "isin": "US3160716052", "exchange": "MUTUAL"},
}

# Generate realistic price data
def generate_price_data(symbol: str) -> dict:
    base_prices = {
        "AAPL": 178.50, "MSFT": 378.90, "GOOGL": 141.80, "AMZN": 178.25, "TSLA": 248.50,
        "META": 505.75, "NVDA": 875.30, "JPM": 198.45, "V": 279.80, "JNJ": 156.20,
        "SPY": 512.40, "QQQ": 438.60, "VTI": 268.30, "IWM": 198.75, "EFA": 78.90,
        "BND": 72.45, "AGG": 98.60, "TLT": 92.30, "VFIAX": 485.20, "FXAIX": 178.50
    }
    
    base_price = base_prices.get(symbol, 100 + random.uniform(0, 200))
    change_pct = random.uniform(-3, 3)
    change = base_price * change_pct / 100
    current_price = base_price + change
    
    return {
        "price": round(current_price, 2),
        "change": round(change, 2),
        "change_percent": round(change_pct, 2),
        "open": round(base_price * random.uniform(0.99, 1.01), 2),
        "high": round(current_price * random.uniform(1.01, 1.03), 2),
        "low": round(current_price * random.uniform(0.97, 0.99), 2),
        "volume": random.randint(5000000, 50000000),
        "market_cap": random.randint(50, 3000) * 1e9,
        "pe_ratio": round(random.uniform(10, 40), 2),
        "dividend_yield": round(random.uniform(0, 0.03), 4),
        "week_52_high": round(current_price * random.uniform(1.1, 1.3), 2),
        "week_52_low": round(current_price * random.uniform(0.7, 0.9), 2),
    }

def generate_historical_data(symbol: str, days: int = 30) -> List[dict]:
    base_prices = {
        "AAPL": 178.50, "MSFT": 378.90, "GOOGL": 141.80, "AMZN": 178.25, "TSLA": 248.50,
        "META": 505.75, "NVDA": 875.30, "JPM": 198.45, "V": 279.80, "JNJ": 156.20,
        "SPY": 512.40, "QQQ": 438.60, "VTI": 268.30, "IWM": 198.75, "EFA": 78.90,
        "BND": 72.45, "AGG": 98.60, "TLT": 92.30, "VFIAX": 485.20, "FXAIX": 178.50
    }
    
    price = base_prices.get(symbol, 100 + random.uniform(0, 200))
    history = []
    
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_change = price * random.uniform(-0.02, 0.02)
        open_price = price
        close_price = price + daily_change
        high_price = max(open_price, close_price) * random.uniform(1.001, 1.02)
        low_price = min(open_price, close_price) * random.uniform(0.98, 0.999)
        
        history.append({
            "date": date,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": random.randint(5000000, 50000000)
        })
        price = close_price
    
    return history

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Financial Analysis API"}

@api_router.get("/search", response_model=List[SearchResult])
async def search_instruments(q: str = Query(..., min_length=1)):
    """Search for financial instruments by symbol, name or ISIN"""
    query = q.upper().strip()
    results = []
    
    for symbol, info in SAMPLE_INSTRUMENTS.items():
        # Match by symbol, name, or ISIN
        if (query in symbol or 
            query.lower() in info["name"].lower() or 
            (info.get("isin") and query in info["isin"])):
            results.append(SearchResult(
                symbol=symbol,
                name=info["name"],
                instrument_type=info["type"],
                exchange=info.get("exchange"),
                currency=info.get("currency", "USD")
            ))
    
    # If exact match not found, try to add it
    if not results and len(query) >= 1:
        # Add as unknown stock
        results.append(SearchResult(
            symbol=query,
            name=f"{query} (Symbol)",
            instrument_type="stock",
            exchange="UNKNOWN",
            currency="USD"
        ))
    
    return results[:10]  # Limit results

@api_router.get("/quote/{symbol}", response_model=QuoteData)
async def get_quote(symbol: str):
    """Get current quote for a symbol"""
    symbol = symbol.upper()
    
    if symbol not in SAMPLE_INSTRUMENTS:
        # Generate data for unknown symbol
        info = {"name": f"{symbol} Stock", "type": "stock", "currency": "USD"}
    else:
        info = SAMPLE_INSTRUMENTS[symbol]
    
    price_data = generate_price_data(symbol)
    
    return QuoteData(
        symbol=symbol,
        name=info["name"],
        price=price_data["price"],
        change=price_data["change"],
        change_percent=price_data["change_percent"],
        open=price_data["open"],
        high=price_data["high"],
        low=price_data["low"],
        volume=price_data["volume"],
        market_cap=price_data["market_cap"],
        pe_ratio=price_data["pe_ratio"],
        dividend_yield=price_data["dividend_yield"],
        week_52_high=price_data["week_52_high"],
        week_52_low=price_data["week_52_low"],
        currency=info.get("currency", "USD")
    )

@api_router.get("/history/{symbol}", response_model=List[HistoricalData])
async def get_history(symbol: str, period: str = "1mo"):
    """Get historical data for a symbol"""
    symbol = symbol.upper()
    
    # Convert period to days
    period_days = {
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "5y": 1825
    }
    
    days = period_days.get(period, 30)
    history = generate_historical_data(symbol, days)
    
    return [HistoricalData(**h) for h in history]

@api_router.get("/details/{symbol}")
async def get_details(symbol: str):
    """Get detailed information for a symbol"""
    symbol = symbol.upper()
    
    if symbol not in SAMPLE_INSTRUMENTS:
        info = {"name": f"{symbol} Stock", "type": "stock", "currency": "USD", "sector": "Unknown"}
    else:
        info = SAMPLE_INSTRUMENTS[symbol]
    
    price_data = generate_price_data(symbol)
    
    return {
        "symbol": symbol,
        "name": info["name"],
        "description": f"{info['name']} is a leading company in the {info.get('sector', 'financial')} sector. This instrument offers investors exposure to {info.get('type', 'equity')} markets.",
        "sector": info.get("sector"),
        "industry": info.get("sector"),
        "country": "United States",
        "website": f"https://finance.yahoo.com/quote/{symbol}",
        "employees": random.randint(10000, 200000) if info.get("type") == "stock" else None,
        "instrument_type": info.get("type", "stock"),
        "exchange": info.get("exchange", "NYSE"),
        "currency": info.get("currency", "USD"),
        "isin": info.get("isin"),
        # Valuation metrics
        "market_cap": price_data["market_cap"],
        "enterprise_value": price_data["market_cap"] * random.uniform(0.9, 1.2),
        "pe_ratio": price_data["pe_ratio"],
        "forward_pe": price_data["pe_ratio"] * random.uniform(0.8, 1.1),
        "peg_ratio": round(random.uniform(0.5, 3), 2),
        "price_to_book": round(random.uniform(1, 15), 2),
        "price_to_sales": round(random.uniform(0.5, 10), 2),
        # Financial metrics
        "revenue": price_data["market_cap"] * random.uniform(0.1, 0.5),
        "gross_profit": price_data["market_cap"] * random.uniform(0.05, 0.2),
        "ebitda": price_data["market_cap"] * random.uniform(0.03, 0.15),
        "net_income": price_data["market_cap"] * random.uniform(0.01, 0.1),
        "profit_margin": round(random.uniform(0.05, 0.3), 4),
        "operating_margin": round(random.uniform(0.1, 0.4), 4),
        "roe": round(random.uniform(0.1, 0.4), 4),
        "roa": round(random.uniform(0.05, 0.2), 4),
        # Dividend info
        "dividend_rate": round(random.uniform(0, 5), 2),
        "dividend_yield": price_data["dividend_yield"],
        "payout_ratio": round(random.uniform(0.1, 0.6), 4),
        "ex_dividend_date": None,
        # Trading info
        "beta": round(random.uniform(0.5, 2), 2),
        "avg_volume": price_data["volume"],
        "avg_volume_10d": price_data["volume"] * random.uniform(0.8, 1.2),
        "shares_outstanding": int(price_data["market_cap"] / price_data["price"]),
        "float_shares": int(price_data["market_cap"] / price_data["price"] * 0.9),
    }

# Watchlist endpoints
@api_router.get("/watchlist", response_model=List[WatchlistItem])
async def get_watchlist():
    """Get all watchlist items"""
    items = await db.watchlist.find({}, {"_id": 0}).to_list(1000)
    for item in items:
        if isinstance(item.get('added_at'), str):
            item['added_at'] = datetime.fromisoformat(item['added_at'])
    return items

@api_router.post("/watchlist", response_model=WatchlistItem)
async def add_to_watchlist(item: WatchlistItemCreate):
    """Add item to watchlist"""
    # Check if already exists
    existing = await db.watchlist.find_one({"symbol": item.symbol.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")
    
    watchlist_item = WatchlistItem(
        symbol=item.symbol.upper(),
        name=item.name,
        instrument_type=item.instrument_type,
        isin=item.isin
    )
    
    doc = watchlist_item.model_dump()
    doc['added_at'] = doc['added_at'].isoformat()
    
    await db.watchlist.insert_one(doc)
    return watchlist_item

@api_router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove item from watchlist"""
    result = await db.watchlist.delete_one({"symbol": symbol.upper()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found in watchlist")
    return {"message": "Removed from watchlist"}

# Compare endpoint - Base 100 rebased chart data
@api_router.get("/compare")
async def compare_instruments(
    symbols: str = Query(..., description="Comma-separated symbols"),
    period: str = Query("1mo", description="Time period: 1mo, 3mo, 6mo, 1y, 2y, 5y")
):
    """Compare multiple instruments with base 100 normalization"""
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    
    if len(symbol_list) < 1:
        raise HTTPException(status_code=400, detail="At least 1 symbol required")
    if len(symbol_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 symbols allowed")
    
    # Convert period to days
    period_days = {
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825
    }
    days = period_days.get(period, 30)
    
    # Generate historical data for each symbol
    all_histories = {}
    symbol_info = {}
    
    for symbol in symbol_list:
        history = generate_historical_data(symbol, days)
        all_histories[symbol] = history
        
        if symbol in SAMPLE_INSTRUMENTS:
            symbol_info[symbol] = SAMPLE_INSTRUMENTS[symbol]
        else:
            symbol_info[symbol] = {"name": f"{symbol} Stock", "type": "stock"}
    
    # Normalize to base 100
    # Find the first price for each symbol and calculate rebased values
    base_prices = {}
    for symbol, history in all_histories.items():
        if history:
            base_prices[symbol] = history[0]["close"]
    
    # Build the chart data with all symbols aligned by date
    chart_data = []
    
    # Use the first symbol's dates as reference
    reference_symbol = symbol_list[0]
    reference_history = all_histories[reference_symbol]
    
    for i, day_data in enumerate(reference_history):
        point = {"date": day_data["date"]}
        
        for symbol in symbol_list:
            if i < len(all_histories[symbol]):
                close_price = all_histories[symbol][i]["close"]
                base_price = base_prices[symbol]
                # Rebase to 100
                rebased_value = (close_price / base_price) * 100
                point[symbol] = round(rebased_value, 2)
        
        chart_data.append(point)
    
    # Calculate performance summary
    performance = []
    for symbol in symbol_list:
        history = all_histories[symbol]
        if history and len(history) > 0:
            start_price = history[0]["close"]
            end_price = history[-1]["close"]
            total_return = ((end_price - start_price) / start_price) * 100
            
            # Calculate volatility (standard deviation of daily returns)
            daily_returns = []
            for i in range(1, len(history)):
                prev_close = history[i-1]["close"]
                curr_close = history[i]["close"]
                daily_return = (curr_close - prev_close) / prev_close
                daily_returns.append(daily_return)
            
            if daily_returns:
                import statistics
                volatility = statistics.stdev(daily_returns) * 100 * (252 ** 0.5)  # Annualized
            else:
                volatility = 0
            
            performance.append({
                "symbol": symbol,
                "name": symbol_info[symbol]["name"],
                "type": symbol_info[symbol].get("type", "stock"),
                "start_value": 100,
                "end_value": round((end_price / start_price) * 100, 2),
                "total_return": round(total_return, 2),
                "volatility": round(volatility, 2)
            })
    
    return {
        "chart_data": chart_data,
        "symbols": symbol_list,
        "period": period,
        "performance": performance
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
