import pandas as pd
from jinja2 import Template
import os
from datetime import datetime


# Funzione per leggere il CSV e generare il report

def generate_expense_reports(csv_file, category_max_spend):
    # Carica il CSV in un DataFrame
    df = pd.read_csv(csv_file, sep=';', dtype={'Spesa': str, 'Entrate': str}, encoding='utf-8')  # Legge come stringa
    df.columns = df.columns.str.strip()
    df['Spesa'] = df['Spesa'].str.replace(',', '.').astype(float)  # Converte "Spesa" in float
    df['Entrate'] = df['Entrate'].str.replace(',', '.').astype(float)  # Converte "Entrate" in float
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y')  # Converte la colonna Data in formato datetime

    # Determina il valore effettivo della transazione
    df['Valore'] = df.apply(lambda row: row['Entrate'] if row['Entrate'] > 0 else row['Spesa'], axis=1)
    df['Tipo'] = df.apply(lambda row: 'Entrata' if row['Entrate'] > 0 else 'Spesa', axis=1)

    # Genera un report per ogni mese disponibile
    for (year, month), month_df in df.groupby([df['Data'].dt.year, df['Data'].dt.month]):
        month_name = datetime(year, month, 1).strftime('%B').upper()
        file_name = f"report_{str(year)[-2:]}-{month:02d}-{month_name}.html"

        month_df = month_df.copy()
        expenses_by_category = month_df.groupby(['Tipo', 'Categoria'])[['Valore']].sum().reset_index()

        # Aggiungi colonne per tetto massimo e percentuale
        expenses_by_category['Budget'] = expenses_by_category['Categoria'].map(category_max_spend).fillna(float('inf'))
        expenses_by_category['Percentuale'] = (expenses_by_category['Valore'] / expenses_by_category['Budget']) * 100

        # Ordina per tipo e valore decrescente
        expenses_by_category = expenses_by_category.sort_values(by=['Tipo', 'Valore'], ascending=[True, False])

        bilancio = expenses_by_category.groupby('Tipo')[['Valore']].sum()
        saldo_finale = bilancio['Valore'].sum()

        expenses_by_category['Valore'] = expenses_by_category['Valore'].apply(lambda x: f"&euro; {x:.2f}")
        expenses_by_category['Budget'] = expenses_by_category['Budget'].apply(lambda x: f"&euro; {x:.2f}")
        expenses_by_category['Percentuale'] = expenses_by_category['Percentuale'].apply(lambda x: f"{x:.2f}%")

        detailed_expenses = {}
        for categoria in month_df['Categoria'].unique():
            categoria_df = month_df[month_df['Categoria'] == categoria].sort_values(by='Spesa', ascending=False)
            total_spesa = categoria_df['Spesa'].sum()

            categoria_df['Evidenziata'] = categoria_df['Spesa'].cumsum() > category_max_spend.get(categoria,
                                                                                                  float('inf'))
            categoria_df['Spesa'] = categoria_df['Spesa'].apply(lambda x: f"- &euro; {x:.2f}")

            detailed_expenses[categoria] = {
                'spese': categoria_df[['Note', 'Spesa', 'Evidenziata']].to_dict(orient='records'),
                'total_spesa': f"&euro; {total_spesa:.2f}"}

        html_template = """
        <html>
        <head>
            <title>Report Spese</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 10px; padding: 10px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .negative { color: #d9534f; }
                .saldo-finale { background-color: #cce5ff; font-weight: bold; }
                .entrata { background-color: #ccffcc; }
                .highlight { background-color: #ffcccc; }
            </style>
        </head>
        <body>
            <h1>Report Spese per Categoria</h1>
            <table>
                <tr>
                    <th>Categoria</th>
                    <th>Totale</th>
                    <th>Budget</th>
                    <th>Percentuale</th>
                </tr>
                {% for row in expenses %}
                <tr class="{{ 'entrata' if row['Tipo'] == 'Entrata' else '' }}">
                    <td>{{ row['Categoria'] }}</td>
                    <td>{{ row['Valore'] }}</td>
                    <td>{{ row['Budget'] }}</td>
                    <td>{{ row['Percentuale'] }}</td>
                </tr>
                {% endfor %}
                <tr class="saldo-finale">
                    <td>Bilancio</td>
                    <td colspan="3">{{ saldo_finale }}</td>
                </tr>
            </table>
            <h2>Dettaglio Spese per Categoria</h2>
            {% for categoria, info in detailed_expenses.items() %}
                <h3>{{ categoria }} - Totale: {{ info['total_spesa'] }}</h3>
                <table>
                    <tr>
                        <th>Note</th>
                        <th>Spesa</th>
                    </tr>
                    {% for row in info['spese'] %}
                    <tr class="{{ 'highlight' if row['Evidenziata'] else '' }}">
                        <td>{{ row['Note'] }}</td>
                        <td class="negative">{{ row['Spesa'] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            {% endfor %}
        </body>
        </html>
        """

        template = Template(html_template)
        html_content = template.render(expenses=expenses_by_category.to_dict(orient='records'),
                                       detailed_expenses=detailed_expenses, saldo_finale=f"&euro; {saldo_finale:.2f}")

        with open(file_name, 'w') as f:
            f.write(html_content)
        print(f"Report generato con successo in {file_name}")


category_max_spend = {'Spese fisse': 1090,
                      'Risparmi': 402,
                      'Alimentari': 38,
                      'Trasporti': 260,
                      'Svago': 160,
                      'Extra': 100}
generate_expense_reports('Conto.csv', category_max_spend)
