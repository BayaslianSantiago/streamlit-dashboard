import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# URL del CSV en GitHub
DATA_URL = "https://raw.githubusercontent.com/BayaslianSantiago/streamlit-dashboard/refs/heads/main/datos.csv"

@st.cache_data(ttl=3600)  # Cachea por 1 hora
def cargar_datos():
    """Carga los datos desde GitHub y prepara columnas temporales"""
    df = pd.read_csv(DATA_URL)
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    
    # ORDENAR por fecha_hora
    df = df.sort_values('fecha_hora').reset_index(drop=True)
    
    return df

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Ciencia de Datos Estancia", page_icon="📊", layout="wide")
st.title("Dashboard Avellaneda")

# Cargar datos automáticamente
try:
    df_limpio = cargar_datos()
    
    # Mostrar info básica
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Registros", f"{len(df_limpio):,}")
    with col2:
        st.metric("Productos Únicos", f"{df_limpio['producto'].nunique():,}")
    with col3:
        fecha_inicio = df_limpio['fecha_hora'].min().strftime('%d/%m/%Y')
        fecha_fin = df_limpio['fecha_hora'].max().strftime('%d/%m/%Y')
        st.metric("📅 Período", f"{fecha_inicio} - {fecha_fin}")
    
    st.divider()
    
    # --- SELECTOR DE MES (ANTES DE TODO) ---
    st.subheader("🔍 Selecciona el período a analizar")
    
    # Preparar datos temporales
    df_temp = df_limpio.copy()
    df_temp['hora_num'] = df_temp['fecha_hora'].dt.hour
    df_temp['dia_semana'] = df_temp['fecha_hora'].dt.day_name()
    df_temp['mes_num'] = df_temp['fecha_hora'].dt.month
    df_temp['año'] = df_temp['fecha_hora'].dt.year
    
    # Diccionario de meses
    meses_español = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Obtener meses disponibles con datos (ordenados por año y mes)
    meses_con_datos = df_temp.groupby(['año', 'mes_num'])['cantidad'].sum()
    meses_con_datos = meses_con_datos[meses_con_datos > 0].reset_index()
    
    # Crear opciones de selección con formato "Mes Año"
    meses_opciones = ['📊 Todos los datos']
    for _, row in meses_con_datos.iterrows():
        mes_nombre = meses_español[row['mes_num']]
        año = int(row['año'])
        meses_opciones.append(f"{mes_nombre} {año}")
    
    periodo_seleccionado = st.selectbox(
        "Elige qué datos quieres analizar:",
        meses_opciones,
        help="Selecciona un mes específico o analiza todos los datos juntos"
    )
    
    # Filtrar datos según selección
    if periodo_seleccionado == '📊 Todos los datos':
        df_analisis = df_temp.copy()
        titulo_periodo = "Todo el período"
    else:
        # Extraer mes y año de la selección (ej: "Octubre 2024")
        partes = periodo_seleccionado.split()
        mes_nombre = partes[0]
        año_sel = int(partes[1])
        mes_num_sel = [k for k, v in meses_español.items() if v == mes_nombre][0]
        
        df_analisis = df_temp[(df_temp['mes_num'] == mes_num_sel) & (df_temp['año'] == año_sel)].copy()
        titulo_periodo = periodo_seleccionado
    
    # Mostrar cuántos registros hay en el período seleccionado
    st.info(f"📋 Analizando **{len(df_analisis):,} registros** del período: **{titulo_periodo}**")
    
    st.divider()
    
    # --- HEATMAP DE HORAS PICO ---
    if not df_analisis.empty:
        st.subheader(f"🔥 Heatmap de Ventas - {titulo_periodo}")
        st.caption("Intensidad de ventas por día de la semana y hora del día")
        
        # Orden y traducción de días
        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_español = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        
        # Crear matriz de ventas por hora y día
        ventas_hora_dia = df_analisis.groupby(['dia_semana', 'hora_num'])['cantidad'].sum().reset_index()
        ventas_matriz = ventas_hora_dia.pivot(index='dia_semana', columns='hora_num', values='cantidad').fillna(0)
        
        # Reordenar días y traducir
        ventas_matriz = ventas_matriz.reindex([d for d in dias_orden if d in ventas_matriz.index])
        ventas_matriz.index = [dias_español[d] for d in ventas_matriz.index]
        
        # Crear heatmap con Plotly
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=ventas_matriz.values,
            x=ventas_matriz.columns,
            y=ventas_matriz.index,
            colorscale='YlOrRd',
            text=ventas_matriz.values.astype(int),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Unidades<br>vendidas")
        ))
        
        fig_heatmap.update_layout(
            xaxis_title="Hora del Día",
            yaxis_title="Día de la Semana",
            height=500,
            xaxis=dict(dtick=1)  # Mostrar todas las horas
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # --- MÉTRICAS CLAVE ---
        st.markdown("### 📊 Métricas del período seleccionado")
        
        # Encontrar hora y día pico
        idx_max = ventas_hora_dia['cantidad'].idxmax()
        hora_pico = int(ventas_hora_dia.loc[idx_max, 'hora_num'])
        dia_pico = dias_español[ventas_hora_dia.loc[idx_max, 'dia_semana']]
        cantidad_pico = int(ventas_hora_dia.loc[idx_max, 'cantidad'])
        
        # Calcular promedios
        promedio_por_hora = df_analisis.groupby('hora_num')['cantidad'].sum().mean()
        total_vendido = df_analisis['cantidad'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🕐 Hora Pico", f"{hora_pico}:00 hs", help="Hora con más ventas")
        with col2:
            st.metric("📅 Día Pico", dia_pico, help="Día con más ventas")
        with col3:
            st.metric("🔥 Ventas en Pico", f"{cantidad_pico} unidades", help="Cantidad vendida en el momento pico")
        with col4:
            st.metric("📦 Total Vendido", f"{int(total_vendido):,} unidades", help="Total de unidades en el período")
        
    else:
        st.warning("⚠️ No hay datos disponibles para el período seleccionado.")

except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
    st.info("Verifica que la URL del CSV sea correcta y que el archivo esté accesible.")



