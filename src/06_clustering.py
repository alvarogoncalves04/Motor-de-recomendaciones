# 06_clustering.py
# CLUSTERING DE CLIENTES CON K-MEANS

import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os

# ============================================
# 1. CARGAR DATOS
# ============================================
def cargar_datos():
    conn = sqlite3.connect('data/olap.db')
    
    # Cargar matriz usuario-producto
    matriz = pd.read_sql_query("SELECT * FROM matriz_usuarios_productos", conn)
    
    # Cargar datos de clientes
    clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    
    # Cargar total gastado
    total_gastado = pd.read_sql_query("SELECT * FROM total_gastado", conn)
    
    conn.close()
    
    return matriz, clientes, total_gastado

# ============================================
# 2. PREPARAR DATOS PARA CLUSTERING
# ============================================
def preparar_datos(matriz, clientes, total_gastado):
    print("🔄 Preparando datos para clustering...")
    
    # 1. Usar la matriz como features (comportamiento de compra)
    X = matriz.copy()
    
    # 2. Eliminar la columna 'index' si existe
    if 'index' in X.columns:
        X = X.drop(columns=['index'])
    
    # 3. Agregar columna de total gastado
    X = X.merge(total_gastado, left_on='id_cliente', right_on='id_cliente', how='left')
    
    # 4. Rellenar valores nulos
    X = X.fillna(0)
    
    # 5. Guardar IDs de clientes para referencia
    clientes_ids = X['id_cliente'].values
    
    # 6. Eliminar columna de ID para el clustering
    X_scaled = X.drop(columns=['id_cliente', 'total_gastado'])
    
    # 7. Escalar los datos
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_scaled)
    
    print(f"✅ Datos preparados: {X_scaled.shape[0]} clientes, {X_scaled.shape[1]} features")
    
    return X_scaled, clientes_ids, scaler

# ============================================
# 3. ENCONTRAR NÚMERO ÓPTIMO DE CLUSTERS (MÉTODO DEL CODO)
# ============================================
def encontrar_optimo_clusters(X, max_clusters=10):
    print("🔍 Encontrando número óptimo de clusters...")
    
    inercia = []
    for k in range(1, max_clusters + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        inercia.append(kmeans.inertia_)
    
    # Graficar el método del codo
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, max_clusters + 1), inercia, marker='o', color='#3498db')
    plt.xlabel('Número de Clusters')
    plt.ylabel('Inercia')
    plt.title('Método del Codo para K-Means')
    plt.grid(True, alpha=0.3)
    
    os.makedirs('outputs', exist_ok=True)
    plt.savefig('outputs/metodo_codo.png', dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    print("✅ Gráfico guardado: outputs/metodo_codo.png")
    
    # Recomendar número de clusters (donde el codo se dobla)
    # Para este caso, usaremos 4 clusters
    return 4

# ============================================
# 4. APLICAR K-MEANS
# ============================================
def aplicar_clustering(X, n_clusters=4):
    print(f"🎯 Aplicando K-Means con {n_clusters} clusters...")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X)
    
    # Guardar el modelo
    joblib.dump(kmeans, 'modelo_kmeans.pkl')
    print("✅ Modelo guardado: modelo_kmeans.pkl")
    
    return clusters, kmeans

# ============================================
# 5. ANALIZAR CLUSTERS
# ============================================
def analizar_clusters(matriz, clientes, total_gastado, clusters):
    print("\n📊 ANÁLISIS DE CLUSTERS")
    print("="*60)
    
    # Agregar clusters a los datos
    clientes_con_cluster = clientes.copy()
    clientes_con_cluster['cluster'] = clusters
    
    # Analizar cada cluster
    for i in range(max(clusters) + 1):
        print(f"\n🔹 CLUSTER {i}")
        print("-"*40)
        
        cluster_data = clientes_con_cluster[clientes_con_cluster['cluster'] == i]
        
        print(f"   Clientes: {len(cluster_data)}")
        print(f"   Ciudades principales: {cluster_data['ciudad'].value_counts().head(3).to_dict()}")
        
        # Total gastado promedio
        gasto_promedio = total_gastado[total_gastado['id_cliente'].isin(cluster_data['id_cliente'])]['total_gastado'].mean()
        print(f"   Gasto promedio: ${gasto_promedio:,.2f}")
    
    return clientes_con_cluster

# ============================================
# 6. VISUALIZAR CLUSTERS (PCA)
# ============================================
def visualizar_clusters(X, clusters):
    print("\n📊 Visualizando clusters con PCA...")
    
    # Reducir a 2 dimensiones para visualización
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)
    
    # Crear DataFrame para graficar
    df_pca = pd.DataFrame({
        'PC1': X_pca[:, 0],
        'PC2': X_pca[:, 1],
        'Cluster': clusters
    })
    
    # Graficar
    plt.figure(figsize=(10, 8))
    
    colores = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    
    for i in range(max(clusters) + 1):
        cluster_data = df_pca[df_pca['Cluster'] == i]
        plt.scatter(
            cluster_data['PC1'],
            cluster_data['PC2'],
            label=f'Cluster {i}',
            color=colores[i % len(colores)],
            alpha=0.7,
            s=50
        )
    
    plt.xlabel('Componente Principal 1')
    plt.ylabel('Componente Principal 2')
    plt.title('Visualización de Clusters de Clientes (PCA)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    os.makedirs('outputs', exist_ok=True)
    plt.savefig('outputs/clusters_pca.png', dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    print("✅ Gráfico guardado: outputs/clusters_pca.png")

# ============================================
# 7. GUARDAR CLUSTERS EN OLAP
# ============================================
def guardar_clusters(clientes_con_cluster):
    print("\n💾 Guardando clusters en OLAP...")
    
    conn = sqlite3.connect('data/olap.db')
    clientes_con_cluster.to_sql('clientes_con_cluster', conn, if_exists='replace', index=False)
    conn.close()
    
    print("✅ Clusters guardados en OLAP")

# ============================================
# EJECUTAR
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("🎯 CLUSTERING DE CLIENTES CON K-MEANS")
    print("="*60)
    
    # 1. Cargar datos
    matriz, clientes, total_gastado = cargar_datos()
    print(f"📊 Datos cargados: {len(clientes)} clientes, {len(matriz.columns)-1} productos")
    
    # 2. Preparar datos
    X, clientes_ids, scaler = preparar_datos(matriz, clientes, total_gastado)
    
    # 3. Encontrar número óptimo de clusters
    n_clusters = encontrar_optimo_clusters(X)
    print(f"🎯 Número óptimo de clusters: {n_clusters}")
    
    # 4. Aplicar clustering
    clusters, kmeans = aplicar_clustering(X, n_clusters)
    
    # 5. Analizar clusters
    clientes_con_cluster = analizar_clusters(matriz, clientes, total_gastado, clusters)
    
    # 6. Visualizar clusters
    visualizar_clusters(X, clusters)
    
    # 7. Guardar resultados
    guardar_clusters(clientes_con_cluster)
    
    # 8. Guardar scaler
    joblib.dump(scaler, 'scaler_kmeans.pkl')
    print("✅ Scaler guardado: scaler_kmeans.pkl")
    
    print("\n✅ CLUSTERING COMPLETADO")
    print("="*60)