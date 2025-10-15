# profesores/chart_factory.py
"""
Implementación del patrón Factory para la generación de gráficas.
Centraliza la lógica de creación de diferentes tipos de gráficas estadísticas.
"""

from abc import ABC, abstractmethod
import matplotlib
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter, defaultdict
import numpy as np

# Configurar matplotlib para trabajar sin entorno gráfico
matplotlib.use('Agg')


class ChartGenerator(ABC):
    # Clase base abstracta para generadores de gráficas.
    # Define la interfaz común para todos los tipos de gráficas.

    
    @abstractmethod
    def generate(self, data):
        # Genera una gráfica específica basada en los datos proporcionados.
        
        pass
    
    def to_base64(self, plt_figure):
        # Método común para convertir una figura de matplotlib a base64.
        buffer = io.BytesIO()
        plt_figure.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        return base64.b64encode(image_png).decode('utf-8')


class BarChartGenerator(ChartGenerator):
    # Muestra la frecuencia de cada calificación (1-5 estrellas).
    
    
    def generate(self, ratings):
        if not ratings:
            return None
            
        counts = dict(Counter(ratings))
        labels = list(range(1, 6))
        values = [counts.get(label, 0) for label in labels]
        
        plt.figure(figsize=(12, 6))
        plt.bar(labels, values, color='skyblue', edgecolor='black', width=0.8)
        plt.xlabel('Calificación', fontsize=14, fontweight='bold')
        plt.ylabel('Frecuencia', fontsize=14, fontweight='bold')
        plt.xticks(labels, fontsize=12)
        
        max_y = max(counts.values()) if counts else 1
        plt.yticks(range(0, int(max_y) + 2), fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        return self.to_base64(plt)


class LineChartGenerator(ChartGenerator):

    # Muestra cómo varía la calificación promedio a lo largo de los semestres.

    
    def generate(self, comentarios):
        if not comentarios or not comentarios.exists():
            return None
            
        # Agrupar calificaciones por semestre
        calificaciones_por_semestre = defaultdict(list)
        for comentario in comentarios:
            calificaciones_por_semestre[comentario.fecha].append(comentario.rating)
        
        # Calcular el promedio por semestre
        semestres_ordenados = sorted(calificaciones_por_semestre.keys())
        calificaciones_promedio = [
            sum(calificaciones_por_semestre[semestre]) / len(calificaciones_por_semestre[semestre])
            for semestre in semestres_ordenados
        ]
        
        plt.figure(figsize=(10, 5))
        plt.plot(semestres_ordenados, calificaciones_promedio, marker='o', linestyle='-', color='blue')
        plt.xlabel('Semestre', fontsize=12)
        plt.ylabel('Rating Promedio', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        
        return self.to_base64(plt)


class ScatterChartGenerator(ChartGenerator):
    # El tamaño de cada punto representa el número de reseñas.
    
    def generate(self, profesores_data):
        if not profesores_data or not profesores_data.exists():
            return None
            
        nombres = [prof.nombre for prof in profesores_data]
        calificaciones = [prof.calificacion_promedio if prof.calificacion_promedio else 0 for prof in profesores_data]
        num_reviews = [prof.num_reviews for prof in profesores_data]
        
        if not nombres:
            return None
        
        plt.figure(figsize=(10, 6))
        plt.scatter(nombres, calificaciones, s=[n * 10 for n in num_reviews], alpha=0.5)
        plt.xlabel("Profesor", fontsize=12)
        plt.ylabel("Calificación promedio", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        return self.to_base64(plt)


class FrequencyDistributionChartGenerator(ChartGenerator):
    # Generador de gráficas de distribución de frecuencias para materias.
    
    def generate(self, ratings):
        if not ratings:
            return None
            
        rating_counts = Counter(ratings)
        ratings_list = [rating_counts.get(rating, 0) for rating in range(1, 6)]
        
        plt.figure(figsize=(10, 6))
        plt.bar(range(1, 6), ratings_list, color='skyblue', edgecolor='black')
        plt.xlabel("Rating", fontsize=12)
        plt.ylabel("Frecuencia", fontsize=12)
        plt.xticks(range(1, 6))
        
        max_y = max(ratings_list) if ratings_list else 1
        plt.yticks(np.arange(0, max_y + 2, 1))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        return self.to_base64(plt)


class SemesterLineChartGenerator(ChartGenerator):
    # Generador de gráficas de líneas para evolución por semestre de materias.
    
    def generate(self, data):
        comentarios = data.get('comentarios')
        titulo = data.get('titulo', 'Promedio de Rating por Semestre')
        
        if not comentarios or not comentarios.exists():
            return None
            
        # Agrupar calificaciones por semestre
        calificaciones_por_semestre = defaultdict(list)
        for comentario in comentarios:
            calificaciones_por_semestre[comentario.fecha].append(comentario.rating)
        
        # Calcular el promedio por semestre
        semestres_ordenados = sorted(calificaciones_por_semestre.keys())
        calificaciones_promedio = [
            sum(calificaciones_por_semestre[semestre]) / len(calificaciones_por_semestre[semestre])
            for semestre in semestres_ordenados
        ]
        
        plt.figure(figsize=(10, 5))
        plt.plot(semestres_ordenados, calificaciones_promedio, marker='o', linestyle='-', color='blue')
        plt.xlabel('Semestre', fontsize=12)
        plt.ylabel('Rating Promedio', fontsize=12)
        plt.title(titulo, fontsize=14)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        
        return self.to_base64(plt)


class ChartFactory:
    # Implementa el patrón Factory Method.
    
    # Registro de generadores disponibles
    _generators = {
        'bar': BarChartGenerator,
        'line': LineChartGenerator,
        'scatter': ScatterChartGenerator,
        'frequency': FrequencyDistributionChartGenerator,
        'semester_line': SemesterLineChartGenerator,
    }
    
    @classmethod
    def create_chart(cls, chart_type, data):
        # Crea y genera una gráfica del tipo especificado.
        
        generator_class = cls._generators.get(chart_type)
        if not generator_class:
            raise ValueError(f"Tipo de gráfica no soportado: {chart_type}. "
                           f"Tipos disponibles: {list(cls._generators.keys())}")
        
        try:
            generator = generator_class()
            return generator.generate(data)
        except Exception as e:
            print(f"Error generando gráfica {chart_type}: {e}")
            return None
    
    @classmethod
    def register_chart_type(cls, name, generator_class):
        # Permite registrar nuevos tipos de gráficas dinámicamente.
        if not issubclass(generator_class, ChartGenerator):
            raise TypeError("El generador debe heredar de ChartGenerator")
        cls._generators[name] = generator_class
    
    @classmethod
    def get_available_types(cls):
        # Retorna la lista de tipos de gráficas disponibles.
        return list(cls._generators.keys())
