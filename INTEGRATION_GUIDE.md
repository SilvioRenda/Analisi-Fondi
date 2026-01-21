# Guida Integrazione Librerie GitHub

Questa guida spiega come installare, configurare e usare le nuove librerie GitHub integrate nel progetto.

## Librerie Integrate

### 1. FinanceToolkit
- **Scopo**: Metriche avanzate (Beta, Alpha, Sharpe, Sortino, Treynor)
- **Installazione**: `pip install financetoolkit`
- **API Key**: Opzionale (alcune funzionalità avanzate potrebbero richiederla)
- **Uso**: Calcolo automatico di metriche avanzate in `data_processor.py`

### 2. FinanceDatabase
- **Scopo**: Classificazione automatica settori/industrie
- **Installazione**: `pip install FinanceDatabase`
- **API Key**: Non richiesta
- **Uso**: Classificazione automatica settori in `sector_classifier.py`

### 3. Riskfolio-Lib
- **Scopo**: Analisi portfolio, ottimizzazione, clustering
- **Installazione**: `pip install Riskfolio-Lib`
- **API Key**: Non richiesta
- **Uso**: Analisi portfolio in `portfolio_analyzer.py`

### 4. pandas-ta
- **Scopo**: Indicatori tecnici (RSI, MACD, Bollinger Bands, medie mobili)
- **Installazione**: `pip install pandas-ta`
- **API Key**: Non richiesta
- **Uso**: Indicatori tecnici in `technical_indicators.py`

### 5. Polars (Opzionale)
- **Scopo**: Alternativa veloce a Pandas per dataset grandi
- **Installazione**: `pip install polars`
- **API Key**: Non richiesta
- **Uso**: Attualmente opzionale, abilitare con `USE_POLARS=True` in config

## Installazione

### Metodo 1: Script Automatico (Consigliato)

Esegui lo script di installazione:

```bash
python install_libraries.py
```

Lo script:
- Verifica versione Python
- Installa tutte le librerie da `requirements.txt`
- Testa import di tutte le librerie
- Verifica API keys

### Metodo 2: Manuale

Installa tutte le librerie:

```bash
pip install -r requirements.txt
```

Oppure installa singolarmente:

```bash
pip install financetoolkit FinanceDatabase Riskfolio-Lib pandas-ta polars
```

## Configurazione

### API Keys (Opzionali)

Alcune librerie potrebbero richiedere API keys per funzionalità avanzate. Configura in `config.py` o come variabili d'ambiente:

```python
# config.py
FINANCETOOLKIT_API_KEY = 'your_api_key_here'
```

Oppure:

```bash
export FINANCETOOLKIT_API_KEY='your_api_key_here'
```

### Flag Polars

Per abilitare Polars (opzionale):

```python
# config.py
USE_POLARS = True
```

Oppure:

```bash
export USE_POLARS=True
```

## Funzionalità Disponibili

### 1. Metriche Avanzate

Con FinanceToolkit installato, il sistema calcola automaticamente:
- **Sortino Ratio**: Sharpe ratio che considera solo downside volatility
- **Alpha**: Excess return rispetto al benchmark
- **Treynor Ratio**: Return per unità di rischio sistematico

Queste metriche appaiono nella sezione "Metriche Avanzate" del report.

### 2. Classificazione Settori Automatica

Con FinanceDatabase installato, il sistema classifica automaticamente i fondi/titoli in settori usando il database completo.

**Priorità classificazione:**
1. FinanceDatabase (se disponibile)
2. config.FUNDS (campo category)
3. Analisi nome/ticker (fallback)

### 3. Analisi Portfolio

Con Riskfolio-Lib installato, il sistema fornisce:
- **Metriche Portfolio Aggregate**: Return, volatilità, Sharpe ratio del portfolio
- **Allocazione Settoriale**: Distribuzione pesi per settore
- **Concentration Risk (HHI)**: Misura concentrazione portfolio
- **Ottimizzazione Portfolio**: Pesi ottimali (Max Sharpe, Min Volatility)

Queste analisi appaiono nella sezione "Analisi Portfolio" del report.

### 4. Indicatori Tecnici

Con pandas-ta installato, il sistema calcola:
- **RSI (Relative Strength Index)**: Momentum oscillator
- **MACD**: Moving Average Convergence Divergence
- **Bollinger Bands**: Bande di volatilità
- **SMA/EMA**: Medie mobili semplici ed esponenziali
- **Segnali Trading**: Buy/sell signals basati su indicatori

Questi indicatori appaiono nella sezione "Indicatori Tecnici" del report.

## Fallback Automatico

Il sistema è progettato per funzionare anche senza le librerie avanzate:

- Se una libreria non è disponibile, il sistema usa implementazioni manuali
- I warning vengono loggati ma l'esecuzione continua
- Le funzionalità base rimangono sempre disponibili

## Testing

Esegui i test per verificare le integrazioni:

```bash
python test_integrations.py
```

I test verificano:
- Disponibilità librerie
- Funzionalità base
- Fallback quando librerie non disponibili

## Troubleshooting

### Errore Import Libreria

Se una libreria non si importa:

1. Verifica installazione: `pip list | grep libreria`
2. Reinstalla: `pip install --upgrade libreria`
3. Verifica versione Python (richiesta >= 3.8)

### Metriche Avanzate Non Appaiono

Se le metriche avanzate non appaiono nel report:

1. Verifica che FinanceToolkit sia installato: `python -c "import financetoolkit"`
2. Controlla i log per errori
3. Le metriche avanzate richiedono dati sufficienti (minimo 30 giorni)

### Classificazione Settori Non Funziona

Se la classificazione settori non funziona:

1. Verifica che FinanceDatabase sia installato
2. Il sistema userà automaticamente il fallback (config.FUNDS o analisi nome)
3. Controlla i log per warning

### Performance Lente

Se le performance sono lente:

1. Considera di abilitare Polars: `USE_POLARS=True`
2. Verifica che la cache funzioni correttamente
3. Riduci il numero di anni analizzati in `config.py`

## Note Importanti

- **Compatibilità**: Le librerie avanzate sono opzionali. Il sistema funziona anche senza.
- **Versioni**: Specifica versioni minime in `requirements.txt`
- **API Keys**: La maggior parte delle funzionalità funziona senza API keys
- **Performance**: Polars è utile solo per dataset molto grandi (> 10k righe)

## Riferimenti

- [FinanceToolkit Documentation](https://github.com/JerBouma/FinanceToolkit)
- [FinanceDatabase Documentation](https://github.com/JerBouma/FinanceDatabase)
- [Riskfolio-Lib Documentation](https://github.com/dcajasn/Riskfolio-Lib)
- [pandas-ta Documentation](https://github.com/twopirllc/pandas-ta)
- [Polars Documentation](https://github.com/pola-rs/polars)
