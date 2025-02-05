#!/usr/bin/python
import pandas as pd
from jinja2 import Template

# Funzione per leggere il CSV e fare le elaborazioni richieste
def generate_expense_report(csv_file, category_max_spend, output_html_file):
    # Carica il CSV in un DataFrame
    df = pd.read_csv(csv_file, sep=';', dtype={'Spesa': str})  # Legge "Spesa" come stringa per sicurezza
    df['Spesa'] = df['Spesa'].str.replace(',', '.').astype(float)  # Converte "Spesa" in float

    
    # Calcola la somma per categoria (Colonna F: Categoria, Colonna E: Spesa)
    expenses_by_category = df.groupby('Categoria')['Spesa'].sum().reset_index()

    # Aggiungi una colonna per indicare se il tetto massimo è stato raggiunto
    print(f"{expenses_by_category['Spesa']}")
    expenses_by_category['Tetto raggiunto'] = expenses_by_category['Spesa'] >= expenses_by_category['Categoria'].map(category_max_spend)

    # Carica il template HTML
    html_template = """
    <html>
    <head>
        <title>Report Spese</title>
        <style>
            body { font-family: Arial, sans-serif; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .tetto-raggiunto { background-color: #f8d7da; }
        </style>
    </head>
    <body>
        <h1>Report Spese per Categoria</h1>
        <table>
            <tr>
                <th>Categoria</th>
                <th>Spesa Totale</th>
                <th>Tetto Raggiunto</th>
            </tr>
            {% for row in expenses %}
            <tr class="{% if row['Tetto raggiunto'] %}tetto-raggiunto{% endif %}">
                <td>{{ row['Categoria'] }}</td>
                <td>{{ row['Spesa'] }}</td>
                <td>{{ 'Sì' if row['Tetto raggiunto'] else 'No' }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    
    # Crea il template con Jinja2
    template = Template(html_template)
    html_content = template.render(expenses=expenses_by_category.to_dict(orient='records'))
    
    # Scrivi il report HTML su un file
    with open(output_html_file, 'w') as f:
        f.write(html_content)
    print(f"Report generato con successo in {output_html_file}")

# Esempio di utilizzo
category_max_spend = {
    'Alimentari': 1000,  # esempio di tetto massimo per categoria
    'Trasporti': 500,
    'Svago': 300
}

generate_expense_report('Conto.csv', category_max_spend, 'report_spese.html')

