# 04_dashboard.py
# DASHBOARD DE RECOMENDACIONES CON CLUSTERING

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
    popularidad = pd.read_sql_query("SELECT * FROM popularidad", conn)
    total_gastado = pd.read_sql_query("SELECT * FROM total_gastado", conn)
    
    # Cargar clusters (si existen)
    try:
        clientes_cluster = pd.read_sql_query("SELECT * FROM clientes_con_cluster", conn)
        tiene_clusters = True
    except:
        clientes_cluster = None
        tiene_clusters = False
    
    conn.close()
    
    return clientes, productos, popularidad, total_gastado, clientes_cluster, tiene_clusters

clientes, productos, popularidad, total_gastado, clientes_cluster, tiene_clusters = cargar_datos()

# ============================================
# SIDEBAR - SELECCIÓN DE CLIENTE
# ============================================
st.sidebar.header("🔍 Seleccionar Cliente")

nombres_clientes = clientes['nombre'].tolist()
cliente_seleccionado = st.sidebar.selectbox(
    "Elige un cliente",
    nombres_clientes
)

cliente_id = clientes[clientes['nombre'] == cliente_seleccionado]['id_cliente'].values[0]
cliente_info = clientes[clientes['id_cliente'] == cliente_id].iloc[0]
gasto = total_gastado[total_gastado['id_cliente'] == cliente_id]

# ============================================
# INFORMACIÓN DEL CLUSTER (si existe)
# ============================================
if tiene_clusters:
    cluster_cliente = clientes_cluster[clientes_cluster['id_cliente'] == cliente_id]['cluster'].values[0]
    cluster_info = clientes_cluster[clientes_cluster['cluster'] == cluster_cliente]
    
    st.sidebar.subheader("📊 Información del Cluster")
    st.sidebar.write(f"**Cluster:** {cluster_cliente}")
    st.sidebar.write(f"**Clientes en cluster:** {len(cluster_info)}")
    
    # Gasto promedio del cluster
    ids_cluster = cluster_info['id_cliente'].tolist()
    gasto_cluster = total_gastado[total_gastado['id_cliente'].isin(ids_cluster)]['total_gastado'].mean()
    st.sidebar.write(f"**Gasto promedio cluster:** ${gasto_cluster:,.2f}")

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
    conn = sqlite3.connect('data/olap.db')
    compras_cliente = pd.read_sql_query(
        f"SELECT COUNT(*) as num_compras FROM compras_enriquecidas WHERE id_cliente = {cliente_id}",
        conn
    )
    conn.close()
    st.metric("📦 Compras", compras_cliente['num_compras'].values[0])

st.markdown("---")

# ============================================
# FILA 2: RECOMENDACIONES (MEJORADAS CON CLUSTERS)
# ============================================
st.subheader("🎯 Productos Recomendados para este Cliente")

conn = sqlite3.connect('data/olap.db')
productos_comprados = pd.read_sql_query(
    f"SELECT id_producto FROM compras_enriquecidas WHERE id_cliente = {cliente_id}",
    conn
)
conn.close()

productos_comprados_lista = productos_comprados['id_producto'].tolist()
productos_no_comprados = productos[~productos['id_producto'].isin(productos_comprados_lista)]

# Si hay clusters, recomendar productos populares en el mismo cluster
if tiene_clusters:
    # Obtener productos comprados por otros clientes del mismo cluster
    ids_cluster = cluster_info['id_cliente'].tolist()
    conn = sqlite3.connect('data/olap.db')
    query = f"""
    SELECT id_producto, COUNT(*) as frecuencia
    FROM compras_enriquecidas
    WHERE id_cliente IN ({','.join(map(str, ids_cluster))})
    AND id_producto NOT IN ({','.join(map(str, productos_comprados_lista)) if productos_comprados_lista else '0'})
    GROUP BY id_producto
    ORDER BY frecuencia DESC
    LIMIT 5
    """
    recomendaciones_cluster = pd.read_sql_query(query, conn)
    conn.close()
    
    if not recomendaciones_cluster.empty:
        # Obtener detalles de los productos recomendados
        ids_recomendados = recomendaciones_cluster['id_producto'].tolist()
        recomendaciones = productos[productos['id_producto'].isin(ids_recomendados)]
        recomendaciones = recomendaciones.merge(recomendaciones_cluster, on='id_producto', how='left')
        recomendaciones = recomendaciones.sort_values('frecuencia', ascending=False)
        metodo = "basado en tu cluster"
    else:
        # Fallback: productos populares globales
        recomendaciones = productos_no_comprados.merge(popularidad, on='id_producto', how='left')
        recomendaciones = recomendaciones.sort_values('total_compras', ascending=False).head(5)
        metodo = "populares globalmente"
else:
    # Sin clusters: productos populares globales
    recomendaciones = productos_no_comprados.merge(popularidad, on='id_producto', how='left')
    recomendaciones = recomendaciones.sort_values('total_compras', ascending=False).head(5)
    metodo = "populares globalmente"

if not recomendaciones.empty:
    st.caption(f"📌 Recomendaciones {metodo}")
    cols = st.columns(5)
    
    for idx, (_, row) in enumerate(recomendaciones.iterrows()):
        with cols[idx]:
            st.markdown(f"""
            <div style="border:1px solid #ddd; border-radius:10px; padding:15px; text-align:center; background-color:#f9f9f9;">
                <h4 style="margin:0; color:#2c3e50;">{row['nombre']}</h4>
                <p style="margin:5px 0; color:#7f8c8d;">{row['categoria']}</p>
                <p style="margin:5px 0; font-size:18px; font-weight:bold; color:#27ae60;">${row['precio']:.2f}</p>
                <p style="margin:5px 0; font-size:14px; color:#3498db;">⭐ {row.get('frecuencia', row.get('total_compras', 0))} compras</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("🎉 Este cliente ya compró todos los productos disponibles.")

st.markdown("---")

# ============================================
# FILA 3: GRÁFICOS
# ============================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Top 10 Productos Más Populares")
    fig, ax = plt.subplots(figsize=(8, 6))
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
# FILA 4: DISTRIBUCIÓN DE CLUSTERS
# ============================================
if tiene_clusters:
    st.subheader("📊 Distribución de Clientes por Cluster")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig, ax = plt.subplots(figsize=(8, 6))
        cluster_counts = clientes_cluster['cluster'].value_counts().sort_index()
        ax.bar(cluster_counts.index, cluster_counts.values, color='#9b59b6')
        ax.set_xlabel("Cluster")
        ax.set_ylabel("Número de Clientes")
        st.pyplot(fig)
        plt.close()
    
    with col2:
        st.write("**Características de cada cluster:**")
        for i in range(len(cluster_counts)):
            cluster_data = clientes_cluster[clientes_cluster['cluster'] == i]
            ids = cluster_data['id_cliente'].tolist()
            gasto_prom = total_gastado[total_gastado['id_cliente'].isin(ids)]['total_gastado'].mean()
            st.write(f"🔹 **Cluster {i}:** {len(cluster_data)} clientes, ${gasto_prom:,.2f} promedio")

# ============================================
# FILA 5: HISTORIAL DE COMPRAS
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