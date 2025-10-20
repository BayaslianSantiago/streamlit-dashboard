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
        
        st.divider()
        
        # --- MATRIZ BCG ---
        st.subheader("📊 Matriz BCG - Boston Consulting Group")
        st.caption("Clasifica tus productos según participación de mercado y crecimiento")
        
        # Calcular participación de mercado (% de ventas de cada producto)
        ventas_por_producto = df_analisis.groupby('producto')['cantidad'].sum().reset_index()
        ventas_por_producto['participacion'] = (ventas_por_producto['cantidad'] / ventas_por_producto['cantidad'].sum()) * 100
        
        # Calcular tasa de crecimiento
        if periodo_seleccionado == '📊 Todos los datos':
            # Comparar primera mitad vs segunda mitad
            fecha_mitad = df_analisis['fecha_hora'].min() + (df_analisis['fecha_hora'].max() - df_analisis['fecha_hora'].min()) / 2
            df_periodo1 = df_analisis[df_analisis['fecha_hora'] < fecha_mitad]
            df_periodo2 = df_analisis[df_analisis['fecha_hora'] >= fecha_mitad]
            periodo_comparacion = "Primera mitad vs Segunda mitad"
        else:
            # Comparar mes seleccionado vs mes anterior
            mes_actual = mes_num_sel
            año_actual = año_sel
            
            # Calcular mes anterior
            if mes_actual == 1:
                mes_anterior = 12
                año_anterior = año_actual - 1
            else:
                mes_anterior = mes_actual - 1
                año_anterior = año_actual
            
            df_periodo1 = df_temp[(df_temp['mes_num'] == mes_anterior) & (df_temp['año'] == año_anterior)]
            df_periodo2 = df_analisis.copy()
            mes_ant_nombre = meses_español[mes_anterior]
            periodo_comparacion = f"{mes_ant_nombre} {año_anterior} vs {titulo_periodo}"
        
        # Ventas por producto en cada período
        ventas_p1 = df_periodo1.groupby('producto')['cantidad'].sum()
        ventas_p2 = df_periodo2.groupby('producto')['cantidad'].sum()
        
        # Calcular crecimiento (manejar productos nuevos o sin ventas previas)
        crecimiento = pd.DataFrame({
            'producto': ventas_p2.index,
            'ventas_periodo1': ventas_p2.index.map(lambda x: ventas_p1.get(x, 0)),
            'ventas_periodo2': ventas_p2.values
        })
        
        # Calcular % de crecimiento
        crecimiento['tasa_crecimiento'] = crecimiento.apply(
            lambda row: ((row['ventas_periodo2'] - row['ventas_periodo1']) / row['ventas_periodo1'] * 100) 
            if row['ventas_periodo1'] > 0 else 100,  # Si no había ventas antes, es 100% de crecimiento
            axis=1
        )
        
        # Unir con participación de mercado
        bcg_data = ventas_por_producto.merge(crecimiento[['producto', 'tasa_crecimiento']], on='producto')
        
        # Calcular promedios para los ejes
        participacion_media = bcg_data['participacion'].median()
        crecimiento_medio = bcg_data['tasa_crecimiento'].median()
        
        # Clasificar productos en cuadrantes
        def clasificar_bcg(row):
            if row['participacion'] >= participacion_media and row['tasa_crecimiento'] >= crecimiento_medio:
                return '⭐ Estrella'
            elif row['participacion'] >= participacion_media and row['tasa_crecimiento'] < crecimiento_medio:
                return '🐄 Vaca Lechera'
            elif row['participacion'] < participacion_media and row['tasa_crecimiento'] >= crecimiento_medio:
                return '❓ Interrogante'
            else:
                return '🐕 Perro'
        
        bcg_data['categoria'] = bcg_data.apply(clasificar_bcg, axis=1)
        
        # Crear scatter plot
        import plotly.express as px
        
        fig_bcg = px.scatter(
            bcg_data,
            x='participacion',
            y='tasa_crecimiento',
            size='cantidad',
            color='categoria',
            hover_name='producto',
            hover_data={
                'participacion': ':.2f',
                'tasa_crecimiento': ':.1f',
                'cantidad': ':,',
                'categoria': True
            },
            labels={
                'participacion': 'Participación de Mercado (%)',
                'tasa_crecimiento': 'Tasa de Crecimiento (%)',
                'categoria': 'Categoría'
            },
            color_discrete_map={
                '⭐ Estrella': '#FFD700',
                '🐄 Vaca Lechera': '#90EE90',
                '❓ Interrogante': '#87CEEB',
                '🐕 Perro': '#D3D3D3'
            },
            height=600
        )
        
        # Agregar líneas de división
        fig_bcg.add_hline(y=crecimiento_medio, line_dash="dash", line_color="gray", opacity=0.5)
        fig_bcg.add_vline(x=participacion_media, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Agregar anotaciones de cuadrantes
        fig_bcg.add_annotation(x=bcg_data['participacion'].max() * 0.9, y=bcg_data['tasa_crecimiento'].max() * 0.9,
                              text="⭐ ESTRELLAS", showarrow=False, font=dict(size=14, color="gray"))
        fig_bcg.add_annotation(x=bcg_data['participacion'].max() * 0.9, y=bcg_data['tasa_crecimiento'].min() * 0.9,
                              text="🐄 VACAS", showarrow=False, font=dict(size=14, color="gray"))
        fig_bcg.add_annotation(x=bcg_data['participacion'].min() * 1.1, y=bcg_data['tasa_crecimiento'].max() * 0.9,
                              text="❓ INTERROGANTES", showarrow=False, font=dict(size=14, color="gray"))
        fig_bcg.add_annotation(x=bcg_data['participacion'].min() * 1.1, y=bcg_data['tasa_crecimiento'].min() * 0.9,
                              text="🐕 PERROS", showarrow=False, font=dict(size=14, color="gray"))
        
        fig_bcg.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        
        st.plotly_chart(fig_bcg, use_container_width=True)
        
        # Info sobre el análisis
        st.info(f"📊 **Comparación:** {periodo_comparacion}")
        
        # Tabla resumen por categoría
        st.markdown("### 📋 Resumen por Categoría")
        
        resumen_categorias = bcg_data.groupby('categoria').agg({
            'producto': 'count',
            'cantidad': 'sum',
            'participacion': 'sum'
        }).reset_index()
        resumen_categorias.columns = ['Categoría', 'Cantidad de Productos', 'Unidades Vendidas', 'Participación Total (%)']
        resumen_categorias['Participación Total (%)'] = resumen_categorias['Participación Total (%)'].round(2)
        
        st.dataframe(resumen_categorias, use_container_width=True, hide_index=True)
        
        # Top productos por categoría
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⭐ Top 5 Estrellas")
            estrellas = bcg_data[bcg_data['categoria'] == '⭐ Estrella'].nlargest(5, 'cantidad')[['producto', 'cantidad', 'tasa_crecimiento']]
            if not estrellas.empty:
                estrellas['tasa_crecimiento'] = estrellas['tasa_crecimiento'].round(1).astype(str) + '%'
                st.dataframe(estrellas, use_container_width=True, hide_index=True)
            else:
                st.info("No hay productos en esta categoría")
        
        with col2:
            st.markdown("#### 🐕 Top 5 Perros (considerar eliminar)")
            perros = bcg_data[bcg_data['categoria'] == '🐕 Perro'].nsmallest(5, 'cantidad')[['producto', 'cantidad', 'tasa_crecimiento']]
            if not perros.empty:
                perros['tasa_crecimiento'] = perros['tasa_crecimiento'].round(1).astype(str) + '%'
                st.dataframe(perros, use_container_width=True, hide_index=True)
            else:
                st.info("No hay productos en esta categoría")
        
    else:
        st.warning("⚠️ No hay datos disponibles para el período seleccionado.")

except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
    st.info("Verifica que la URL del CSV sea correcta y que el archivo esté accesible.")


