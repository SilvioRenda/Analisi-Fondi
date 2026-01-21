"""
Modulo per la generazione di grafici interattivi
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Optional, List
import json
from datetime import datetime


class Visualizer:
    """Genera visualizzazioni interattive per i fondi"""
    
    def __init__(self):
        # Colori base: blu, rosso, arancione
        self.base_colors = {
            'blue': '#1a365d',      # Blu scuro istituzionale
            'red': '#dc2626',       # Rosso scuro istituzionale
            'orange': '#ed8936'     # Arancione scuro istituzionale
        }
        
        # Palette completa: blu, rosso, arancione e derivati
        self.colors = [
            '#1a365d',  # Blu scuro istituzionale
            '#2c5282',  # Blu medio
            '#3182ce',  # Blu chiaro
            '#4299e1',  # Blu cielo
            '#63b3ed',  # Blu chiaro cielo
            '#90cdf4',  # Blu molto chiaro
            '#ed8936',  # Arancione scuro istituzionale
            '#f6ad55',  # Arancione medio
            '#fbbf24',  # Arancione chiaro
            '#fcd34d',  # Giallo arancione
            '#dc2626',  # Rosso scuro istituzionale
            '#ef4444',  # Rosso medio
            '#f87171',  # Rosso chiaro
            '#fca5a5',  # Rosso molto chiaro
            '#991b1b',  # Rosso molto scuro
            '#7f1d1d'   # Rosso quasi nero
        ]
    
    def get_colors_for_chart(self, num_items: int) -> list:
        """
        Seleziona colori appropriati in base al numero di elementi da visualizzare.
        
        Per pochi elementi (<= 5): usa colori molto diversi (blu, grigio, arancione)
        Per molti elementi (> 5): usa colori della stessa famiglia (varie tonalità)
        
        Args:
            num_items: Numero di elementi da visualizzare
            
        Returns:
            Lista di colori hex
        """
        if num_items <= 5:
            # Per pochi elementi, usa colori molto diversi
            # Ordine: blu scuro, arancione, rosso scuro, blu medio, arancione chiaro
            distinct_colors = [
                '#1a365d',  # Blu scuro istituzionale
                '#ed8936',  # Arancione scuro istituzionale
                '#dc2626',  # Rosso scuro istituzionale
                '#2c5282',  # Blu medio
                '#f6ad55'   # Arancione medio
            ]
            return distinct_colors[:num_items]
        else:
            # Per molti elementi, usa la palette completa con tutte le tonalità
            # Ripeti la palette se necessario
            return self.colors * ((num_items // len(self.colors)) + 1)
    
    def create_performance_chart(self, comparison_df: pd.DataFrame, 
                                processed_data: Dict) -> str:
        """
        Crea grafico interattivo delle performance normalizzate in base 100
        Restituisce HTML come stringa
        """
        if comparison_df.empty:
            return "<p>Nessun dato disponibile per la visualizzazione</p>"
        
        fig = go.Figure()
        
        # Colori per ogni fondo - usa funzione intelligente
        num_funds = len(comparison_df.columns)
        colors_list = self.get_colors_for_chart(num_funds)
        
        for i, fund_name in enumerate(comparison_df.columns):
            fund_data = comparison_df[fund_name].dropna()
            
            if len(fund_data) > 0:
                # Trova il nome completo del fondo
                full_name = fund_name
                for key, value in processed_data.items():
                    if value.get('name_short') == fund_name:
                        full_name = key
                        break
                
                # Aggiungi traccia
                fig.add_trace(go.Scatter(
                    x=fund_data.index,
                    y=fund_data.values,
                    mode='lines',
                    name=fund_name,
                    hovertemplate=(
                        '<b>%{fullData.name}</b><br>' +
                        'Data: %{x|%d/%m/%Y}<br>' +
                        'Valore: %{y:.2f}<br>' +
                        '<extra></extra>'
                    ),
                    line=dict(
                        color=colors_list[i],
                        width=2
                    )
                ))
        
        # Layout
        fig.update_layout(
            title={
                'text': 'Confronto Performance Fondi Healthcare (Base 100)',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_title='Data',
            yaxis_title='Valore Normalizzato (Base 100)',
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            height=600,
            template='plotly_white',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )
        )
        
        # Converti in HTML
        html_str = fig.to_html(include_plotlyjs='cdn', div_id='performance-chart')
        return html_str
    
    def create_metrics_table(self, processed_data: Dict) -> str:
        """
        Crea tabella HTML con le metriche comparative
        """
        table_rows = []
        
        # Verifica se almeno un fondo ha Beta
        has_beta = any(fund_data.get('metrics', {}).get('beta') is not None 
                      for fund_data in processed_data.values())
        
        # Header
        table_rows.append('<thead><tr>')
        table_rows.append('<th>Fondo</th>')
        table_rows.append('<th>Return Totale (%)</th>')
        table_rows.append('<th>Return Annualizzato (%)</th>')
        table_rows.append('<th>Volatilità (%)</th>')
        table_rows.append('<th>Sharpe Ratio</th>')
        if has_beta:
            table_rows.append('<th>Beta</th>')
        table_rows.append('<th>Max Drawdown (%)</th>')
        table_rows.append('</tr></thead>')
        
        # Body
        table_rows.append('<tbody>')
        for fund_name, fund_data in processed_data.items():
            metrics = fund_data.get('metrics', {})
            name_short = fund_data.get('name_short', fund_name)
            
            table_rows.append('<tr>')
            table_rows.append(f'<td><strong>{name_short}</strong></td>')
            table_rows.append(f'<td>{metrics.get("total_return", "N/A")}</td>')
            table_rows.append(f'<td>{metrics.get("annualized_return", "N/A")}</td>')
            table_rows.append(f'<td>{metrics.get("volatility", "N/A")}</td>')
            table_rows.append(f'<td>{metrics.get("sharpe_ratio", "N/A")}</td>')
            if has_beta:
                beta = metrics.get("beta", "N/A")
                benchmark = metrics.get("benchmark", "")
                if beta != "N/A" and benchmark:
                    table_rows.append(f'<td>{beta} (vs {benchmark})</td>')
                else:
                    table_rows.append(f'<td>{beta}</td>')
            table_rows.append(f'<td>{metrics.get("max_drawdown", "N/A")}</td>')
            table_rows.append('</tr>')
        table_rows.append('</tbody>')
        
        table_html = f'''
        <div class="metrics-table">
            <h2>Metriche Comparative</h2>
            <table class="table table-striped table-hover">
                {''.join(table_rows)}
            </table>
        </div>
        '''
        return table_html
    
    def create_funds_description_section(self, processed_data: Dict) -> str:
        """
        Crea sezione HTML con descrizione dei fondi
        """
        import config
        
        description_html = ['<div class="funds-description-section">']
        
        for fund_name, fund_data in processed_data.items():
            # Recupera info dal config
            fund_info = config.FUNDS.get(fund_name, {})
            name_short = fund_data.get('name_short', fund_name)
            isin = fund_data.get('isin', 'N/A')
            manager = fund_info.get('manager', 'N/A')
            category = fund_info.get('category', 'N/A')
            
            # Priorità 1: Descrizione dettagliata recuperata da multiple fonti
            description = fund_data.get('description')
            description_source = fund_data.get('description_source', '')
            
            # Priorità 2: Descrizione dal config (se non abbiamo descrizione dettagliata)
            if not description:
                description = fund_info.get('description', '')
            
            # Priorità 3: Genera descrizione generica se ancora non disponibile
            if not description or description == 'Descrizione non disponibile':
                # Determina tipo basandosi sul nome e ISIN
                name_lower = fund_name.lower()
                name_short_lower = name_short.lower() if name_short else ''
                
                # Controlla se è un indice/ETF
                if any(indice in name_lower or indice in name_short_lower for indice in 
                       ['s&p', 'sp500', 'nasdaq', 'qqq', 'russell', 'euro stoxx', 'ezu', 'iwm', 'spy']):
                    description = f"Indice/ETF che replica la performance di {name_short}. Strumento finanziario quotato che permette di investire in un paniere diversificato di titoli."
                # Controlla se è un titolo azionario (ISIN è un ticker breve, non un ISIN standard)
                elif isin and len(isin) <= 5 and isin.isalpha():
                    description = f"Titolo azionario quotato. {name_short} è una società quotata sui mercati finanziari."
                # Controlla se è un fondo comune (ISIN standard)
                elif isin and len(isin) >= 12:
                    description = f"Fondo comune di investimento identificato tramite ISIN {isin}. {name_short} è un veicolo di investimento collettivo."
                else:
                    description = f"Strumento finanziario: {name_short}. Informazioni dettagliate disponibili tramite ISIN {isin}."
            
            description_html.append('<div class="fund-description">')
            description_html.append(f'<h3>{name_short}</h3>')
            description_html.append(f'<div class="fund-info">')
            description_html.append(f'<p><strong>Nome Completo:</strong> {fund_name}</p>')
            description_html.append(f'<p><strong>ISIN:</strong> {isin}</p>')
            description_html.append(f'<p><strong>Gestore:</strong> {manager}</p>')
            description_html.append(f'<p><strong>Categoria:</strong> {category}</p>')
            if description_source:
                description_html.append(f'<p><strong>Fonte descrizione:</strong> {description_source}</p>')
            description_html.append('</div>')
            description_html.append(f'<div class="fund-description-text">')
            description_html.append(f'<p>{description}</p>')
            description_html.append('</div>')
            description_html.append('</div>')
            description_html.append('<hr>')
        
        description_html.append('</div>')
        return ''.join(description_html)
    
    def create_sector_analysis_section(self, processed_data: Dict, comparison_df: pd.DataFrame) -> str:
        """
        Crea sezione HTML con analisi settoriale dettagliata
        Confronta fondi/titoli dello stesso settore
        
        Args:
            processed_data: Dizionario con dati processati dei fondi
            comparison_df: DataFrame con dati comparativi normalizzati
            
        Returns:
            HTML della sezione analisi settoriale
        """
        from data_processor import DataProcessor
        
        processor = DataProcessor()
        sectors = processor.group_by_sector(processed_data)
        
        if not sectors:
            return ''  # Nessun settore con almeno 2 fondi
        
        sector_html = ['<div class="sector-analysis-section">']
        sector_html.append('<h2>Analisi Settoriale</h2>')
        
        for sector, fund_names in sectors.items():
            if len(fund_names) < 2:
                continue  # Salta settori con meno di 2 fondi
            
            sector_html.append(f'<div class="sector-group">')
            sector_html.append(f'<h3>Settore: {sector}</h3>')
            
            # Filtra DataFrame per questo settore
            sector_funds = [name for name in fund_names if name in comparison_df.columns]
            if len(sector_funds) < 2:
                continue
            
            sector_df = comparison_df[sector_funds]
            
            # Crea grafico per questo settore
            sector_chart = self._create_sector_chart(sector_df, processed_data, sector)
            sector_html.append('<div class="sector-chart-container">')
            sector_html.append(sector_chart)
            sector_html.append('</div>')
            
            # Crea tabella metriche per questo settore
            sector_table = self._create_sector_metrics_table(sector_funds, processed_data)
            sector_html.append(sector_table)
            
            sector_html.append('</div>')
            sector_html.append('<hr>')
        
        sector_html.append('</div>')
        return ''.join(sector_html)
    
    def _create_sector_chart(self, sector_df: pd.DataFrame, processed_data: Dict, sector_name: str) -> str:
        """
        Crea grafico Plotly per un settore specifico
        """
        if sector_df.empty:
            return "<p>Nessun dato disponibile per questo settore</p>"
        
        fig = go.Figure()
        
        num_funds = len(sector_df.columns)
        colors_list = self.get_colors_for_chart(num_funds)
        
        for i, fund_name in enumerate(sector_df.columns):
            fund_data = sector_df[fund_name].dropna()
            
            if len(fund_data) > 0:
                fig.add_trace(go.Scatter(
                    x=fund_data.index,
                    y=fund_data.values,
                    mode='lines',
                    name=fund_name,
                    hovertemplate=(
                        '<b>%{fullData.name}</b><br>' +
                        'Data: %{x|%d/%m/%Y}<br>' +
                        'Valore: %{y:.2f}<br>' +
                        '<extra></extra>'
                    ),
                    line=dict(
                        color=colors_list[i],
                        width=2
                    )
                ))
        
        fig.update_layout(
            title={
                'text': f'Confronto Performance - {sector_name} (Base 100)',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            xaxis_title='Data',
            yaxis_title='Valore Normalizzato (Base 100)',
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            height=500,
            template='plotly_white',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )
        )
        
        return fig.to_html(include_plotlyjs=False, div_id=f'sector-chart-{sector_name.lower().replace(" ", "-")}')
    
    def _create_sector_metrics_table(self, fund_names: List[str], processed_data: Dict) -> str:
        """
        Crea tabella metriche per fondi di un settore
        """
        table_rows = []
        
        # Header
        table_rows.append('<thead><tr>')
        table_rows.append('<th>Fondo</th>')
        table_rows.append('<th>Return Totale (%)</th>')
        table_rows.append('<th>Return Annualizzato (%)</th>')
        table_rows.append('<th>Volatilità (%)</th>')
        table_rows.append('<th>Sharpe Ratio</th>')
        table_rows.append('<th>Max Drawdown (%)</th>')
        table_rows.append('</tr></thead>')
        
        # Body
        table_rows.append('<tbody>')
        for fund_name in fund_names:
            if fund_name in processed_data:
                fund_data = processed_data[fund_name]
                metrics = fund_data.get('metrics', {})
                name_short = fund_data.get('name_short', fund_name)
                
                table_rows.append('<tr>')
                table_rows.append(f'<td><strong>{name_short}</strong></td>')
                table_rows.append(f'<td>{metrics.get("total_return", "N/A")}</td>')
                table_rows.append(f'<td>{metrics.get("annualized_return", "N/A")}</td>')
                table_rows.append(f'<td>{metrics.get("volatility", "N/A")}</td>')
                table_rows.append(f'<td>{metrics.get("sharpe_ratio", "N/A")}</td>')
                table_rows.append(f'<td>{metrics.get("max_drawdown", "N/A")}</td>')
                table_rows.append('</tr>')
        table_rows.append('</tbody>')
        
        table_html = f'''
        <div class="sector-metrics-table">
            <table class="table table-striped table-hover">
                {''.join(table_rows)}
            </table>
        </div>
        '''
        return table_html
    
    def create_executive_summary(self, processed_data: Dict, comparison_df: pd.DataFrame) -> str:
        """
        Crea sezione Executive Summary con sintesi performance
        
        Args:
            processed_data: Dizionario con dati processati dei fondi
            comparison_df: DataFrame con dati comparativi normalizzati
            
        Returns:
            HTML della sezione executive summary
        """
        if not processed_data or comparison_df.empty:
            return ''
        
        summary_html = ['<div class="executive-summary-section">']
        summary_html.append('<h2>Executive Summary</h2>')
        
        # Trova migliori e peggiori performer
        final_values = {}
        for fund_name in comparison_df.columns:
            series = comparison_df[fund_name].dropna()
            if len(series) > 0:
                final_values[fund_name] = series.iloc[-1]
        
        if final_values:
            sorted_funds = sorted(final_values.items(), key=lambda x: x[1], reverse=True)
            best_fund = sorted_funds[0][0]
            worst_fund = sorted_funds[-1][0]
            
            best_data = processed_data.get(best_fund, {})
            worst_data = processed_data.get(worst_fund, {})
            best_metrics = best_data.get('metrics', {})
            worst_metrics = worst_data.get('metrics', {})
            
            summary_html.append('<div class="summary-highlights">')
            
            # Highlight 1: Miglior performer
            best_name = best_data.get('name_short', best_fund)
            best_return = best_metrics.get('annualized_return', 'N/A')
            summary_html.append('<div class="highlight-box highlight-best">')
            summary_html.append(f'<h4>Miglior Performer</h4>')
            summary_html.append(f'<p><strong>{best_name}</strong></p>')
            summary_html.append(f'<p>Return Annualizzato: {best_return}%</p>')
            summary_html.append('</div>')
            
            # Highlight 2: Peggior performer
            worst_name = worst_data.get('name_short', worst_fund)
            worst_return = worst_metrics.get('annualized_return', 'N/A')
            summary_html.append('<div class="highlight-box highlight-worst">')
            summary_html.append(f'<h4>Peggior Performer</h4>')
            summary_html.append(f'<p><strong>{worst_name}</strong></p>')
            summary_html.append(f'<p>Return Annualizzato: {worst_return}%</p>')
            summary_html.append('</div>')
            
            # Highlight 3: Media settore
            all_returns = [m.get('annualized_return', 0) for f, m in 
                          [(f, processed_data.get(f, {}).get('metrics', {})) 
                           for f in final_values.keys()] 
                          if isinstance(m.get('annualized_return'), (int, float))]
            if all_returns:
                avg_return = sum(all_returns) / len(all_returns)
                summary_html.append('<div class="highlight-box highlight-avg">')
                summary_html.append(f'<h4>Media Settore</h4>')
                summary_html.append(f'<p>Return Annualizzato Medio: {avg_return:.2f}%</p>')
                summary_html.append(f'<p>Fondi Analizzati: {len(final_values)}</p>')
                summary_html.append('</div>')
            
            summary_html.append('</div>')
        
        # Punti chiave (3-5 highlights)
        summary_html.append('<div class="key-points">')
        summary_html.append('<h3>Punti Chiave</h3>')
        summary_html.append('<ul>')
        
        # Punto 1: Periodo analizzato
        if not comparison_df.empty:
            start_date = comparison_df.index[0]
            end_date = comparison_df.index[-1]
            days = (end_date - start_date).days
            years = days / 365.25
            summary_html.append(f'<li>Analisi su periodo di {years:.1f} anni ({start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")})</li>')
        
        # Punto 2: Numero fondi
        summary_html.append(f'<li>{len(processed_data)} strumenti finanziari analizzati</li>')
        
        # Punto 3: Volatilità media
        volatilities = [m.get('volatility', 0) for f, m in 
                       [(f, processed_data.get(f, {}).get('metrics', {})) 
                        for f in processed_data.keys()] 
                       if isinstance(m.get('volatility'), (int, float))]
        if volatilities:
            avg_vol = sum(volatilities) / len(volatilities)
            summary_html.append(f'<li>Volatilità media: {avg_vol:.2f}%</li>')
        
        # Punto 4: Sharpe ratio medio
        sharpe_ratios = [m.get('sharpe_ratio', 0) for f, m in 
                        [(f, processed_data.get(f, {}).get('metrics', {})) 
                         for f in processed_data.keys()] 
                        if isinstance(m.get('sharpe_ratio'), (int, float))]
        if sharpe_ratios:
            avg_sharpe = sum(sharpe_ratios) / len(sharpe_ratios)
            summary_html.append(f'<li>Sharpe Ratio medio: {avg_sharpe:.2f}</li>')
        
        summary_html.append('</ul>')
        summary_html.append('</div>')
        
        summary_html.append('</div>')
        return ''.join(summary_html)
    
    def create_instrument_manager_section(self, current_instruments: Dict = None) -> str:
        """
        Crea sezione HTML per gestione strumenti (aggiungi/rimuovi)
        
        Args:
            current_instruments: Dizionario con strumenti attuali (opzionale)
            
        Returns:
            HTML della sezione gestione strumenti
        """
        html = ['<div class="instrument-manager-section">']
        html.append('<h2>Gestione Strumenti da Analizzare</h2>')
        
        # Form aggiunta strumento
        html.append('<div class="add-instrument-form">')
        html.append('<h3>Aggiungi Strumento</h3>')
        html.append('<div class="form-group">')
        html.append('<label for="isin-input">ISIN o Ticker:</label>')
        html.append('<input type="text" id="isin-input" placeholder="Es: LU0097089360 o AAPL" class="form-input">')
        html.append('<button id="add-instrument-btn" class="btn-primary">Aggiungi</button>')
        html.append('</div>')
        html.append('<div id="add-instrument-status" class="status-message"></div>')
        html.append('</div>')
        
        # Lista strumenti attuali
        html.append('<div class="current-instruments">')
        html.append('<h3>Strumenti Attuali</h3>')
        html.append('<div id="instruments-list" class="instruments-list">')
        
        if current_instruments:
            for identifier, instrument in current_instruments.items():
                name = instrument.get('name_short', instrument.get('name', identifier))
                isin = instrument.get('isin', identifier)
                html.append(f'<div class="instrument-item" data-identifier="{identifier}">')
                html.append(f'<span class="instrument-name">{name}</span>')
                html.append(f'<span class="instrument-id">({isin})</span>')
                html.append(f'<button class="btn-remove" onclick="removeInstrument(\'{identifier}\')">Rimuovi</button>')
                html.append('</div>')
        else:
            html.append('<div class="empty-instruments"><p>Nessun strumento aggiunto. Aggiungi un ISIN o ticker per iniziare.</p></div>')
        
        html.append('</div>')
        html.append('<div class="instrument-actions">')
        html.append('<button id="clear-all-btn" class="btn-secondary">Rimuovi Tutti</button>')
        html.append('<button id="regenerate-btn" class="btn-primary">Rigenera Report</button>')
        html.append('</div>')
        html.append('</div>')
        
        html.append('</div>')
        return ''.join(html)
    
    def create_portfolio_analysis_section(self, processed_data: Dict, comparison_df: pd.DataFrame) -> str:
        """
        Crea sezione Analisi Portfolio con allocazione settoriale e metriche aggregate
        
        Args:
            processed_data: Dizionario con dati processati dei fondi
            comparison_df: DataFrame con dati comparativi normalizzati
            
        Returns:
            HTML della sezione analisi portfolio
        """
        try:
            from portfolio_analyzer import PortfolioAnalyzer
            
            analyzer = PortfolioAnalyzer()
            
            # Calcola returns per analisi portfolio
            returns_df = comparison_df.pct_change().dropna()
            
            # Metriche portfolio
            portfolio_metrics = analyzer.calculate_portfolio_metrics(returns_df)
            
            # Analisi allocazione settoriale
            sector_analysis = analyzer.sector_allocation_analysis(processed_data)
            
            html = ['<div class="portfolio-analysis-section">']
            html.append('<h2>Analisi Portfolio</h2>')
            
            # Metriche portfolio aggregate
            if portfolio_metrics:
                html.append('<div class="portfolio-metrics">')
                html.append('<h3>Metriche Portfolio Aggregate</h3>')
                html.append('<div class="metrics-grid">')
                html.append(f'<div class="metric-box"><strong>Return Portfolio:</strong> {portfolio_metrics.get("portfolio_return", "N/A")}%</div>')
                html.append(f'<div class="metric-box"><strong>Volatilità Portfolio:</strong> {portfolio_metrics.get("portfolio_volatility", "N/A")}%</div>')
                html.append(f'<div class="metric-box"><strong>Sharpe Ratio:</strong> {portfolio_metrics.get("portfolio_sharpe", "N/A")}</div>')
                html.append(f'<div class="metric-box"><strong>Diversification Ratio:</strong> {portfolio_metrics.get("diversification_ratio", "N/A")}</div>')
                html.append('</div>')
                html.append('</div>')
            
            # Allocazione settoriale
            if sector_analysis and sector_analysis.get('sector_weights'):
                html.append('<div class="sector-allocation">')
                html.append('<h3>Allocazione Settoriale</h3>')
                
                # Pie chart allocazione (HTML semplice, Plotly può essere aggiunto dopo)
                html.append('<div class="allocation-chart">')
                sector_weights = sector_analysis['sector_weights']
                for sector, weight in sector_weights.items():
                    html.append(f'<div class="allocation-item"><span class="sector-name">{sector}:</span> <span class="sector-weight">{weight}%</span></div>')
                html.append('</div>')
                
                # Concentration Risk
                if sector_analysis.get('concentration_risk'):
                    hhi = sector_analysis['concentration_risk']
                    html.append(f'<p><strong>Concentration Risk (HHI):</strong> {hhi}</p>')
                    if hhi < 1500:
                        html.append('<p class="risk-low">Portfolio ben diversificato</p>')
                    elif hhi < 2500:
                        html.append('<p class="risk-medium">Portfolio moderatamente concentrato</p>')
                    else:
                        html.append('<p class="risk-high">Portfolio concentrato</p>')
                
                html.append('</div>')
            
            html.append('</div>')
            return ''.join(html)
        except Exception as e:
            # Fallback: sezione vuota se errore
            return ''
    
    def create_technical_indicators_section(self, processed_data: Dict, comparison_df: pd.DataFrame) -> str:
        """
        Crea sezione Indicatori Tecnici
        
        Args:
            processed_data: Dizionario con dati processati dei fondi
            comparison_df: DataFrame con dati comparativi normalizzati
            
        Returns:
            HTML della sezione indicatori tecnici
        """
        try:
            from technical_indicators import TechnicalIndicators
            
            indicators_calc = TechnicalIndicators()
            
            html = ['<div class="technical-indicators-section">']
            html.append('<h2>Indicatori Tecnici</h2>')
            
            # Calcola indicatori per ogni fondo
            for fund_name, fund_data in processed_data.items():
                normalized = fund_data.get('normalized_data')
                if normalized is None or normalized.empty:
                    continue
                
                # Prepara DataFrame per indicatori
                price_df = pd.DataFrame({
                    'Price': normalized['Normalized_Value']
                })
                
                # Calcola indicatori
                indicators_df = indicators_calc.calculate_indicators(price_df)
                
                # Genera segnali
                signals_df = indicators_calc.generate_signals(indicators_df)
                
                if 'RSI' in indicators_df.columns:
                    html.append(f'<div class="fund-indicators">')
                    html.append(f'<h3>{fund_data.get("name_short", fund_name)}</h3>')
                    
                    # Ultimi valori indicatori
                    last_row = indicators_df.iloc[-1]
                    html.append('<div class="indicators-values">')
                    if pd.notna(last_row.get('RSI')):
                        html.append(f'<p><strong>RSI (14):</strong> {last_row["RSI"]:.2f}</p>')
                    if pd.notna(last_row.get('MACD')):
                        html.append(f'<p><strong>MACD:</strong> {last_row["MACD"]:.2f}</p>')
                    html.append('</div>')
                    
                    # Segnali
                    if 'buy_signal' in signals_df.columns:
                        last_signal = signals_df.iloc[-1]
                        if last_signal['buy_signal']:
                            html.append('<p class="signal-buy">Segnale: ACQUISTO</p>')
                        elif last_signal['sell_signal']:
                            html.append('<p class="signal-sell">Segnale: VENDITA</p>')
                        else:
                            html.append('<p class="signal-neutral">Segnale: NEUTRO</p>')
                    
                    html.append('</div>')
            
            html.append('</div>')
            return ''.join(html)
        except Exception as e:
            # Fallback: sezione vuota se errore
            return ''
    
    def create_advanced_metrics_section(self, processed_data: Dict) -> str:
        """
        Crea sezione Metriche Avanzate
        
        Args:
            processed_data: Dizionario con dati processati dei fondi
            
        Returns:
            HTML della sezione metriche avanzate
        """
        html = ['<div class="advanced-metrics-section">']
        html.append('<h2>Metriche Avanzate</h2>')
        
        # Verifica se ci sono metriche avanzate
        has_advanced = False
        for fund_data in processed_data.values():
            metrics = fund_data.get('metrics', {})
            if any(key in metrics for key in ['sortino_ratio', 'alpha', 'treynor_ratio']):
                has_advanced = True
                break
        
        if not has_advanced:
            html.append('<p>Metriche avanzate non disponibili. Installa FinanceToolkit per abilitarle.</p>')
            html.append('</div>')
            return ''.join(html)
        
        # Tabella metriche avanzate
        table_rows = []
        table_rows.append('<thead><tr>')
        table_rows.append('<th>Fondo</th>')
        table_rows.append('<th>Sortino Ratio</th>')
        table_rows.append('<th>Alpha</th>')
        table_rows.append('<th>Treynor Ratio</th>')
        table_rows.append('</tr></thead>')
        
        table_rows.append('<tbody>')
        for fund_name, fund_data in processed_data.items():
            metrics = fund_data.get('metrics', {})
            name_short = fund_data.get('name_short', fund_name)
            
            table_rows.append('<tr>')
            table_rows.append(f'<td><strong>{name_short}</strong></td>')
            table_rows.append(f'<td>{metrics.get("sortino_ratio", "N/A")}</td>')
            table_rows.append(f'<td>{metrics.get("alpha", "N/A")}</td>')
            table_rows.append(f'<td>{metrics.get("treynor_ratio", "N/A")}</td>')
            table_rows.append('</tr>')
        table_rows.append('</tbody>')
        
        table_html = f'''
        <div class="advanced-metrics-table">
            <table class="table table-striped table-hover">
                {''.join(table_rows)}
            </table>
        </div>
        '''
        
        html.append(table_html)
        html.append('</div>')
        return ''.join(html)
    
    def create_composition_section(self, processed_data: Dict) -> str:
        """
        Crea sezione HTML con composizione settoriale e top holdings
        """
        composition_html = ['<div class="composition-section"><h2>Composizione Fondi</h2>']
        
        for fund_name, fund_data in processed_data.items():
            composition = fund_data.get('composition', {})
            name_short = fund_data.get('name_short', fund_name)
            
            composition_html.append(f'<div class="fund-composition">')
            composition_html.append(f'<h3>{name_short}</h3>')
            
            # Settori
            sectors = composition.get('sectors', {})
            if sectors:
                composition_html.append('<h4>Allocazione Settoriale</h4>')
                composition_html.append('<ul>')
                for sector, percentage in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
                    composition_html.append(f'<li>{sector}: {percentage:.2f}%</li>')
                composition_html.append('</ul>')
            else:
                composition_html.append('<p><em>Dati di allocazione settoriale non disponibili</em></p>')
            
            # Top Holdings
            top_holdings = composition.get('top_holdings', [])
            if top_holdings and len(top_holdings) > 0:
                composition_html.append('<h4>Top Holdings</h4>')
                composition_html.append('<ul>')
                for holding in top_holdings[:10]:  # Primi 10
                    if isinstance(holding, dict):
                        name = holding.get('name', 'N/A')
                        weight = holding.get('weight', holding.get('percentHeld', 'N/A'))
                        composition_html.append(f'<li>{name}: {weight}%</li>')
                    elif isinstance(holding, str):
                        composition_html.append(f'<li>{holding}</li>')
                composition_html.append('</ul>')
            else:
                composition_html.append('<p><em>Dati di top holdings non disponibili</em></p>')
            
            # Nota informativa se non ci sono dati
            if not sectors and not top_holdings:
                data_source = composition.get('data_source', 'N/A')
                composition_html.append('<div class="data-note">')
                composition_html.append('<p><strong>Nota:</strong> I dati di composizione dettagliata non sono attualmente disponibili ')
                composition_html.append('tramite le fonti pubbliche utilizzate (Yahoo Finance). ')
                composition_html.append('Per informazioni complete su allocazione settoriale e top holdings, ')
                composition_html.append('si consiglia di consultare i documenti ufficiali del fondo ')
                composition_html.append('(KIID, prospetto informativo) o il sito web del gestore.</p>')
                composition_html.append('</div>')
            
            composition_html.append('</div>')
            composition_html.append('<hr>')
        
        composition_html.append('</div>')
        return ''.join(composition_html)
    
    def _serialize_data_for_javascript(self, comparison_df: pd.DataFrame, 
                                       processed_data: Dict) -> str:
        """
        Serializza dati raw per uso JavaScript client-side
        Crea struttura dati con date e valori per ogni fondo
        """
        if comparison_df.empty:
            return '{}'
        
        # Trova date min/max globali
        all_dates = comparison_df.index
        min_date = all_dates.min().strftime('%Y-%m-%d')
        max_date = all_dates.max().strftime('%Y-%m-%d')
        
        # Crea struttura dati per ogni fondo
        funds_data = {}
        for fund_name in comparison_df.columns:
            fund_series = comparison_df[fund_name].dropna()
            
            if len(fund_series) > 0:
                # Converti serie in lista di oggetti {date, value}
                data_points = []
                for date, value in fund_series.items():
                    data_points.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'value': float(value)
                    })
                
                funds_data[fund_name] = {
                    'data': data_points,
                    'min_date': fund_series.index.min().strftime('%Y-%m-%d'),
                    'max_date': fund_series.index.max().strftime('%Y-%m-%d'),
                    'dates': [d.strftime('%Y-%m-%d') for d in fund_series.index]
                }
        
        # Struttura completa
        data_structure = {
            'funds': funds_data,
            'global_min_date': min_date,
            'global_max_date': max_date,
            'base_value': 100
        }
        
        # Serializza come JSON
        return json.dumps(data_structure, indent=2)
    
    def generate_full_report(self, comparison_df: pd.DataFrame, 
                           processed_data: Dict, template_path: str) -> str:
        """
        Genera report HTML completo
        """
        # Carica template
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Genera componenti
        chart_html = self.create_performance_chart(comparison_df, processed_data)
        metrics_table = self.create_metrics_table(processed_data)
        funds_description = self.create_funds_description_section(processed_data)
        sector_analysis = self.create_sector_analysis_section(processed_data, comparison_df)
        executive_summary = self.create_executive_summary(processed_data, comparison_df)
        portfolio_analysis = self.create_portfolio_analysis_section(processed_data, comparison_df)
        technical_indicators = self.create_technical_indicators_section(processed_data, comparison_df)
        advanced_metrics = self.create_advanced_metrics_section(processed_data)
        
        # Serializza dati raw per JavaScript
        raw_data_json = self._serialize_data_for_javascript(comparison_df, processed_data)
        
        # Carica configurazione branding
        import config
        report_config = config.REPORT_CONFIG
        
        # Sostituisci placeholder nel template
        report = template.replace('{{PERFORMANCE_CHART}}', chart_html)
        report = report.replace('{{METRICS_TABLE}}', metrics_table)
        report = report.replace('{{FUNDS_DESCRIPTION}}', funds_description)
        report = report.replace('{{SECTOR_ANALYSIS}}', sector_analysis)
        report = report.replace('{{EXECUTIVE_SUMMARY}}', executive_summary)
        report = report.replace('{{PORTFOLIO_ANALYSIS}}', portfolio_analysis)
        report = report.replace('{{TECHNICAL_INDICATORS}}', technical_indicators)
        report = report.replace('{{ADVANCED_METRICS}}', advanced_metrics)
        report = report.replace('{{COMPOSITION_SECTION}}', '')  # Rimossa sezione composizione
        
        # Aggiungi sezione gestione strumenti solo se richiesto (modalità interattiva)
        # In modalità normale, lascia vuoto
        instrument_manager = ''
        report = report.replace('{{INSTRUMENT_MANAGER}}', instrument_manager)
        report = report.replace('{{RAW_DATA}}', raw_data_json)  # Aggiungi dati raw
        
        # Sostituisci placeholder branding
        report = report.replace('{{COMPANY_NAME}}', report_config.get('company_name', 'Analisi Fondi Healthcare'))
        report = report.replace('{{FOOTER_TEXT}}', report_config.get('footer_text', 'Report generato automaticamente'))
        report = report.replace('{{DISCLAIMER}}', report_config.get('disclaimer', ''))
        report = report.replace('{{ datetime }}', datetime.now().strftime('%d/%m/%Y %H:%M'))
        
        return report
