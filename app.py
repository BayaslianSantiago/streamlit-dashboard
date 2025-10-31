import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from itertools import combinations
from collections import Counter

# -------------------------------
# Configuración
# -------------------------------
st.set_page_config(page_title="Dashboard de Ventas", page_icon="📈", layout="wide")
st.title("Dashboard de Ventas — Informe profesional")

DATA_URL = "https://raw.githubusercontent.com/BayaslianSantiago/streamlit-dashboard/refs/heads/main/datos.csv"

# -------------------------------
# Utilidades y carga de datos
# -------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos(url: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(url)
        if 'fecha_hora' in df.columns:
            df['fecha_hora'] = pd.to_datetime(df['fecha_hora'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error al leer CSV: {e}")
        return pd.DataFrame()

def preparar_datos(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # Normalizar columnas esperadas
    if 'cantidad' not in df.columns or 'producto' not in df.columns:
        st.error("El CSV debe contener al menos las columnas 'fecha_hora', 'producto' y 'cantidad'.")
        return pd.DataFrame()
    df = df.dropna(subset=['fecha_hora', 'producto', 'cantidad']).copy()
    df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce').fillna(0).astype(int)
    df['hora_num'] = df['fecha_hora'].dt.hour
    df['minuto'] = df['fecha_hora'].dt.minute
    df['media_hora'] = df['hora_num'] + (df['minuto'] >= 30).astype(int) * 0.5
    df['dia_semana'] = df['fecha_hora'].dt.day_name()
    df['mes_num'] = df['fecha_hora'].dt.month
    df['año'] = df['fecha_hora'].dt.year
    df['semana_del_mes'] = ((df['fecha_hora'].dt.day - 1) // 7) + 1
    df['fecha'] = df['fecha_hora'].dt.date
    return df.reset_index(drop=True)

def safe_strftime(dt):
    try:
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return str(dt)

# -------------------------------
# Cálculo matriz BCG
# -------------------------------
@st.cache_data
def calcular_bcg(df_analisis: pd.DataFrame, periodo_seleccionado: str, mes_num_sel, año_sel, df_temp: pd.DataFrame, meses_español: dict):
    ventas_por_producto = df_analisis.groupby('producto')['cantidad'].sum().reset_index()
    if ventas_por_producto.empty:
        return pd.DataFrame(), "", 0, 0
    ventas_por_producto['participacion'] = (ventas_por_producto['cantidad'] / ventas_por_producto['cantidad'].sum()) * 100

    # Calcular tasa de crecimiento
    if periodo_seleccionado == '📊 Todos los datos':
        fecha_min = df_analisis['fecha_hora'].min()
        fecha_max = df_analisis['fecha_hora'].max()
        fecha_mitad = fecha_min + (fecha_max - fecha_min) / 2 if pd.notna(fecha_min) and pd.notna(fecha_max) else fecha_min
        df_periodo1 = df_analisis[df_analisis['fecha_hora'] < fecha_mitad]
        df_periodo2 = df_analisis[df_analisis['fecha_hora'] >= fecha_mitad]
        periodo_comparacion = "Primera mitad vs Segunda mitad"
    else:
        if mes_num_sel is None or año_sel is None:
            df_periodo1 = pd.DataFrame()
        else:
            mes_actual = mes_num_sel
            año_actual = año_sel
            if mes_actual == 1:
                mes_anterior = 12
                año_anterior = año_actual - 1
            else:
                mes_anterior = mes_actual - 1
                año_anterior = año_actual
            df_periodo1 = df_temp[(df_temp['mes_num'] == mes_anterior) & (df_temp['año'] == año_anterior)]
        df_periodo2 = df_analisis.copy()
        mes_ant_nombre = meses_español.get((df_periodo1['mes_num'].iloc[0] if not df_periodo1.empty else mes_num_sel), "")
        periodo_comparacion = f"{mes_ant_nombre} {año_anterior}" if mes_ant_nombre else "Periodo anterior"

    ventas_p1 = df_periodo1.groupby('producto')['cantidad'].sum() if not df_periodo1.empty else pd.Series(dtype=int)
    ventas_p2 = df_periodo2.groupby('producto')['cantidad'].sum()

    crecimiento = pd.DataFrame({
        'producto': ventas_p2.index,
        'ventas_periodo1': ventas_p2.index.map(lambda x: ventas_p1.get(x, 0)),
        'ventas_periodo2': ventas_p2.values
    })

    crecimiento['tasa_crecimiento'] = crecimiento.apply(
        lambda row: ((row['ventas_periodo2'] - row['ventas_periodo1']) / row['ventas_periodo1'] * 100)
        if row['ventas_periodo1'] > 0 else 100,
        axis=1
    )

    bcg_data = ventas_por_producto.merge(crecimiento[['producto', 'tasa_crecimiento']], on='producto', how='left').fillna(0)

    participacion_media = bcg_data['participacion'].median() if not bcg_data['participacion'].empty else 0
    crecimiento_medio = bcg_data['tasa_crecimiento'].median() if not bcg_data['tasa_crecimiento'].empty else 0

    def clasificar_bcg(row):
        if row['participacion'] >= participacion_media and row['tasa_crecimiento'] >= crecimiento_medio:
            return 'Estrella'
        elif row['participacion'] >= participacion_media and row['tasa_crecimiento'] < crecimiento_medio:
            return 'Vaca Lechera'
        elif row['participacion'] < participacion_media and row['tasa_crecimiento'] >= crecimiento_medio:
            return 'Interrogante'
        else:
            return 'Perro'

    bcg_data['categoria'] = bcg_data.apply(clasificar_bcg, axis=1)
    return bcg_data, periodo_comparacion, participacion_media, crecimiento_medio

# -------------------------------
# Cargar y preparar datos
# -------------------------------
df_limpio = cargar_datos(DATA_URL)
if df_limpio.empty:
    st.error("No se pudieron cargar los datos desde la URL proporcionada o el CSV no contiene datos válidos.")
    st.stop()

df_temp = preparar_datos(df_limpio)
if df_temp.empty:
    st.error("Los datos no contienen las columnas requeridas o están vacíos después de procesar.")
    st.stop()

# Diccionarios
meses_espanol = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
dias_espanol = {'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miércoles','Thursday':'Jueves','Friday':'Viernes','Saturday':'Sábado','Sunday':'Domingo'}
dias_orden = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

# -------------------------------
# Interfaz: selección de período
# -------------------------------
st.subheader("Selecciona el período a analizar")
meses_con_datos = df_temp.groupby(['año', 'mes_num'])['cantidad'].sum()
meses_con_datos = meses_con_datos[meses_con_datos > 0].reset_index()

meses_opciones = ['📊 Todos los datos']
for _, row in meses_con_datos.iterrows():
    mes_nombre = meses_espanol.get(int(row['mes_num']), str(int(row['mes_num'])))
    año = int(row['año'])
    meses_opciones.append(f\"{mes_nombre} {año}\")

periodo_seleccionado = st.selectbox("Elige qué datos quieres analizar:", meses_opciones)

if periodo_seleccionado == '📊 Todos los datos':
    df_analisis = df_temp.copy()
    titulo_periodo = "Todo el período"
    mes_num_sel = None
    año_sel = None
else:
    partes = periodo_seleccionado.split()
    mes_nombre = partes[0]
    año_sel = int(partes[1])
    mes_num_sel = [k for k, v in meses_espanol.items() if v == mes_nombre][0]
    df_analisis = df_temp[(df_temp['mes_num'] == mes_num_sel) & (df_temp['año'] == año_sel)].copy()
    titulo_periodo = periodo_seleccionado

st.info(f\"Analizando {len(df_analisis):,} registros del período: {titulo_periodo}\")

if df_analisis.empty:
    st.warning(\"No hay datos disponibles para el período seleccionado.\")
    st.stop()

# -------------------------------
# Tabs principales
# -------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    \"Resumen General\",
    \"Análisis de Horarios\",
    \"Análisis de Productos\",
    \"Búsqueda Detallada\",
    \"Análisis de Canastas\",
    \"Fechas Especiales\"
])

# ========== TAB 1: Resumen General ==========
with tab1:
    st.header(\"Resumen General\")
    ventas_hora_dia = df_analisis.groupby(['dia_semana', 'hora_num'])['cantidad'].sum().reset_index()
    if ventas_hora_dia.empty:
        st.info(\"No hay ventas para mostrar en el período seleccionado.\")
    else:
        idx_max = ventas_hora_dia['cantidad'].idxmax()
        hora_pico = int(ventas_hora_dia.loc[idx_max, 'hora_num'])
        dia_pico = dias_espanol.get(ventas_hora_dia.loc[idx_max, 'dia_semana'], ventas_hora_dia.loc[idx_max, 'dia_semana'])
        cantidad_pico = int(ventas_hora_dia.loc[idx_max, 'cantidad'])
        total_vendido = int(df_analisis['cantidad'].sum())

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(\"Hora Pico\", f\"{hora_pico}:00 hs\")
        col2.metric(\"Día Pico\", dia_pico)
        col3.metric(\"Ventas en Pico\", f\"{cantidad_pico} unidades\")
        col4.metric(\"Total Vendido\", f\"{total_vendido:,} unidades\")

        # Ventas por día de la semana
        ventas_por_dia = df_analisis.groupby('dia_semana')['cantidad'].sum().reset_index()
        ventas_por_dia['dia_es'] = ventas_por_dia['dia_semana'].map(dias_espanol)
        ventas_por_dia = ventas_por_dia.set_index('dia_semana').reindex(dias_orden).fillna(0).reset_index()

        fig_dias = go.Figure(data=[
            go.Bar(x=[dias_espanol[d] for d in ventas_por_dia['dia_semana']], y=ventas_por_dia['cantidad'],
                   text=ventas_por_dia['cantidad'], textposition='auto')
        ])
        fig_dias.update_layout(height=400, xaxis_title=\"Día de la semana\", yaxis_title=\"Unidades vendidas\", showlegend=False)
        st.plotly_chart(fig_dias, width='stretch')

        # Ventas por hora
        ventas_por_hora = df_analisis.groupby('hora_num')['cantidad'].sum().reset_index()
        fig_horas = go.Figure(data=[
            go.Scatter(x=ventas_por_hora['hora_num'], y=ventas_por_hora['cantidad'], mode='lines+markers', fill='tozeroy')
        ])
        fig_horas.update_layout(height=400, xaxis_title=\"Hora del día\", yaxis_title=\"Unidades vendidas\", showlegend=False, xaxis=dict(dtick=2))
        st.plotly_chart(fig_horas, width='stretch')

# ========== TAB 2: Análisis de Horarios ==========
with tab2:
    st.header(\"Heatmap de Ventas por Media Hora\")
    ventas_mh = df_analisis.groupby(['dia_semana', 'media_hora'])['cantidad'].sum().reset_index()
    if ventas_mh.empty:
        st.info(\"No hay datos para el heatmap en este período.\")
    else:
        ventas_matriz = ventas_mh.pivot(index='dia_semana', columns='media_hora', values='cantidad').fillna(0)
        ventas_matriz = ventas_matriz.reindex([d for d in dias_orden if d in ventas_matriz.index])
        ventas_matriz.index = [dias_espanol[d] for d in ventas_matriz.index]

        etiquetas_horas = [f\"{int(h)}:{'00' if h % 1 == 0 else '30'}\" for h in ventas_matriz.columns]

        fig_heat = go.Figure(data=go.Heatmap(
            z=ventas_matriz.values,
            x=etiquetas_horas,
            y=ventas_matriz.index,
            colorscale='YlOrRd'
        ))
        fig_heat.update_layout(height=500, xaxis_title=\"Hora del día\", yaxis_title=\"Dia de la semana\")
        st.plotly_chart(fig_heat, width='stretch')

# ========== TAB 3: Análisis de Productos ==========
with tab3:
    st.header(\"Análisis de Productos\")
    bcg_data, periodo_comparacion, participacion_media, crecimiento_medio = calcular_bcg(df_analisis, periodo_seleccionado, mes_num_sel, año_sel, df_temp, meses_espanol)
    if bcg_data.empty:
        st.info(\"No hay datos suficientes para el análisis de productos.\")
    else:
        st.subheader(\"Matriz BCG\")
        categorias_map = {'Estrella':'#FFD700','Vaca Lechera':'#32CD32','Interrogante':'#1E90FF','Perro':'#DC143C'}
        fig_bcg = go.Figure()
        for cat, color in categorias_map.items():
            df_cat = bcg_data[bcg_data['categoria'] == cat]
            if not df_cat.empty:
                sizes = 15 + (df_cat['cantidad'] / bcg_data['cantidad'].max()) * 35
                fig_bcg.add_trace(go.Scatter(
                    x=df_cat['participacion'],
                    y=df_cat['tasa_crecimiento'],
                    mode='markers',
                    name=cat,
                    marker=dict(size=sizes, color=color, line=dict(width=1, color='white')),
                    text=df_cat['producto'],
                    hovertemplate='<b>%{text}</b><br>Participación: %{x:.2f}%<br>Crecimiento: %{y:.1f}%<extra></extra>'
                ))

        fig_bcg.add_hline(y=crecimiento_medio, line_dash='dash', line_color='gray', line_width=2)
        fig_bcg.add_vline(x=participacion_media, line_dash='dash', line_color='gray', line_width=2)
        fig_bcg.update_layout(height=600, xaxis_title='Participación (%)', yaxis_title='Tasa crecimiento (%)', plot_bgcolor='white')
        st.plotly_chart(fig_bcg, width='stretch')
        st.info(f\"Comparación: {periodo_comparacion}\")

        # Ranking
        st.subheader('Ranking de Productos')
        ranking_data = bcg_data.copy()
        ranking_data = ranking_data.sort_values('cantidad', ascending=False).reset_index(drop=True)
        limit = st.selectbox('Mostrar top:', [10,20,50,'Todos'], index=0)
        if limit != 'Todos':
            ranking_display = ranking_data.head(int(limit))
        else:
            ranking_display = ranking_data
        ranking_display['Participación (%)'] = ranking_display['participacion'].map(lambda x: f\"{x:.2f}%\")
        ranking_display['Crecimiento (%)'] = ranking_display['tasa_crecimiento'].map(lambda x: f\"{x:+.1f}%\")
        st.dataframe(ranking_display[['producto','cantidad','Participación (%)','Crecimiento (%)']].rename(columns={'producto':'Producto','cantidad':'Unidades'}), width=800)

# ========== TAB 4: Búsqueda Detallada ==========
with tab4:
    st.header('Buscador de Productos')
    productos_disponibles = sorted(df_analisis['producto'].unique())
    producto_seleccionado = st.selectbox('Selecciona un producto', [''] + productos_disponibles)
    if producto_seleccionado:
        df_producto = df_analisis[df_analisis['producto'] == producto_seleccionado].copy()
        if df_producto.empty:
            st.warning('No hay datos para ese producto en el período.')
        else:
            info_bcg = bcg_data[bcg_data['producto'] == producto_seleccionado]
            cantidad_total = int(df_producto['cantidad'].sum())
            participacion = float(info_bcg['participacion'].iloc[0]) if not info_bcg.empty else 0.0
            crecimiento = float(info_bcg['tasa_crecimiento'].iloc[0]) if not info_bcg.empty else 0.0

            col1,col2,col3,col4 = st.columns(4)
            col1.metric('Unidades vendidas', f\"{cantidad_total:,}\")
            col2.metric('Participación', f\"{participacion:.2f}%\")
            col3.metric('Crecimiento', f\"{crecimiento:+.1f}%\")
            # Series temporal
            ventas_t = df_producto.groupby(df_producto['fecha'])['cantidad'].sum().reset_index()
            fig_t = go.Figure(data=[go.Scatter(x=ventas_t['fecha'], y=ventas_t['cantidad'], mode='lines+markers')])
            fig_t.update_layout(height=300, xaxis_title='Fecha', yaxis_title='Unidades')
            st.plotly_chart(fig_t, width='stretch')

# ========== TAB 5: Análisis de Canastas ==========
with tab5:
    st.header('Análisis de Canastas')
    productos_excluir = st.multiselect('Excluir productos del análisis', options=sorted(df_analisis['producto'].unique()), default=[])
    if productos_excluir:
        df_canastas = df_analisis[~df_analisis['producto'].isin(productos_excluir)].copy()
    else:
        df_canastas = df_analisis.copy()

    df_canastas['transaccion_id'] = df_canastas['fecha_hora'].astype(str)
    canastas = df_canastas.groupby('transaccion_id')['producto'].apply(list).reset_index()
    canastas['num_productos'] = canastas['producto'].apply(len)
    canastas_multiples = canastas[canastas['num_productos'] > 1].copy()

    total_transacciones = len(canastas)
    transacciones_multiples = len(canastas_multiples)
    pct_multiples = (transacciones_multiples / total_transacciones * 100) if total_transacciones > 0 else 0
    promedio_productos = canastas['num_productos'].mean() if total_transacciones > 0 else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Total transacciones', f\"{total_transacciones:,}\")
    c2.metric('Transacciones múltiples', f\"{transacciones_multiples:,}\", delta=f\"{pct_multiples:.1f}%\")
    c3.metric('Promedio productos/venta', f\"{promedio_productos:.1f}\")
    c4.metric('Máximo en una venta', f\"{int(canastas['num_productos'].max())}\")

    if canastas_multiples.empty:
        st.info('No hay transacciones con múltiples productos para analizar.')
    else:
        pares = []
        for productos in canastas_multiples['producto']:
            if len(productos) >= 2:
                for combo in combinations(sorted(productos), 2):
                    pares.append(combo)
        contador_pares = Counter(pares)
        top_pares = contador_pares.most_common(20)
        if top_pares:
            num_mostrar = st.slider('Cantidad de combinaciones a mostrar', min_value=5, max_value=min(20, len(top_pares)), value=min(10, len(top_pares)))
            df_pares = pd.DataFrame(top_pares[:num_mostrar], columns=['Par','Frecuencia'])
            df_pares['Producto 1'] = df_pares['Par'].apply(lambda x: x[0])
            df_pares['Producto 2'] = df_pares['Par'].apply(lambda x: x[1])
            df_pares['Soporte (%)'] = (df_pares['Frecuencia'] / len(canastas_multiples) * 100).round(2)
            df_pares['Combinación'] = df_pares.apply(lambda r: f\"{r['Producto 1']} + {r['Producto 2']}\", axis=1)
            fig_p = go.Figure([go.Bar(y=df_pares['Combinación'][::-1], x=df_pares['Frecuencia'][::-1], orientation='h')])
            fig_p.update_layout(height=400, xaxis_title='Frecuencia', yaxis_title='')
            st.plotly_chart(fig_p, width='stretch')
            st.dataframe(df_pares[['Producto 1','Producto 2','Frecuencia','Soporte (%)']].rename(columns={'Soporte (%)':'Soporte (%)'}), width=800)

# ========== TAB 6: Fechas Especiales ==========
with tab6:
    st.header('Fechas Especiales')
    fechas_disponibles = sorted(df_temp['fecha'].unique())
    if not fechas_disponibles:
        st.info('No hay fechas disponibles para comparar.')
    else:
        fecha_seleccionada = st.selectbox('Seleccionar fecha', fechas_disponibles, index=len(fechas_disponibles)-1)
        tipo_comparacion = st.radio('Comparar con', ['Mismo día de la semana','Promedio general'])
        df_fecha = df_temp[df_temp['fecha'] == fecha_seleccionada].copy()
        if df_fecha.empty:
            st.warning('No hay datos para la fecha seleccionada.')
        else:
            dia_sem = df_fecha['dia_semana'].iloc[0]
            if tipo_comparacion == 'Mismo día de la semana':
                df_comparacion = df_temp[(df_temp['dia_semana'] == dia_sem) & (df_temp['fecha'] != fecha_seleccionada)].copy()
                titulo_comparacion = f\"Promedio de {dias_espanol.get(dia_sem, dia_sem)}s\"
            else:
                df_comparacion = df_temp[df_temp['fecha'] != fecha_seleccionada].copy()
                titulo_comparacion = 'Promedio general'

            dias_comp = df_comparacion['fecha'].nunique() if not df_comparacion.empty else 0
            ventas_fecha = df_fecha.groupby('producto')['cantidad'].sum().reset_index().rename(columns={'cantidad':'cantidad_fecha'})
            ventas_promedio = (df_comparacion.groupby('producto')['cantidad'].sum() / dias_comp).reset_index().rename(columns={0:'promedio_diario','cantidad':'promedio_diario'}) if dias_comp > 0 else pd.DataFrame(columns=['producto','promedio_diario'])
            ventas_promedio = ventas_promedio.rename(columns={0:'promedio_diario'}) if 'cantidad' not in ventas_promedio.columns else ventas_promedio
            comparacion = ventas_fecha.merge(ventas_promedio, on='producto', how='outer').fillna(0)
            comparacion['diferencia'] = comparacion['cantidad_fecha'] - comparacion['promedio_diario']
            comparacion['diferencia_pct'] = ((comparacion['cantidad_fecha'] - comparacion['promedio_diario']) / comparacion['promedio_diario'] * 100).replace([np.inf, -np.inf], 0).fillna(0)

            total_fecha = int(df_fecha['cantidad'].sum())
            total_promedio = int(df_comparacion.groupby('fecha')['cantidad'].sum().mean()) if dias_comp > 0 else 0
            diferencia_total = ((total_fecha - total_promedio) / total_promedio * 100) if total_promedio > 0 else 0

            c1,c2,c3 = st.columns(3)
            c1.metric('Ventas del día', f\"{total_fecha:,} unidades\")
            c2.metric('Promedio comparación', f\"{total_promedio:,} unidades\", help=titulo_comparacion)
            c3.metric('Diferencia', f\"{diferencia_total:+.1f}%\", delta=f\"{int(total_fecha - total_promedio):+,} unidades\")

            top_crecimiento = comparacion[comparacion['cantidad_fecha'] > 0].nlargest(15, 'diferencia_pct')
            if not top_crecimiento.empty:
                fig_c = go.Figure([go.Bar(y=top_crecimiento['producto'][::-1][:10], x=top_crecimiento['diferencia_pct'][::-1][:10], orientation='h')])
                fig_c.update_layout(height=400, xaxis_title='Variación (%)', yaxis_title='')
                st.plotly_chart(fig_c, width='stretch')
                st.dataframe(top_crecimiento[['producto','cantidad_fecha','promedio_diario','diferencia','diferencia_pct']].rename(columns={
                    'producto':'Producto','cantidad_fecha':'Vendido en Fecha','promedio_diario':'Promedio diario','diferencia':'Diferencia (unidades)','diferencia_pct':'Diferencia (%)'}), width=800)

            # Recomendaciones simples
            if diferencia_total > 20:
                st.success(f\"Fecha especial: ventas {diferencia_total:.1f}% superiores al promedio.\")
            elif diferencia_total < -20:
                st.warning(f\"Día de baja actividad: ventas {abs(diferencia_total):.1f}% inferiores al promedio.\")
            else:
                st.info('Día con comportamiento similar al promedio.')

st.caption('Versión limpia y profesional - lista para Streamlit Cloud')

