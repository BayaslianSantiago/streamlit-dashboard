import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

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
    
    # Preparar datos temporales
    df_temp = df_limpio.copy()
    df_temp['hora_num'] = df_temp['fecha_hora'].dt.hour
    df_temp['minuto'] = df_temp['fecha_hora'].dt.minute
    df_temp['media_hora'] = df_temp['hora_num'] + (df_temp['minuto'] >= 30).astype(int) * 0.5
    df_temp['dia_semana'] = df_temp['fecha_hora'].dt.day_name()
    df_temp['mes_num'] = df_temp['fecha_hora'].dt.month
    df_temp['año'] = df_temp['fecha_hora'].dt.year
    df_temp['semana_del_mes'] = ((df_temp['fecha_hora'].dt.day - 1) // 7) + 1
    
    # Diccionarios
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
    
    # --- SIDEBAR: FILTROS GLOBALES ---
    with st.sidebar:
        st.header("🔍 Filtros")
        
        # Obtener meses disponibles
        meses_con_datos = df_temp.groupby(['año', 'mes_num'])['cantidad'].sum()
        meses_con_datos = meses_con_datos[meses_con_datos > 0].reset_index()
        
        meses_opciones = ['📊 Todos los datos']
        for _, row in meses_con_datos.iterrows():
            mes_nombre = meses_español[row['mes_num']]
            año = int(row['año'])
            meses_opciones.append(f"{mes_nombre} {año}")
        
        periodo_seleccionado = st.selectbox(
            "Período:",
            meses_opciones,
            help="Selecciona el período a analizar"
        )
        
        st.divider()
        
        # Info del período
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
        
        st.metric("📋 Registros", f"{len(df_analisis):,}")
        st.metric("🏷️ Productos", f"{df_analisis['producto'].nunique():,}")
        st.metric("📅 Rango", f"{df_analisis['fecha_hora'].min().strftime('%d/%m/%y')} - {df_analisis['fecha_hora'].max().strftime('%d/%m/%y')}")
    
    # --- MÉTRICAS PRINCIPALES ---
    if not df_analisis.empty:
        st.markdown(f"### 📊 Resumen General - {titulo_periodo}")
        
        total_vendido = df_analisis['cantidad'].sum()
        ventas_hora_dia = df_analisis.groupby(['dia_semana', 'hora_num'])['cantidad'].sum().reset_index()
        idx_max = ventas_hora_dia['cantidad'].idxmax()
        hora_pico = int(ventas_hora_dia.loc[idx_max, 'hora_num'])
        dia_pico = dias_español[ventas_hora_dia.loc[idx_max, 'dia_semana']]
        cantidad_pico = int(ventas_hora_dia.loc[idx_max, 'cantidad'])
        promedio_diario = df_analisis.groupby(df_analisis['fecha_hora'].dt.date)['cantidad'].sum().mean()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Total Vendido", f"{int(total_vendido):,} unidades")
        with col2:
            st.metric("📊 Promedio Diario", f"{promedio_diario:.0f} unidades")
        with col3:
            st.metric("🕐 Hora Pico", f"{hora_pico}:00 hs - {dia_pico}")
        with col4:
            st.metric("🔥 Ventas Máximas", f"{cantidad_pico} unidades")
        
        st.divider()
        
        # --- TABS PRINCIPALES ---
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Análisis de Ventas", "🎯 Matriz BCG", "🏆 Ranking de Productos", "🔍 Búsqueda Detallada"])
        
        # ==================== TAB 1: ANÁLISIS DE VENTAS ====================
        with tab1:
            st.markdown("### 🔥 Patrones de Venta")
            
            # Heatmap principal (siempre visible)
            st.markdown("#### Mapa de Calor por Media Hora")
            
            ventas_media_hora = df_analisis.groupby(['dia_semana', 'media_hora'])['cantidad'].sum().reset_index()
            ventas_matriz_mh = ventas_media_hora.pivot(index='dia_semana', columns='media_hora', values='cantidad').fillna(0)
            ventas_matriz_mh = ventas_matriz_mh.reindex([d for d in dias_orden if d in ventas_matriz_mh.index])
            ventas_matriz_mh.index = [dias_español[d] for d in ventas_matriz_mh.index]
            etiquetas_horas = [f"{int(h)}:{('00' if h % 1 == 0 else '30')}" for h in ventas_matriz_mh.columns]
            
            fig_heatmap_mh = go.Figure(data=go.Heatmap(
                z=ventas_matriz_mh.values,
                x=etiquetas_horas,
                y=ventas_matriz_mh.index,
                colorscale='YlOrRd',
                text=ventas_matriz_mh.values.astype(int),
                texttemplate='%{text}',
                textfont={"size": 9},
                colorbar=dict(title="Unidades")
            ))
            
            fig_heatmap_mh.update_layout(
                xaxis_title="Hora del Día",
                yaxis_title="Día de la Semana",
                height=450,
                xaxis=dict(tickangle=-45)
            )
            
            st.plotly_chart(fig_heatmap_mh, use_container_width=True)
            
            # Análisis adicional (colapsable)
            with st.expander("📊 Ver análisis adicional de ventas"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Ventas por día de la semana
                    st.markdown("##### Ventas por Día de la Semana")
                    ventas_dia = df_analisis.groupby('dia_semana')['cantidad'].sum().reset_index()
                    ventas_dia['dia_semana'] = ventas_dia['dia_semana'].map(dias_español)
                    ventas_dia = ventas_dia.set_index('dia_semana').reindex([dias_español[d] for d in dias_orden if d in df_analisis['dia_semana'].unique()])
                    
                    fig_dias = go.Figure(data=[
                        go.Bar(x=ventas_dia.index, y=ventas_dia['cantidad'].values, 
                               marker_color='#1E90FF',
                               text=ventas_dia['cantidad'].values,
                               textposition='auto')
                    ])
                    fig_dias.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig_dias, use_container_width=True)
                
                with col2:
                    # Ventas por hora
                    st.markdown("##### Ventas por Hora del Día")
                    ventas_hora = df_analisis.groupby('hora_num')['cantidad'].sum().reset_index()
                    
                    fig_horas = go.Figure(data=[
                        go.Scatter(x=ventas_hora['hora_num'], y=ventas_hora['cantidad'],
                                  mode='lines+markers',
                                  line=dict(color='#32CD32', width=3),
                                  marker=dict(size=8),
                                  fill='tozeroy',
                                  fillcolor='rgba(50,205,50,0.2)')
                    ])
                    fig_horas.update_layout(height=300, showlegend=False, xaxis=dict(dtick=2))
                    st.plotly_chart(fig_horas, use_container_width=True)
                
                # Heatmap por semana del mes (solo si es mes específico)
                if mes_num_sel is not None:
                    st.markdown("##### Heatmap por Semana del Mes")
                    ventas_semana = df_analisis.groupby(['semana_del_mes', 'dia_semana'])['cantidad'].sum().reset_index()
                    ventas_matriz_sem = ventas_semana.pivot(index='semana_del_mes', columns='dia_semana', values='cantidad').fillna(0)
                    
                    dias_disponibles = [d for d in dias_orden if d in ventas_matriz_sem.columns]
                    ventas_matriz_sem = ventas_matriz_sem[dias_disponibles]
                    ventas_matriz_sem.columns = [dias_español[d] for d in ventas_matriz_sem.columns]
                    ventas_matriz_sem.index = [f"Semana {int(s)}" for s in ventas_matriz_sem.index]
                    
                    fig_heatmap_sem = go.Figure(data=go.Heatmap(
                        z=ventas_matriz_sem.values,
                        x=ventas_matriz_sem.columns,
                        y=ventas_matriz_sem.index,
                        colorscale='Viridis',
                        text=ventas_matriz_sem.values.astype(int),
                        texttemplate='%{text}',
                        textfont={"size": 12},
                        colorbar=dict(title="Unidades")
                    ))
                    
                    fig_heatmap_sem.update_layout(height=350)
                    st.plotly_chart(fig_heatmap_sem, use_container_width=True)
        
        # ==================== TAB 2: MATRIZ BCG ====================
        with tab2:
            st.markdown("### 📊 Matriz BCG - Boston Consulting Group")
            
            # Calcular datos BCG
            ventas_por_producto = df_analisis.groupby('producto')['cantidad'].sum().reset_index()
            ventas_por_producto['participacion'] = (ventas_por_producto['cantidad'] / ventas_por_producto['cantidad'].sum()) * 100
            
            # Calcular crecimiento
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
            
            # Filtrar productos relevantes
            bcg_data_plot = bcg_data[
                (bcg_data['participacion'] >= 0.5) | 
                (bcg_data['cantidad'].rank(ascending=False) <= 40)
            ].copy()
            
            bcg_data_plot['tasa_crecimiento_plot'] = bcg_data_plot['tasa_crecimiento'].clip(-100, 300)
            
            st.info(f"📊 **Comparación:** {periodo_comparacion}")
            
            # Gráfico BCG
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
            
            fig_bcg.add_hline(y=crecimiento_medio, line_dash="dash", line_color="gray", line_width=2)
            fig_bcg.add_vline(x=participacion_media, line_dash="dash", line_color="gray", line_width=2)
            
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
                height=550,
                showlegend=True,
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02, font=dict(size=12)),
                plot_bgcolor='white',
                xaxis=dict(title="Participación de Mercado (%)", gridcolor='lightgray', showgrid=True),
                yaxis=dict(title="Tasa de Crecimiento (%)", gridcolor='lightgray', showgrid=True)
            )
            
            st.plotly_chart(fig_bcg, use_container_width=True)
            
            # Resumen por categoría (colapsable)
            with st.expander("📋 Ver resumen detallado por categoría"):
                resumen_categorias = bcg_data.groupby('categoria').agg({
                    'producto': 'count',
                    'cantidad': 'sum',
                    'participacion': 'sum'
                }).reset_index()
                resumen_categorias.columns = ['Categoría', 'Cantidad de Productos', 'Unidades Vendidas', 'Participación Total (%)']
                resumen_categorias['Participación Total (%)'] = resumen_categorias['Participación Total (%)'].round(2)
                
                st.dataframe(resumen_categorias, use_container_width=True, hide_index=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### ⭐ Top 5 Estrellas")
                    estrellas = bcg_data[bcg_data['categoria'] == '⭐ Estrella'].nlargest(5, 'cantidad')[['producto', 'cantidad', 'tasa_crecimiento']]
                    if not estrellas.empty:
                        estrellas['tasa_crecimiento'] = estrellas['tasa_crecimiento'].round(1).astype(str) + '%'
                        st.dataframe(estrellas, use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay productos en esta categoría")
                
                with col2:
                    st.markdown("##### 🐕 Top 5 Perros")
                    perros = bcg_data[bcg_data['categoria'] == '🐕 Perro'].nsmallest(5, 'cantidad')[['producto', 'cantidad', 'tasa_crecimiento']]
                    if not perros.empty:
                        perros['tasa_crecimiento'] = perros['tasa_crecimiento'].round(1).astype(str) + '%'
                        st.dataframe(perros, use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay productos en esta categoría")
        
        # ==================== TAB 3: RANKING ====================
        with tab3:
            st.markdown("### 🏆 Ranking de Productos")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                criterio_ranking = st.selectbox(
                    "Ordenar por:",
                    ["📊 Unidades Vendidas", "📈 Participación de Mercado (%)", "🔥 Tasa de Crecimiento (%)", "🏷️ Categoría BCG"]
                )
            
            with col2:
                orden = st.radio("Orden:", ["⬇️ Mayor a Menor", "⬆️ Menor a Mayor"], horizontal=True)
            
            with col3:
                limite = st.selectbox("Mostrar:", [10, 20, 50, 100, "Todos"], index=1)
            
            # Preparar ranking
            ranking_data = bcg_data.copy()
            
            if criterio_ranking == "📊 Unidades Vendidas":
                col_orden = 'cantidad'
            elif criterio_ranking == "📈 Participación de Mercado (%)":
                col_orden = 'participacion'
            elif criterio_ranking == "🔥 Tasa de Crecimiento (%)":
                col_orden = 'tasa_crecimiento'
            else:
                col_orden = 'categoria'
            
            ascending = True if orden == "⬆️ Menor a Mayor" else False
            ranking_data = ranking_data.sort_values(col_orden, ascending=ascending).reset_index(drop=True)
            
            if limite != "Todos":
                ranking_data = ranking_data.head(limite)
            
            ranking_data.insert(0, '#', range(1, len(ranking_data) + 1))
            
            tabla_ranking = ranking_data[['#', 'producto', 'cantidad', 'participacion', 'tasa_crecimiento', 'categoria']].copy()
            tabla_ranking.columns = ['#', 'Producto', 'Unidades Vendidas', 'Participación (%)', 'Crecimiento (%)', 'Categoría BCG']
            
            tabla_ranking['Unidades Vendidas'] = tabla_ranking['Unidades Vendidas'].apply(lambda x: f"{int(x):,}")
            tabla_ranking['Participación (%)'] = tabla_ranking['Participación (%)'].apply(lambda x: f"{x:.2f}%")
            tabla_ranking['Crecimiento (%)'] = tabla_ranking['Crecimiento (%)'].apply(lambda x: f"{x:+.1f}%")
            
            st.dataframe(tabla_ranking, use_container_width=True, hide_index=True)
            
            # Estadísticas del ranking (colapsable)
            with st.expander("📊 Ver estadísticas del ranking"):
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
                
                st.markdown("##### 🎯 Distribución por Categoría BCG")
                
                distribucion_bcg = ranking_data.groupby('categoria').agg({
                    'producto': 'count',
                    'cantidad': 'sum'
                }).reset_index()
                distribucion_bcg.columns = ['Categoría', 'Cantidad de Productos', 'Unidades Vendidas']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_dist_cat = go.Figure(data=[
                        go.Pie(
                            labels=distribucion_bcg['Categoría'],
                            values=distribucion_bcg['Cantidad de Productos'],
                            hole=0.4,
                            marker=dict(colors=['#FFD700', '#32CD32', '#1E90FF', '#DC143C'])
                        )
                    ])
                    fig_dist_cat.update_layout(title="Productos por Categoría", height=300, showlegend=True)
                    st.plotly_chart(fig_dist_cat, use_container_width=True)
                
                with col2:
                    fig_dist_ventas = go.Figure(data=[
                        go.Pie(
                            labels=distribucion_bcg['Categoría'],
                            values=distribucion_bcg['Unidades Vendidas'],
                            hole=0.4,
                            marker=dict(colors=['#FFD700', '#32CD32', '#1E90FF', '#DC143C'])
                        )
                    ])
                    fig_dist_ventas.update_layout(title="Ventas por Categoría", height=300, showlegend=True)
                    st.plotly_chart(fig_dist_ventas, use_container_width=True)
        
        # ==================== TAB 4: BÚSQUEDA DETALLADA ====================
        with tab4:
            st.markdown("### 🔍 Análisis Detallado por Producto")
            
            productos_disponibles = sorted(df_analisis['producto'].unique())
            producto_seleccionado = st.selectbox(
                "Selecciona un producto:",
                productos_disponibles,
                help="Elige un producto para ver su análisis completo"
            )
            
            if producto_seleccionado:
                df_producto = df_analisis[df_analisis['producto'] == producto_seleccionado].copy()
                info_bcg = bcg_data[bcg_data['producto'] == producto_seleccionado].iloc[0]
                
                st.markdown(f"#### 📦 {producto_seleccionado}")
                
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
                
                # Gráficos
                col1, col2 = st.columns(2)
