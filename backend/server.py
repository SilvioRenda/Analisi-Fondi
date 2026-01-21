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

# Helper function to get instrument type
def get_instrument_type(info: dict) -> str:
    quote_type = info.get('quoteType', '').lower()
    if quote_type == 'etf':
        return 'etf'
    elif quote_type == 'mutualfund':
        return 'fund'
    elif quote_type == 'equity':
        return 'stock'
    elif quote_type == 'bond':
        return 'bond'
    return 'stock'

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
