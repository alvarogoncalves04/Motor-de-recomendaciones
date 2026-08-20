# 02_etl_pipeline.py
# PIPELINE ETL PARA SISTEMA DE RECOMENDACIÓN (VERSIÓN CORREGIDA)

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os

# ============================================
# 1. EXTRACCIÓN (E)
# ============================================
def extraer_de_oltp():
    conn = sqlite3.connect('data/oltp.db')
    
    clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    productos = pd.read_sql_query("SELECT * FROM productos", conn)
    compras = pd.read_sql_query("SELECT * FROM compras", conn)
    
    conn.close()
    
    print(f"📤 Datos extraídos:")
    print(f"   - Clientes: {len(clientes)}")
    print(f"   - Productos: {len(productos)}")
    print(f"   - Compras: {len(compras)}")
    
    return clientes, productos, compras

# ============================================
# 2. TRANSFORMACIÓN (T)
# ============================================
def transformar_datos(clientes, productos, compras):
    print("🔄 Transformando datos...")
    
    # Renombrar columna 'id' a 'id_producto' en productos
    productos = productos.rename(columns={'id': 'id_producto'})
    
    # 1. Crear matriz de usuarios-productos
    matriz_usuario_producto = compras.pivot_table(
        index='id_cliente',
        columns='id_producto',
        values='cantidad',
        fill_value=0
    )
    
    # 2. Calcular total gastado por cliente
    compras['total'] = compras['cantidad'] * compras['precio_unitario']
    total_gastado = compras.groupby('id_cliente')['total'].sum().reset_index()
    total_gastado.columns = ['id_cliente', 'total_gastado']
    
    # 3. Calcular número de compras por cliente
    num_compras = compras.groupby('id_cliente').size().reset_index(name='num_compras')
    
    # 4. Productos más comprados por cliente (top 3)
    top_productos = compras.groupby(['id_cliente', 'id_producto']).size().reset_index(name='veces_comprado')
    top_productos = top_productos.sort_values(['id_cliente', 'veces_comprado'], ascending=[True, False])
    top_productos = top_productos.groupby('id_cliente').head(3)
    top_productos = top_productos.rename(columns={'id_producto': 'top_1', 'veces_comprado': 'veces_1'})
    
    # 5. Compras enriquecidas con información de productos
    compras_enriquecidas = compras.merge(productos, on='id_producto', how='left')
    
    # 6. Popularidad de productos (con nombre incluido)
    popularidad = compras.groupby('id_producto').size().reset_index(name='total_compras')
    popularidad = popularidad.merge(productos, on='id_producto', how='left')  # <-- Ahora incluye nombre
    popularidad = popularidad.sort_values('total_compras', ascending=False)
    
    print(f"✅ Transformación completada")
    print(f"   - Matriz usuario-producto: {matriz_usuario_producto.shape}")
    print(f"   - Producto más popular: {popularidad.iloc[0]['nombre']} ({popularidad.iloc[0]['total_compras']} compras)")
    
    return {
        'matriz_usuario_producto': matriz_usuario_producto,
        'total_gastado': total_gastado,
        'num_compras': num_compras,
        'top_productos': top_productos,
        'compras_enriquecidas': compras_enriquecidas,
        'popularidad': popularidad,
        'clientes': clientes,
        'productos': productos
    }
# ============================================
# 3. CARGA (L)
# ============================================
def cargar_en_olap(datos):
    print("📥 Cargando en Data Warehouse (OLAP)...")
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect('data/olap.db')
    
    # Guardar cada tabla transformada
    datos['matriz_usuario_producto'].to_sql('matriz_usuarios_productos', conn, if_exists='replace')
    datos['total_gastado'].to_sql('total_gastado', conn, if_exists='replace')
    datos['num_compras'].to_sql('num_compras', conn, if_exists='replace')
    datos['top_productos'].to_sql('top_productos', conn, if_exists='replace')
    datos['compras_enriquecidas'].to_sql('compras_enriquecidas', conn, if_exists='replace')
    datos['popularidad'].to_sql('popularidad', conn, if_exists='replace')
    datos['clientes'].to_sql('clientes', conn, if_exists='replace')
    datos['productos'].to_sql('productos', conn, if_exists='replace')
    
    conn.close()
    print(f"✅ Datos cargados en OLAP")

# ============================================
# EJECUTAR
# ============================================
def ejecutar_etl():
    print("="*60)
    print("🚀 PIPELINE ETL - SISTEMA DE RECOMENDACIÓN")
    print("="*60)
    
    clientes, productos, compras = extraer_de_oltp()
    datos = transformar_datos(clientes, productos, compras)
    cargar_en_olap(datos)
    
    print("\n✅ PIPELINE ETL COMPLETADO")
    print("="*60)
    
    return datos

if __name__ == "__main__":
    ejecutar_etl()