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
    try:
        results = []
        
        # Try direct symbol lookup
        ticker = yf.Ticker(q.upper())
        info = ticker.info
        
        if info and info.get('symbol'):
            results.append(SearchResult(
                symbol=info.get('symbol', q.upper()),
                name=info.get('longName') or info.get('shortName', q.upper()),
                instrument_type=get_instrument_type(info),
                exchange=info.get('exchange'),
                currency=info.get('currency')
            ))
        
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        # Return empty list on error
        return []

@api_router.get("/quote/{symbol}", response_model=QuoteData)
async def get_quote(symbol: str):
    """Get current quote for a symbol"""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        if not info or not info.get('symbol'):
            raise HTTPException(status_code=404, detail="Symbol not found")
        
        # Get current price data
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
        previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose', current_price)
        
        change = current_price - previous_close if previous_close else 0
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        return QuoteData(
            symbol=info.get('symbol', symbol.upper()),
            name=info.get('longName') or info.get('shortName', symbol.upper()),
            price=round(current_price, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            open=info.get('open') or info.get('regularMarketOpen'),
            high=info.get('dayHigh') or info.get('regularMarketDayHigh'),
            low=info.get('dayLow') or info.get('regularMarketDayLow'),
            volume=info.get('volume') or info.get('regularMarketVolume'),
            market_cap=info.get('marketCap'),
            pe_ratio=info.get('trailingPE'),
            dividend_yield=info.get('dividendYield'),
            week_52_high=info.get('fiftyTwoWeekHigh'),
            week_52_low=info.get('fiftyTwoWeekLow'),
            currency=info.get('currency', 'USD')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quote error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/history/{symbol}", response_model=List[HistoricalData])
async def get_history(symbol: str, period: str = "1mo"):
    """Get historical data for a symbol"""
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="No historical data found")
        
        result = []
        for date, row in hist.iterrows():
            result.append(HistoricalData(
                date=date.strftime('%Y-%m-%d'),
                open=round(row['Open'], 2),
                high=round(row['High'], 2),
                low=round(row['Low'], 2),
                close=round(row['Close'], 2),
                volume=int(row['Volume'])
            ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/details/{symbol}")
async def get_details(symbol: str):
    """Get detailed information for a symbol"""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        if not info or not info.get('symbol'):
            raise HTTPException(status_code=404, detail="Symbol not found")
        
        return {
            "symbol": info.get('symbol'),
            "name": info.get('longName') or info.get('shortName'),
            "description": info.get('longBusinessSummary'),
            "sector": info.get('sector'),
            "industry": info.get('industry'),
            "country": info.get('country'),
            "website": info.get('website'),
            "employees": info.get('fullTimeEmployees'),
            "instrument_type": get_instrument_type(info),
            "exchange": info.get('exchange'),
            "currency": info.get('currency'),
            "isin": info.get('isin'),
            # Valuation metrics
            "market_cap": info.get('marketCap'),
            "enterprise_value": info.get('enterpriseValue'),
            "pe_ratio": info.get('trailingPE'),
            "forward_pe": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "price_to_book": info.get('priceToBook'),
            "price_to_sales": info.get('priceToSalesTrailing12Months'),
            # Financial metrics
            "revenue": info.get('totalRevenue'),
            "gross_profit": info.get('grossProfits'),
            "ebitda": info.get('ebitda'),
            "net_income": info.get('netIncomeToCommon'),
            "profit_margin": info.get('profitMargins'),
            "operating_margin": info.get('operatingMargins'),
            "roe": info.get('returnOnEquity'),
            "roa": info.get('returnOnAssets'),
            # Dividend info
            "dividend_rate": info.get('dividendRate'),
            "dividend_yield": info.get('dividendYield'),
            "payout_ratio": info.get('payoutRatio'),
            "ex_dividend_date": info.get('exDividendDate'),
            # Trading info
            "beta": info.get('beta'),
            "avg_volume": info.get('averageVolume'),
            "avg_volume_10d": info.get('averageVolume10days'),
            "shares_outstanding": info.get('sharesOutstanding'),
            "float_shares": info.get('floatShares'),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Details error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Compare endpoint
@api_router.get("/compare")
async def compare_instruments(symbols: str = Query(..., description="Comma-separated symbols")):
    """Compare multiple instruments"""
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    
    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 symbols required")
    if len(symbol_list) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 symbols allowed")
    
    results = []
    for symbol in symbol_list:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if info and info.get('symbol'):
                current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
                previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose', current_price)
                change = current_price - previous_close if previous_close else 0
                change_percent = (change / previous_close * 100) if previous_close else 0
                
                results.append({
                    "symbol": info.get('symbol'),
                    "name": info.get('longName') or info.get('shortName'),
                    "price": round(current_price, 2),
                    "change_percent": round(change_percent, 2),
                    "market_cap": info.get('marketCap'),
                    "pe_ratio": info.get('trailingPE'),
                    "dividend_yield": info.get('dividendYield'),
                    "beta": info.get('beta'),
                    "week_52_high": info.get('fiftyTwoWeekHigh'),
                    "week_52_low": info.get('fiftyTwoWeekLow'),
                    "currency": info.get('currency', 'USD')
                })
        except Exception as e:
            logger.error(f"Compare error for {symbol}: {e}")
            continue
    
    return results

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
