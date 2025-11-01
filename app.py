import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from itertools import combinations
from collections import Counter
from datetime import datetime

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
    df_temp['fecha'] = df_temp['fecha_hora'].dt.date
    df_temp['dia_mes'] = df_temp['fecha_hora'].dt.day
    
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
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Resumen General", 
            "🔥 Análisis de Horarios", 
            "📊 Análisis de Productos",
            "🔍 Búsqueda Detallada",
            "🛒 Análisis de Canastas",
            "🎉 Fechas Especiales"
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
            
            # Productos a excluir del análisis
            PRODUCTOS_EXCLUIR = ["BAGUETTES CHICOS"]
            
            # Agrupar productos vendidos en la misma fecha y hora (misma transacción)
            df_transacciones = df_analisis.copy()
            df_transacciones['transaccion_id'] = df_transacciones['fecha_hora'].astype(str)
            
            # Filtrar productos excluidos
            df_transacciones_filtrado = df_transacciones[~df_transacciones['producto'].isin(PRODUCTOS_EXCLUIR)]
            
            # Crear canastas: productos agrupados por transacción
            canastas = df_transacciones_filtrado.groupby('transaccion_id')['producto'].apply(list).reset_index()
            canastas['num_productos'] = canastas['producto'].apply(len)
            
            # Filtrar solo transacciones con más de 1 producto
            canastas_multiples = canastas[canastas['num_productos'] > 1].copy()
            
            # Métricas generales
            st.markdown("#### 📊 Estadísticas Generales")
            st.caption(f"⚠️ Productos excluidos del análisis: {', '.join(PRODUCTOS_EXCLUIR)}")
            
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
                # Subtabs para diferentes análisis
                subtab1, subtab2 = st.tabs(["🔗 Productos Frecuentes", "🔍 Buscar por Producto"])
                
                with subtab1:
                    st.markdown("#### 🔗 Productos que se Compran Juntos")
                    
                    # Calcular todas las combinaciones de pares
                    pares = []
                    for productos in canastas_multiples['producto']:
                        if len(productos) >= 2:
                            for combo in combinations(sorted(productos), 2):
                                pares.append(combo)
                    
                    # Contar frecuencia de cada par
                    contador_pares = Counter(pares)
                    top_pares = contador_pares.most_common(20)
                    
                    if len(top_pares) > 0:
                        # Selector de cantidad a mostrar
                        max_disponible = min(20, len(top_pares))
                        if max_disponible > 5:
                            num_mostrar = st.slider(
                                "Cantidad de combinaciones a mostrar:",
                                min_value=5,
                                max_value=max_disponible,
                                value=min(10, max_disponible),
                                step=5,
                                key="slider_pares"
                            )
                        else:
                            num_mostrar = max_disponible
                            st.info(f"Mostrando {num_mostrar} combinaciones disponibles")
                        
                        # Crear dataframe de pares
                        df_pares = pd.DataFrame(top_pares[:num_mostrar], columns=['Par', 'Frecuencia'])
                        df_pares['Producto 1'] = df_pares['Par'].apply(lambda x: x[0])
                        df_pares['Producto 2'] = df_pares['Par'].apply(lambda x: x[1])
                        
                        # Calcular soporte
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
                        
                        # Análisis de triples
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
                        
                        top_combo = df_pares.iloc[0]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.success(f"**🏆 COMBO MÁS POPULAR**")
                            st.markdown(f"**{top_combo['Producto 1']}** + **{top_combo['Producto 2']}**")
                            st.info(f"Se compran juntos en {top_combo['Frecuencia']} ocasiones ({top_combo['Soporte (%)']}%)")
                            st.markdown("**Acciones sugeridas:**\n- Crear promoción de combo\n- Colocar productos cercanos\n- Destacar en marketing")
                        
                        with col2:
                            st.success(f"**🎯 OPORTUNIDADES**")
                            st.markdown(f"Identificadas **{num_mostrar}** combinaciones frecuentes")
                            st.info("Productos con alta afinidad que se pueden potenciar")
                            st.markdown("**Acciones sugeridas:**\n- Entrenar al personal\n- Crear paquetes promocionales\n- Señalización en PDV")
                        
                        # Análisis por horario
                        with st.expander("🕐 Ver Análisis de Canastas por Horario", expanded=False):
                            st.markdown("##### Tamaño de Canasta por Hora del Día")
                            
                            df_trans_hora = df_transacciones_filtrado.copy()
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
                
                with subtab2:
                    st.markdown("#### 🔍 Buscar Combinaciones por Producto")
                    st.caption("Selecciona un producto para ver con qué otros productos se compra frecuentemente")
                    
                    # Selector de producto
                    productos_en_canastas = sorted(df_transacciones_filtrado['producto'].unique())
                    producto_buscar = st.selectbox(
                        "Selecciona un producto:",
                        productos_en_canastas,
                        help="Elige un producto para ver sus combinaciones",
                        key="selector_producto_canasta"
                    )
                    
                    if producto_buscar:
                        # Filtrar pares que contienen el producto seleccionado
                        pares_producto = []
                        for productos in canastas_multiples['producto']:
                            if producto_buscar in productos and len(productos) >= 2:
                                for otro_producto in productos:
                                    if otro_producto != producto_buscar:
                                        pares_producto.append(otro_producto)
                        
                        if len(pares_producto) > 0:
                            contador_producto = Counter(pares_producto)
                            top_combinaciones = contador_producto.most_common(15)
                            
                            df_combinaciones = pd.DataFrame(top_combinaciones, columns=['Producto Combinado', 'Frecuencia'])
                            df_combinaciones['Soporte (%)'] = (df_combinaciones['Frecuencia'] / len(canastas_multiples) * 100).round(2)
                            
                            # Métricas del producto
                            col1, col2, col3 = st.columns(3)
                            
                            total_apariciones = len([p for p in canastas_multiples['producto'] if producto_buscar in p])
                            
                            with col1:
                                st.metric("🛒 Aparece en Transacciones", f"{total_apariciones:,}")
                            with col2:
                                st.metric("🔗 Productos Únicos Combinados", f"{len(contador_producto)}")
                            with col3:
                                combo_mas_frecuente = df_combinaciones.iloc[0]['Producto Combinado']
                                st.metric("⭐ Combinación #1", combo_mas_frecuente[:30])
                            
                            st.divider()
                            
                            # Gráfico de barras
                            num_mostrar_busqueda = st.slider(
                                "Cantidad a mostrar:",
                                min_value=5,
                                max_value=min(15, len(df_combinaciones)),
                                value=min(10, len(df_combinaciones)),
                                step=5,
                                key="slider_busqueda"
                            )
                            
                            df_combinaciones_plot = df_combinaciones.head(num_mostrar_busqueda)
                            
                            fig_combinaciones = go.Figure(data=[
                                go.Bar(
                                    y=df_combinaciones_plot['Producto Combinado'][::-1],
                                    x=df_combinaciones_plot['Frecuencia'][::-1],
                                    orientation='h',
                                    marker_color='#32CD32',
                                    text=df_combinaciones_plot['Frecuencia'][::-1],
                                    textposition='auto',
                                    hovertemplate='<b>%{y}</b><br>Frecuencia: %{x}<br>Soporte: %{customdata:.2f}%<extra></extra>',
                                    customdata=df_combinaciones_plot['Soporte (%)'][::-1]
                                )
                            ])
                            
                            fig_combinaciones.update_layout(
                                title=f"Productos que se compran con '{producto_buscar}'",
                                xaxis_title="Frecuencia",
                                yaxis_title="",
                                height=max(400, num_mostrar_busqueda * 40),
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig_combinaciones, use_container_width=True)
                            
                            # Tabla detallada
                            st.markdown("#### 📋 Tabla Detallada")
                            st.dataframe(df_combinaciones_plot, use_container_width=True, hide_index=True)
                            
                            # Recomendaciones específicas
                            st.markdown("#### 💡 Recomendaciones Específicas")
                            
                            top_3 = df_combinaciones.head(3)
                            
                            st.success(f"**Productos Top para Cross-Selling con '{producto_buscar}':**")
                            for idx, row in top_3.iterrows():
                                st.markdown(f"• **{row['Producto Combinado']}** - {row['Frecuencia']} veces ({row['Soporte (%)']}% de las transacciones)")
                            
                            st.info(f"💼 **Estrategia sugerida:** Cuando un cliente compre '{producto_buscar}', el personal debería sugerir estos productos para incrementar el ticket promedio.")
                        
                        else:
                            st.warning(f"No se encontraron combinaciones para el producto '{producto_buscar}' en el período seleccionado.")
        
# ========== TAB 6: ANÁLISIS DE PICADAS ==========
        with tab6:
            st.markdown("### 🍽️ Análisis Inteligente de Picadas")
            st.caption("Predicciones, tendencias y recomendaciones para optimizar la producción de picadas")
            
            # Lista de productos de picadas
            PRODUCTOS_PICADAS = [
                'TABLA SAN FRANCISCO CHICA', 'TABLA SAN FRANCISCO MEDIANA', 'TABLA SAN FRANCISCO GRANDE',
                'TABLA CRIOLLA CHICA', 'TABLA CRIOLLA MEDIANA', 'TABLA CRIOLLA GRANDE',
                'TABLA ITALIANA CHICA', 'TABLA ITALIANA MEDIANA', 'TABLA ITALIANA GRANDE',
                'TABLA PAMPEANA CHICA', 'TABLA PAMPEANA MEDIANA', 'TABLA PAMPEANA GRANDE',
                'TABLA IBERICA CHICA', 'TABLA IBERICA MEDIANA', 'TABLA IBERICA GRANDE',
                'TABLA DE QUESOS CHICA', 'TABLA DE QUESOS MEDIANA', 'TABLA DE QUESOS GRANDE',
                'TABLA CHACARERA CHICA', 'TABLA CHACARERA MEDIANA', 'TABLA CHACARERA GRANDE',
                'TABLA TRADICIONAL CHICA', 'TABLA TRADICIONAL MEDIANA', 'TABLA TRADICIONAL GRANDE'
            ]
            
            # Filtrar datos de picadas
            df_picadas = df_temp[df_temp['producto'].isin(PRODUCTOS_PICADAS)].copy()
            
            if df_picadas.empty:
                st.warning("⚠️ No se encontraron datos de picadas en el período seleccionado")
            else:
                # Crear tabs secundarios
                subtab1, subtab2, subtab3, subtab4 = st.tabs([
                    "📅 Predicción por Fechas",
                    "📊 Análisis General",
                    "🕐 Horarios Óptimos",
                    "💡 Recomendaciones"
                ])
                
                # ========== SUBTAB 1: PREDICCIÓN POR FECHAS ==========
                with subtab1:
                    st.markdown("#### 📅 Predicción de Ventas por Rango de Fechas")
                    st.caption("Selecciona un período futuro para predecir cuántas picadas necesitarás")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fecha_inicio_pred = st.date_input(
                            "Fecha Inicio:",
                            value=df_picadas['fecha'].max() + pd.Timedelta(days=1),
                            min_value=df_picadas['fecha'].min(),
                            key="fecha_inicio_pred"
                        )
                    
                    with col2:
                        fecha_fin_pred = st.date_input(
                            "Fecha Fin:",
                            value=df_picadas['fecha'].max() + pd.Timedelta(days=7),
                            min_value=fecha_inicio_pred,
                            key="fecha_fin_pred"
                        )
                    
                    if st.button("🔮 Generar Predicción", type="primary"):
                        # Convertir a datetime
                        fecha_inicio_pred = pd.to_datetime(fecha_inicio_pred)
                        fecha_fin_pred = pd.to_datetime(fecha_fin_pred)
                        
                        # Calcular días de la semana en el rango
                        dias_rango = pd.date_range(fecha_inicio_pred, fecha_fin_pred)
                        dias_semana_rango = [dia.day_name() for dia in dias_rango]
                        contador_dias = Counter(dias_semana_rango)
                        
                        st.markdown(f"### 📊 Predicción para {len(dias_rango)} días ({fecha_inicio_pred.strftime('%d/%m/%Y')} - {fecha_fin_pred.strftime('%d/%m/%Y')})")
                        
                        # Calcular promedio por día de la semana y por tipo de picada
                        df_picadas['tipo_picada'] = df_picadas['producto'].str.extract(r'TABLA (.+?) (CHICA|MEDIANA|GRANDE)')[0]
                        df_picadas['tamaño'] = df_picadas['producto'].str.extract(r'(CHICA|MEDIANA|GRANDE)')[0]
                        
                        # Promedio por día de semana y producto
                        ventas_por_dia_producto = df_picadas.groupby(['dia_semana', 'producto'])['cantidad'].sum().reset_index()
                        dias_por_semana = df_picadas.groupby('dia_semana')['fecha'].nunique()
                        
                        promedios = {}
                        for dia in contador_dias.keys():
                            if dia in dias_por_semana.index:
                                productos_dia = ventas_por_dia_producto[ventas_por_dia_producto['dia_semana'] == dia]
                                for _, row in productos_dia.iterrows():
                                    producto = row['producto']
                                    promedio = row['cantidad'] / dias_por_semana[dia]
                                    if producto not in promedios:
                                        promedios[producto] = {}
                                    promedios[producto][dia] = promedio
                        
                        # Calcular predicción
                        predicciones = {}
                        for producto in PRODUCTOS_PICADAS:
                            total_pred = 0
                            for dia, count in contador_dias.items():
                                if producto in promedios and dia in promedios[producto]:
                                    total_pred += promedios[producto][dia] * count
                            if total_pred > 0:
                                predicciones[producto] = total_pred
                        
                        if predicciones:
                            # Crear DataFrame de predicciones
                            df_pred = pd.DataFrame(list(predicciones.items()), columns=['Producto', 'Cantidad Estimada'])
                            df_pred['Cantidad Estimada'] = df_pred['Cantidad Estimada'].round(0).astype(int)
                            df_pred = df_pred.sort_values('Cantidad Estimada', ascending=False)
                            
                            # Extraer tipo y tamaño
                            df_pred['Tipo'] = df_pred['Producto'].str.extract(r'TABLA (.+?) (CHICA|MEDIANA|GRANDE)')[0]
                            df_pred['Tamaño'] = df_pred['Producto'].str.extract(r'(CHICA|MEDIANA|GRANDE)')[0]
                            
                            # Métricas generales
                            col1, col2, col3 = st.columns(3)
                            
                            total_picadas = df_pred['Cantidad Estimada'].sum()
                            promedio_diario = total_picadas / len(dias_rango)
                            producto_top = df_pred.iloc[0]['Producto']
                            
                            with col1:
                                st.metric("🍽️ Total Picadas Estimadas", f"{int(total_picadas):,}")
                            with col2:
                                st.metric("📊 Promedio Diario", f"{promedio_diario:.1f}")
                            with col3:
                                st.metric("⭐ Más Demandada", producto_top.split('TABLA ')[1][:20])
                            
                            st.divider()
                            
                            # Gráfico por tipo de picada
                            st.markdown("#### 📊 Distribución por Tipo de Picada")
                            
                            ventas_por_tipo = df_pred.groupby('Tipo')['Cantidad Estimada'].sum().reset_index()
                            ventas_por_tipo = ventas_por_tipo.sort_values('Cantidad Estimada', ascending=False)
                            
                            fig_tipo = go.Figure(data=[
                                go.Bar(
                                    x=ventas_por_tipo['Tipo'],
                                    y=ventas_por_tipo['Cantidad Estimada'],
                                    marker_color='#FFD700',
                                    text=ventas_por_tipo['Cantidad Estimada'],
                                    textposition='auto'
                                )
                            ])
                            
                            fig_tipo.update_layout(
                                xaxis_title="Tipo de Picada",
                                yaxis_title="Unidades Estimadas",
                                height=400,
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig_tipo, use_container_width=True)
                            
                            # Gráfico por tamaño
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 📏 Distribución por Tamaño")
                                ventas_por_tamaño = df_pred.groupby('Tamaño')['Cantidad Estimada'].sum().reset_index()
                                orden_tamaño = {'CHICA': 1, 'MEDIANA': 2, 'GRANDE': 3}
                                ventas_por_tamaño['orden'] = ventas_por_tamaño['Tamaño'].map(orden_tamaño)
                                ventas_por_tamaño = ventas_por_tamaño.sort_values('orden')
                                
                                fig_tamaño = go.Figure(data=[
                                    go.Pie(
                                        labels=ventas_por_tamaño['Tamaño'],
                                        values=ventas_por_tamaño['Cantidad Estimada'],
                                        hole=0.4,
                                        marker=dict(colors=['#32CD32', '#FFD700', '#FF6347'])
                                    )
                                ])
                                fig_tamaño.update_layout(height=350)
                                st.plotly_chart(fig_tamaño, use_container_width=True)
                            
                            with col2:
                                st.markdown("#### 📋 Resumen por Tamaño")
                                tabla_tamaño = ventas_por_tamaño[['Tamaño', 'Cantidad Estimada']].copy()
                                tabla_tamaño['Porcentaje'] = (tabla_tamaño['Cantidad Estimada'] / tabla_tamaño['Cantidad Estimada'].sum() * 100).round(1).astype(str) + '%'
                                st.dataframe(tabla_tamaño[['Tamaño', 'Cantidad Estimada', 'Porcentaje']], use_container_width=True, hide_index=True)
                                
                                st.markdown("---")
                                st.markdown("**💡 Tip de Producción:**")
                                tamaño_preferido = tabla_tamaño.iloc[0]['Tamaño']
                                st.info(f"El tamaño **{tamaño_preferido}** representa el {tabla_tamaño.iloc[0]['Porcentaje']} de las ventas. Prioriza su producción.")
                            
                            st.divider()
                            
                            # Tabla detallada completa
                            st.markdown("#### 📋 Lista Completa de Producción")
                            
                            # Agrupar por tipo para mejor visualización
                            for tipo in ventas_por_tipo['Tipo'].values:
                                with st.expander(f"🍽️ TABLA {tipo}", expanded=(tipo == ventas_por_tipo.iloc[0]['Tipo'])):
                                    df_tipo = df_pred[df_pred['Tipo'] == tipo][['Tamaño', 'Cantidad Estimada']].copy()
                                    df_tipo = df_tipo.sort_values('Tamaño', key=lambda x: x.map(orden_tamaño))
                                    
                                    total_tipo = df_tipo['Cantidad Estimada'].sum()
                                    st.metric(f"Total {tipo}", f"{int(total_tipo)} unidades")
                                    
                                    st.dataframe(df_tipo, use_container_width=True, hide_index=True)
                            
                            # Distribución por día de la semana
                            st.divider()
                            st.markdown("#### 📅 Distribución Estimada por Día de la Semana")
                            
                            dias_texto = [dias_español[d] for d in dias_semana_rango]
                            contador_dias_español = Counter(dias_texto)
                            
                            # Calcular ventas promedio por día de la semana
                            ventas_dia_semana = df_picadas.groupby('dia_semana')['cantidad'].sum() / df_picadas.groupby('dia_semana')['fecha'].nunique()
                            ventas_dia_semana = ventas_dia_semana.reset_index()
                            ventas_dia_semana['dia_español'] = ventas_dia_semana['dia_semana'].map(dias_español)
                            
                            # Crear predicción por día
                            pred_por_dia = []
                            for dia_eng, dia_esp in dias_español.items():
                                if dia_esp in contador_dias_español:
                                    cantidad_dias = contador_dias_español[dia_esp]
                                    if dia_eng in ventas_dia_semana['dia_semana'].values:
                                        promedio = ventas_dia_semana[ventas_dia_semana['dia_semana'] == dia_eng]['cantidad'].values[0]
                                        pred_por_dia.append({
                                            'Día': dia_esp,
                                            'Días en Período': cantidad_dias,
                                            'Promedio por Día': promedio,
                                            'Total Estimado': promedio * cantidad_dias
                                        })
                            
                            df_pred_dias = pd.DataFrame(pred_por_dia)
                            df_pred_dias = df_pred_dias.set_index('Día').reindex([dias_español[d] for d in dias_orden if dias_español[d] in df_pred_dias.index]).reset_index()
                            df_pred_dias['Promedio por Día'] = df_pred_dias['Promedio por Día'].round(1)
                            df_pred_dias['Total Estimado'] = df_pred_dias['Total Estimado'].round(0).astype(int)
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                fig_dias_pred = go.Figure(data=[
                                    go.Bar(
                                        x=df_pred_dias['Día'],
                                        y=df_pred_dias['Total Estimado'],
                                        marker_color='#1E90FF',
                                        text=df_pred_dias['Total Estimado'],
                                        textposition='auto'
                                    )
                                ])
                                
                                fig_dias_pred.update_layout(
                                    xaxis_title="Día de la Semana",
                                    yaxis_title="Picadas Estimadas",
                                    height=350,
                                    showlegend=False
                                )
                                
                                st.plotly_chart(fig_dias_pred, use_container_width=True)
                            
                            with col2:
                                st.markdown("**📊 Tabla Detallada**")
                                st.dataframe(df_pred_dias, use_container_width=True, hide_index=True)
                        
                        else:
                            st.warning("No hay suficientes datos históricos para generar predicciones confiables")
                
                # ========== SUBTAB 2: ANÁLISIS GENERAL ==========
                with subtab2:
                    st.markdown("#### 📊 Análisis General de Picadas")
                    
                    # Extraer tipo y tamaño
                    df_picadas_analysis = df_picadas.copy()
                    df_picadas_analysis['tipo_picada'] = df_picadas_analysis['producto'].str.extract(r'TABLA (.+?) (CHICA|MEDIANA|GRANDE)')[0]
                    df_picadas_analysis['tamaño'] = df_picadas_analysis['producto'].str.extract(r'(CHICA|MEDIANA|GRANDE)')[0]
                    
                    # Métricas generales
                    total_vendido = df_picadas_analysis['cantidad'].sum()
                    tipos_unicos = df_picadas_analysis['tipo_picada'].nunique()
                    promedio_diario = total_vendido / df_picadas_analysis['fecha'].nunique()
                    picada_mas_vendida = df_picadas_analysis.groupby('producto')['cantidad'].sum().idxmax()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🍽️ Total Picadas Vendidas", f"{int(total_vendido):,}")
                    with col2:
                        st.metric("📊 Promedio Diario", f"{promedio_diario:.1f}")
                    with col3:
                        st.metric("🎯 Tipos Diferentes", f"{tipos_unicos}")
                    with col4:
                        st.metric("⭐ Más Vendida", picada_mas_vendida.split('TABLA ')[1][:15] + "...")
                    
                    st.divider()
                    
                    # Ranking de picadas
                    st.markdown("#### 🏆 Ranking de Picadas")
                    
                    ranking_picadas = df_picadas_analysis.groupby('producto')['cantidad'].sum().reset_index()
                    ranking_picadas = ranking_picadas.sort_values('cantidad', ascending=False).reset_index(drop=True)
                    ranking_picadas['participacion'] = (ranking_picadas['cantidad'] / ranking_picadas['cantidad'].sum() * 100).round(2)
                    ranking_picadas.insert(0, '#', range(1, len(ranking_picadas) + 1))
                    ranking_picadas.columns = ['#', 'Picada', 'Unidades Vendidas', 'Participación (%)']
                    
                    # Mostrar top 10
                    st.dataframe(ranking_picadas.head(10), use_container_width=True, hide_index=True)
                    
                    with st.expander("📋 Ver Ranking Completo", expanded=False):
                        st.dataframe(ranking_picadas, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    # Análisis por tipo
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📊 Ventas por Tipo de Picada")
                        ventas_tipo = df_picadas_analysis.groupby('tipo_picada')['cantidad'].sum().reset_index()
                        ventas_tipo = ventas_tipo.sort_values('cantidad', ascending=False)
                        
                        fig_tipo_general = go.Figure(data=[
                            go.Bar(
                                x=ventas_tipo['tipo_picada'],
                                y=ventas_tipo['cantidad'],
                                marker_color='#FFD700',
                                text=ventas_tipo['cantidad'],
                                textposition='auto'
                            )
                        ])
                        
                        fig_tipo_general.update_layout(
                            xaxis_title="Tipo",
                            yaxis_title="Unidades",
                            height=400,
                            showlegend=False,
                            xaxis=dict(tickangle=-45)
                        )
                        
                        st.plotly_chart(fig_tipo_general, use_container_width=True)
                    
                    with col2:
                        st.markdown("#### 📏 Ventas por Tamaño")
                        ventas_tamaño = df_picadas_analysis.groupby('tamaño')['cantidad'].sum().reset_index()
                        orden_tamaño = {'CHICA': 1, 'MEDIANA': 2, 'GRANDE': 3}
                        ventas_tamaño['orden'] = ventas_tamaño['tamaño'].map(orden_tamaño)
                        ventas_tamaño = ventas_tamaño.sort_values('orden')
                        
                        fig_tamaño_general = go.Figure(data=[
                            go.Pie(
                                labels=ventas_tamaño['tamaño'],
                                values=ventas_tamaño['cantidad'],
                                hole=0.4,
                                marker=dict(colors=['#32CD32', '#FFD700', '#FF6347']),
                                textinfo='label+percent',
                                textposition='auto'
                            )
                        ])
                        
                        fig_tamaño_general.update_layout(height=400)
                        st.plotly_chart(fig_tamaño_general, use_container_width=True)
                    
                    st.divider()
                    
                    # Tendencia temporal
                    st.markdown("#### 📈 Tendencia de Ventas en el Tiempo")
                    
                    ventas_tiempo = df_picadas_analysis.groupby('fecha')['cantidad'].sum().reset_index()
                    
                    fig_tendencia = go.Figure(data=[
                        go.Scatter(
                            x=ventas_tiempo['fecha'],
                            y=ventas_tiempo['cantidad'],
                            mode='lines+markers',
                            line=dict(color='#1E90FF', width=2),
                            marker=dict(size=6),
                            fill='tozeroy',
                            fillcolor='rgba(30,144,255,0.2)'
                        )
                    ])
                    
                    # Agregar línea de promedio
                    promedio_general = ventas_tiempo['cantidad'].mean()
                    fig_tendencia.add_hline(y=promedio_general, line_dash="dash", line_color="red", 
                                           annotation_text=f"Promedio: {promedio_general:.1f}",
                                           annotation_position="right")
                    
                    fig_tendencia.update_layout(
                        xaxis_title="Fecha",
                        yaxis_title="Picadas Vendidas",
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_tendencia, use_container_width=True)
                    
                    # Ventas por día de la semana
                    st.markdown("#### 📅 Ventas por Día de la Semana")
                    
                    ventas_dia_picadas = df_picadas_analysis.groupby('dia_semana')['cantidad'].sum().reset_index()
                    ventas_dia_picadas = ventas_dia_picadas.set_index('dia_semana').reindex(dias_orden).reset_index()
                    ventas_dia_picadas['dia_español'] = ventas_dia_picadas['dia_semana'].map(dias_español)
                    
                    fig_dias_picadas = go.Figure(data=[
                        go.Bar(
                            x=ventas_dia_picadas['dia_español'],
                            y=ventas_dia_picadas['cantidad'],
                            marker_color='#32CD32',
                            text=ventas_dia_picadas['cantidad'],
                            textposition='auto'
                        )
                    ])
                    
                    fig_dias_picadas.update_layout(
                        xaxis_title="Día de la Semana",
                        yaxis_title="Picadas Vendidas",
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_dias_picadas, use_container_width=True)
                
                # ========== SUBTAB 3: HORARIOS ÓPTIMOS ==========
                with subtab3:
                    st.markdown("#### 🕐 Análisis de Horarios Óptimos")
                    st.caption("Identifica los mejores momentos para tener picadas armadas y listas")
                    
                    # Ventas por hora
                    ventas_hora_picadas = df_picadas.groupby('hora_num')['cantidad'].sum().reset_index()
                    
                    # Identificar horas pico
                    promedio_hora = ventas_hora_picadas['cantidad'].mean()
                    horas_pico = ventas_hora_picadas[ventas_hora_picadas['cantidad'] >= promedio_hora * 1.2]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    hora_max = ventas_hora_picadas.loc[ventas_hora_picadas['cantidad'].idxmax(), 'hora_num']
                    cantidad_max = ventas_hora_picadas['cantidad'].max()
                    
                    with col1:
                        st.metric("🔥 Hora Pico", f"{int(hora_max)}:00 hs")
                    with col2:
                        st.metric("📊 Ventas en Pico", f"{int(cantidad_max)} picadas")
                    with col3:
                        st.metric("⏰ Horarios Destacados", f"{len(horas_pico)} horas")
                    
                    st.divider()
                    
                    # Gráfico de ventas por hora
                    st.markdown("#### 📊 Distribución de Ventas por Hora")
                    
                    fig_hora_picadas = go.Figure()
                    
                    fig_hora_picadas.add_trace(go.Scatter(
                        x=ventas_hora_picadas['hora_num'],
                        y=ventas_hora_picadas['cantidad'],
                        mode='lines+markers',
                        line=dict(color='#FFD700', width=3),
                        marker=dict(size=10),
                        fill='tozeroy',
                        fillcolor='rgba(255,215,0,0.3)',
                        name='Ventas'
                    ))
                    
                    # Línea de promedio
                    fig_hora_picadas.add_hline(y=promedio_hora, line_dash="dash", line_color="red",
                                              annotation_text=f"Promedio: {promedio_hora:.1f}",
                                              annotation_position="right")
                    
                    # Marcar horas pico
                    fig_hora_picadas.add_trace(go.Scatter(
                        x=horas_pico['hora_num'],
                        y=horas_pico['cantidad'],
                        mode='markers',
                        marker=dict(size=15, color='red', symbol='star'),
                        name='Horas Pico'
                    ))
                    
                    fig_hora_picadas.update_layout(
                        xaxis_title="Hora del Día",
                        yaxis_title="Picadas Vendidas",
                        height=450,
                        xaxis=dict(dtick=1),
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig_hora_picadas, use_container_width=True)
                    
                    st.divider()
                    
                    # Heatmap día x hora
                    st.markdown("#### 🔥 Heatmap: Día vs Hora")
                    
                    ventas_dia_hora = df_picadas.groupby(['dia_semana', 'hora_num'])['cantidad'].sum().reset_index()
                    matriz_dia_hora = ventas_dia_hora.pivot(index='dia_semana', columns='hora_num', values='cantidad').fillna(0)
                    matriz_dia_hora = matriz_dia_hora.reindex(dias_orden)
                    matriz_dia_hora.index = [dias_español[d] for d in matriz_dia_hora.index]
                    
                    fig_heatmap_picadas = go.Figure(data=go.Heatmap(
                        z=matriz_dia_hora.values,
                        x=[f"{int(h)}:00" for h in matriz_dia_hora.columns],
                        y=matriz_dia_hora.index,
                        colorscale='YlOrRd',
                        text=matriz_dia_hora.values.astype(int),
                        texttemplate='%{text}',
                        textfont={"size": 10},
                        colorbar=dict(title="Picadas<br>vendidas")
                    ))
                    
                    fig_heatmap_picadas.update_layout(
                        xaxis_title="Hora del Día",
                        yaxis_title="Día de la Semana",
                        height=500
                    )
                    
                    st.plotly_chart(fig_heatmap_picadas, use_container_width=True)
                    
                    st.divider()
                    
                    # Recomendaciones de pre-armado
                    st.markdown("#### 💡 Recomendaciones de Pre-Armado")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.success("**🕐 HORARIOS CRÍTICOS**")
                        st.markdown("Tener picadas armadas en estos horarios:")
                        for _, row in horas_pico.sort_values('cantidad', ascending=False).iterrows():
                            hora = int(row['hora_num'])
                            cant = int(row['cantidad'])
                            st.markdown(f"• **{hora}:00 - {hora+1}:00** → ~{cant} picadas")
                    
                    with col2:
                        st.info("**📅 DÍAS CRÍTICOS**")
                        dias_mas_ventas = ventas_dia_picadas.nlargest(3, 'cantidad')
                        st.markdown("Reforzar producción estos días:")
                        for _, row in dias_mas_ventas.iterrows():
                            dia = row['dia_español']
                            cant = int(row['cantidad'])
                            st.markdown(f"• **{dia}** → ~{cant} picadas/día")
                    
                    # Análisis por tamaño y hora
                    with st.expander("📏 Ver Análisis de Tamaños por Hora", expanded=False):
                        st.markdown("##### Preferencia de Tamaño según Horario")
                        
                        df_picadas_hora_tamaño = df_picadas.copy()
                        df_picadas_hora_tamaño['tamaño'] = df_picadas_hora_tamaño['producto'].str.extract(r'(CHICA|MEDIANA|GRANDE)')[0]
                        
                        ventas_hora_tamaño = df_picadas_hora_tamaño.groupby(['hora_num', 'tamaño'])['cantidad'].sum().reset_index()
                        
                        fig_hora_tamaño = go.Figure()
                        
                        colores_tamaño = {'CHICA': '#32CD32', 'MEDIANA': '#FFD700', 'GRANDE': '#FF6347'}
                        
                        for tamaño in ['CHICA', 'MEDIANA', 'GRANDE']:
                            datos_tamaño = ventas_hora_tamaño[ventas_hora_tamaño['tamaño'] == tamaño]
                            fig_hora_tamaño.add_trace(go.Scatter(
                                x=datos_tamaño['hora_num'],
                                y=datos_tamaño['cantidad'],
                                mode='lines+markers',
                                name=tamaño,
                                line=dict(width=3),
                                marker=dict(size=8, color=colores_tamaño[tamaño])
                            ))
                        
                        fig_hora_tamaño.update_layout(
                            xaxis_title="Hora del Día",
                            yaxis_title="Picadas Vendidas",
                            height=400,
                            xaxis=dict(dtick=2),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        st.plotly_chart(fig_hora_tamaño, use_container_width=True)
                        
                        # Análisis de conclusiones
                        for hora in horas_pico['hora_num'].values:
                            datos_hora = ventas_hora_tamaño[ventas_hora_tamaño['hora_num'] == hora]
                            if not datos_hora.empty:
                                tamaño_preferido = datos_hora.loc[datos_hora['cantidad'].idxmax(), 'tamaño']
                                st.info(f"A las **{int(hora)}:00** se prefieren las picadas **{tamaño_preferido}**")
                
                # ========== SUBTAB 4: RECOMENDACIONES ==========
                with subtab4:
                    st.markdown("#### 💡 Recomendaciones Inteligentes de Producción")
                    st.caption("Estrategias basadas en datos para optimizar tu producción")
                    
                    # Calcular métricas clave
                    df_picadas_rec = df_picadas.copy()
                    df_picadas_rec['tipo_picada'] = df_picadas_rec['producto'].str.extract(r'TABLA (.+?) (CHICA|MEDIANA|GRANDE)')[0]
                    df_picadas_rec['tamaño'] = df_picadas_rec['producto'].str.extract(r'(CHICA|MEDIANA|GRANDE)')[0]
                    
                    # Top 3 productos
                    top3_productos = df_picadas_rec.groupby('producto')['cantidad'].sum().nlargest(3)
                    
                    # Top 3 tipos
                    top3_tipos = df_picadas_rec.groupby('tipo_picada')['cantidad'].sum().nlargest(3)
                    
                    # Tamaño más vendido
                    tamaño_top = df_picadas_rec.groupby('tamaño')['cantidad'].sum().idxmax()
                    
                    # Día más vendido
                    dia_top = df_picadas_rec.groupby('dia_semana')['cantidad'].sum().idxmax()
                    dia_top_esp = dias_español[dia_top]
                    
                    # Hora más vendida
                    hora_top = df_picadas_rec.groupby('hora_num')['cantidad'].sum().idxmax()
                    
                    # RECOMENDACIÓN 1: Producción Prioritaria
                    st.markdown("### 🎯 1. Producción Prioritaria")
                    st.success("**Estos productos deben estar SIEMPRE disponibles:**")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    productos_prioritarios = list(top3_productos.index)
                    for idx, (col, producto) in enumerate(zip([col1, col2, col3], productos_prioritarios)):
                        with col:
                            st.markdown(f"**#{idx+1}**")
                            st.markdown(f"**{producto.replace('TABLA ', '')}**")
                            cant = int(top3_productos[producto])
                            promedio_diario = cant / df_picadas_rec['fecha'].nunique()
                            st.metric("Ventas Totales", f"{cant}")
                            st.metric("Promedio Diario", f"{promedio_diario:.1f}")
                    
                    st.divider()
                    
                    # RECOMENDACIÓN 2: Stock por Día
                    st.markdown("### 📅 2. Plan de Stock Semanal")
                    st.info("**Cantidad recomendada de picadas por día de la semana:**")
                    
                    ventas_por_dia_rec = df_picadas_rec.groupby('dia_semana')['cantidad'].sum() / df_picadas_rec.groupby('dia_semana')['fecha'].nunique()
                    ventas_por_dia_rec = ventas_por_dia_rec.reindex(dias_orden)
                    
                    tabla_semanal = pd.DataFrame({
                        'Día': [dias_español[d] for d in ventas_por_dia_rec.index],
                        'Picadas Recomendadas': ventas_por_dia_rec.values.round(0).astype(int),
                        'Nivel': ['🔴 ALTO' if v > ventas_por_dia_rec.mean() * 1.2 else 
                                 '🟡 MEDIO' if v > ventas_por_dia_rec.mean() * 0.8 else 
                                 '🟢 BAJO' for v in ventas_por_dia_rec.values]
                    })
                    
                    st.dataframe(tabla_semanal, use_container_width=True, hide_index=True)
                    
                    st.markdown(f"💡 **Reforzar producción los días {dia_top_esp}** (día con mayor demanda)")
                    
                    st.divider()
                    
                    # RECOMENDACIÓN 3: Pre-armado por Horario
                    st.markdown("### 🕐 3. Estrategia de Pre-Armado")
                    st.warning("**Plan horario para tener picadas listas:**")
                    
                    ventas_por_hora_rec = df_picadas_rec.groupby('hora_num')['cantidad'].sum()
                    horas_ordenadas = ventas_por_hora_rec.sort_values(ascending=False)
                    
                    st.markdown("**🔴 HORARIOS CRÍTICOS (Pre-armar con anticipación):**")
                    for hora in horas_ordenadas.head(5).index:
                        cantidad = int(horas_ordenadas[hora])
                        porcentaje = (cantidad / ventas_por_hora_rec.sum() * 100)
                        st.markdown(f"• **{int(hora)-1}:30 - {int(hora)}:00** → Armar **{cantidad}** picadas ({porcentaje:.1f}% del día)")
                    
                    st.markdown("\n**🟡 HORARIOS MODERADOS (Preparar según demanda):**")
                    for hora in horas_ordenadas[5:10].index:
                        cantidad = int(horas_ordenadas[hora])
                        st.markdown(f"• **{int(hora)}:00 - {int(hora)+1}:00** → ~**{cantidad}** picadas")
                    
                    st.divider()
                    
                    # RECOMENDACIÓN 4: Mix de Productos
                    st.markdown("### 📊 4. Mix Óptimo de Productos")
                    st.success("**Distribución recomendada de tu producción:**")
                    
                    # Por tipo
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Por Tipo de Picada:**")
                        dist_tipo = df_picadas_rec.groupby('tipo_picada')['cantidad'].sum()
                        dist_tipo_pct = (dist_tipo / dist_tipo.sum() * 100).round(1)
                        
                        for tipo in dist_tipo_pct.nlargest(5).index:
                            pct = dist_tipo_pct[tipo]
                            st.markdown(f"• **{tipo}**: {pct}%")
                    
                    with col2:
                        st.markdown("**Por Tamaño:**")
                        dist_tamaño = df_picadas_rec.groupby('tamaño')['cantidad'].sum()
                        dist_tamaño_pct = (dist_tamaño / dist_tamaño.sum() * 100).round(1)
                        
                        orden_tamaño = {'CHICA': 1, 'MEDIANA': 2, 'GRANDE': 3}
                        for tamaño in sorted(dist_tamaño_pct.index, key=lambda x: orden_tamaño[x]):
                            pct = dist_tamaño_pct[tamaño]
                            st.markdown(f"• **{tamaño}**: {pct}%")
                    
                    st.info(f"💡 **Insight**: El tamaño **{tamaño_top}** representa el {dist_tamaño_pct[tamaño_top]}% de las ventas. Ajusta tu producción en consecuencia.")
                    
                    st.divider()
                    
                    # RECOMENDACIÓN 5: Detección de Oportunidades
                    st.markdown("### 🚀 5. Oportunidades de Mejora")
                    
                    # Productos con bajo rendimiento
                    ventas_productos = df_picadas_rec.groupby('producto')['cantidad'].sum().sort_values()
                    bottom_5 = ventas_productos.head(5)
                    
                    if len(bottom_5) > 0:
                        st.warning("**⚠️ Productos con Bajas Ventas (Considerar):**")
                        for producto in bottom_5.index:
                            cant = int(bottom_5[producto])
                            pct = (cant / ventas_productos.sum() * 100)
                            st.markdown(f"• **{producto.replace('TABLA ', '')}**: {cant} unidades ({pct:.2f}%)")
                        
                        st.markdown("\n**Acciones sugeridas:**")
                        st.markdown("- Reducir cantidad producida de estos productos")
                        st.markdown("- Considerar promociones especiales")
                        st.markdown("- Evaluar si mantener en el catálogo")
                    
                    st.divider()
                    
                    # RECOMENDACIÓN 6: Checklist de Producción
                    st.markdown("### ✅ 6. Checklist Diario de Producción")
                    
                    st.markdown("**📋 Usa este checklist cada día:**")
                    
                    # Generar checklist inteligente
                    promedio_diario_total = df_picadas_rec['cantidad'].sum() / df_picadas_rec['fecha'].nunique()
                    
                    st.markdown(f"""
                    **ANTES DE ABRIR ({int(hora_top-2)}:00):**
                    - [ ] Verificar stock de ingredientes
                    - [ ] Pre-armar {int(promedio_diario_total * 0.3)} picadas mixtas (priorizar tamaño {tamaño_top})
                    - [ ] Preparar {int(top3_productos.iloc[0] / df_picadas_rec['fecha'].nunique())} unidades de {top3_productos.index[0].replace('TABLA ', '')}
                    
                    **HORARIO PICO ({int(hora_top-1)}:00 - {int(hora_top+1)}:00):**
                    - [ ] Tener armadas al menos {int(horas_ordenadas.iloc[0])} picadas
                    - [ ] Monitorear stock en tiempo real
                    - [ ] Personal adicional disponible
                    
                    **DÍA COMPLETO:**
                    - [ ] Meta de producción: {int(promedio_diario_total)} picadas
                    - [ ] Registrar ventas por tipo y tamaño
                    - [ ] Ajustar producción según demanda real
                    """)
                    
                    st.divider()
                    
                    # RECOMENDACIÓN 7: Alertas y Predicciones
                    st.markdown("### 🔔 7. Sistema de Alertas")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.error("**🚨 ALERTAS ROJAS:**")
                        st.markdown(f"• Si {dia_top_esp} → Duplicar stock de {top3_productos.index[0].replace('TABLA ', '')}")
                        st.markdown(f"• Si hora ≥ {int(hora_top)}:00 → Verificar picadas armadas")
                        st.markdown(f"• Si ventas > {int(promedio_diario_total * 1.5)}/día → Activar producción extra")
                    
                    with col2:
                        st.warning("**⚠️ ALERTAS AMARILLAS:**")
                        st.markdown(f"• Si stock < 5 picadas a las {int(hora_top-1)}:00 → Pre-armar más")
                        st.markdown(f"• Si tamaño {tamaño_top} < 30% → Ajustar producción")
                        st.markdown("• Si fin de semana → Aumentar stock 20%")
                    
                    st.divider()
                    
                    # Resumen Final
                    st.markdown("### 📌 Resumen Ejecutivo")
                    
                    st.success(f"""
                    **🎯 DATOS CLAVE PARA TU NEGOCIO:**
                    
                    **Producción Diaria Recomendada:** {int(promedio_diario_total)} picadas
                    
                    **Top 3 Productos (Nunca Faltar):**
                    1. {top3_productos.index[0].replace('TABLA ', '')}
                    2. {top3_productos.index[1].replace('TABLA ', '')}
                    3. {top3_productos.index[2].replace('TABLA ', '')}
                    
                    **Momento Crítico:** {dia_top_esp} a las {int(hora_top)}:00
                    
                    **Mix Ideal:** {dist_tamaño_pct['CHICA']:.0f}% Chicas, {dist_tamaño_pct['MEDIANA']:.0f}% Medianas, {dist_tamaño_pct['GRANDE']:.0f}% Grandes
                    
                    **Horario de Pre-Armado:** Comenzar a las {int(hora_top-2)}:00
                    """)
                    
                    # Botón de descarga (simulado)
                    st.markdown("---")
                    st.info("💾 **Tip:** Toma captura de pantalla de estas recomendaciones y compártelas con tu equipo de producción")
        
    else:
        st.warning("⚠️ No hay datos disponibles para el período seleccionado.")

except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
    st.info("Verifica que la URL del CSV sea correcta y que el archivo esté accesible.")import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from itertools import combinations
from collections import Counter
from datetime import datetime

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
    df_temp['fecha'] = df_temp['fecha_hora'].dt.date
    df_temp['dia_mes'] = df_temp['fecha_hora'].dt.day
    
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
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Resumen General", 
            "🔥 Análisis de Horarios", 
            "📊 Análisis de Productos",
            "🔍 Búsqueda Detallada",
            "🛒 Análisis de Canastas",
            "🎉 Fechas Especiales"
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
            
            # Productos a excluir del análisis
            PRODUCTOS_EXCLUIR = ["BAGUETTES CHICOS"]
            
            # Agrupar productos vendidos en la misma fecha y hora (misma transacción)
            df_transacciones = df_analisis.copy()
            df_transacciones['transaccion_id'] = df_transacciones['fecha_hora'].astype(str)
            
            # Filtrar productos excluidos
            df_transacciones_filtrado = df_transacciones[~df_transacciones['producto'].isin(PRODUCTOS_EXCLUIR)]
            
            # Crear canastas: productos agrupados por transacción
            canastas = df_transacciones_filtrado.groupby('transaccion_id')['producto'].apply(list).reset_index()
            canastas['num_productos'] = canastas['producto'].apply(len)
            
            # Filtrar solo transacciones con más de 1 producto
            canastas_multiples = canastas[canastas['num_productos'] > 1].copy()
            
            # Métricas generales
            st.markdown("#### 📊 Estadísticas Generales")
            st.caption(f"⚠️ Productos excluidos del análisis: {', '.join(PRODUCTOS_EXCLUIR)}")
            
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
                # Subtabs para diferentes análisis
                subtab1, subtab2 = st.tabs(["🔗 Productos Frecuentes", "🔍 Buscar por Producto"])
                
                with subtab1:
                    st.markdown("#### 🔗 Productos que se Compran Juntos")
                    
                    # Calcular todas las combinaciones de pares
                    pares = []
                    for productos in canastas_multiples['producto']:
                        if len(productos) >= 2:
                            for combo in combinations(sorted(productos), 2):
                                pares.append(combo)
                    
                    # Contar frecuencia de cada par
                    contador_pares = Counter(pares)
                    top_pares = contador_pares.most_common(20)
                    
                    if len(top_pares) > 0:
                        # Selector de cantidad a mostrar
                        max_disponible = min(20, len(top_pares))
                        if max_disponible > 5:
                            num_mostrar = st.slider(
                                "Cantidad de combinaciones a mostrar:",
                                min_value=5,
                                max_value=max_disponible,
                                value=min(10, max_disponible),
                                step=5,
                                key="slider_pares"
                            )
                        else:
                            num_mostrar = max_disponible
                            st.info(f"Mostrando {num_mostrar} combinaciones disponibles")
                        
                        # Crear dataframe de pares
                        df_pares = pd.DataFrame(top_pares[:num_mostrar], columns=['Par', 'Frecuencia'])
                        df_pares['Producto 1'] = df_pares['Par'].apply(lambda x: x[0])
                        df_pares['Producto 2'] = df_pares['Par'].apply(lambda x: x[1])
                        
                        # Calcular soporte
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
                        
                        # Análisis de triples
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
                        
                        top_combo = df_pares.iloc[0]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.success(f"**🏆 COMBO MÁS POPULAR**")
                            st.markdown(f"**{top_combo['Producto 1']}** + **{top_combo['Producto 2']}**")
                            st.info(f"Se compran juntos en {top_combo['Frecuencia']} ocasiones ({top_combo['Soporte (%)']}%)")
                            st.markdown("**Acciones sugeridas:**\n- Crear promoción de combo\n- Colocar productos cercanos\n- Destacar en marketing")
                        
                        with col2:
                            st.success(f"**🎯 OPORTUNIDADES**")
                            st.markdown(f"Identificadas **{num_mostrar}** combinaciones frecuentes")
                            st.info("Productos con alta afinidad que se pueden potenciar")
                            st.markdown("**Acciones sugeridas:**\n- Entrenar al personal\n- Crear paquetes promocionales\n- Señalización en PDV")
                        
                        # Análisis por horario
                        with st.expander("🕐 Ver Análisis de Canastas por Horario", expanded=False):
                            st.markdown("##### Tamaño de Canasta por Hora del Día")
                            
                            df_trans_hora = df_transacciones_filtrado.copy()
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
                
                with subtab2:
                    st.markdown("#### 🔍 Buscar Combinaciones por Producto")
                    st.caption("Selecciona un producto para ver con qué otros productos se compra frecuentemente")
                    
                    # Selector de producto
                    productos_en_canastas = sorted(df_transacciones_filtrado['producto'].unique())
                    producto_buscar = st.selectbox(
                        "Selecciona un producto:",
                        productos_en_canastas,
                        help="Elige un producto para ver sus combinaciones",
                        key="selector_producto_canasta"
                    )
                    
                    if producto_buscar:
                        # Filtrar pares que contienen el producto seleccionado
                        pares_producto = []
                        for productos in canastas_multiples['producto']:
                            if producto_buscar in productos and len(productos) >= 2:
                                for otro_producto in productos:
                                    if otro_producto != producto_buscar:
                                        pares_producto.append(otro_producto)
                        
                        if len(pares_producto) > 0:
                            contador_producto = Counter(pares_producto)
                            top_combinaciones = contador_producto.most_common(15)
                            
                            df_combinaciones = pd.DataFrame(top_combinaciones, columns=['Producto Combinado', 'Frecuencia'])
                            df_combinaciones['Soporte (%)'] = (df_combinaciones['Frecuencia'] / len(canastas_multiples) * 100).round(2)
                            
                            # Métricas del producto
                            col1, col2, col3 = st.columns(3)
                            
                            total_apariciones = len([p for p in canastas_multiples['producto'] if producto_buscar in p])
                            
                            with col1:
                                st.metric("🛒 Aparece en Transacciones", f"{total_apariciones:,}")
                            with col2:
                                st.metric("🔗 Productos Únicos Combinados", f"{len(contador_producto)}")
                            with col3:
                                combo_mas_frecuente = df_combinaciones.iloc[0]['Producto Combinado']
                                st.metric("⭐ Combinación #1", combo_mas_frecuente[:30])
                            
                            st.divider()
                            
                            # Gráfico de barras
                            max_combinaciones = min(15, len(df_combinaciones))
                            if max_combinaciones > 5:
                                num_mostrar_busqueda = st.slider(
                                    "Cantidad a mostrar:",
                                    min_value=5,
                                    max_value=max_combinaciones,
                                    value=min(10, max_combinaciones),
                                    step=5,
                                    key="slider_busqueda"
                                )
                            else:
                                num_mostrar_busqueda = max_combinaciones
                                st.info(f"Mostrando {num_mostrar_busqueda} combinaciones disponibles")
                            
                            df_combinaciones_plot = df_combinaciones.head(num_mostrar_busqueda)
                            
                            fig_combinaciones = go.Figure(data=[
                                go.Bar(
                                    y=df_combinaciones_plot['Producto Combinado'][::-1],
                                    x=df_combinaciones_plot['Frecuencia'][::-1],
                                    orientation='h',
                                    marker_color='#32CD32',
                                    text=df_combinaciones_plot['Frecuencia'][::-1],
                                    textposition='auto',
                                    hovertemplate='<b>%{y}</b><br>Frecuencia: %{x}<br>Soporte: %{customdata:.2f}%<extra></extra>',
                                    customdata=df_combinaciones_plot['Soporte (%)'][::-1]
                                )
                            ])
                            
                            fig_combinaciones.update_layout(
                                title=f"Productos que se compran con '{producto_buscar}'",
                                xaxis_title="Frecuencia",
                                yaxis_title="",
                                height=max(400, num_mostrar_busqueda * 40),
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig_combinaciones, use_container_width=True)
                            
                            # Tabla detallada
                            st.markdown("#### 📋 Tabla Detallada")
                            st.dataframe(df_combinaciones_plot, use_container_width=True, hide_index=True)
                            
                            # Recomendaciones específicas
                            st.markdown("#### 💡 Recomendaciones Específicas")
                            
                            top_3 = df_combinaciones.head(3)
                            
                            st.success(f"**Productos Top para Cross-Selling con '{producto_buscar}':**")
                            for idx, row in top_3.iterrows():
                                st.markdown(f"• **{row['Producto Combinado']}** - {row['Frecuencia']} veces ({row['Soporte (%)']}% de las transacciones)")
                            
                            st.info(f"💼 **Estrategia sugerida:** Cuando un cliente compre '{producto_buscar}', el personal debería sugerir estos productos para incrementar el ticket promedio.")
                        
                        else:
                            st.warning(f"No se encontraron combinaciones para el producto '{producto_buscar}' en el período seleccionado.")
        
        # ========== TAB 6: FECHAS ESPECIALES ==========
        with tab6:
            st.markdown("### 🎉 Análisis de Fechas Especiales")
            st.caption("Compara las ventas de días específicos vs el promedio general")
            
            # Selector de fecha
            st.markdown("#### 📅 Selecciona una Fecha para Analizar")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Obtener años disponibles
                años_disponibles = sorted(df_temp['año'].unique())
                año_especial = st.selectbox("Año:", años_disponibles, key="año_especial")
            
            with col2:
                # Obtener meses con datos para ese año
                meses_disponibles_año = sorted(df_temp[df_temp['año'] == año_especial]['mes_num'].unique())
                mes_especial = st.selectbox(
                    "Mes:",
                    meses_disponibles_año,
                    format_func=lambda x: meses_español[x],
                    key="mes_especial"
                )
            
            # Obtener días disponibles para ese mes/año
            df_mes_especial = df_temp[(df_temp['año'] == año_especial) & (df_temp['mes_num'] == mes_especial)]
            dias_disponibles = sorted(df_mes_especial['dia_mes'].unique())
            
            dia_especial = st.selectbox("Día:", dias_disponibles, key="dia_especial")
            
            # Botón para analizar
            if st.button("🔍 Analizar Fecha", type="primary"):
                fecha_seleccionada = pd.Timestamp(year=año_especial, month=mes_especial, day=dia_especial).date()
                
                st.markdown(f"### 📊 Análisis del {dia_especial} de {meses_español[mes_especial]} de {año_especial}")
                
                # Filtrar datos de la fecha especial
                df_fecha_especial = df_temp[df_temp['fecha'] == fecha_seleccionada]
                
                if df_fecha_especial.empty:
                    st.warning("No hay datos disponibles para esta fecha")
                else:
                    # Calcular ventas de la fecha especial por producto
                    ventas_fecha = df_fecha_especial.groupby('producto')['cantidad'].sum().reset_index()
                    ventas_fecha.columns = ['producto', 'cantidad_fecha']
                    
                    # Calcular promedio general (excluyendo la fecha especial)
                    df_sin_fecha = df_temp[df_temp['fecha'] != fecha_seleccionada]
                    
                    # Calcular promedio diario por producto
                    dias_totales = df_sin_fecha['fecha'].nunique()
                    ventas_promedio = df_sin_fecha.groupby('producto')['cantidad'].sum().reset_index()
                    ventas_promedio['cantidad_promedio'] = ventas_promedio['cantidad'] / dias_totales
                    ventas_promedio = ventas_promedio[['producto', 'cantidad_promedio']]
                    
                    # Combinar datos
                    comparacion = ventas_fecha.merge(ventas_promedio, on='producto', how='outer').fillna(0)
                    comparacion['diferencia'] = comparacion['cantidad_fecha'] - comparacion['cantidad_promedio']
                    comparacion['variacion_pct'] = ((comparacion['cantidad_fecha'] - comparacion['cantidad_promedio']) / 
                                                     comparacion['cantidad_promedio'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
                    
                    # Filtrar productos con ventas significativas
                    comparacion_filtrada = comparacion[
                        (comparacion['cantidad_fecha'] > 0) | (comparacion['cantidad_promedio'] > 1)
                    ].copy()
                    
                    # Métricas generales
                    st.markdown("#### 📈 Métricas Generales del Día")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_fecha = comparacion_filtrada['cantidad_fecha'].sum()
                    total_promedio = comparacion_filtrada['cantidad_promedio'].sum()
                    variacion_total = ((total_fecha - total_promedio) / total_promedio * 100) if total_promedio > 0 else 0
                    productos_mas_vendidos = len(comparacion_filtrada[comparacion_filtrada['variacion_pct'] > 20])
                    
                    with col1:
                        st.metric("📦 Ventas del Día", f"{int(total_fecha):,} unidades")
                    with col2:
                        st.metric("📊 Promedio Diario", f"{int(total_promedio):,} unidades")
                    with col3:
                        st.metric("📈 Variación Total", f"{variacion_total:+.1f}%", 
                                 delta=f"{int(total_fecha - total_promedio):+,} unidades")
                    with col4:
                        st.metric("🔥 Productos Destacados", f"{productos_mas_vendidos}", 
                                 help="Productos con +20% de ventas vs promedio")
                    
                    st.divider()
                    
                    # Top productos que más subieron
                    st.markdown("#### 🚀 Productos que MÁS Aumentaron")
                    
                    top_subida = comparacion_filtrada.nlargest(15, 'variacion_pct')
                    top_subida = top_subida[top_subida['cantidad_fecha'] > 0]
                    
                    if not top_subida.empty:
                        max_productos_subida = min(15, len(top_subida))
                        if max_productos_subida > 5:
                            num_mostrar_subida = st.slider(
                                "Cantidad de productos a mostrar:",
                                min_value=5,
                                max_value=max_productos_subida,
                                value=min(10, max_productos_subida),
                                step=5,
                                key="slider_subida"
                            )
                        else:
                            num_mostrar_subida = max_productos_subida
                            st.info(f"Mostrando {num_mostrar_subida} productos disponibles")
                        
                        top_subida_plot = top_subida.head(num_mostrar_subida)
                        
                        # Crear gráfico comparativo
                        fig_comparacion = go.Figure()
                        
                        fig_comparacion.add_trace(go.Bar(
                            name='Promedio Diario',
                            y=top_subida_plot['producto'][::-1],
                            x=top_subida_plot['cantidad_promedio'][::-1],
                            orientation='h',
                            marker_color='lightgray',
                            text=top_subida_plot['cantidad_promedio'][::-1].round(1),
                            textposition='auto'
                        ))
                        
                        fig_comparacion.add_trace(go.Bar(
                            name=f'{dia_especial}/{mes_especial}/{año_especial}',
                            y=top_subida_plot['producto'][::-1],
                            x=top_subida_plot['cantidad_fecha'][::-1],
                            orientation='h',
                            marker_color='#32CD32',
                            text=top_subida_plot['cantidad_fecha'][::-1],
                            textposition='auto'
                        ))
                        
                        fig_comparacion.update_layout(
                            title="Comparación: Fecha Especial vs Promedio",
                            xaxis_title="Unidades Vendidas",
                            yaxis_title="",
                            height=max(400, num_mostrar_subida * 50),
                            barmode='group',
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        st.plotly_chart(fig_comparacion, use_container_width=True)
                        
                        # Tabla detallada
                        st.markdown("#### 📋 Tabla Detallada de Incrementos")
                        
                        tabla_subida = top_subida_plot[['producto', 'cantidad_promedio', 'cantidad_fecha', 'diferencia', 'variacion_pct']].copy()
                        tabla_subida.columns = ['Producto', 'Promedio Diario', 'Ventas en Fecha', 'Diferencia', 'Variación (%)']
                        tabla_subida['Promedio Diario'] = tabla_subida['Promedio Diario'].round(1)
                        tabla_subida['Ventas en Fecha'] = tabla_subida['Ventas en Fecha'].astype(int)
                        tabla_subida['Diferencia'] = tabla_subida['Diferencia'].apply(lambda x: f"{x:+.1f}")
                        tabla_subida['Variación (%)'] = tabla_subida['Variación (%)'].apply(lambda x: f"{x:+.1f}%")
                        
                        st.dataframe(tabla_subida, use_container_width=True, hide_index=True)
                        
                        st.divider()
                        
                        # Productos que bajaron
                        st.markdown("#### 📉 Productos que Disminuyeron")
                        
                        top_bajada = comparacion_filtrada.nsmallest(10, 'variacion_pct')
                        top_bajada = top_bajada[top_bajada['cantidad_promedio'] > 1]
                        
                        if not top_bajada.empty:
                            tabla_bajada = top_bajada[['producto', 'cantidad_promedio', 'cantidad_fecha', 'diferencia', 'variacion_pct']].copy()
                            tabla_bajada.columns = ['Producto', 'Promedio Diario', 'Ventas en Fecha', 'Diferencia', 'Variación (%)']
                            tabla_bajada['Promedio Diario'] = tabla_bajada['Promedio Diario'].round(1)
                            tabla_bajada['Ventas en Fecha'] = tabla_bajada['Ventas en Fecha'].astype(int)
                            tabla_bajada['Diferencia'] = tabla_bajada['Diferencia'].apply(lambda x: f"{x:+.1f}")
                            tabla_bajada['Variación (%)'] = tabla_bajada['Variación (%)'].apply(lambda x: f"{x:+.1f}%")
                            
                            st.dataframe(tabla_bajada, use_container_width=True, hide_index=True)
                        else:
                            st.info("No se encontraron productos con disminución significativa")
                        
                        st.divider()
                        
                        # Insights y recomendaciones
                        st.markdown("#### 💡 Insights y Recomendaciones")
                        
                        # Identificar el producto con mayor incremento absoluto
                        producto_estrella = top_subida.iloc[0]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.success("**🌟 PRODUCTO ESTRELLA DEL DÍA**")
                            st.markdown(f"**{producto_estrella['producto']}**")
                            st.info(f"Incremento del **{producto_estrella['variacion_pct']:.1f}%**\n\n"
                                   f"Vendió **{int(producto_estrella['cantidad_fecha'])}** unidades vs **{producto_estrella['cantidad_promedio']:.1f}** promedio")
                            
                        with col2:
                            st.success("**📊 RESUMEN GENERAL**")
                            productos_con_incremento = len(comparacion_filtrada[comparacion_filtrada['variacion_pct'] > 0])
                            pct_productos_incremento = (productos_con_incremento / len(comparacion_filtrada) * 100) if len(comparacion_filtrada) > 0 else 0
                            st.info(f"**{productos_con_incremento}** productos ({pct_productos_incremento:.1f}%) tuvieron incremento en ventas\n\n"
                                   f"Ventas totales {variacion_total:+.1f}% vs promedio")
                        
                        # Recomendaciones estratégicas
                        st.markdown("---")
                        st.markdown("**📋 Acciones Recomendadas para Fechas Similares:**")
                        
                        if variacion_total > 20:
                            st.markdown("✅ **Fecha de alta demanda detectada**")
                            st.markdown("• Aumentar stock de los productos destacados")
                            st.markdown("• Considerar promociones especiales")
                            st.markdown("• Reforzar personal en horarios pico")
                        elif variacion_total < -10:
                            st.markdown("⚠️ **Fecha de baja demanda detectada**")
                            st.markdown("• Revisar estrategia de comunicación")
                            st.markdown("• Considerar promociones para activar ventas")
                        else:
                            st.markdown("📊 **Fecha con comportamiento normal**")
                            st.markdown("• Mantener niveles de stock habituales")
                        
                        # Productos para preparar con anticipación
                        productos_preparar = top_subida.head(5)
                        st.markdown(f"\n**🎯 Top 5 Productos para Preparar:**")
                        for idx, row in productos_preparar.iterrows():
                            st.markdown(f"• **{row['producto']}**: preparar ~{int(row['cantidad_fecha'])} unidades ({row['variacion_pct']:+.0f}% vs promedio)")
                        
                    else:
                        st.info("No hay datos suficientes para mostrar productos destacados en esta fecha")
                    
                    # Análisis por hora del día especial
                    with st.expander("🕐 Ver Análisis por Hora de la Fecha Especial", expanded=False):
                        st.markdown("##### Distribución de Ventas por Hora")
                        
                        ventas_hora_especial = df_fecha_especial.groupby('hora_num')['cantidad'].sum().reset_index()
                        ventas_hora_promedio = df_sin_fecha.groupby('hora_num')['cantidad'].sum() / dias_totales
                        ventas_hora_promedio = ventas_hora_promedio.reset_index()
                        ventas_hora_promedio.columns = ['hora_num', 'cantidad_promedio']
                        
                        comparacion_hora = ventas_hora_especial.merge(ventas_hora_promedio, on='hora_num', how='outer').fillna(0)
                        
                        fig_hora_especial = go.Figure()
                        
                        fig_hora_especial.add_trace(go.Scatter(
                            x=comparacion_hora['hora_num'],
                            y=comparacion_hora['cantidad_promedio'],
                            mode='lines+markers',
                            name='Promedio',
                            line=dict(color='lightgray', width=2),
                            marker=dict(size=6)
                        ))
                        
                        fig_hora_especial.add_trace(go.Scatter(
                            x=comparacion_hora['hora_num'],
                            y=comparacion_hora['cantidad'],
                            mode='lines+markers',
                            name='Fecha Especial',
                            line=dict(color='#FFD700', width=3),
                            marker=dict(size=8),
                            fill='tonexty',
                            fillcolor='rgba(255,215,0,0.2)'
                        ))
                        
                        fig_hora_especial.update_layout(
                            xaxis_title="Hora del Día",
                            yaxis_title="Unidades Vendidas",
                            height=400,
                            xaxis=dict(dtick=2),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        st.plotly_chart(fig_hora_especial, use_container_width=True)
                        
                        hora_pico_fecha = comparacion_hora.loc[comparacion_hora['cantidad'].idxmax(), 'hora_num']
                        cantidad_hora_pico = comparacion_hora['cantidad'].max()
                        st.info(f"💡 La hora pico en esta fecha fue a las **{int(hora_pico_fecha)}:00** con **{int(cantidad_hora_pico)}** unidades vendidas")
    
    else:
        st.warning("⚠️ No hay datos disponibles para el período seleccionado.")

except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
    st.info("Verifica que la URL del CSV sea correcta y que el archivo esté accesible.")
