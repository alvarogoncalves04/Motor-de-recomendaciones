# 🎯 Motor de Recomendación de Productos

## 📌 Descripción
Sistema de recomendación de productos basado en el historial de compras de los clientes. Utiliza técnicas de filtrado colaborativo y análisis de popularidad para sugerir productos personalizados.

## 🛠️ Tecnologías
- Python 3.x
- Pandas (manipulación de datos)
- SQLite (OLTP + OLAP)
- Streamlit (dashboard)
- Matplotlib (visualizaciones)
- Scikit-learn (Machine Learning)

## 📁 Estructura del Proyecto
motor-de-recomendaciones/

├── data/

│ ├── oltp.db # Base de datos transaccional

│ └── olap.db # Data Warehouse

├── src/

│ ├── 01_generar_datos.py # Genera 500 clientes, 50 productos, 10,000 compras

│ ├── 02_etl_pipeline.py # Pipeline ETL

│ ├── 03_consultas_sql.py # Consultas analíticas

│ └── 04_dashboard.py # Dashboard Streamlit

├── requirements.txt

└── README.md

## 📊 Funcionalidades

### Dashboard
- **Selección de cliente**: Elige un cliente para ver sus recomendaciones
- **Recomendaciones personalizadas**: Sugiere 5 productos populares no comprados
- **Historial de compras**: Muestra el historial del cliente
- **Top productos**: Visualización de los productos más populares
- **Distribución por ciudad**: Gráfico de clientes por ubicación

### Análisis
- Top 10 productos más comprados
- Clientes que más gastan
- Categorías más populares
- Productos que se compran juntos
- Distribución geográfica de clientes

👤 Autor
Álvaro Goncalves - GitHub
-Link 
https://enginerecommendations.streamlit.app/
