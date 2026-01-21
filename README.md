# Analisi Comparativa Fondi Healthcare

Applicazione per l'analisi comparativa delle performance di fondi healthcare con visualizzazione interattiva.

## Caratteristiche

- **Confronto Performance**: Visualizzazione delle performance normalizzate in base 100 degli ultimi 5 anni
- **Grafico Interattivo**: Grafico Plotly interattivo con zoom, pan e tooltip
- **Metriche Comparative**: Return totale, annualizzato, volatilità, Sharpe ratio, max drawdown
- **Composizione Fondi**: Analisi della composizione settoriale e top holdings per ogni fondo

## Installazione

1. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

## Utilizzo

### Modalità Base (Configurazione da config.py)

Esegui l'applicazione principale con i fondi configurati in `config.py`:
```bash
python main.py
```

### Modalità Flessibile - Analisi Singolo ISIN

Analizza un singolo fondo specificando l'ISIN:
```bash
python main.py --isin LU0097089360
```

### Modalità Flessibile - Lista ISIN da File

Analizza multiple fondi da un file di testo (un ISIN per riga):
```bash
python main.py --isin-list funds_list.txt
```

Crea un file `funds_list.txt` con gli ISIN:
```
LU0097089360
LU1960219225
LU0823417067
```

### Modalità Flessibile - Configurazione JSON Custom

Usa un file JSON con configurazione custom dei fondi:
```bash
python main.py --funds-file funds_custom.json
```

Vedi `funds_custom.json` per un esempio di formato.

### Utility per Aggiungere Fondi

Testa e aggiungi fondi dinamicamente:
```bash
python add_fund.py LU0097089360 LU1960219225
```

Questa utility:
- Recupera automaticamente i metadati del fondo tramite Open FIGI
- Testa il recupero dati storici
- Mostra informazioni sul fondo

## Configurazione

### Configurazione Base

I fondi da analizzare possono essere configurati in `config.py`. Puoi modificare:
- Gli ISIN dei fondi nel dizionario `FUNDS`
- Il numero di anni da analizzare (`YEARS_BACK`)
- Le directory di cache e output

### Configurazione Dinamica

Il sistema supporta anche il caricamento dinamico da file:

1. **File di testo semplice** (`funds_list.txt`): Lista ISIN, uno per riga
2. **File JSON** (`funds_custom.json`): Configurazione completa con metadati custom

Imposta `USE_DYNAMIC_ISINS = True` in `config.py` per abilitare il caricamento automatico da file.

### Open FIGI (Gratuito)

Il sistema usa Open FIGI per recuperare automaticamente metadati dei fondi (nome, ticker, exchange, categoria). 
- Funziona senza API key (con rate limit più bassi)
- Opzionalmente puoi aggiungere `OPEN_FIGI_API_KEY` in `config.py` per rate limit più alti

## Struttura Progetto

```
.
├── main.py                 # Entry point principale con supporto CLI
├── data_collector.py       # Raccolta dati da fonti esterne (Open FIGI, scraping)
├── data_processor.py       # Elaborazione e normalizzazione
├── visualizer.py          # Generazione grafici Plotly
├── fund_manager.py        # Gestione dinamica fondi e metadati Open FIGI
├── add_fund.py            # Utility CLI per aggiungere/testare fondi
├── config.py              # Configurazione ISIN e parametri
├── requirements.txt        # Dipendenze Python
├── funds_list.txt         # Esempio: lista ISIN (uno per riga)
├── funds_custom.json      # Esempio: configurazione JSON custom
├── templates/
│   └── report.html        # Template HTML per il report
├── output/
│   └── report.html        # Report finale generato
└── cache/                 # Cache dati (generata automaticamente)
```

## Note

- **Fonti Dati**: Il sistema usa Open FIGI (gratuito) per metadati e scraping da fonti affidabili per dati storici
- **Cache**: I dati vengono cachati per 24 ore per evitare chiamate ripetute
- **Flessibilità**: Puoi analizzare qualsiasi ISIN senza modificare il codice
- **Auto-Discovery**: I metadati (nome, ticker, categoria) vengono recuperati automaticamente da Open FIGI
- Se alcuni fondi non hanno dati disponibili, verranno indicati nel report

## Vantaggi del Sistema Flessibile

✅ **Accetta qualsiasi ISIN** - Non serve modificare il codice per aggiungere nuovi fondi
✅ **Auto-discovery metadati** - Open FIGI recupera automaticamente nome, ticker, categoria
✅ **Input multipli** - File di testo, JSON, o command line
✅ **Facile da usare** - Utility CLI per testare fondi prima di aggiungerli
✅ **Scalabile** - Può gestire centinaia di fondi senza problemi

## Fondi Analizzati

1. Alliance Bernstein (International Health Care Portfolio) - LU0097089360
2. BlackRock (World Healthscience Fund) - LU1960219225
3. BNP Paribas (Health Care Innovators) - LU0823417067
4. Wellington (Global Health Care Equity Fund) - IE0003111113
5. Robeco (Healthy Living) - LU2400458779
6. Fidelity (Global Healthcare Fund) - LU2078916223
7. Pictet (Longevity) - LU0188500879
8. Polar Capital (Healthcare Opportunities Fund) - IE00BKSBD728
9. T. Rowe Price (Health Sciences Fund) - US87281Y1029
