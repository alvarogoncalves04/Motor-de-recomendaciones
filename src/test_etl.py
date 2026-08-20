# test_etl.py
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/oltp.db')

# 1. Verificar columnas de compras
print("=== Columnas de compras ===")
compras = pd.read_sql_query("SELECT * FROM compras", conn)
print(compras.columns.tolist())
print(compras.head())

# 2. Verificar columnas de productos
print("\n=== Columnas de productos ===")
productos = pd.read_sql_query("SELECT * FROM productos", conn)
print(productos.columns.tolist())
print(productos.head())

# 3. Intentar la transformación
print("\n=== Creando matriz ===")
try:
    matriz = compras.pivot_table(
        index='id_cliente',
        columns='id_producto',
        values='cantidad',
        fill_value=0
    )
    print(f"✅ Matriz creada: {matriz.shape}")
except Exception as e:
    print(f"❌ Error: {e}")

conn.close()