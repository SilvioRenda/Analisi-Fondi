import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Search, TrendingUp, TrendingDown, Star, StarOff, BarChart3, RefreshCw, X, Plus, ArrowUpDown, LayoutGrid, List, Flame, Target, Building2, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Area, AreaChart } from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Format utilities
const formatNumber = (num, decimals = 2) => {
  if (num === null || num === undefined) return "N/A";
  return new Intl.NumberFormat('it-IT', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(num);
};

const formatCurrency = (num, currency = "USD") => {
  if (num === null || num === undefined) return "N/A";
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency }).format(num);
};

const formatLargeNumber = (num) => {
  if (num === null || num === undefined) return "N/A";
  if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
  return formatNumber(num);
};

const formatPercent = (num) => {
  if (num === null || num === undefined) return "N/A";
  return `${num >= 0 ? '+' : ''}${formatNumber(num)}%`;
};

// Navbar Component
const Navbar = () => (
  <nav className="bg-white border-b border-slate-200 sticky top-0 z-50" data-testid="navbar">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between h-16">
        <div className="flex items-center">
          <BarChart3 className="h-8 w-8 text-blue-600" />
          <span className="ml-2 text-xl font-semibold text-slate-900">FinAnalytics</span>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-slate-500">Piattaforma di Analisi Finanziaria</span>
        </div>
      </div>
    </div>
  </nav>
);

// Search Component with Autocomplete
const SearchBar = ({ onSearch, isLoading, onSelectSymbol }) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Debounced autocomplete
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length >= 1) {
        try {
          const res = await axios.get(`${API}/autocomplete?q=${encodeURIComponent(query)}`);
          setSuggestions(res.data);
          setShowSuggestions(true);
          setSelectedIndex(-1);
        } catch (err) {
          console.error("Autocomplete error:", err);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [query]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target) &&
          inputRef.current && !inputRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) return;
    
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, -1));
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      handleSelectSuggestion(suggestions[selectedIndex]);
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
    }
  };

  const handleSelectSuggestion = (suggestion) => {
    setQuery(suggestion.symbol);
    setShowSuggestions(false);
    onSelectSymbol(suggestion.symbol);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setShowSuggestions(false);
      onSearch(query.trim());
    }
  };

  const typeColors = {
    stock: "bg-blue-100 text-blue-700",
    etf: "bg-purple-100 text-purple-700",
    fund: "bg-amber-100 text-amber-700",
    bond: "bg-emerald-100 text-emerald-700"
  };

  return (
    <div className="relative" data-testid="search-form">
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
          <Input
            ref={inputRef}
            type="text"
            placeholder="Cerca per simbolo, nome o ISIN (es. AAPL, Apple, US0378331005)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => query.length >= 1 && suggestions.length > 0 && setShowSuggestions(true)}
            className="pl-12 pr-24 h-14 text-lg bg-white border-slate-200 focus:border-blue-500 focus:ring-blue-500 rounded-xl shadow-sm"
            data-testid="search-input"
          />
          <Button 
            type="submit" 
            disabled={isLoading || !query.trim()}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-600 hover:bg-blue-700 rounded-lg"
            data-testid="search-button"
          >
            {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : "Analizza"}
          </Button>
        </div>
      </form>

      {/* Autocomplete Suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div 
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-2 bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden"
          data-testid="autocomplete-suggestions"
        >
          {suggestions.map((suggestion, index) => (
            <div
              key={suggestion.symbol}
              className={`flex items-center justify-between px-4 py-3 cursor-pointer transition-colors ${
                index === selectedIndex ? 'bg-blue-50' : 'hover:bg-slate-50'
              }`}
              onClick={() => handleSelectSuggestion(suggestion)}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <span className="font-bold text-slate-600 text-sm">{suggestion.symbol.slice(0, 2)}</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900">{suggestion.symbol}</span>
                    <Badge className={`text-xs ${typeColors[suggestion.type] || typeColors.stock}`}>
                      {suggestion.type?.toUpperCase()}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-500">{suggestion.name}</p>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-400" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Price Change Component
const PriceChange = ({ change, changePercent, size = "default" }) => {
  const isPositive = change >= 0;
  const Icon = isPositive ? TrendingUp : TrendingDown;
  const colorClass = isPositive ? "text-green-600" : "text-red-600";
  const bgClass = isPositive ? "bg-green-50" : "bg-red-50";
  
  const sizeClasses = size === "large" 
    ? "text-lg px-3 py-1.5" 
    : "text-sm px-2 py-1";

  return (
    <span className={`inline-flex items-center gap-1 ${bgClass} ${colorClass} ${sizeClasses} rounded-lg font-medium`}>
      <Icon className={size === "large" ? "h-5 w-5" : "h-4 w-4"} />
      {formatPercent(changePercent)}
    </span>
  );
};

// Mini Sparkline Component
const Sparkline = ({ data, positive = true, width = 80, height = 30 }) => {
  if (!data || data.length === 0) return null;
  
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  const color = positive ? "#16a34a" : "#dc2626";

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        points={points}
      />
    </svg>
  );
};

// Analyst Rating Badge
const AnalystRating = ({ rating }) => {
  if (!rating) return null;
  
  const ratingColors = {
    "Strong Buy": "bg-green-600 text-white",
    "Buy": "bg-green-500 text-white",
    "Hold": "bg-amber-500 text-white",
    "Neutral": "bg-slate-500 text-white",
    "Sell": "bg-red-500 text-white",
    "Strong Sell": "bg-red-600 text-white",
  };

  return (
    <div className="flex items-center gap-2">
      <Badge className={ratingColors[rating.rating] || "bg-slate-500 text-white"}>
        {rating.rating}
      </Badge>
      {rating.target_price && (
        <span className="text-sm text-slate-600">
          Target: <span className="font-semibold">${rating.target_price}</span>
          {rating.upside && (
            <span className={`ml-1 ${rating.upside >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ({rating.upside >= 0 ? '+' : ''}{rating.upside}%)
            </span>
          )}
        </span>
      )}
    </div>
  );
};

// Trending Instruments Component
const TrendingSection = ({ onSelect }) => {
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const res = await axios.get(`${API}/trending`);
        setTrending(res.data);
      } catch (err) {
        console.error("Error fetching trending:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchTrending();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-24 bg-slate-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <Flame className="h-5 w-5 text-orange-500" />
        <h3 className="font-semibold text-slate-700">Strumenti Popolari</h3>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {trending.slice(0, 5).map((item) => (
          <div
            key={item.symbol}
            onClick={() => onSelect(item.symbol)}
            className="bg-white rounded-xl border border-slate-200 p-4 cursor-pointer hover:border-blue-300 hover:shadow-md transition-all"
            data-testid={`trending-${item.symbol}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-slate-900">{item.symbol}</span>
              <Sparkline 
                data={item.sparkline} 
                positive={item.change_percent >= 0}
                width={50}
                height={20}
              />
            </div>
            <p className="text-xs text-slate-500 truncate mb-2">{item.name}</p>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-sm tabular-nums">${item.price?.toFixed(2)}</span>
              <span className={`text-xs font-medium ${item.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {item.change_percent >= 0 ? '+' : ''}{item.change_percent?.toFixed(2)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Instrument Card Component
const InstrumentCard = ({ data, onSelect, onAddToWatchlist, isInWatchlist, onRemoveFromWatchlist }) => {
  const typeColors = {
    stock: "bg-blue-100 text-blue-800",
    etf: "bg-purple-100 text-purple-800",
    fund: "bg-amber-100 text-amber-800",
    bond: "bg-emerald-100 text-emerald-800"
  };

  return (
    <Card 
      className="card-hover cursor-pointer bg-white border-slate-200" 
      onClick={() => onSelect(data.symbol)}
      data-testid={`instrument-card-${data.symbol}`}
    >
      <CardContent className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-semibold text-slate-900">{data.symbol}</h3>
              <Badge className={typeColors[data.instrument_type] || typeColors.stock}>
                {data.instrument_type?.toUpperCase()}
              </Badge>
            </div>
            <p className="text-sm text-slate-500 line-clamp-1">{data.name}</p>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    isInWatchlist ? onRemoveFromWatchlist(data.symbol) : onAddToWatchlist(data);
                  }}
                  className="text-slate-400 hover:text-amber-500"
                  data-testid={`watchlist-btn-${data.symbol}`}
                >
                  {isInWatchlist ? <Star className="h-5 w-5 fill-amber-400 text-amber-400" /> : <StarOff className="h-5 w-5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {isInWatchlist ? "Rimuovi dalla watchlist" : "Aggiungi alla watchlist"}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        {data.price !== undefined && (
          <div className="flex items-end justify-between">
            <div>
              <p className="text-2xl font-bold text-slate-900 tabular-nums">
                {formatCurrency(data.price, data.currency)}
              </p>
            </div>
            {data.change_percent !== undefined && (
              <PriceChange change={data.change} changePercent={data.change_percent} />
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Detail View Component
const DetailView = ({ symbol, onClose, onAddToWatchlist, isInWatchlist, onRemoveFromWatchlist }) => {
  const [quote, setQuote] = useState(null);
  const [details, setDetails] = useState(null);
  const [history, setHistory] = useState([]);
  const [period, setPeriod] = useState("1mo");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [quoteRes, detailsRes, historyRes] = await Promise.all([
        axios.get(`${API}/quote/${symbol}`),
        axios.get(`${API}/details/${symbol}`),
        axios.get(`${API}/history/${symbol}?period=${period}`)
      ]);
      setQuote(quoteRes.data);
      setDetails(detailsRes.data);
      setHistory(historyRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Errore nel caricamento dei dati");
    } finally {
      setLoading(false);
    }
  }, [symbol, period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-8" data-testid="detail-loading">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/3"></div>
          <div className="h-4 bg-slate-200 rounded w-1/2"></div>
          <div className="h-64 bg-slate-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="bg-white border-slate-200" data-testid="detail-error">
        <CardContent className="p-8 text-center">
          <p className="text-red-500">{error}</p>
          <Button onClick={fetchData} className="mt-4">Riprova</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden fade-in" data-testid="detail-view">
      {/* Header */}
      <div className="p-6 border-b border-slate-100">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold text-slate-900">{quote?.symbol}</h2>
              <Badge className="bg-blue-100 text-blue-800">
                {details?.instrument_type?.toUpperCase()}
              </Badge>
              {details?.exchange && (
                <span className="text-sm text-slate-500">{details.exchange}</span>
              )}
            </div>
            <p className="text-slate-600">{quote?.name}</p>
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => isInWatchlist ? onRemoveFromWatchlist(symbol) : onAddToWatchlist({ symbol: quote?.symbol, name: quote?.name, instrument_type: details?.instrument_type })}
                    data-testid="detail-watchlist-btn"
                  >
                    {isInWatchlist ? <Star className="h-5 w-5 fill-amber-400 text-amber-400" /> : <StarOff className="h-5 w-5" />}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {isInWatchlist ? "Rimuovi dalla watchlist" : "Aggiungi alla watchlist"}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button variant="outline" size="icon" onClick={fetchData} data-testid="refresh-btn">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={onClose} data-testid="close-detail-btn">
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>
        
        {/* Price */}
        <div className="mt-4 flex items-end gap-4">
          <span className="text-4xl font-bold text-slate-900 tabular-nums">
            {formatCurrency(quote?.price, quote?.currency)}
          </span>
          {quote && <PriceChange change={quote.change} changePercent={quote.change_percent} size="large" />}
        </div>
      </div>

      {/* Chart */}
      <div className="p-6 border-b border-slate-100">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold text-slate-700">Andamento Storico</h3>
          <div className="flex gap-1">
            {["1mo", "3mo", "6mo", "1y", "5y"].map((p) => (
              <Button
                key={p}
                variant={period === p ? "default" : "ghost"}
                size="sm"
                onClick={() => setPeriod(p)}
                className={period === p ? "bg-blue-600" : ""}
                data-testid={`period-${p}`}
              >
                {p.toUpperCase()}
              </Button>
            ))}
          </div>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12, fill: '#64748B' }}
                tickLine={false}
                axisLine={{ stroke: '#E2E8F0' }}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#64748B' }}
                tickLine={false}
                axisLine={false}
                domain={['auto', 'auto']}
                tickFormatter={(value) => formatNumber(value, 0)}
              />
              <RechartsTooltip 
                contentStyle={{ backgroundColor: 'white', border: '1px solid #E2E8F0', borderRadius: '8px' }}
                formatter={(value) => [formatCurrency(value, quote?.currency), 'Prezzo']}
              />
              <Area 
                type="monotone" 
                dataKey="close" 
                stroke="#3B82F6" 
                strokeWidth={2}
                fill="url(#colorPrice)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="p-6">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="overview">Panoramica</TabsTrigger>
            <TabsTrigger value="fundamentals">Fondamentali</TabsTrigger>
            <TabsTrigger value="trading">Trading</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Apertura" value={formatCurrency(quote?.open, quote?.currency)} />
              <MetricCard label="Massimo" value={formatCurrency(quote?.high, quote?.currency)} />
              <MetricCard label="Minimo" value={formatCurrency(quote?.low, quote?.currency)} />
              <MetricCard label="Volume" value={formatLargeNumber(quote?.volume)} />
              <MetricCard label="Max 52 sett." value={formatCurrency(quote?.week_52_high, quote?.currency)} />
              <MetricCard label="Min 52 sett." value={formatCurrency(quote?.week_52_low, quote?.currency)} />
              <MetricCard label="Market Cap" value={formatLargeNumber(details?.market_cap)} />
              <MetricCard label="P/E Ratio" value={formatNumber(details?.pe_ratio)} />
            </div>
            {details?.description && (
              <div className="mt-6">
                <h4 className="font-semibold text-slate-700 mb-2">Descrizione</h4>
                <p className="text-sm text-slate-600 leading-relaxed line-clamp-4">{details.description}</p>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="fundamentals">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Ricavi" value={formatLargeNumber(details?.revenue)} />
              <MetricCard label="EBITDA" value={formatLargeNumber(details?.ebitda)} />
              <MetricCard label="Utile Netto" value={formatLargeNumber(details?.net_income)} />
              <MetricCard label="Margine Profitto" value={details?.profit_margin ? formatPercent(details.profit_margin * 100) : "N/A"} />
              <MetricCard label="ROE" value={details?.roe ? formatPercent(details.roe * 100) : "N/A"} />
              <MetricCard label="ROA" value={details?.roa ? formatPercent(details.roa * 100) : "N/A"} />
              <MetricCard label="Price to Book" value={formatNumber(details?.price_to_book)} />
              <MetricCard label="PEG Ratio" value={formatNumber(details?.peg_ratio)} />
            </div>
          </TabsContent>
          
          <TabsContent value="trading">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Beta" value={formatNumber(details?.beta)} />
              <MetricCard label="Volume Medio" value={formatLargeNumber(details?.avg_volume)} />
              <MetricCard label="Azioni in Circolazione" value={formatLargeNumber(details?.shares_outstanding)} />
              <MetricCard label="Float" value={formatLargeNumber(details?.float_shares)} />
              <MetricCard label="Dividend Yield" value={details?.dividend_yield ? formatPercent(details.dividend_yield * 100) : "N/A"} />
              <MetricCard label="Dividend Rate" value={details?.dividend_rate ? formatCurrency(details.dividend_rate, quote?.currency) : "N/A"} />
              <MetricCard label="Payout Ratio" value={details?.payout_ratio ? formatPercent(details.payout_ratio * 100) : "N/A"} />
              <MetricCard label="Settore" value={details?.sector || "N/A"} isText />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ label, value, isText = false }) => (
  <div className="bg-slate-50 rounded-xl p-4">
    <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">{label}</p>
    <p className={`font-semibold text-slate-900 ${!isText ? 'tabular-nums' : ''}`}>{value}</p>
  </div>
);

// Watchlist Component
const Watchlist = ({ items, onSelect, onRemove, onRefresh, loading }) => {
  if (items.length === 0) {
    return (
      <Card className="bg-white border-slate-200" data-testid="watchlist-empty">
        <CardContent className="p-8 text-center">
          <Star className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">La tua watchlist è vuota</p>
          <p className="text-sm text-slate-400 mt-1">Cerca uno strumento e aggiungilo alla watchlist</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-white border-slate-200" data-testid="watchlist">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">Watchlist</CardTitle>
          <Button variant="ghost" size="sm" onClick={onRefresh} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <ScrollArea className="h-[400px]">
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={item.symbol}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                onClick={() => onSelect(item.symbol)}
                data-testid={`watchlist-item-${item.symbol}`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900">{item.symbol}</span>
                    <Badge variant="outline" className="text-xs">{item.instrument_type}</Badge>
                  </div>
                  <p className="text-sm text-slate-500 truncate">{item.name}</p>
                </div>
                {item.price && (
                  <div className="text-right mr-4">
                    <p className="font-semibold tabular-nums">{formatCurrency(item.price, item.currency)}</p>
                    {item.change_percent !== undefined && (
                      <span className={`text-sm ${item.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(item.change_percent)}
                      </span>
                    )}
                  </div>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(item.symbol);
                  }}
                  className="text-slate-400 hover:text-red-500"
                  data-testid={`remove-watchlist-${item.symbol}`}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

// Compare View Component - Base 100 Chart
const CompareView = ({ symbols, onRemoveSymbol, onAddSymbol }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [newSymbol, setNewSymbol] = useState("");
  const [period, setPeriod] = useState("1mo");

  // Colors for different lines
  const lineColors = [
    "#3B82F6", // blue
    "#10B981", // green  
    "#F59E0B", // amber
    "#EF4444", // red
    "#8B5CF6", // purple
    "#EC4899", // pink
    "#06B6D4", // cyan
    "#F97316", // orange
    "#6366F1", // indigo
    "#84CC16", // lime
  ];

  const fetchComparison = useCallback(async () => {
    if (symbols.length < 1) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API}/compare?symbols=${symbols.join(',')}&period=${period}`);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [symbols, period]);

  useEffect(() => {
    if (symbols.length >= 1) {
      fetchComparison();
    } else {
      setData(null);
    }
  }, [fetchComparison, symbols, period]);

  const handleAddSymbol = (e) => {
    e.preventDefault();
    if (newSymbol.trim() && !symbols.includes(newSymbol.toUpperCase())) {
      onAddSymbol(newSymbol.toUpperCase());
      setNewSymbol("");
    }
  };

  const periods = [
    { value: "1mo", label: "1M" },
    { value: "3mo", label: "3M" },
    { value: "6mo", label: "6M" },
    { value: "1y", label: "1A" },
    { value: "2y", label: "2A" },
    { value: "5y", label: "5A" },
  ];

  if (symbols.length < 1) {
    return (
      <Card className="bg-white border-slate-200" data-testid="compare-empty">
        <CardContent className="p-8 text-center">
          <ArrowUpDown className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-600 font-medium mb-2">Confronto Performance Base 100</p>
          <p className="text-slate-500 text-sm mb-4">Aggiungi strumenti per confrontare le performance normalizzate</p>
          <form onSubmit={handleAddSymbol} className="flex gap-2 max-w-sm mx-auto">
            <Input
              placeholder="Simbolo (es. AAPL, SPY, MSFT)"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              className="flex-1"
              data-testid="compare-input"
            />
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="compare-add-btn">
              <Plus className="h-4 w-4 mr-1" /> Aggiungi
            </Button>
          </form>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-white border-slate-200" data-testid="compare-view">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <CardTitle className="text-xl">Confronto Performance Base 100</CardTitle>
            <CardDescription>Tutti gli strumenti normalizzati a 100 all'inizio del periodo</CardDescription>
          </div>
          <form onSubmit={handleAddSymbol} className="flex gap-2">
            <Input
              placeholder="Aggiungi simbolo"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              className="w-36"
              disabled={symbols.length >= 10}
            />
            <Button type="submit" size="sm" disabled={symbols.length >= 10} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4" />
            </Button>
          </form>
        </div>
        
        {/* Symbol badges */}
        <div className="flex flex-wrap gap-2 mt-3">
          {symbols.map((s, index) => (
            <Badge 
              key={s} 
              className="cursor-pointer px-3 py-1 text-white"
              style={{ backgroundColor: lineColors[index % lineColors.length] }}
              onClick={() => onRemoveSymbol(s)}
            >
              {s} <X className="h-3 w-3 ml-1" />
            </Badge>
          ))}
        </div>

        {/* Period selector */}
        <div className="flex gap-1 mt-4">
          {periods.map((p) => (
            <Button
              key={p.value}
              variant={period === p.value ? "default" : "outline"}
              size="sm"
              onClick={() => setPeriod(p.value)}
              className={period === p.value ? "bg-blue-600 hover:bg-blue-700" : ""}
              data-testid={`compare-period-${p.value}`}
            >
              {p.label}
            </Button>
          ))}
        </div>
      </CardHeader>
      
      <CardContent>
        {loading ? (
          <div className="h-80 flex items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : data ? (
          <>
            {/* Chart */}
            <div className="h-80 mb-6">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.chart_data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 11, fill: '#64748B' }}
                    tickLine={false}
                    axisLine={{ stroke: '#E2E8F0' }}
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return date.toLocaleDateString('it-IT', { month: 'short', day: 'numeric' });
                    }}
                  />
                  <YAxis 
                    tick={{ fontSize: 11, fill: '#64748B' }}
                    tickLine={false}
                    axisLine={false}
                    domain={['auto', 'auto']}
                    tickFormatter={(value) => value.toFixed(0)}
                  />
                  <RechartsTooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #E2E8F0', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                    formatter={(value, name) => [value.toFixed(2), name]}
                    labelFormatter={(label) => new Date(label).toLocaleDateString('it-IT', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  />
                  {/* Reference line at 100 */}
                  <Line
                    type="monotone"
                    dataKey={() => 100}
                    stroke="#CBD5E1"
                    strokeDasharray="5 5"
                    strokeWidth={1}
                    dot={false}
                    name="Base 100"
                  />
                  {symbols.map((symbol, index) => (
                    <Line
                      key={symbol}
                      type="monotone"
                      dataKey={symbol}
                      stroke={lineColors[index % lineColors.length]}
                      strokeWidth={2}
                      dot={false}
                      name={symbol}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Performance Table */}
            <div className="bg-slate-50 rounded-xl p-4">
              <h4 className="font-semibold text-slate-700 mb-3">Riepilogo Performance</h4>
              <div className="overflow-x-auto">
                <table className="w-full data-table text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-2 px-2 font-medium">Strumento</th>
                      <th className="text-right py-2 px-2 font-medium">Valore Iniziale</th>
                      <th className="text-right py-2 px-2 font-medium">Valore Finale</th>
                      <th className="text-right py-2 px-2 font-medium">Rendimento</th>
                      <th className="text-right py-2 px-2 font-medium">Volatilità Ann.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.performance?.map((item, index) => (
                      <tr key={item.symbol} className="border-b border-slate-100">
                        <td className="py-2 px-2">
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: lineColors[index % lineColors.length] }}
                            />
                            <div>
                              <span className="font-semibold">{item.symbol}</span>
                              <p className="text-xs text-slate-500 truncate max-w-[120px]">{item.name}</p>
                            </div>
                          </div>
                        </td>
                        <td className="text-right py-2 px-2 tabular-nums">100,00</td>
                        <td className="text-right py-2 px-2 tabular-nums font-medium">{formatNumber(item.end_value)}</td>
                        <td className="text-right py-2 px-2">
                          <span className={`font-semibold ${item.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatPercent(item.total_return)}
                          </span>
                        </td>
                        <td className="text-right py-2 px-2 tabular-nums text-slate-600">
                          {formatNumber(item.volatility)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
};

// Main App Component
function App() {
  const [searchResults, setSearchResults] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [compareSymbols, setCompareSymbols] = useState([]);
  const [activeTab, setActiveTab] = useState("search");
  const [isSearching, setIsSearching] = useState(false);
  const [watchlistLoading, setWatchlistLoading] = useState(false);

  // Fetch watchlist on mount
  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      const res = await axios.get(`${API}/watchlist`);
      setWatchlist(res.data);
    } catch (err) {
      console.error("Error fetching watchlist:", err);
    }
  };

  const refreshWatchlistPrices = async () => {
    setWatchlistLoading(true);
    try {
      const updatedItems = await Promise.all(
        watchlist.map(async (item) => {
          try {
            const res = await axios.get(`${API}/quote/${item.symbol}`);
            return { ...item, price: res.data.price, change_percent: res.data.change_percent, currency: res.data.currency };
          } catch {
            return item;
          }
        })
      );
      setWatchlist(updatedItems);
    } finally {
      setWatchlistLoading(false);
    }
  };

  const handleSearch = async (query) => {
    setIsSearching(true);
    try {
      // For single instrument search, go directly to detail view
      const res = await axios.get(`${API}/instrument/${encodeURIComponent(query)}`);
      setSelectedSymbol(query.toUpperCase());
      setSearchResults([]);
    } catch (err) {
      console.error("Search error:", err);
      // Fallback to search if instrument not found
      try {
        const searchRes = await axios.get(`${API}/search?q=${encodeURIComponent(query)}`);
        if (searchRes.data.length === 1) {
          setSelectedSymbol(searchRes.data[0].symbol);
          setSearchResults([]);
        } else {
          setSearchResults(searchRes.data);
          setSelectedSymbol(null);
        }
      } catch {
        setSearchResults([]);
      }
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectSymbol = (symbol) => {
    setSelectedSymbol(symbol);
    setSearchResults([]);
    setActiveTab("search");
  };

  const handleAddToWatchlist = async (item) => {
    try {
      await axios.post(`${API}/watchlist`, {
        symbol: item.symbol,
        name: item.name,
        instrument_type: item.instrument_type,
        isin: item.isin
      });
      fetchWatchlist();
    } catch (err) {
      console.error("Error adding to watchlist:", err);
    }
  };

  const handleRemoveFromWatchlist = async (symbol) => {
    try {
      await axios.delete(`${API}/watchlist/${symbol}`);
      setWatchlist(watchlist.filter(item => item.symbol !== symbol));
    } catch (err) {
      console.error("Error removing from watchlist:", err);
    }
  };

  const isInWatchlist = (symbol) => watchlist.some(item => item.symbol === symbol);

  return (
    <div className="min-h-screen bg-slate-50" data-testid="app">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Analisi Strumenti Finanziari</h1>
          <p className="text-slate-500 mb-6">Cerca e analizza azioni, ETF, obbligazioni e fondi</p>
          <SearchBar onSearch={handleSearch} isLoading={isSearching} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-4">
                <TabsTrigger value="search" data-testid="tab-search">Ricerca</TabsTrigger>
                <TabsTrigger value="compare" data-testid="tab-compare">Confronta</TabsTrigger>
              </TabsList>

              <TabsContent value="search" className="space-y-4">
                {selectedSymbol ? (
                  <DetailView
                    symbol={selectedSymbol}
                    onClose={() => setSelectedSymbol(null)}
                    onAddToWatchlist={handleAddToWatchlist}
                    isInWatchlist={isInWatchlist(selectedSymbol)}
                    onRemoveFromWatchlist={handleRemoveFromWatchlist}
                  />
                ) : searchResults.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {searchResults.map((result) => (
                      <InstrumentCard
                        key={result.symbol}
                        data={result}
                        onSelect={setSelectedSymbol}
                        onAddToWatchlist={handleAddToWatchlist}
                        isInWatchlist={isInWatchlist(result.symbol)}
                        onRemoveFromWatchlist={handleRemoveFromWatchlist}
                      />
                    ))}
                  </div>
                ) : (
                  <Card className="bg-white border-slate-200" data-testid="search-placeholder">
                    <CardContent className="p-12 text-center">
                      <Search className="h-16 w-16 text-slate-300 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-slate-700 mb-2">Cerca uno strumento finanziario</h3>
                      <p className="text-slate-500">Inserisci un simbolo (AAPL), nome (Apple) o codice ISIN</p>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              <TabsContent value="compare">
                <CompareView
                  symbols={compareSymbols}
                  onRemoveSymbol={(s) => setCompareSymbols(compareSymbols.filter(sym => sym !== s))}
                  onAddSymbol={(s) => setCompareSymbols([...compareSymbols, s])}
                />
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Watchlist
              items={watchlist}
              onSelect={(symbol) => {
                setSelectedSymbol(symbol);
                setActiveTab("search");
              }}
              onRemove={handleRemoveFromWatchlist}
              onRefresh={refreshWatchlistPrices}
              loading={watchlistLoading}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 mt-16 py-8 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-slate-500">
          <p>FinAnalytics - Piattaforma di Analisi Finanziaria</p>
          <p className="mt-1">I dati sono forniti da Yahoo Finance e sono da considerarsi indicativi</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
