import requests
import pandas as pd

url_mad = "https://meteometrics.rlopez.org/historical-data/MAD"
url_lon = "https://meteometrics.rlopez.org/historical-data/LON"

try:
    # Realiza la petición para Madrid
    response = requests.get(url_mad)
    response.raise_for_status()
    raw_data_madrid = response.json()
    
    # Normalizar y añadir columna para Madrid
    df_madrid = pd.json_normalize(raw_data_madrid)
    df_madrid['city'] = 'Madrid'

    # Realiza la petición para Londres
    response = requests.get(url_lon)
    response.raise_for_status()
    raw_data_londres = response.json()
    
    # Normalizar y añadir columna para Londres
    df_londres = pd.json_normalize(raw_data_londres)
    df_londres['city'] = 'London'

    # Unificar datos en un solo dataframe
    df_final = pd.concat([df_madrid, df_londres], ignore_index=True)
    
    # Guardamos el conteo inicial para el informe
    n_inicial = len(df_final)

    # 1. Reemplazar comas por puntos en columnas de métricas (asegurando que sean tratadas como strings primero)
    cols_metricas = [c for c in df_final.columns if 'metrics.' in c and 'unit' not in c]
    df_final[cols_metricas] = df_final[cols_metricas].astype(str).replace(',', '.', regex=True)

    # 2 y 3. Identificar y convertir columnas numéricas (excepto las de unidades y la ciudad)
    # Usamos pd.to_numeric con errors='coerce' para transformar textos a float/int
    cols_excluidas = ['metrics.temperature.unit', 'metrics.precipitation.unit', 'city']
    cols_a_numericas = [c for c in df_final.columns if c not in cols_excluidas]
    df_final[cols_a_numericas] = df_final[cols_a_numericas].apply(pd.to_numeric, errors='coerce')

    # 4. Reemplazar valores centinela -999.0 por nulos (NaN)
    df_final = df_final.replace(-999.0, pd.NA)

    # 5. Eliminar duplicados por combinación de ciudad, año y mes
    df_final = df_final.drop_duplicates(subset=['city', 'year', 'month'])

    # 6. Ordenar cronológicamente
    df_final = df_final.sort_values(by=['city', 'year', 'month']).reset_index(drop=True)

    # 7. Transformaciones vectorizadas de unidades
    # Conversión de Fahrenheit a Celsius: (F - 32) * 5/9
    mask_f = df_final['metrics.temperature.unit'] == 'F'
    cols_temp = ['metrics.temperature.max', 'metrics.temperature.avg', 'metrics.temperature.min']
    df_final.loc[mask_f, cols_temp] = (df_final.loc[mask_f, cols_temp] - 32) * 5/9
    df_final.loc[mask_f, 'metrics.temperature.unit'] = 'C'

    # Conversión de Pulgadas a Milímetros: pulgadas * 25.4
    mask_in = df_final['metrics.precipitation.unit'] == 'inches'
    col_precip = 'metrics.precipitation.avg'
    df_final.loc[mask_in, col_precip] = df_final.loc[mask_in, col_precip] * 25.4
    df_final.loc[mask_in, 'metrics.precipitation.unit'] = 'mm'

    # 8. Enriquecimiento: Oscilación Térmica (Diferencia entre Máxima y Mínima)
    df_final['thermal_range'] = df_final['metrics.temperature.max'] - df_final['metrics.temperature.min']

    # 9. Enriquecimiento: Precipitación Acumulada Anual (Suma acumulada por ciudad y año)
    df_final['cumulative_rain_year'] = df_final.groupby(['city', 'year'])['metrics.precipitation.avg'].cumsum()

    # 10. KPI: Índice de Estrés Térmico (Combinación de calor y falta de lluvia)
    # Se calcula como la Max / (Lluvia + 1) para evitar divisiones por cero; a mayor valor, más estrés.
    df_final['kpi.heat_stress_index'] = df_final['metrics.temperature.max'] / (df_final['metrics.precipitation.avg'] + 1)

    # 11. KPI: Anomalía Térmica (Z-score: desviación estándar respecto a la media histórica de la ciudad)
    df_final['kpi.temp_zscore'] = df_final.groupby('city')['metrics.temperature.avg'].transform(lambda x: (x - x.mean()) / x.std())

    # Estadísticas finales y generación del informe
    n_final = len(df_final)
    n_borrados = n_inicial - n_final

    with open('informe_limpieza.txt', 'w') as f:
        f.write("Resumen del proceso de limpieza\n")
        f.write(f"------------------------------\n")
        f.write(f"Número de registros iniciales: {n_inicial}\n")
        f.write(f"Número de registros borrados: {n_borrados}\n")
        f.write(f"Número de registros finales: {n_final}\n")

    # 12. Reportes Agregados finales
    print("\n--- RESUMEN POR CIUDAD: Temperatura Media Histórica y Lluvia Total ---")
    print(df_final.groupby('city').agg({
        'metrics.temperature.avg': 'mean',
        'metrics.precipitation.avg': 'sum'
    }))

    print("\n--- RESUMEN ANUAL: Temperaturas Extremas (Máxima y Mínima Absoluta) ---")
    print(df_final.groupby(['year', 'city']).agg({
        'metrics.temperature.max': 'max',
        'metrics.temperature.min': 'min'
    }))

    print("Proceso completado. Se ha generado 'informe_limpieza.txt'.")
    print(df_final.head())

except requests.exceptions.RequestException as e:
    print(f'Error en la petición: {e}')
