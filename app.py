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
    
    print("Primeras filas del DataFrame unificado:")
    print(df_final)

except requests.exceptions.RequestException as e:
    print(f'Error en la petición: {e}')
