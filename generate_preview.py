"""
Genera un report HTML di preview con dati di test
Per vedere come appare il report con le correzioni applicate
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_processor import DataProcessor
from visualizer import Visualizer

def create_mock_funds_data():
    """Crea dati mock per 3 fondi di esempio"""

    # Date comuni (ultimi 2 anni)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')

    funds_data = {}

    # Fondo 1: US Mutual Fund (Adj Close - nessun doppio conteggio)
    np.random.seed(42)
    prices_us = 100 * (1 + 0.12/365) ** np.arange(len(dates))  # 12% annuo
    prices_us = prices_us * (1 + np.random.randn(len(dates)) * 0.015)

    funds_data['T. Rowe Price Health Sciences'] = {
        'isin': 'US87281Y1029',
        'name_short': 'T. Rowe Price Health Sciences',
        'historical_data': pd.DataFrame({
            'Price': prices_us,
            'Dividends': 0.0,  # ✅ CORRETTO: Adj Close
            'Capital Gains': 0.0,
            '_is_adjusted': True
        }, index=dates),
        'composition': {
            'sectors': {
                'Healthcare': 95.0,
                'Biotechnology': 5.0
            },
            'top_holdings': []
        }
    }

    # Fondo 2: Fondo EU - Performance superiore
    np.random.seed(43)
    prices_eu1 = 100 * (1 + 0.15/365) ** np.arange(len(dates))  # 15% annuo
    prices_eu1 = prices_eu1 * (1 + np.random.randn(len(dates)) * 0.018)

    # Dividendi trimestrali
    dividends_eu1 = np.zeros(len(dates))
    for i in range(0, len(dates), 90):
        if i > 0:
            dividends_eu1[i] = prices_eu1[i] * 0.006  # 0.6% quarterly

    funds_data['BlackRock World Healthscience'] = {
        'isin': 'LU1960219225',
        'name_short': 'BlackRock World Healthscience',
        'historical_data': pd.DataFrame({
            'Price': prices_eu1,
            'Dividends': dividends_eu1,  # Dividendi separati
            'Capital Gains': 0.0,
            '_is_adjusted': False
        }, index=dates),
        'composition': {
            'sectors': {
                'Pharmaceuticals': 60.0,
                'Biotechnology': 25.0,
                'Medical Devices': 15.0
            },
            'top_holdings': []
        }
    }

    # Fondo 3: Fondo EU - Performance media
    np.random.seed(44)
    prices_eu2 = 100 * (1 + 0.09/365) ** np.arange(len(dates))  # 9% annuo
    prices_eu2 = prices_eu2 * (1 + np.random.randn(len(dates)) * 0.012)

    # Dividendi semestrali
    dividends_eu2 = np.zeros(len(dates))
    for i in range(0, len(dates), 180):
        if i > 0:
            dividends_eu2[i] = prices_eu2[i] * 0.008  # 0.8% semiannual

    funds_data['Fidelity Global Healthcare'] = {
        'isin': 'LU2078916223',
        'name_short': 'Fidelity Global Healthcare',
        'historical_data': pd.DataFrame({
            'Price': prices_eu2,
            'Dividends': dividends_eu2,
            'Capital Gains': 0.0,
            '_is_adjusted': False
        }, index=dates),
        'composition': {
            'sectors': {
                'Healthcare Services': 40.0,
                'Pharmaceuticals': 35.0,
                'Biotechnology': 25.0
            },
            'top_holdings': []
        }
    }

    return funds_data

def generate_preview_report():
    """Genera report HTML di preview"""

    print("=" * 70)
    print("GENERAZIONE PREVIEW REPORT HTML")
    print("=" * 70)

    # Crea dati mock
    print("\n📊 Creazione dati di esempio...")
    funds_data = create_mock_funds_data()
    print(f"✓ {len(funds_data)} fondi creati")

    # Processa i dati
    print("\n📈 Elaborazione dati...")
    processor = DataProcessor()
    processed_data = processor.process_all_funds(funds_data)
    print(f"✓ Dati elaborati per {len(processed_data)} fondi")

    # Mostra metriche
    print("\n📊 Metriche calcolate:")
    print("-" * 70)
    for fund_name, fund_data in processed_data.items():
        metrics = fund_data['metrics']
        print(f"\n{fund_name}:")
        print(f"  Total Return: {metrics['total_return']:.2f}%")
        print(f"  Annualized Return: {metrics['annualized_return']:.2f}%")
        print(f"  Volatility: {metrics['volatility']:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")

    # Crea DataFrame di comparazione
    print("\n📊 Creazione DataFrame di comparazione...")
    comparison_df = processor.create_comparison_dataframe(processed_data)
    print(f"✓ DataFrame creato: {len(comparison_df)} righe, {len(comparison_df.columns)} colonne")

    # Genera visualizzazione
    print("\n🎨 Generazione report HTML...")
    visualizer = Visualizer()

    # Usa output_dir e template dalla config
    import config
    import os
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # Path del template
    template_path = os.path.join(config.TEMPLATES_DIR, 'report_template.html')

    # Genera HTML
    html_content = visualizer.generate_full_report(
        comparison_df=comparison_df,
        processed_data=processed_data,
        template_path=template_path
    )

    # Salva file
    output_file = os.path.join(config.OUTPUT_DIR, "preview_report.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Report generato: {output_file}")

    # Verifica file
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"✓ File creato con successo ({file_size:,} bytes)")
        print(f"\n📄 Percorso completo: {os.path.abspath(output_file)}")
        print("\n" + "=" * 70)
        print("✅ PREVIEW GENERATA CON SUCCESSO!")
        print("=" * 70)
        print("\nPer visualizzare il report:")
        print(f"  - Apri il file: {output_file}")
        print("  - Oppure esegui: xdg-open {output_file}")
        print("\nNOTA: Questo è un report di ESEMPIO con dati simulati.")
        print("      Le correzioni ai calcoli ISIN sono già applicate.")
        print("=" * 70)
    else:
        print("❌ ERRORE: File non creato")

    return output_file

if __name__ == "__main__":
    generate_preview_report()
