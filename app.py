import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from itertools import combinations
from collections import Counter

# URL del CSV en GitHub
DATA_URL = "https://raw.githubusercontent.com/BayaslianSantiago/streamlit-dashboard/refs/heads/main/datos.csv"

@st.cache_data(ttl=3600)
def cargar_datos():
    """Carga los datos desde GitHub y prepara columnas temporales"""
    df = pd.read_csv(DATA_URL)
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    df = df.sort_values('fecha_hora').reset_index(drop=True)
    return df

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Análisis Fiambrería", page_icon="📊", layout="wide")
st.title("📊 Dashboard de Ventas - Fiambrería")

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
    
    # --- SELECTOR DE MES ---
    st.subheader("🔍 Selecciona el período a analizar")
    
    # Preparar datos temporales
    df_temp = df_limpio.copy()
    df_temp['hora_num'] = df_temp['fecha_hora'].dt.hour
    df_temp['minuto'] = df_temp['fecha_hora'].dt.minute
    df_temp['media_hora'] = df_temp['hora_num'] + (df_temp['minuto'] >= 30).astype(int) * 0.5
    df_temp['dia_semana'] = df_temp['fecha_hora'].dt.day_name()
    df_temp['mes_num'] = df_temp['fecha_hora'].dt.month
    df_temp['año'] = df_temp['fecha_hora'].dt.year
    df_temp['semana_del_mes'] = ((df_temp['fecha_hora'].dt.day - 1) // 7) + 1
    
    # Diccionario de meses
    meses_español = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    dias_español = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles', 
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    
    dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Obtener meses disponibles con datos
    meses_con_datos = df_temp.groupby(['año', 'mes_num'])['cantidad'].sum()
    meses_con_datos = meses_con_datos[meses_con_datos > 0].reset_index()
    
    # Crear opciones de selección
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
        mes_num_sel = None
        año_sel = None
    else:
        partes = periodo_seleccionado.split()
        mes_nombre = partes[0]
        año_sel = int(partes[1])
        mes_num_sel = [k for k, v in meses_español.items() if v == mes_nombre][0]
        
        df_analisis = df_temp[(df_temp['mes_num'] == mes_num_sel) & (df_temp['año'] == año_sel)].copy()
        titulo_periodo = periodo_seleccionado
    
    st.info(f"📋 Analizando **{len(df_analisis):,} registros** del período: **{titulo_periodo}**")
    
    st.divider()
    
    # --- TABS PRINCIPALES ---
    if not df_analisis.empty:
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Resumen General", 
            "🔥 Análisis de Horarios", 
            "📊 Análisis de Productos",
            "🔍 Búsqueda Detallada",
            "🛒 Análisis de Canastas"
        ])
        
        # ========== TAB 1: RESUMEN GENERAL ==========
        with tab1:
            st.markdown("### 📊 Métricas Principales")
            
            # Métricas clave
            ventas_hora_dia = df_analisis.groupby(['dia_semana', 'hora_num'])['cantidad'].sum().reset_index()
            idx_max = ventas_hora_dia['cantidad'].idxmax()
            hora_pico = int(ventas_hora_dia.loc[idx_max, 'hora_num'])
            dia_pico = dias_español[ventas_hora_dia.loc[idx_max, 'dia_semana']]
            cantidad_pico = int(ventas_hora_dia.loc[idx_max, 'cantidad'])
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
            
            # Gráfico de ventas por día
            st.markdown("### 📅 Ventas por Día de la Semana")
            ventas_por_dia = df_analisis.groupby('dia_semana')['cantidad'].sum().reset_index()
            ventas_por_dia['dia_español'] = ventas_por_dia['dia_semana'].map(dias_español)
            ventas_por_dia = ventas_por_dia.set_index('dia_semana').reindex(dias_orden).reset_index()
            
            fig_dias = go.Figure(data=[
                go.Bar(
                    x=[dias_español[d] for d in ventas_por_dia['dia_semana']],
                    y=ventas_por_dia['cantidad'],
                    marker_color='#1E90FF',
                    text=ventas_por_dia['cantidad'],
                    textposition='auto'
                )
            ])
            fig_dias.update_layout(
                height=400,
                xaxis_title="Día de la Semana",
                yaxis_title="Unidades Vendidas",
                showlegend=False
            )
            st.plotly_chart(fig_dias, use_container_width=True)
            
            # Gráfico de ventas por hora
            st.markdown("### 🕐 Ventas por Hora del Día")
            ventas_por_hora = df_analisis.groupby('hora_num')['cantidad'].sum().reset_index()
            
            fig_horas = go.Figure(data=[
                go.Scatter(
                    x=ventas_por_hora['hora_num'],
                    y=ventas_por_hora['cantidad'],
                    mode='lines+markers',
                    line=dict(color='#32CD32', width=3),
                    marker=dict(size=8),
                    fill='tozeroy',
                    fillcolor='rgba(50,205,50,0.2)'
                )
            ])
            fig_horas.update_layout(
                height=400,
                xaxis_title="Hora del Día",
                yaxis_title="Unidades Vendidas",
                showlegend=False,
                xaxis=dict(dtick=2)
            )
            st.plotly_chart(fig_horas, use_container_width=True)
        
        # ========== TAB 2: ANÁLISIS DE HORARIOS ==========
        with tab2:
            st.markdown("### 🔥 Heatmap de Ventas por Media Hora")
            st.caption("Intensidad de ventas por día de la semana cada 30 minutos")
            
            # Crear matriz por media hora
            ventas_media_hora = df_analisis.groupby(['dia_semana', 'media_hora'])['cantidad'].sum().reset_index()
            ventas_matriz_mh = ventas_media_hora.pivot(index='dia_semana', columns='media_hora', values='cantidad').fillna(0)
            
            # Reordenar y traducir
            ventas_matriz_mh = ventas_matriz_mh.reindex([d for d in dias_orden if d in ventas_matriz_mh.index])
            ventas_matriz_mh.index = [dias_español[d] for d in ventas_matriz_mh.index]
            
            # Crear etiquetas para el eje X
            etiquetas_horas = [f"{int(h)}:{('00' if h % 1 == 0 else '30')}" for h in ventas_matriz_mh.columns]
            
            fig_heatmap_mh = go.Figure(data=go.Heatmap(
                z=ventas_matriz_mh.values,
                x=etiquetas_horas,
                y=ventas_matriz_mh.index,
                colorscale='YlOrRd',
                text=ventas_matriz_mh.values.astype(int),
                texttemplate='%{text}',
                textfont={"size": 9},
                colorbar=dict(title="Unidades<br>vendidas")
            ))
            
            fig_heatmap_mh.update_layout(
                xaxis_title="Hora del Día",
                yaxis_title="Día de la Semana",
                height=500,
                xaxis=dict(tickangle=-45)
            )
            
            st.plotly_chart(fig_heatmap_mh, use_container_width=True)
            
            # Heatmap por semana del mes (solo si es un mes específico)
            if mes_num_sel is not None:
                with st.expander("📅 Ver Heatmap por Semana del Mes", expanded=False):
                    st.caption("Intensidad de ventas por semana y día de la semana")
                    
                    ventas_semana = df_analisis.groupby(['semana_del_mes', 'dia_semana'])['cantidad'].sum().reset_index()
                    ventas_matriz_sem = ventas_semana.pivot(index='semana_del_mes', columns='dia_semana', values='cantidad').fillna(0)
                    
                    # Reordenar columnas por día de la semana
                    dias_disponibles = [d for d in dias_orden if d in ventas_matriz_sem.columns]
                    ventas_matriz_sem = ventas_matriz_sem[dias_disponibles]
                    ventas_matriz_sem.columns = [dias_español[d] for d in ventas_matriz_sem.columns]
                    
                    # Renombrar índice
                    ventas_matriz_sem.index = [f"Semana {int(s)}" for s in ventas_matriz_sem.index]
                    
                    fig_heatmap_sem = go.Figure(data=go.Heatmap(
                        z=ventas_matriz_sem.values,
                        x=ventas_matriz_sem.columns,
                        y=ventas_matriz_sem.index,
                        colorscale='Viridis',
                        text=ventas_matriz_sem.values.astype(int),
                        texttemplate='%{text}',
                        textfont={"size": 12},
                        colorbar=dict(title="Unidades<br>vendidas")
                    ))
                    
                    fig_heatmap_sem.update_layout(
                        xaxis_title="Día de la Semana",
                        yaxis_title="Semana del Mes",
                        height=400
                    )
                    
                    st.plotly_chart(fig_heatmap_sem, use_container_width=True)
        
        # ========== TAB 3: ANÁLISIS DE PRODUCTOS ==========
        with tab3:
            # Calcular datos BCG
            ventas_por_producto = df_analisis.groupby('producto')['cantidad'].sum().reset_index()
            ventas_por_producto['participacion'] = (ventas_por_producto['cantidad'] / ventas_por_producto['cantidad'].sum()) * 100
            
            # Calcular tasa de crecimiento
            if periodo_seleccionado == '📊 Todos los datos':
                fecha_mitad = df_analisis['fecha_hora'].min() + (df_analisis['fecha_hora'].max() - df_analisis['fecha_hora'].min()) / 2
                df_periodo1 = df_analisis[df_analisis['fecha_hora'] < fecha_mitad]
                df_periodo2 = df_analisis[df_analisis['fecha_hora'] >= fecha_mitad]
                periodo_comparacion = "Primera mitad vs Segunda mitad"
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
                mes_ant_nombre = meses_español[mes_anterior]
                periodo_comparacion = f"{mes_ant_nombre} {año_anterior} vs {titulo_periodo}"
            
            ventas_p1 = df_periodo1.groupby('producto')['cantidad'].sum()
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
            
            bcg_data = ventas_por_producto.merge(crecimiento[['producto', 'tasa_crecimiento']], on='producto')
            
            participacion_media = bcg_data['participacion'].median()
            crecimiento_medio = bcg_data['tasa_crecimiento'].median()
            
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
            
            # Subtabs dentro de Análisis de Productos
            subtab1, subtab2, subtab3 = st.tabs(["📊 Matriz BCG", "🏆 Ranking", "📋 Resumen por Categoría"])
            
            with subtab1:
                st.markdown("### 📊 Matriz BCG - Boston Consulting Group")
                st.caption("Clasifica tus productos según participación de mercado y crecimiento")
                
                # Filtrar productos relevantes
                bcg_data_plot = bcg_data[
                    (bcg_data['participacion'] >= 0.5) | 
                    (bcg_data['cantidad'].rank(ascending=False) <= 40)
                ].copy()
                
                st.info(f"📌 Mostrando {len(bcg_data_plot)} productos más relevantes de {len(bcg_data)} totales")
                
                bcg_data_plot['tasa_crecimiento_plot'] = bcg_data_plot['tasa_crecimiento'].clip(-100, 300)
                
                # GRÁFICO BCG
                fig_bcg = go.Figure()
                
                categorias = {
                    '⭐ Estrella': '#FFD700',
                    '🐄 Vaca Lechera': '#32CD32',
                    '❓ Interrogante': '#1E90FF',
                    '🐕 Perro': '#DC143C'
                }
                
                top_por_categoria = 8
                
                for cat, color in categorias.items():
                    df_cat = bcg_data_plot[bcg_data_plot['categoria'] == cat].nlargest(top_por_categoria, 'cantidad')
                    if not df_cat.empty:
                        sizes = 15 + (df_cat['cantidad'] / bcg_data_plot['cantidad'].max()) * 35
                        
                        fig_bcg.add_trace(go.Scatter(
                            x=df_cat['participacion'],
                            y=df_cat['tasa_crecimiento_plot'],
                            mode='markers',
                            name=cat,
                            marker=dict(
                                size=sizes,
                                color=color,
                                line=dict(width=1, color='white'),
                                opacity=0.7
                            ),
                            text=df_cat['producto'],
                            hovertemplate='<b>%{text}</b><br>' +
                                          'Participación: %{x:.2f}%<br>' +
                                          'Crecimiento: %{y:.1f}%<br>' +
                                          '<extra></extra>'
                        ))
                
                # Líneas divisorias
                fig_bcg.add_hline(y=crecimiento_medio, line_dash="dash", line_color="gray", line_width=2)
                fig_bcg.add_vline(x=participacion_media, line_dash="dash", line_color="gray", line_width=2)
                
                # Etiquetas de cuadrantes
                max_x = bcg_data_plot['participacion'].max()
                min_x = bcg_data_plot['participacion'].min()
                max_y = bcg_data_plot['tasa_crecimiento_plot'].max()
                min_y = bcg_data_plot['tasa_crecimiento_plot'].min()
                
                fig_bcg.add_annotation(x=participacion_media + (max_x - participacion_media) * 0.5, 
                                       y=crecimiento_medio + (max_y - crecimiento_medio) * 0.9,
                                       text="⭐ ESTRELLAS", showarrow=False,
                                       font=dict(size=14, color='gray'))
                
                fig_bcg.add_annotation(x=participacion_media + (max_x - participacion_media) * 0.5,
                                       y=min_y + (crecimiento_medio - min_y) * 0.1,
                                       text="🐄 VACAS LECHERAS", showarrow=False,
                                       font=dict(size=14, color='gray'))
                
                fig_bcg.add_annotation(x=min_x + (participacion_media - min_x) * 0.5,
                                       y=crecimiento_medio + (max_y - crecimiento_medio) * 0.9,
                                       text="❓ INTERROGANTES", showarrow=False,
                                       font=dict(size=14, color='gray'))
                
                fig_bcg.add_annotation(x=min_x + (participacion_media - min_x) * 0.5,
                                       y=min_y + (crecimiento_medio - min_y) * 0.1,
                                       text="🐕 PERROS", showarrow=False,
                                       font=dict(size=14, color='gray'))
                
                fig_bcg.update_layout(
                    height=600,
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.02,
                        font=dict(size=12)
                    ),
                    plot_bgcolor='white',
                    xaxis=dict(
                        title="Participación de Mercado (%)",
                        gridcolor='lightgray',
                        showgrid=True
                    ),
                    yaxis=dict(
                        title="Tasa de Crecimiento (%)",
                        gridcolor='lightgray',
                        showgrid=True
                    )
                )
                
                st.plotly_chart(fig_bcg, use_container_width=True)
                st.info(f"📊 **Comparación:** {periodo_comparacion}")
            
            with subtab2:
                st.markdown("### 🏆 Ranking de Productos")
                
                # Opciones de ranking
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    criterio_ranking = st.selectbox(
                        "Ordenar por:",
                        ["📊 Unidades Vendidas", "📈 Participación de Mercado (%)", "🔥 Tasa de Crecimiento (%)", "🏷️ Categoría BCG"],
                        help="Selecciona el criterio para ordenar los productos"
                    )
                
                with col2:
                    orden = st.radio("Orden:", ["⬇️ Mayor a Menor", "⬆️ Menor a Mayor"], horizontal=True)
                
                with col3:
                    limite = st.selectbox("Mostrar:", [10, 20, 50, 100, "Todos"], index=1)
                
                # Preparar datos para el ranking
                ranking_data = bcg_data.copy()
                
                # Definir columna de ordenamiento
                if criterio_ranking == "📊 Unidades Vendidas":
                    col_orden = 'cantidad'
                elif criterio_ranking == "📈 Participación de Mercado (%)":
                    col_orden = 'participacion'
                elif criterio_ranking == "🔥 Tasa de Crecimiento (%)":
                    col_orden = 'tasa_crecimiento'
                else:
                    col_orden = 'categoria'
                
                # Ordenar datos
                ascending = True if orden == "⬆️ Menor a Mayor" else False
                ranking_data = ranking_data.sort_values(col_orden, ascending=ascending).reset_index(drop=True)
                
                # Aplicar límite
                if limite != "Todos":
                    ranking_data = ranking_data.head(limite)
                
                # Agregar columna de ranking
                ranking_data.insert(0, '#', range(1, len(ranking_data) + 1))
                
                # Preparar tabla para mostrar
                tabla_ranking = ranking_data[['#', 'producto', 'cantidad', 'participacion', 'tasa_crecimiento', 'categoria']].copy()
                tabla_ranking.columns = ['#', 'Producto', 'Unidades Vendidas', 'Participación (%)', 'Crecimiento (%)', 'Categoría BCG']
                
                # Formatear números
                tabla_ranking['Unidades Vendidas'] = tabla_ranking['Unidades Vendidas'].apply(lambda x: f"{int(x):,}")
                tabla_ranking['Participación (%)'] = tabla_ranking['Participación (%)'].apply(lambda x: f"{x:.2f}%")
                tabla_ranking['Crecimiento (%)'] = tabla_ranking['Crecimiento (%)'].apply(lambda x: f"{x:+.1f}%")
                
                # Mostrar tabla
                st.dataframe(
                    tabla_ranking,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "#": st.column_config.NumberColumn("#", help="Posición en el ranking", width="small"),
                        "Producto": st.column_config.TextColumn("Producto", width="large"),
                        "Categoría BCG": st.column_config.TextColumn("Categoría BCG", width="medium")
                    }
                )
                
                # Estadísticas del ranking
                with st.expander("📊 Ver Estadísticas del Ranking", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    productos_mostrados = len(tabla_ranking)
                    total_unidades = ranking_data['cantidad'].sum()
                    participacion_total = ranking_data['participacion'].sum()
                    promedio_crecimiento = ranking_data['tasa_crecimiento'].mean()
                    
                    with col1:
                        st.metric("📦 Productos", f"{productos_mostrados}")
                    with col2:
                        st.metric("🛒 Unidades Totales", f"{int(total_unidades):,}")
                    with col3:
                        st.metric("📈 Participación Total", f"{participacion_total:.1f}%")
                    with col4:
                        st.metric("📊 Crecimiento Promedio", f"{promedio_crecimiento:+.1f}%")
            
            with subtab3:
                st.markdown("### 📋 Resumen por Categoría BCG")
                
                resumen_categorias = bcg_data.groupby('categoria').agg({
                    'producto': 'count',
                    'cantidad': 'sum',
                    'participacion': 'sum'
                }).reset_index()
                resumen_categorias.columns = ['Categoría', 'Cantidad de Productos', 'Unidades Vendidas', 'Participación Total (%)']
                resumen_categorias['Participación Total (%)'] = resumen_categorias['Participación Total (%)'].round(2)
                
                st.dataframe(resumen_categorias, use_container_width=True, hide_index=True)
                
                # Gráficos de distribución
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_dist_cat = go.Figure(data=[
                        go.Pie(
                            labels=resumen_categorias['Categoría'],
                            values=resumen_categorias['Cantidad de Productos'],
                            hole=0.4,
                            marker=dict(colors=['#FFD700', '#32CD32', '#1E90FF', '#DC143C'])
                        )
                    ])
                    fig_dist_cat.update_layout(title="Productos por Categoría", height=350)
                    st.plotly_chart(fig_dist_cat, use_container_width=True)
                
                with col2:
                    fig_dist_ventas = go.Figure(data=[
                        go.Pie(
                            labels=resumen_categorias['Categoría'],
                            values=resumen_categorias['Unidades Vendidas'],
                            hole=0.4,
                            marker=dict(colors=['#FFD700', '#32CD32', '#1E90FF', '#DC143C'])
                        )
                    ])
                    fig_dist_ventas.update_layout(title="Ventas por Categoría", height=350)
                    st.plotly_chart(fig_dist_ventas, use_container_width=True)
                
                # Top productos por categoría
                with st.expander("⭐ Ver Top Productos por Categoría", expanded=False):
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
        
        # ========== TAB 4: BÚSQUEDA DETALLADA ==========
        with tab4:
            st.markdown("### 🔍 Buscador de Productos")
            st.caption("Busca y analiza cualquier producto en detalle")
            
            # Selector de producto
            productos_disponibles = sorted(df_analisis['producto'].unique())
            producto_seleccionado = st.selectbox(
                "Selecciona un producto:",
                productos_disponibles,
                help="Elige un producto para ver su análisis completo"
            )
            
            if producto_seleccionado:
                # Filtrar datos del producto
                df_producto = df_analisis[df_analisis['producto'] == producto_seleccionado].copy()
                
                # Obtener información BCG del producto
                info_bcg = bcg_data[bcg_data['producto'] == producto_seleccionado].iloc[0]
                
                # Métricas principales del producto
                st.markdown(f"### 📦 {producto_seleccionado}")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("🏷️ Categoría BCG", info_bcg['categoria'])
                with col2:
                    st.metric("📊 Unidades Vendidas", f"{int(info_bcg['cantidad']):,}")
                with col3:
                    st.metric("📈 Participación", f"{info_bcg['participacion']:.2f}%")
                with col4:
                    st.metric("📉 Crecimiento", f"{info_bcg['tasa_crecimiento']:.1f}%")
                with col5:
                    ranking = bcg_data['cantidad'].rank(ascending=False)[bcg_data['producto'] == producto_seleccionado].values[0]
                    st.metric("🏆 Ranking", f"#{int(ranking)}")
                
                st.divider()
                
                # Gráficos del producto en dos columnas
                col1, col2 = st.columns(2)
                
                with col1:
                    # Ventas por día de la semana
                    st.markdown("#### 📅 Ventas por Día de la Semana")
                    ventas_dia = df_producto.groupby('dia_semana')['cantidad'].sum().reset_index()
                    ventas_dia['dia_semana'] = ventas_dia['dia_semana'].map(dias_español)
                    ventas_dia = ventas_dia.set_index('dia_semana').reindex([dias_español[d] for d in dias_orden if d in df_producto['dia_semana'].unique()])
                    
                    fig_dias = go.Figure(data=[
                        go.Bar(x=ventas_dia.index, y=ventas_dia['cantidad'].values, 
                               marker_color='#1E90FF',
                               text=ventas_dia['cantidad'].values,
                               textposition='auto')
                    ])
                    fig_dias.update_layout(
                        height=350,
                        xaxis_title="Día",
                        yaxis_title="Unidades",
                        showlegend=False
                    )
                    st.plotly_chart(fig_dias, use_container_width=True)
                
                with col2:
                    # Ventas por hora
                    st.markdown("#### 🕐 Ventas por Hora del Día")
                    ventas_hora = df_producto.groupby('hora_num')['cantidad'].sum().reset_index()
                    
                    fig_horas = go.Figure(data=[
                        go.Scatter(x=ventas_hora['hora_num'], y=ventas_hora['cantidad'],
                                  mode='lines+markers',
                                  line=dict(color='#32CD32', width=3),
                                  marker=dict(size=8),
                                  fill='tozeroy',
                                  fillcolor='rgba(50,205,50,0.2)')
                    ])
                    fig_horas.update_layout(
                        height=350,
                        xaxis_title="Hora",
                        yaxis_title="Unidades",
                        showlegend=False,
                        xaxis=dict(dtick=2)
                    )
                    st.plotly_chart(fig_horas, use_container_width=True)
                
                # Tendencia temporal
                with st.expander("📈 Ver Tendencia de Ventas en el Tiempo", expanded=True):
                    df_producto_tiempo = df_producto.copy()
                    df_producto_tiempo['fecha'] = df_producto_tiempo['fecha_hora'].dt.date
                    ventas_tiempo = df_producto_tiempo.groupby('fecha')['cantidad'].sum().reset_index()
                    
                    fig_tendencia = go.Figure(data=[
                        go.Scatter(x=ventas_tiempo['fecha'], y=ventas_tiempo['cantidad'],
                                  mode='lines+markers',
                                  line=dict(color='#FFD700', width=2),
                                  marker=dict(size=6),
                                  fill='tozeroy',
                                  fillcolor='rgba(255,215,0,0.2)')
                    ])
                    fig_tendencia.update_layout(
                        height=300,
                        xaxis_title="Fecha",
                        yaxis_title="Unidades Vendidas",
                        showlegend=False
                    )
                    st.plotly_chart(fig_tendencia, use_container_width=True)
                
                # Estadísticas adicionales
                with st.expander("📊 Ver Estadísticas Detalladas", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("##### 📊 Estadísticas")
                        promedio_diario = df_producto_tiempo.groupby('fecha')['cantidad'].sum().mean()
                        st.write(f"**Promedio diario:** {promedio_diario:.1f} unidades")
                        st.write(f"**Máximo en un día:** {df_producto_tiempo.groupby('fecha')['cantidad'].sum().max():.0f} unidades")
                        st.write(f"**Mínimo en un día:** {df_producto_tiempo.groupby('fecha')['cantidad'].sum().min():.0f} unidades")
                    
                    with col2:
                        st.markdown("##### 🕐 Hora Pico")
                        hora_pico_prod = ventas_hora.loc[ventas_hora['cantidad'].idxmax(), 'hora_num']
                        cantidad_hora_pico = ventas_hora['cantidad'].max()
                        st.write(f"**Mejor hora:** {int(hora_pico_prod)}:00 hs")
                        st.write(f"**Ventas en pico:** {int(cantidad_hora_pico)} unidades")
                    
                    with col3:
                        st.markdown("##### 📅 Día Pico")
                        dia_pico_prod = ventas_dia.idxmax()
                        cantidad_dia_pico = ventas_dia.max()
                        st.write(f"**Mejor día:** {dia_pico_prod}")
                        st.write(f"**Ventas en pico:** {int(cantidad_dia_pico)} unidades")
        
        # ========== TAB 5: ANÁLISIS DE CANASTAS ==========
        with tab5:
            st.markdown("### 🛒 Análisis de Canastas de Compra")
            st.caption("Descubre qué productos se compran juntos en la misma transacción")
            
            # Agrupar productos vendidos en la misma fecha y hora (misma transacción)
            df_transacciones = df_analisis.copy()
            df_transacciones['transaccion_id'] = df_transacciones['fecha_hora'].astype(str)
            
            # Crear canastas: productos agrupados por transacción
            canastas = df_transacciones.groupby('transaccion_id')['producto'].apply(list).reset_index()
            canastas['num_productos'] = canastas['producto'].apply(len)
            
            # Filtrar solo transacciones con más de 1 producto
            canastas_multiples = canastas[canastas['num_productos'] > 1].copy()
            
            # Métricas generales
            st.markdown("#### 📊 Estadísticas Generales")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_transacciones = len(canastas)
            transacciones_multiples = len(canastas_multiples)
            pct_multiples = (transacciones_multiples / total_transacciones * 100) if total_transacciones > 0 else 0
            promedio_productos = canastas['num_productos'].mean()
            
            with col1:
                st.metric(
                    "🛒 Total Transacciones",
                    f"{total_transacciones:,}",
                    help="Número total de compras registradas"
                )
            
            with col2:
                st.metric(
                    "📦 Transacciones Múltiples",
                    f"{transacciones_multiples:,}",
                    delta=f"{pct_multiples:.1f}%",
                    help="Compras con más de 1 producto"
                )
            
            with col3:
                st.metric(
                    "📊 Promedio Productos/Venta",
                    f"{promedio_productos:.1f}",
                    help="Cantidad promedio de productos por transacción"
                )
            
            with col4:
                max_productos = canastas['num_productos'].max()
                st.metric(
                    "🎯 Máximo en una Venta",
                    f"{max_productos}",
                    help="Mayor cantidad de productos en una sola transacción"
                )
            
            st.divider()
            
            if len(canastas_multiples) == 0:
                st.warning("⚠️ No se encontraron transacciones con múltiples productos en el período seleccionado")
            else:
                # Encontrar pares de productos más frecuentes
                st.markdown("#### 🔗 Productos que se Compran Juntos")
                
                # Calcular todas las combinaciones de pares
                pares = []
                for productos in canastas_multiples['producto']:
                    if len(productos) >= 2:
                        # Generar todos los pares posibles
                        for combo in combinations(sorted(productos), 2):
                            pares.append(combo)
                
                # Contar frecuencia de cada par
                contador_pares = Counter(pares)
                top_pares = contador_pares.most_common(20)
                
                if len(top_pares) > 0:
                    # Selector de cantidad a mostrar
                    num_mostrar = st.slider(
                        "Cantidad de combinaciones a mostrar:",
                        min_value=5,
                        max_value=min(20, len(top_pares)),
                        value=min(10, len(top_pares)),
                        step=5
                    )
                    
                    # Crear dataframe de pares
                    df_pares = pd.DataFrame(top_pares[:num_mostrar], columns=['Par', 'Frecuencia'])
                    df_pares['Producto 1'] = df_pares['Par'].apply(lambda x: x[0])
                    df_pares['Producto 2'] = df_pares['Par'].apply(lambda x: x[1])
                    
                    # Calcular soporte (% de transacciones que contienen este par)
                    df_pares['Soporte (%)'] = (df_pares['Frecuencia'] / len(canastas_multiples) * 100).round(2)
                    
                    # Gráfico de barras
                    df_pares['Combinación'] = df_pares.apply(
                        lambda row: f"{row['Producto 1'][:20]} + {row['Producto 2'][:20]}", 
                        axis=1
                    )
                    
                    fig_pares = go.Figure(data=[
                        go.Bar(
                            y=df_pares['Combinación'][::-1],
                            x=df_pares['Frecuencia'][::-1],
                            orientation='h',
                            marker_color='#1E90FF',
                            text=df_pares['Frecuencia'][::-1],
                            textposition='auto',
                            hovertemplate='<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>'
                        )
                    ])
                    
                    fig_pares.update_layout(
                        title="Top Combinaciones de Productos",
                        xaxis_title="Frecuencia (veces que se compraron juntos)",
                        yaxis_title="",
                        height=max(400, num_mostrar * 40),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_pares, use_container_width=True)
                    
                    # Tabla detallada
                    st.markdown("#### 📋 Tabla Detallada de Combinaciones")
                    
                    tabla_pares = df_pares[['Producto 1', 'Producto 2', 'Frecuencia', 'Soporte (%)']].copy()
                    st.dataframe(tabla_pares, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    # Análisis de triples (si existen)
                    st.markdown("#### 🎯 Combinaciones de 3 Productos")
                    
                    triples = []
                    for productos in canastas_multiples['producto']:
                        if len(productos) >= 3:
                            for combo in combinations(sorted(productos), 3):
                                triples.append(combo)
                    
                    if len(triples) > 0:
                        contador_triples = Counter(triples)
                        top_triples = contador_triples.most_common(10)
                        
                        df_triples = pd.DataFrame(top_triples, columns=['Triple', 'Frecuencia'])
                        df_triples['Producto 1'] = df_triples['Triple'].apply(lambda x: x[0])
                        df_triples['Producto 2'] = df_triples['Triple'].apply(lambda x: x[1])
                        df_triples['Producto 3'] = df_triples['Triple'].apply(lambda x: x[2])
                        df_triples['Soporte (%)'] = (df_triples['Frecuencia'] / len(canastas_multiples) * 100).round(2)
                        
                        tabla_triples = df_triples[['Producto 1', 'Producto 2', 'Producto 3', 'Frecuencia', 'Soporte (%)']].copy()
                        st.dataframe(tabla_triples, use_container_width=True, hide_index=True)
                    else:
                        st.info("No se encontraron transacciones con 3 o más productos diferentes")
                    
                    st.divider()
                    
                    # RECOMENDACIONES AUTOMÁTICAS
                    st.markdown("#### 💡 Recomendaciones de Negocio")
                    
                    recomendaciones = []
                    
                    # Top combo
                    top_combo = df_pares.iloc[0]
                    recomendaciones.append({
                        "tipo": "🏆 COMBO MÁS POPULAR",
                        "mensaje": f"**{top_combo['Producto 1']}** + **{top_combo['Producto 2']}**",
                        "detalle": f"Se compran juntos en {top_combo['Frecuencia']} ocasiones ({top_combo['Soporte (%)']}% de las transacciones)",
                        "accion": "• Crear promoción de combo\n• Colocar productos cercanos físicamente\n• Destacar en marketing"
                    })
                    
                    # Oportunidades de cross-selling
                    if len(df_pares) >= 3:
                        recomendaciones.append({
                            "tipo": "🎯 OPORTUNIDADES DE CROSS-SELLING",
                            "mensaje": f"Identificadas **{num_mostrar}** combinaciones frecuentes",
                            "detalle": "Productos con alta afinidad que se pueden potenciar",
                            "accion": "• Entrenar al personal para sugerir estos productos\n• Crear paquetes promocionales\n• Señalización en punto de venta"
                        })
                    
                    # Análisis de ticket promedio
                    ticket_simple = canastas[canastas['num_productos'] == 1]['num_productos'].count()
                    if transacciones_multiples > ticket_simple:
                        recomendaciones.append({
                            "tipo": "📈 ESTRATEGIA DE TICKET PROMEDIO",
                            "mensaje": f"**{pct_multiples:.1f}%** de tus clientes compran múltiples productos",
                            "detalle": f"Hay {transacciones_multiples:,} transacciones con más de 1 producto",
                            "accion": "• Incentivos para compras múltiples\n• Descuentos por volumen\n• Bundling estratégico"
                        })
                    
                    # Mostrar recomendaciones
                    for rec in recomendaciones:
                        with st.container():
                            st.markdown(f"**{rec['tipo']}**")
                            st.success(rec['mensaje'])
                            st.info(rec['detalle'])
                            st.markdown(rec['accion'])
                            st.markdown("---")
                    
                    # Análisis por horario
                    with st.expander("🕐 Ver Análisis de Canastas por Horario", expanded=False):
                        st.markdown("##### Tamaño de Canasta por Hora del Día")
                        
                        df_trans_hora = df_analisis.copy()
                        df_trans_hora['hora'] = df_trans_hora['fecha_hora'].dt.hour
                        df_trans_hora['transaccion_id'] = df_trans_hora['fecha_hora'].astype(str)
                        
                        productos_por_hora = df_trans_hora.groupby(['transaccion_id', 'hora']).size().reset_index(name='productos_en_canasta')
                        promedio_por_hora = productos_por_hora.groupby('hora')['productos_en_canasta'].mean().reset_index()
                        
                        fig_hora = go.Figure(data=[
                            go.Scatter(
                                x=promedio_por_hora['hora'],
                                y=promedio_por_hora['productos_en_canasta'],
                                mode='lines+markers',
                                line=dict(color='#32CD32', width=3),
                                marker=dict(size=8),
                                fill='tozeroy',
                                fillcolor='rgba(50,205,50,0.2)'
                            )
                        ])
                        
                        fig_hora.update_layout(
                            xaxis_title="Hora del Día",
                            yaxis_title="Promedio de Productos por Venta",
                            height=350,
                            showlegend=False,
                            xaxis=dict(dtick=2)
                        )
                        
                        st.plotly_chart(fig_hora, use_container_width=True)
                        
                        hora_max_canasta = promedio_por_hora.loc[promedio_por_hora['productos_en_canasta'].idxmax()]
                        st.info(f"💡 A las **{int(hora_max_canasta['hora'])}:00** los clientes compran más productos por transacción (promedio: {hora_max_canasta['productos_en_canasta']:.2f} productos)")
                
                else:
                    st.info("No se encontraron suficientes pares de productos para analizar")
        
    else:
        st.warning("⚠️ No hay datos disponibles para el período seleccionado.")

except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
    st.info("Verifica que la URL del CSV sea correcta y que el archivo esté accesible.")
