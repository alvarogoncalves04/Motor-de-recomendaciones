    # 01_generar_datos.py
# Genera datos para un sistema de recomendación de productos

import sqlite3
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# ============================================
# CONFIGURACIÓN
# ============================================
fake = Faker('es_ES')

NUM_CLIENTES = 500
NUM_PRODUCTOS = 50
NUM_COMPRAS = 10000

# ============================================
# PRODUCTOS DE EJEMPLO
# ============================================
PRODUCTOS = [
    {'id': i+1, 'nombre': fake.word().capitalize(), 'categoria': random.choice(['Electrónicos', 'Hogar', 'Deportes', 'Moda', 'Libros', 'Juguetes']), 'precio': round(random.uniform(10, 500), 2)}
    for i in range(NUM_PRODUCTOS)
]

# ============================================
# GENERAR CLIENTES
# ============================================
def generar_clientes(n):
    clientes = []
    for i in range(n):
        clientes.append({
            'id_cliente': i + 1,
            'nombre': fake.name(),
            'email': fake.email(),
            'ciudad': random.choice(['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Bucaramanga']),
            'fecha_registro': fake.date_between(start_date='-365d', end_date='today').strftime('%Y-%m-%d')
        })
    return pd.DataFrame(clientes)

# ============================================
# GENERAR COMPRAS
# ============================================
def generar_compras(n, clientes, productos):
    compras = []
    for i in range(n):
        cliente = random.choice(clientes)
        producto = random.choice(productos)
        
        fecha = fake.date_between(start_date='-180d', end_date='today')
        cantidad = random.randint(1, 5)
        
        compras.append({
            'id_compra': i + 1,
            'id_cliente': cliente['id_cliente'],
            'id_producto': producto['id'],  # <-- Asegurar que esta columna existe
            'fecha': fecha.strftime('%Y-%m-%d'),
            'cantidad': cantidad,
            'precio_unitario': producto['precio']
        })
    return pd.DataFrame(compras)

# ============================================
# GUARDAR EN OLTP
# ============================================
def guardar_en_oltp(clientes_df, productos_df, compras_df):
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect('data/oltp.db')
    
    # Tabla clientes
    clientes_df.to_sql('clientes', conn, if_exists='replace', index=False)
    
    # Tabla productos
    productos_df.to_sql('productos', conn, if_exists='replace', index=False)
    
    # Tabla compras
    compras_df.to_sql('compras', conn, if_exists='replace', index=False)
    
    conn.close()
    print("✅ Datos guardados en OLTP (data/oltp.db)")

# ============================================
# EJECUCIÓN
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("🚀 GENERANDO DATOS PARA SISTEMA DE RECOMENDACIÓN")
    print("="*60)
    
    print(f"📊 Generando {NUM_CLIENTES} clientes...")
    clientes_df = generar_clientes(NUM_CLIENTES)
    
    print(f"📊 Generando {NUM_PRODUCTOS} productos...")
    productos_df = pd.DataFrame(PRODUCTOS)
    
    print(f"📊 Generando {NUM_COMPRAS} compras...")
    compras_df = generar_compras(NUM_COMPRAS, clientes_df.to_dict('records'), PRODUCTOS)
    
    print("\n📋 Ejemplo de datos:")
    print("\nClientes:", clientes_df.head(2))
    print("\nProductos:", productos_df.head(2))
    print("\nCompras:", compras_df.head(2))
    
    guardar_en_oltp(clientes_df, productos_df, compras_df)
    
    print("\n🔍 Resumen:")
    print(f"   - Clientes: {len(clientes_df)}")
    print(f"   - Productos: {len(productos_df)}")
    print(f"   - Compras: {len(compras_df)}")
    print("="*60)