# 📊 Análisis Estratégico de Ventas - Dashboard BCG & Heatmaps

![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 📋 Descripción

Sistema de análisis estratégico de datos de ventas que combina la **Matriz BCG** (Boston Consulting Group) con **Mapas de Calor** para transformar datos dispersos en decisiones estratégicas concretas.

Este proyecto permite:
- ✅ Clasificar productos según su potencial y participación (Estrellas, Vacas Lecheras, Interrogantes, Perros)
- ✅ Identificar patrones temporales de demanda por día, hora y semana
- ✅ Optimizar recursos operativos, logísticos y comerciales
- ✅ Tomar decisiones basadas en datos, no en intuición

---

## 🎯 Características Principales

### Matriz BCG
Clasifica productos en cuatro categorías estratégicas:
- **⭐ ESTRELLAS**: Alto crecimiento + Alta participación → Inversión prioritaria
- **🐄 VACAS LECHERAS**: Bajo crecimiento + Alta participación → Motor de efectivo
- **❓ INTERROGANTES**: Alto crecimiento + Baja participación → Decisión de inversión
- **🐕 PERROS**: Bajo crecimiento + Baja participación → Evaluar eliminación

### Mapas de Calor
- **Heatmap Semanal**: Identifica días de mayor/menor demanda
- **Heatmap Horario**: Detecta picos de actividad por día y hora
- Visualización intuitiva con gradientes de color

---

## 🛠️ Tecnologías Utilizadas

```
Python 3.8+
├── pandas          # Procesamiento de datos
├── numpy           # Cálculos numéricos
├── matplotlib      # Visualizaciones
├── seaborn         # Mapas de calor
└── plotly          # Gráficos interactivos (opcional)
```

---

## 📊 Uso

### Procesamiento de Datos

```python
from src.data_processing import cargar_datos, limpiar_datos

# Cargar datos de ventas
df = cargar_datos('data/raw/ventas.csv')

# Limpiar y preparar
df_limpio = limpiar_datos(df)
```

### Generación de Matriz BCG

```python
from src.bcg_matrix import calcular_matriz_bcg

# Calcular posición de productos
resultados = calcular_matriz_bcg(df_limpio)

# Visualizar
resultados.plot_matriz()
```

### Creación de Heatmaps

```python
from src.visualizations import generar_heatmap_semanal, generar_heatmap_horario

# Mapa de calor por semanas
generar_heatmap_semanal(df_limpio, mes='julio')

# Mapa de calor por día y hora
generar_heatmap_horario(df_limpio, mes='julio')
```

---

## 📈 Resultados del Análisis (Ejemplo - Julio)

### Distribución de Productos (Matriz BCG)

| Categoría | Porcentaje | Interpretación |
|-----------|-----------|----------------|
| ⭐ Estrellas | 51.2% | Alto crecimiento - Inversión prioritaria |
| 🐄 Vacas Lecheras | 44.6% | Motor de efectivo estable |
| ❓ Interrogantes | 2.35% | Evaluar potencial |
| 🐕 Perros | 1.79% | Revisar continuidad |

**Conclusión**: Portafolio saludable con 92% en categorías de alto rendimiento.

### Patrones Temporales Identificados

**Días de Mayor Demanda:**
- 🔥 Viernes y Sábados: 700-760 unidades
- 📉 Martes: Día más bajo consistentemente

**Horarios Críticos:**
- 🕐 **13:00 - 15:30**: Pico de mediodía
- 🕖 **18:30 - 19:30**: Pico de tarde-noche
- 🏆 **Sábado 15:00**: Máximo absoluto (312 unidades)

---

## 💡 Decisiones Estratégicas Derivadas

### 🏭 Operaciones
- Reforzar personal viernes/sábados en horarios pico
- Reducir recursos en martes y franjas 15:30-17:00

### 📢 Marketing
- Promociones concentradas en picos de tráfico
- Posicionar productos Estrella los fines de semana

### 📦 Logística
- Pedidos mayores los viernes
- Revisión de inventarios los lunes post-pico

### 💰 Compras
- Inversión sostenida en productos Estrella
- Evaluación de productos Perro

---

## ✉️ Contacto

**Instituto Tecnológico Beltrán**

- 📧 Email: bayasliansantiago@gmail.com
- 🌐 Website: [www.ejemplo.com](https://dashboard-esfav.streamlit.app/)

---

## 🙏 Agradecimientos

- Instituto Tecnológico Beltrán y a sus docentes.
- Metodología BCG desarrollada por Boston Consulting Group
- Comunidad de Python y bibliotecas de análisis de datos

---

*Última actualización: Octubre 2025*
