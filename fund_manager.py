"""
Gestione dinamica dei fondi con auto-discovery metadati tramite Open FIGI
"""

import requests
import json
import os
from typing import Dict, List, Optional
import config


class FundManager:
    """Gestisce aggiunta e gestione dinamica di fondi"""
    
    def __init__(self):
        self.figi_base_url = config.OPEN_FIGI_BASE_URL
        self.figi_api_key = config.OPEN_FIGI_API_KEY
    
    def _fetch_metadata_from_figi(self, isin: str) -> Dict:
        """
        Recupera metadati da Open FIGI API usando ISIN
        Ritorna dizionario con nome, ticker, exchange, etc.
        """
        try:
            url = f"{self.figi_base_url}/mapping"
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Open FIGI richiede array di richieste
            payload = [{
                "idType": "ID_ISIN",
                "idValue": isin
            }]
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and len(data[0].get('data', [])) > 0:
                    figi_data = data[0]['data'][0]  # Prendi il primo risultato
                    
                    return {
                        'name': figi_data.get('name', ''),
                        'ticker': figi_data.get('ticker', ''),
                        'exchange': figi_data.get('exchCode', ''),
                        'market_sector': figi_data.get('marketSector', ''),
                        'security_type': figi_data.get('securityType', ''),
                        'figi': figi_data.get('figi', ''),
                        'composite_figi': figi_data.get('compositeFIGI', '')
                    }
        except Exception as e:
            print(f"Errore recupero metadati Open FIGI per {isin}: {e}")
        
        return {}
    
    def add_fund_by_isin(self, isin: str, auto_fetch_metadata: bool = True) -> Dict:
        """
        Aggiunge un fondo per ISIN, opzionalmente fetcha metadati da Open FIGI
        
        Args:
            isin: Codice ISIN del fondo
            auto_fetch_metadata: Se True, recupera metadati da Open FIGI
        
        Returns:
            Dict con informazioni del fondo
        """
        if auto_fetch_metadata:
            metadata = self._fetch_metadata_from_figi(isin)
            
            # Estrai nome dal metadata o usa ISIN
            name_short = metadata.get('name', '')
            if not name_short:
                name_short = f'Fondo {isin}'
            else:
                # Accorcia nome se troppo lungo
                if len(name_short) > 50:
                    name_short = name_short[:47] + '...'
            
            # Determina categoria dal market sector
            category = metadata.get('market_sector', '')
            if not category:
                category = metadata.get('security_type', '')
            
            fund_info = {
                'isin': isin,
                'name_short': name_short,
                'description': f"Fondo identificato tramite ISIN {isin}",
                'manager': '',  # Open FIGI non fornisce manager direttamente
                'category': category or 'Fondo',
                'ticker': metadata.get('ticker'),
                'exchange': metadata.get('exchange'),
                'figi': metadata.get('figi')
            }
        else:
            fund_info = {
                'isin': isin,
                'name_short': f'Fondo {isin}',
                'description': '',
                'manager': '',
                'category': '',
                'ticker': None,
                'exchange': None,
                'figi': None
            }
        
        return fund_info
    
    def add_funds_from_list(self, isin_list: List[str], auto_fetch_metadata: bool = True) -> Dict:
        """
        Aggiunge multiple fondi da lista ISIN
        
        Args:
            isin_list: Lista di codici ISIN
            auto_fetch_metadata: Se True, recupera metadati per ogni ISIN
        
        Returns:
            Dict con tutti i fondi aggiunti
        """
        funds = {}
        for isin in isin_list:
            isin = isin.strip()
            if not isin or len(isin) < 12:  # ISIN minimo 12 caratteri
                continue
            
            fund_info = self.add_fund_by_isin(isin, auto_fetch_metadata)
            # Usa name_short come chiave, ma se duplicato aggiungi ISIN
            key = fund_info['name_short']
            if key in funds:
                key = f"{fund_info['name_short']} ({isin})"
            
            funds[key] = fund_info
        
        return funds
    
    def load_funds_from_file(self, filepath: str, auto_fetch_metadata: bool = True) -> Dict:
        """
        Carica fondi da file (txt con ISIN o JSON)
        
        Args:
            filepath: Percorso del file (txt o json)
            auto_fetch_metadata: Se True, recupera metadati per ISIN
        
        Returns:
            Dict con configurazione fondi
        """
        if not os.path.exists(filepath):
            print(f"File non trovato: {filepath}")
            return {}
        
        if filepath.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                isins = [line.strip() for line in f 
                        if line.strip() and not line.strip().startswith('#')]
            return self.add_funds_from_list(isins, auto_fetch_metadata)
        elif filepath.endswith('.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Errore caricamento JSON {filepath}: {e}")
                return {}
        else:
            print(f"Formato file non supportato: {filepath}")
            return {}
    
    def save_funds_to_json(self, funds: Dict, filepath: str):
        """
        Salva configurazione fondi in file JSON
        
        Args:
            funds: Dict con configurazione fondi
            filepath: Percorso file di output
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(funds, f, indent=2, ensure_ascii=False)
            print(f"Fondi salvati in {filepath}")
        except Exception as e:
            print(f"Errore salvataggio {filepath}: {e}")
