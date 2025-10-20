import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# URL del CSV en GitHub
DATA_URL = "https://raw.githubusercontent.com/BayaslianSantiago/streamlit-dashboard/refs/heads/main/datos.csv"

@st.cache_data(ttl=3600)  # Cachea por 1 hora
def cargar_datos():
    """Carga los datos desde GitHub y prepara columnas temporales"""
    df = pd.read_csv(DATA_URL)
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    return df

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Análisis Fiambrería", page_icon="📊", layout="wide")
st.title("📊 Análisis de Ventas - Fiambrería")

# Cargar datos automáticamente
try:
    df_limpio = cargar_datos()
    
    # Mostrar info básica
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Total Registros", f"{len(df_limpio):,}")
    with col2:
        st.metric("🏷️ Productos Únicos", f"{df_limpio['producto'].nunique():,}")
    with col3:
        fecha_inicio = df_limpio['fecha_hora'].min().strftime('%d/%m/%Y')
        fecha_fin = df_limpio['fecha_hora'].max().strftime('%d/%m/%Y')
        st.metric("📅 Período", f"{fecha_inicio} - {fecha_fin}")
    
    st.divider()
    
    # --- ANÁLISIS DE PATRONES TEMPORALES ---
    st.subheader("⏰ Análisis de Patrones Temporales")
    
    if not df_limpio.empty:
        # Extraer componentes temporales
        df_temp = df_limpio.copy()
        df_temp['hora_num'] = df_temp['fecha_hora'].dt.hour
        df_temp['dia_semana'] = df_temp['fecha_hora'].dt.day_name()
        df_temp['dia_semana_num'] = df_temp['fecha_hora'].dt.dayofweek
        df_temp['mes'] = df_temp['fecha_hora'].dt.month_name()
        df_temp['mes_num'] = df_temp['fecha_hora'].dt.month
        
        # Orden correcto de días
        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_español = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 
                       'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
        
        # --- 1. HEATMAP: Horas pico de venta ---
        st.markdown("### 🔥 1. Heatmap de Ventas por Hora y Día")
        st.caption("Identifica las horas más activas de tu fiambrería")
        
        # Crear matriz de ventas por hora y día
        ventas_hora_dia = df_temp.groupby(['dia_semana', 'hora_num'])['cantidad'].sum().reset_index()
        ventas_matriz = ventas_hora_dia.pivot(index='dia_semana', columns='hora_num', values='cantidad').fillna(0)
        
        # Reordenar días
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
            colorbar=dict(title="Unidades")
        ))
        
        fig_heatmap.update_layout(
            title="Intensidad de Ventas por Día y Hora",
            xaxis_title="Hora del Día",
            yaxis_title="Día de la Semana",
            height=400
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Encontrar hora y día pico
        idx_max = ventas_hora_dia['cantidad'].idxmax()
        hora_pico = ventas_hora_dia.loc[idx_max, 'hora_num']
        dia_pico = dias_español[ventas_hora_dia.loc[idx_max, 'dia_semana']]
        cantidad_pico = ventas_hora_dia.loc[idx_max, 'cantidad']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🕐 Hora Pico", f"{int(hora_pico)}:00 hs")
        with col2:
            st.metric("📅 Día Pico", dia_pico)
        with col3:
            st.metric("📦 Unidades en Pico", f"{int(cantidad_pico)}")
        
        st.divider()
        
        # --- 2. DÍAS DE LA SEMANA MÁS RENTABLES ---
        st.markdown("### 📅 2. Comparativa de Ventas por Día de la Semana")
        st.caption("¿Qué días venden más en tu fiambrería?")
        
        ventas_dia = df_temp.groupby('dia_semana')['cantidad'].agg(['sum', 'mean', 'count']).reset_index()
        ventas_dia['dia_semana'] = pd.Categorical(ventas_dia['dia_semana'], categories=dias_orden, ordered=True)
        ventas_dia = ventas_dia.sort_values('dia_semana')
        ventas_dia['dia_español'] = ventas_dia['dia_semana'].map(dias_español)
        
        # Gráfico de barras
        fig_dias = px.bar(
            ventas_dia,
            x='dia_español',
            y='sum',
            title='Total de Unidades Vendidas por Día',
            labels={'sum': 'Unidades Vendidas', 'dia_español': 'Día'},
            color='sum',
            color_continuous_scale='Blues'
        )
        
        fig_dias.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_dias, use_container_width=True)
        
        # Métricas comparativas
        mejor_dia = ventas_dia.loc[ventas_dia['sum'].idxmax(), 'dia_español']
        peor_dia = ventas_dia.loc[ventas_dia['sum'].idxmin(), 'dia_español']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏆 Mejor Día", mejor_dia)
        with col2:
            st.metric("📉 Día Más Flojo", peor_dia)
        with col3:
            promedio_diario = ventas_dia['sum'].mean()
            st.metric("📊 Promedio Diario", f"{int(promedio_diario)} unidades")
        
        st.divider()
        
        # --- 3. ESTACIONALIDAD MENSUAL ---
        st.markdown("### 📆 3. Estacionalidad Mensual")
        st.caption("Tendencias de ventas a lo largo de los meses")
        
        # Ventas por mes - solo meses con datos
        ventas_mes = df_temp.groupby('mes_num')['cantidad'].sum().reset_index()
        ventas_mes = ventas_mes[ventas_mes['cantidad'] > 0]  # Filtrar meses sin datos
        
        meses_español = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        ventas_mes['mes'] = ventas_mes['mes_num'].map(meses_español)
        
        # Gráfico de línea
        fig_meses = px.line(
            ventas_mes,
            x='mes',
            y='cantidad',
            title='Evolución de Ventas Mensual',
            labels={'cantidad': 'Unidades Vendidas', 'mes': 'Mes'},
            markers=True
        )
        
        fig_meses.update_traces(line_color='#FF6B6B', line_width=3, marker=dict(size=10))
        fig_meses.update_layout(height=400)
        st.plotly_chart(fig_meses, use_container_width=True)
        
        # Top productos por mes
        st.markdown("#### 🔍 Productos más vendidos por mes")
        mes_seleccionado = st.selectbox("Selecciona un mes", ventas_mes['mes'].tolist())
        
        mes_num = [k for k, v in meses_español.items() if v == mes_seleccionado][0]
        df_mes = df_temp[df_temp['mes_num'] == mes_num]
        
        top_productos_mes = df_mes.groupby('producto')['cantidad'].sum().nlargest(10).reset_index()
        
        fig_top_mes = px.bar(
            top_productos_mes,
            x='cantidad',
            y='producto',
            orientation='h',
            title=f'Top 10 Productos en {mes_seleccionado}',
            labels={'cantidad': 'Unidades', 'producto': 'Producto'}
        )
        
        st.plotly_chart(fig_top_mes, use_container_width=True)
        
    else:
        st.warning("No hay datos disponibles para análisis temporal.")

except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
    st.info("Verifica que la URL del CSV sea correcta y que el archivo esté accesible.")

