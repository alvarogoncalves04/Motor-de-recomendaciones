# 04_dashboard.py
# DASHBOARD DE RECOMENDACIONES CON STREAMLIT

import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="Sistema de Recomendación",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sistema de Recomendación de Productos")
st.markdown("---")

# ============================================
# CARGAR DATOS
# ============================================
@st.cache_data
def cargar_datos():
    conn = sqlite3.connect('data/olap.db')
    
    clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    productos = pd.read_sql_query("SELECT * FROM productos", conn)
    matriz = pd.read_sql_query("SELECT * FROM matriz_usuarios_productos", conn)
    popularidad = pd.read_sql_query("SELECT * FROM popularidad", conn)
    total_gastado = pd.read_sql_query("SELECT * FROM total_gastado", conn)
    
    conn.close()
    
    return clientes, productos, matriz, popularidad, total_gastado

clientes, productos, matriz, popularidad, total_gastado = cargar_datos()

# ============================================
# SIDEBAR - SELECCIÓN DE CLIENTE
# ============================================
st.sidebar.header("🔍 Seleccionar Cliente")

# Selector de cliente
nombres_clientes = clientes['nombre'].tolist()
cliente_seleccionado = st.sidebar.selectbox(
    "Elige un cliente",
    nombres_clientes
)

# Obtener ID del cliente
cliente_id = clientes[clientes['nombre'] == cliente_seleccionado]['id_cliente'].values[0]

# Obtener datos del cliente
cliente_info = clientes[clientes['id_cliente'] == cliente_id].iloc[0]
gasto = total_gastado[total_gastado['id_cliente'] == cliente_id]

# ============================================
# FILA 1: INFORMACIÓN DEL CLIENTE
# ============================================
st.subheader(f"👤 Cliente: {cliente_seleccionado}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📧 Email", cliente_info['email'])

with col2:
    st.metric("📍 Ciudad", cliente_info['ciudad'])

with col3:
    st.metric("💰 Total Gastado", f"${gasto['total_gastado'].values[0]:,.2f}" if not gasto.empty else "$0.00")

with col4:
    # Productos comprados por el cliente
    conn = sqlite3.connect('data/olap.db')
    compras_cliente = pd.read_sql_query(
        f"SELECT COUNT(*) as num_compras FROM compras_enriquecidas WHERE id_cliente = {cliente_id}",
        conn
    )
    conn.close()
    st.metric("📦 Compras", compras_cliente['num_compras'].values[0])

st.markdown("---")

# ============================================
# FILA 2: RECOMENDACIONES
# ============================================
st.subheader("🎯 Productos Recomendados para este Cliente")

# Obtener productos que el cliente NO ha comprado
conn = sqlite3.connect('data/olap.db')
productos_comprados = pd.read_sql_query(
    f"SELECT id_producto FROM compras_enriquecidas WHERE id_cliente = {cliente_id}",
    conn
)
conn.close()

productos_comprados_lista = productos_comprados['id_producto'].tolist()
productos_no_comprados = productos[~productos['id_producto'].isin(productos_comprados_lista)]

# Recomendar los productos más populares NO comprados
recomendaciones = productos_no_comprados.merge(popularidad, on='id_producto', how='left')
recomendaciones = recomendaciones.sort_values('total_compras', ascending=False).head(5)

if not recomendaciones.empty:
    cols = st.columns(5)
    
    for idx, (_, row) in enumerate(recomendaciones.iterrows()):
        # Verificar si la columna existe
        nombre = row.get('nombre', 'Producto')
        categoria = row.get('categoria', 'General')
        precio = row.get('precio', 0.0)
        total_compras = row.get('total_compras', 0)
        
        with cols[idx]:
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; text-align:center; background-color:#f9f9f9;">
                <h4 style="margin:0; color:#2c3e50;">{nombre}</h4>
                <p style="margin:5px 0; color:#7f8c8d;">{categoria}</p>
                <p style="margin:5px 0; font-size:18px; font-weight:bold; color:#27ae60;">${precio:.2f}</p>
                <p style="margin:5px 0; font-size:14px; color:#3498db;">⭐ {total_compras} compras</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("🎉 Este cliente ya compró todos los productos disponibles.")

st.markdown("---")

# ============================================
# FILA 3: GRÁFICOS
# ============================================
# ============================================
# FILA 3: GRÁFICOS
# ============================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Top 10 Productos Más Populares")
    fig, ax = plt.subplots(figsize=(8, 6))
    # popularidad ya tiene nombre, categoria, precio desde el ETL
    top_populares = popularidad.head(10).copy()
    ax.barh(top_populares['nombre'], top_populares['total_compras'], color='#3498db')
    ax.set_xlabel("Número de Compras")
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("📈 Distribución de Clientes por Ciudad")
    fig, ax = plt.subplots(figsize=(8, 6))
    ciudad_counts = clientes['ciudad'].value_counts()
    ax.pie(ciudad_counts.values, labels=ciudad_counts.index, autopct='%1.1f%%', startangle=90)
    st.pyplot(fig)
    plt.close()

# ============================================
# FILA 4: HISTORIAL DE COMPRAS DEL CLIENTE
# ============================================
st.subheader("📋 Historial de Compras del Cliente")

conn = sqlite3.connect('data/olap.db')
historial = pd.read_sql_query(
    f"""
    SELECT 
        fecha,
        nombre as producto,
        cantidad,
        precio_unitario,
        total,
        categoria
    FROM compras_enriquecidas
    WHERE id_cliente = {cliente_id}
    ORDER BY fecha DESC
    LIMIT 20
    """,
    conn
)
conn.close()

if not historial.empty:
    st.dataframe(historial, use_container_width=True)
else:
    st.info("Este cliente no tiene compras registradas.")

# ============================================
# DESCARGA
# ============================================
st.markdown("---")
if st.button("📥 Descargar recomendaciones (CSV)"):
    csv = recomendaciones.to_csv(index=False)
    st.download_button(
        label="Click para descargar",
        data=csv,
        file_name=f"recomendaciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )