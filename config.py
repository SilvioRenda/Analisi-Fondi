"""
Configurazione per l'analisi comparativa dei fondi healthcare
"""

import os
import json
from typing import Dict, Optional

# ISIN dei fondi da analizzare
FUNDS = {
    "Alliance Bernstein (International Health Care Portfolio)": {
        "isin": "LU0097089360",
        "ticker": None,  # Da determinare
        "name_short": "AB International Health Care",
        "description": "Fondo azionario internazionale che investe in società operanti nel settore sanitario e healthcare a livello globale. Gestito da Alliance Bernstein, si concentra su aziende con solide fondamenta e potenziale di crescita nel settore della salute.",
        "manager": "Alliance Bernstein",
        "category": "Azionario Internazionale - Healthcare"
    },
    "BlackRock (World Healthscience Fund)": {
        "isin": "LU1960219225",
        "ticker": None,
        "name_short": "BlackRock World Healthscience",
        "description": "Fondo globale che investe in società del settore healthscience, includendo biotecnologie, farmaceutiche, dispositivi medici e servizi sanitari. Gestito da BlackRock, uno dei più grandi gestori patrimoniali al mondo.",
        "manager": "BlackRock",
        "category": "Azionario Globale - Healthscience"
    },
    "BNP Paribas (Health Care Innovators)": {
        "isin": "LU0823417067",
        "ticker": None,
        "name_short": "BNP Health Care Innovators",
        "description": "Fondo focalizzato su aziende innovative nel settore healthcare, con particolare attenzione alle tecnologie mediche emergenti, biotecnologie e soluzioni digitali per la salute. Gestito da BNP Paribas Asset Management.",
        "manager": "BNP Paribas Asset Management",
        "category": "Azionario - Healthcare Innovation"
    },
    "Wellington (Global Health Care Equity Fund)": {
        "isin": "IE0003111113",
        "ticker": None,
        "name_short": "Wellington Global Health Care",
        "description": "Fondo azionario globale che investe in società del settore sanitario in tutto il mondo. Gestito da Wellington Management, si concentra su aziende con modelli di business sostenibili e leadership nel settore healthcare.",
        "manager": "Wellington Management",
        "category": "Azionario Globale - Healthcare"
    },
    "Robeco (Healthy Living)": {
        "isin": "LU2400458779",
        "ticker": None,
        "name_short": "Robeco Healthy Living",
        "description": "Fondo tematico che investe in aziende che promuovono stili di vita sani, includendo nutrizione, benessere, prevenzione e tecnologie per la salute. Gestito da Robeco, con focus su sostenibilità e impatto sociale positivo.",
        "manager": "Robeco",
        "category": "Azionario Tematico - Healthy Living"
    },
    "Fidelity (Global Healthcare Fund)": {
        "isin": "LU2078916223",
        "ticker": None,
        "name_short": "Fidelity Global Healthcare",
        "description": "Fondo globale che investe in società del settore sanitario in tutto il mondo, includendo farmaceutiche, biotecnologie, dispositivi medici e servizi sanitari. Gestito da Fidelity Investments con approccio di ricerca fondamentale.",
        "manager": "Fidelity Investments",
        "category": "Azionario Globale - Healthcare"
    },
    "Pictet (Longevity)": {
        "isin": "LU0188500879",
        "ticker": None,
        "name_short": "Pictet Longevity",
        "description": "Fondo tematico che investe in aziende che beneficiano dell'invecchiamento della popolazione e dell'aumento dell'aspettativa di vita. Include farmaceutiche, dispositivi medici, servizi per anziani e tecnologie anti-aging. Gestito da Pictet Asset Management.",
        "manager": "Pictet Asset Management",
        "category": "Azionario Tematico - Longevity"
    },
    "Polar Capital (Healthcare Opportunities Fund)": {
        "isin": "IE00BKSBD728",
        "ticker": None,
        "name_short": "Polar Capital Healthcare",
        "description": "Fondo specializzato che investe in opportunità nel settore healthcare, con focus su aziende in fase di crescita e innovazione. Gestito da Polar Capital, un gestore specializzato in settori specifici.",
        "manager": "Polar Capital",
        "category": "Azionario - Healthcare Opportunities"
    },
    "T. Rowe Price (Health Sciences Fund)": {
        "isin": "US87281Y1029",
        "ticker": "PRHSX",
        "name_short": "T. Rowe Price Health Sciences",
        "description": "Fondo statunitense che investe principalmente in società del settore health sciences, includendo biotecnologie, farmaceutiche, dispositivi medici e servizi sanitari. Gestito da T. Rowe Price, uno dei più grandi gestori indipendenti al mondo.",
        "manager": "T. Rowe Price",
        "category": "Azionario USA - Health Sciences"
    },
    "JSS Safra Sarasin (Sustainable Equity Future Health)": {
        "isin": "LU2041626974",
        "ticker": None,
        "name_short": "JSS Future Health",
        "description": "Fondo azionario sostenibile che investe in aziende del settore healthcare e future health, con focus su innovazione, sostenibilità e soluzioni per la salute del futuro. Gestito da J. Safra Sarasin Fund Management, si concentra su investimenti responsabili nel settore sanitario. Classe I CHF acc (accumulazione), lanciato il 15 dicembre 2020.",
        "manager": "J. Safra Sarasin Fund Management",
        "category": "Azionario Sostenibile - Future Health"
    }
}

# Parametri di analisi
YEARS_BACK = 5
BASE_VALUE = 100

# Directory per cache e output
CACHE_DIR = "cache"
OUTPUT_DIR = "output"
TEMPLATES_DIR = "templates"

# Modalità operativa - Caricamento dinamico fondi
USE_DYNAMIC_ISINS = False  # Se True, legge ISIN da file o input
FUNDS_LIST_FILE = "funds_list.txt"  # File con lista ISIN (uno per riga)
FUNDS_JSON_FILE = "funds_custom.json"  # File JSON con configurazione fondi custom

# Open FIGI API (gratuito, opzionale API key per rate limit più alti)
OPEN_FIGI_API_KEY = os.getenv('OPEN_FIGI_API_KEY', '')  # Opzionale
OPEN_FIGI_BASE_URL = 'https://api.openfigi.com/v3'

# EOD Historical Data API (per dati adjusted total return)
EOD_API_KEY = os.getenv('EOD_API_KEY', '')  # Inserisci la tua API key qui o come variabile d'ambiente

# Alpha Vantage API (gratuito, limiti: 5 calls/min, 500 calls/day)
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'U3Q7DATZGJIAEQEK')  # Gratuito: https://www.alphavantage.co/support/#api-key

# Financial Modeling Prep API
FMP_API_KEY = os.getenv('FMP_API_KEY', '')  # https://site.financialmodelingprep.com/developer/docs/

# Configurazione Report per Clienti
REPORT_CONFIG = {
    'company_name': os.getenv('REPORT_COMPANY_NAME', 'Analisi Fondi Healthcare'),
    'logo_path': os.getenv('REPORT_LOGO_PATH', ''),  # Opzionale: path al logo
    'primary_color': os.getenv('REPORT_PRIMARY_COLOR', '#1a365d'),  # Colore principale
    'footer_text': os.getenv('REPORT_FOOTER_TEXT', 'Report generato automaticamente'),
    'disclaimer': os.getenv('REPORT_DISCLAIMER', '''I dati presentati in questo report sono forniti a scopo informativo e non costituiscono consulenza finanziaria. 
Le performance passate non sono indicative di risultati futuri. Si consiglia di consultare un consulente finanziario qualificato prima di prendere decisioni di investimento.''')
}

# Configurazione Librerie Avanzate
USE_POLARS = os.getenv('USE_POLARS', 'False').lower() == 'true'  # Default: False (usa Pandas)

# API Keys per librerie avanzate (opzionali)
FINANCETOOLKIT_API_KEY = os.getenv('FINANCETOOLKIT_API_KEY', '')  # Opzionale per funzionalità avanzate


def load_funds_from_json(filepath: str) -> Dict:
    """Carica configurazione fondi da file JSON"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Errore caricamento {filepath}: {e}")
        return FUNDS


def load_funds_from_list(filepath: str) -> Dict:
    """Carica lista ISIN da file di testo e crea configurazione base"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            isins = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        # Crea configurazione base per ogni ISIN
        funds = {}
        for isin in isins:
            if len(isin) >= 12:  # ISIN valido ha almeno 12 caratteri
                funds[f"Fondo {isin}"] = {
                    'isin': isin,
                    'ticker': None,
                    'name_short': f'Fondo {isin}',
                    'description': '',
                    'manager': '',
                    'category': ''
                }
        return funds
    except Exception as e:
        print(f"Errore caricamento {filepath}: {e}")
        return FUNDS


def load_funds_config() -> Dict:
    """Carica configurazione fondi da file o usa default"""
    if USE_DYNAMIC_ISINS:
        # Prova a caricare da file JSON prima
        if os.path.exists(FUNDS_JSON_FILE):
            return load_funds_from_json(FUNDS_JSON_FILE)
        # Poi prova file di testo con lista ISIN
        elif os.path.exists(FUNDS_LIST_FILE):
            return load_funds_from_list(FUNDS_LIST_FILE)
    return FUNDS  # Default hardcoded
