import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.utils import resample
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import numpy as np
import os

# Diccionario para guardar modelos entrenados en memoria (no se usa en este ejemplo, pero está preparado)
modelos_entrenados = {}

# Agrega ruido aleatorio (jitter) a las columnas de velocidad y distancia para mejorar la generalización
def agregar_jitter(df, std_vel=0.5, std_dist=3):
    df = df.copy()
    # Aplica ruido a la columna de velocidad
    df[df.columns[0]] = df[df.columns[0]].astype(float) + np.random.normal(0, std_vel, size=len(df))
    # Aplica ruido a la columna de distancia
    df[df.columns[1]] = df[df.columns[1]].astype(float) + np.random.normal(0, std_dist, size=len(df))
    return df

# Función principal para entrenar un modelo (árbol, knn o red neuronal)
def entrenar_modelo(ruta_csv, modelo='arbol'):
    # Si existe una versión "limpia" del archivo, usarla en lugar del original
    ruta_limpia = ruta_csv.replace('.csv', '_limpio.csv')
    if os.path.exists(ruta_limpia):
        ruta_csv = ruta_limpia

    # Cargar el dataset desde CSV
    datos = pd.read_csv(ruta_csv)

    # Filtrar por distancia < 200
    datos = datos[datos.iloc[:, 1] < 200]

    # Separar los datos por clase para balancear
    clase_0 = datos[datos.iloc[:, -1] == 0]
    clase_1 = datos[datos.iloc[:, -1] == 1]
    # Balancear si hay diferencia significativa entre clases
    if len(clase_0) > 0 and len(clase_1) > 0 and abs(len(clase_0) - len(clase_1)) > 10:
        clase_minoria = clase_0 if len(clase_0) < len(clase_1) else clase_1
        clase_mayoria = clase_0 if len(clase_0) >= len(clase_1) else clase_1
        clase_minoria_upsampled = resample(clase_minoria, replace=True, n_samples=len(clase_mayoria), random_state=42)
        datos = pd.concat([clase_mayoria, clase_minoria_upsampled])

    # Si el modelo es árbol o knn, aplicar jitter para evitar sobreajuste a valores exactos
    if modelo in ['arbol', 'knn']:
        datos = agregar_jitter(datos)

    # Separar características (X) y etiquetas (y)
    X = datos.iloc[:, :-1]
    y = datos.iloc[:, -1]
    # Dividir datos en entrenamiento y prueba (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if modelo == 'arbol':
        # Configurar y entrenar árbol de decisión
        clf = DecisionTreeClassifier(
            criterion='entropy',
            max_depth=5,
            min_samples_split=5,
            min_samples_leaf=3
        )
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"[ARBOL] Precisión: {acc:.2f}")
        return clf

    elif modelo == 'knn':
        # Configurar y entrenar KNN con pesos por distancia y 3 vecinos
        clf = KNeighborsClassifier(n_neighbors=3, weights='distance')
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"[KNN] Precisión: {acc:.2f}")
        return clf

    elif modelo == 'red':
        # Convertir los datos a NumPy para uso con Keras
        X_train_np, X_test_np = X_train.values, X_test.values
        y_train_np, y_test_np = y_train.values, y_test.values

        model = Sequential([
            # Crear red neuronal secuencial con 3 capas ocultas
            Dense(64, input_dim=X_train.shape[1], activation='relu'),
            Dense(32, activation='relu'),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        # Compilar el modelo con optimizador Adam y función de pérdida binaria
        model.compile(optimizer=Adam(learning_rate=0.001),
                      loss='binary_crossentropy',
                      metrics=['accuracy'])
        # Entrenar la red neuronal
        model.fit(X_train_np, y_train_np, epochs=100, batch_size=64, verbose=0)
        loss, acc = model.evaluate(X_test_np, y_test_np, verbose=0)
        print(f"[RED] Precisión: {acc:.2f}")
        # Envolver la red para que tenga método .predict compatible con los otros modelos
        class RedWrapper:
            def __init__(self, model):
                self.model = model

            def predict(self, X):
                X_np = X.values if isinstance(X, pd.DataFrame) else X
                pred = self.model.predict(X_np, verbose=0)
                return (pred > 0.5).astype(int).flatten()

        return RedWrapper(model)

    else:
        raise ValueError("Modelo no reconocido")
