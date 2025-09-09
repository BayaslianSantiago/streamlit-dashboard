import streamlit as st
import pandas as pd
import plotly.express as px
from prophet import Prophet

def limpiar_excel(file):
    """
    Función que recibe un archivo Excel (uploaded_file de Streamlit)
    y devuelve un DataFrame limpio y listo para analizar.
    """
    # --- 1. Cargar Excel y limpiar encabezado ---
    df = (
        pd.read_excel(file, header=None)
        .iloc[5:]                          # Saltar filas iniciales
        .rename(columns=lambda x: str(x))  # Normalizar nombres temporales
    )
    df.columns = df.iloc[0]  # Usar fila como encabezado
    df = df.iloc[1:]         # Eliminar fila de encabezado real

    # --- 2. Eliminar columnas innecesarias ---
    df = df.drop(df.columns[[3, 4]], axis=1)

    # --- 3. Eliminar filas con "Codigo" en columna Hora ---
    df = df[~df["Hora"].str.contains("Codigo", case=False, na=False)]

    # --- 4. Rellenar fechas ---
    df["Fecha"] = df["Fecha"].ffill()

    # --- 5. Renombrar columnas finales ---
    df.columns = ["fecha", "hora", "producto", "cantidad", "precio", "venta"]

    # --- 6. Validar y corregir horas ---
    mask_hora = df["hora"].astype(str).str.match(r"^(?:[01]?\d|2[0-3]):[0-5]\d$")
    df.loc[~mask_hora, "hora"] = None
    df["hora"] = df["hora"].ffill()

    # --- 7. Limpiar columnas y filas ---
    df = (
        df.drop(columns=["precio", "venta"])
          .dropna(subset=["cantidad"])      # Eliminar filas sin cantidad
          .reset_index(drop=True)           # Resetear índices
    )

    # Asegurar que cantidad sea numérica
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0)
    # --- 8. Combinar fecha y hora y convertir a datetime ---
    df['hora'] = df['hora'].astype(str)

    # Usar dayfirst=True para interpretar correctamente día/mes/año
    df['fecha_hora'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'], dayfirst=True, errors='coerce')

    # Eliminar filas donde la fecha_hora no se pudo crear
    df = df.dropna(subset=['fecha_hora'])

    return df


# --- INTERFAZ STREAMLIT ---
st.title("📊 Limpieza y Análisis de Ventas")

# Subida de archivo
uploaded_file = st.file_uploader("📂 Elige un archivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Limpiar el archivo
        df_limpio = limpiar_excel(uploaded_file)

        st.success("✅ Archivo procesado correctamente")
        # --- TABS ---
        tab1, tab2, tab3, tab4 = st.tabs(["📑 Datos completos", "🔎 Datos filtrados","​📊 Estadisticas","🔮 Predicción de Ventas"])

        with tab1:
            st.subheader("📑 DataFrame completo")
            st.dataframe(df_limpio)

        with tab2:
            st.subheader("🔎 Filtrar por producto")
            productos = df_limpio["producto"].unique()
            producto_sel = st.selectbox("Selecciona un producto", productos)

            df_filtrado = df_limpio[df_limpio["producto"] == producto_sel]

            # Calcular total vendido
            total_vendido = df_filtrado["cantidad"].sum()

            st.metric(
                label=f"Total vendido de {producto_sel}",
                value=int(total_vendido)
            )

            st.dataframe(df_filtrado)
        with tab3:
            st.subheader("📊 Estadísticas Generales")

            # Asegurarse de que el DataFrame no esté vacío
            if not df_limpio.empty:
                # --- Gráfico 1: Top 20 Productos más vendidos ---
                st.markdown("#### 📈 Top 20 Productos más Vendidos")
                
                # Agrupar por producto y sumar las cantidades
                top_productos = (
                    df_limpio.groupby("producto")["cantidad"]
                    .sum()
                    .nlargest(20) # Tomar los 20 más grandes
                    .sort_values(ascending=True) # Ordenar para el gráfico de barras
                )

                # Usar st.bar_chart para un gráfico interactivo
                st.bar_chart(top_productos)
                
                # --- Gráfico 2: Ventas a lo largo del tiempo ---
                st.markdown("#### 🕒 Evolución de Ventas por Día")

                # Preparar los datos: agrupar por fecha y sumar cantidades
                # Usaremos la columna 'fecha_hora' que creamos
                ventas_por_dia = df_limpio.set_index("fecha_hora").resample("D")["cantidad"].sum()

                # Usar st.line_chart para un gráfico de líneas
                st.line_chart(ventas_por_dia)
                
                # --- Métrica adicional: Producto más vendido ---
                producto_estrella = top_productos.idxmax()
                cantidad_estrella = top_productos.max()
                
                st.metric(
                    label="⭐ Producto Estrella",
                    value=producto_estrella,
                    delta=f"{int(cantidad_estrella)} unidades vendidas",
                    delta_color="off" # Para no mostrarlo como aumento/disminución
                )
                

            else:
                st.warning("No hay datos disponibles para mostrar estadísticas.")
                
                # --- TAB DE PREDICCIÓN ---

        with tab4:
            st.subheader("🔮 Predicción de Ventas por Producto")

            # Seleccionar producto
            productos = df_limpio["producto"].unique()
            producto_sel = st.selectbox("Selecciona un producto para predecir", productos)

            # Filtrar ventas semanales del producto
            df_prod = df_limpio[df_limpio["producto"]==producto_sel].copy()
            df_prod = df_prod.set_index("fecha_hora").resample("W")["cantidad"].sum().reset_index()
            df_prod.rename(columns={"fecha_hora":"ds","cantidad":"y"}, inplace=True)

            # Validar que haya suficientes datos
            if len(df_prod) < 4:
                st.warning("No hay suficientes datos para hacer predicción.")
            else:
                # Crear modelo Prophet
                m = Prophet()
                m.fit(df_prod)

                # Hacer predicción a 4 semanas
                future = m.make_future_dataframe(periods=4, freq="W")
                forecast = m.predict(future)

                # Mostrar gráfico interactivo
                fig = px.line(forecast, x="ds", y="yhat", title=f"Predicción de ventas de {producto_sel}")
                fig.add_scatter(x=df_prod["ds"], y=df_prod["y"], mode="markers", name="Ventas reales")
                st.plotly_chart(fig)

                # Métricas clave
                st.markdown("#### 📊 Ventas proyectadas para las próximas semanas")
                proyeccion = forecast[["ds","yhat"]].tail(4)
                proyeccion["yhat"] = proyeccion["yhat"].round().astype(int)
                st.table(proyeccion.rename(columns={"ds":"Semana","yhat":"Cantidad estimada"}))


    except Exception as e:
        st.error(f"❌ Ocurrió un error al procesar el archivo: {e}")
