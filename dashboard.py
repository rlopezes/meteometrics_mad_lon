import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración de la página
st.set_page_config(page_title="Clima: Madrid vs Londres", layout="wide")

@st.cache_data
def load_data():
    # Cargamos el dataframe procesado anteriormente
    df = pd.read_parquet('/home/rlopez_es/meteometrics_mad_lon/data/df_total.parquet')
    # Mapeo de meses para las gráficas
    meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 
                 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
    df['month_name'] = df['month'].map(meses_map)
    return df

df_total = load_data()
colors = {'Madrid': 'red', 'London': 'blue'}

st.title("🌦️ Comparativa Climática Histórica")

# 1. Resumen instantáneo
st.header("1. Resumen Instantáneo")
c1, c2, c3, c4 = st.columns(4)

for i, city in enumerate(['Madrid', 'London']):
    city_data = df_total[df_total['city'] == city]
    avg_t = city_data['metrics.temperature.avg'].mean()
    total_p = city_data['metrics.precipitation.avg'].sum()
    
    cols = [c1, c3] if city == 'Madrid' else [c2, c4]
    cols[0].metric(f"Temp. Media {city}", f"{avg_t:.1f} °C")
    cols[1].metric(f"Precip. Total {city}", f"{total_p:.0f} mm")

st.divider()

# 2. Gráfico de Evolución (Banda de Rango)
st.header("2. Evolución Térmica y Rangos (Máx/Mín)")
fig_evol = go.Figure()

for city in ['Madrid', 'London']:
    df_city = df_total[df_total['city'] == city].sort_values(['year', 'month'])
    # Creamos un eje temporal legible
    timeline = df_city['year'].astype(str) + "-" + df_city['month'].astype(str).str.zfill(2)
    
    # Banda de rango (sombreado)
    fig_evol.add_trace(go.Scatter(
        x=pd.concat([timeline, timeline[::-1]]),
        y=pd.concat([df_city['metrics.temperature.max'], df_city['metrics.temperature.min'][::-1]]),
        fill='toself',
        fillcolor=colors[city],
        opacity=0.2,
        line=dict(color='rgba(255,255,255,0)'),
        name=f"Rango {city}",
        showlegend=False
    ))
    
    # Línea de media
    fig_evol.add_trace(go.Scatter(
        x=timeline, y=df_city['metrics.temperature.avg'],
        line=dict(color=colors[city], width=3),
        name=f"Media {city}"
    ))

fig_evol.update_layout(hovermode="x unified", xaxis_title="Periodo", yaxis_title="Temperatura (°C)")
st.plotly_chart(fig_evol, use_container_width=True)

st.markdown("""
**Interpretación de Evolución:** Se observa que **Madrid** presenta una oscilación térmica mucho más agresiva que Londres. 
Mientras que Londres mantiene rangos estrechos y estables (clima oceánico), Madrid muestra picos de máximas muy elevados 
en verano y caídas pronunciadas en invierno, evidenciando su carácter continental/mediterráneo.
""")

st.divider()

# 3. Gráfico de Radar
st.header("3. Perfil Climático Mensual")
df_radar = df_total.groupby(['city', 'month', 'month_name'])[['metrics.temperature.avg', 'metrics.precipitation.avg']].mean().reset_index().sort_values('month')

fig_radar = make_subplots(rows=1, cols=2, specs=[[{'type': 'polar'}, {'type': 'polar'}]], 
                          subplot_titles=("Temperatura Media (°C)", "Precipitación Media (mm)"))

for city in ['Madrid', 'London']:
    df_c = df_radar[df_radar['city'] == city]
    
    # Radar Temperatura
    fig_radar.add_trace(go.Scatterpolar(
        r=df_c['metrics.temperature.avg'], theta=df_c['month_name'],
        fill='toself', name=f"Temp {city}", line=dict(color=colors[city])
    ), row=1, col=1)
    
    # Radar Precipitación
    fig_radar.add_trace(go.Scatterpolar(
        r=df_c['metrics.precipitation.avg'], theta=df_c['month_name'],
        fill='toself', name=f"Lluvia {city}", line=dict(color=colors[city]),
        showlegend=False
    ), row=1, col=2)

fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), polar2=dict(radialaxis=dict(visible=True)))
st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("""
**Interpretación de Perfil:** El radar de temperatura resalta el "calor estival" de Madrid frente a la moderación londinense. 
Sin embargo, el radar de precipitación es el más revelador: **Londres** mantiene un aporte de lluvia constante y superior 
durante casi todo el año, mientras que Madrid sufre una sequía estival severa en los meses de julio y agosto.
""")