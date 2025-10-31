import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from itertools import combinations
from collections import Counter

# ===============================================================
# CONFIGURACIÓN INICIAL
# ===============================================================

st.set_page_config(page_title="Dashboard de Ventas", page_icon="📈", layout="wide")
st.title("📈 Dashboard de Ventas Inteligente")

DATA_URL = "https://raw.githubusercontent.com/BayaslianSantiago/streamlit-dashboard/refs/heads/main/datos.csv"

# ===============================================================
# CARGA Y PROCESAMIENTO DE DATOS
# ===============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos():
    try:
        df = pd.read_csv(DATA_URL)
        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
        df = df.sort_values('fecha_hora').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()


def preparar_datos(df):
    if df.empty:
        return df

    df['hora_num'] = df['fecha_hora'].dt.hour
    df['minuto'] = df['fecha_hora'].dt.minute
    df['media_hora'] = df['hora_num'] + (df['minuto'] >= 30).astype(int) * 0.5
    df['dia_semana'] = df['fecha_hora'].dt.day_name()
    df['mes_num'] = df['fecha_hora'].dt.month
    df['año'] = df['fecha_hora'].dt.year
    df['semana_del_mes'] = ((df['fecha_hora'].dt.day - 1) // 7) + 1
    df['fecha'] = df['fecha_hora'].dt.date
    return df


def calcular_bcg(df, meses_es, periodo, mes_sel, año_sel, df_temp):
    ventas_por_prod = df.groupby('producto')['cantidad'].sum().reset_index()
    if ventas_por_prod.empty:
        return pd.DataFrame(), None, 0, 0

    ventas_por_prod['participacion'] = (ventas_por_prod['cantidad'] / ventas_por_prod['cantidad'].sum()) * 100

    if periodo == '📊 Todos los datos':
        fecha_mitad = df['fecha_hora'].min() + (df['fecha_hora'].max() - df['fecha_hora'].min()) / 2
        p1, p2 = df[df['fecha_hora'] < fecha_mitad], df[df['fecha_hora'] >= fecha_mitad]
        periodo_txt = "Primera mitad vs Segunda mitad"
    else:
        mes_act, año_act = mes_sel, año_sel
        mes_ant, año_ant = (12, año_act - 1) if mes_act == 1 else (mes_act - 1, año_act)
        p1 = df_temp[(df_temp['mes_num'] == mes_ant) & (df_temp['año'] == año_ant)]
        p2 = df.copy()
        periodo_txt = f"{meses_es[mes_ant]} {año_ant}"

    v1, v2 = p1.groupby('producto')['cantidad'].sum(), p2.groupby('producto')['cantidad'].sum()

    crecimiento = pd.DataFrame({
        'producto': v2.index,
        'ventas1': v2.index.map(lambda x: v1.get(x, 0)),
        'ventas2': v2.values
    })

    crecimiento['tasa'] = crecimiento.apply(lambda r: ((r['ventas2'] - r['ventas1']) / r['ventas1'] * 100)
                                            if r['ventas1'] > 0 else 100, axis=1)

    bcg = ventas_por_prod.merge(crecimiento[['producto', 'tasa']], on='producto')
    p_med, c_med = bcg['participacion'].median(), bcg['tasa'].median()

    def cat(r):
        if r['participacion'] >= p_med and r['tasa'] >= c_med: return '⭐ Estrella'
        if r['participacion'] >= p_med and r['tasa'] < c_med: return '🐄 Vaca Lechera'
        if r['participacion'] < p_med and r['tasa'] >= c_med: return '❓ Interrogante'
        return '🐕 Perro'

    bcg['categoria'] = bcg.apply(cat, axis=1)
    return bcg, periodo_txt, p_med, c_med

# ===============================================================
# INTERFAZ PRINCIPAL
# ===============================================================

df = cargar_datos()
if df.empty:
    st.error("❌ No se pudieron cargar datos desde GitHub.")
    st.stop()

df = preparar_datos(df)

meses_es = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
dias_es = {'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miércoles','Thursday':'Jueves','Friday':'Viernes','Saturday':'Sábado','Sunday':'Domingo'}

st.sidebar.header("🔍 Filtros")
meses_opc = ['📊 Todos los datos'] + [f"{meses_es[m]} {a}" for a, m in sorted(df.groupby(['año','mes_num']).groups.keys())]

sel = st.sidebar.selectbox("Selecciona período", meses_opc)

if sel == '📊 Todos los datos':
    df_sel = df.copy()
    mes_sel = año_sel = None
else:
    mes_txt, año_sel = sel.split()
    mes_sel = [k for k,v in meses_es.items() if v == mes_txt][0]
    df_sel = df[(df['mes_num']==mes_sel)&(df['año']==int(año_sel))]

if df_sel.empty:
    st.warning("⚠️ No hay datos para este período.")
    st.stop()

st.info(f"📋 Analizando {len(df_sel):,} registros del período: {sel}")

# ===============================================================
# RESUMEN GENERAL
# ===============================================================

st.header("📊 Resumen General")
total = df_sel['cantidad'].sum()
dia_top = df_sel.groupby('dia_semana')['cantidad'].sum().idxmax()
hora_top = df_sel.groupby('hora_num')['cantidad'].sum().idxmax()

col1,col2,col3 = st.columns(3)
col1.metric("📦 Total Vendido", f"{int(total):,}")
col2.metric("📅 Día Pico", dias_es.get(dia_top,dia_top))
col3.metric("🕐 Hora Pico", f"{int(hora_top)}:00")

# ===============================================================
# GRÁFICOS
# ===============================================================

st.subheader("📅 Ventas por Día de la Semana")
dias_orden = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
ventas_dia = df_sel.groupby('dia_semana')['cantidad'].sum().reindex(dias_orden).fillna(0)
fig_dias = go.Figure([go.Bar(x=[dias_es[d] for d in ventas_dia.index], y=ventas_dia.values, text=ventas_dia.values, textposition='auto', marker_color='#1E90FF')])
fig_dias.update_layout(height=400, xaxis_title="Día", yaxis_title="Unidades Vendidas", showlegend=False)
st.plotly_chart(fig_dias, width='stretch')

st.subheader("🕐 Ventas por Hora del Día")
ventas_hora = df_sel.groupby('hora_num')['cantidad'].sum()
fig_horas = go.Figure([go.Scatter(x=ventas_hora.index, y=ventas_hora.values, mode='lines+markers', line=dict(color='#32CD32',width=3), fill='tozeroy', fillcolor='rgba(50,205,50,0.2)')])
fig_horas.update_layout(height=400, xaxis_title="Hora", yaxis_title="Unidades", showlegend=False, xaxis=dict(dtick=2))
st.plotly_chart(fig_horas, width='stretch')

# ===============================================================
# MATRIZ BCG
# ===============================================================

st.header("📈 Matriz BCG - Análisis de Productos")
bcg, per_txt, p_med, c_med = calcular_bcg(df_sel, meses_es, sel, mes_sel, año_sel, df)
if bcg.empty:
    st.warning("⚠️ No hay datos suficientes para calcular la matriz BCG.")
    st.stop()

cats = {'⭐ Estrella':'#FFD700','🐄 Vaca Lechera':'#32CD32','❓ Interrogante':'#1E90FF','🐕 Perro':'#DC143C'}
fig_bcg = go.Figure()
for cat,col in cats.items():
    dcat = bcg[bcg['categoria']==cat]
    if not dcat.empty:
        fig_bcg.add_trace(go.Scatter(x=dcat['participacion'], y=dcat['tasa'], mode='markers', name=cat,
            marker=dict(size=10+(dcat['cantidad']/bcg['cantidad'].max())*20, color=col, line=dict(width=1,color='white')), text=dcat['producto']))

fig_bcg.add_hline(y=c_med, line_dash='dash', line_color='gray')
fig_bcg.add_vline(x=p_med, line_dash='dash', line_color='gray')
fig_bcg.update_layout(height=600, xaxis_title='Participación de Mercado (%)', yaxis_title='Tasa de Crecimiento (%)', plot_bgcolor='white')
st.plotly_chart(fig_bcg, width='stretch')
st.info(f"📊 Comparación: {per_txt}")

# ===============================================================
# FINAL
# ===============================================================

st.caption("App optimizada para Streamlit Cloud - por Santiago Bayaslian 🚀")

