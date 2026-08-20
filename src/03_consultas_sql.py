# 03_consultas_sql.py
# CONSULTAS ANALÍTICAS PARA EL SISTEMA DE RECOMENDACIÓN

import sqlite3
import pandas as pd

def conectar():
    return sqlite3.connect('data/olap.db')

def ejecutar_consulta(query, descripcion):
    print(f"\n📊 {descripcion}")
    print("-"*60)
    conn = conectar()
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(df)
    print(f"\nTotal: {len(df)} registros")
    return df

def consultas_analiticas():
    print("="*60)
    print("🔍 CONSULTAS ANALÍTICAS - SISTEMA DE RECOMENDACIÓN")
    print("="*60)
    
    # 1. Top 10 productos más comprados
    query1 = """
    SELECT 
        p.nombre,
        p.categoria,
        p.precio,
        pop.total_compras
    FROM popularidad pop
    JOIN productos p ON pop.id_producto = p.id_producto
    ORDER BY pop.total_compras DESC
    LIMIT 10
    """
    ejecutar_consulta(query1, "1. TOP 10 PRODUCTOS MÁS COMPRADOS")
    
    # 2. Clientes que más gastan
    query2 = """
    SELECT 
        c.nombre,
        c.ciudad,
        tg.total_gastado,
        nc.num_compras,
        ROUND(tg.total_gastado / nc.num_compras, 2) as ticket_promedio
    FROM total_gastado tg
    JOIN clientes c ON tg.id_cliente = c.id_cliente
    JOIN num_compras nc ON tg.id_cliente = nc.id_cliente
    ORDER BY tg.total_gastado DESC
    LIMIT 10
    """
    ejecutar_consulta(query2, "2. TOP 10 CLIENTES QUE MÁS GASTAN")
    
    # 3. Categorías más populares
    query3 = """
    SELECT 
        categoria,
        COUNT(*) as num_productos,
        SUM(compras) as total_compras,
        AVG(precio) as precio_promedio
    FROM (
        SELECT 
            p.categoria,
            p.precio,
            COUNT(c.id_compra) as compras
        FROM productos p
        LEFT JOIN compras_enriquecidas c ON p.id_producto = c.id_producto
        GROUP BY p.id_producto
    )
    GROUP BY categoria
    ORDER BY total_compras DESC
    """
    ejecutar_consulta(query3, "3. CATEGORÍAS MÁS POPULARES")
    
    # 4. Productos que más compran juntos (frecuencia)
    query4 = """
    SELECT 
        p1.nombre as producto_1,
        p2.nombre as producto_2,
        COUNT(*) as veces_juntos
    FROM compras_enriquecidas c1
    JOIN compras_enriquecidas c2 
        ON c1.id_cliente = c2.id_cliente 
        AND c1.id_producto < c2.id_producto
    JOIN productos p1 ON c1.id_producto = p1.id_producto
    JOIN productos p2 ON c2.id_producto = p2.id_producto
    GROUP BY c1.id_producto, c2.id_producto
    ORDER BY veces_juntos DESC
    LIMIT 10
    """
    ejecutar_consulta(query4, "4. PRODUCTOS QUE SE COMPRAN JUNTOS")
    
    # 5. Distribución de clientes por ciudad
    query5 = """
    SELECT 
        ciudad,
        COUNT(*) as num_clientes,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM clientes), 2) as porcentaje
    FROM clientes
    GROUP BY ciudad
    ORDER BY num_clientes DESC
    """
    ejecutar_consulta(query5, "5. DISTRIBUCIÓN DE CLIENTES POR CIUDAD")
    
    # 6. Popularidad por precio
    query6 = """
    SELECT 
        CASE 
            WHEN p.precio < 50 THEN 'Bajo (<$50)'
            WHEN p.precio < 150 THEN 'Medio ($50-$150)'
            ELSE 'Alto (>$150)'
        END as rango_precio,
        COUNT(*) as num_productos,
        SUM(pop.total_compras) as compras_totales
    FROM popularidad pop
    JOIN productos p ON pop.id_producto = p.id_producto
    GROUP BY rango_precio
    ORDER BY rango_precio
    """
    ejecutar_consulta(query6, "6. POPULARIDAD POR RANGO DE PRECIO")

if __name__ == "__main__":
    consultas_analiticas()