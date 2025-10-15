"""
Implementación del patrón Strategy para el sistema de recomendación de profesores.
Aplica diferentes estrategias de ordenamiento según las preferencias del usuario.
"""

from abc import ABC, abstractmethod
from django.db.models import QuerySet


class RecommendationStrategy(ABC):
    # Define la interfaz común para todas las estrategias de ordenamiento.
    
    @abstractmethod
    def apply(self, queryset: QuerySet) -> QuerySet:
        # Aplica la estrategia de ordenamiento al queryset.
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        # Retorna nombre descriptivo de la estrategia
        pass


class BestRatedFirstStrategy(RecommendationStrategy):
    # Los profesores con mayor calificación_media aparecen primero.
    
    def apply(self, queryset: QuerySet) -> QuerySet:
        return queryset.order_by('-calificacion_media', '-numcomentarios')
    
    def get_name(self) -> str:
        return "Mejor calificados primero"


class MostReviewedFirstStrategy(RecommendationStrategy):
    # Los profesores con más reseñas aparecen primero.
    
    def apply(self, queryset: QuerySet) -> QuerySet:
        return queryset.order_by('-numcomentarios', '-calificacion_media')
    
    def get_name(self) -> str:
        return "Más comentados primero"


class BalancedRecommendationStrategy(RecommendationStrategy):

    # Considera tanto calificación como número de comentarios.
    # Filtra profesores con al menos 3 comentarios para evitar ratings engañosos.
    
    def apply(self, queryset: QuerySet) -> QuerySet:
        # Profesores con al menos 3 comentarios ordenados por rating
        profesores_con_suficientes_reviews = queryset.filter(
            numcomentarios__gte=3
        ).order_by('-calificacion_media', '-numcomentarios')
        
        # Profesores con menos comentarios al final
        profesores_nuevos = queryset.filter(
            numcomentarios__lt=3
        ).order_by('-calificacion_media', '-numcomentarios')
        
        # Combinar: primero los confiables, luego los nuevos
        return profesores_con_suficientes_reviews.union(
            profesores_nuevos, all=True
        )
    
    def get_name(self) -> str:
        return "Recomendación balanceada"


class AlphabeticalStrategy(RecommendationStrategy):
    def apply(self, queryset: QuerySet) -> QuerySet:
        return queryset.order_by('nombre')
    
    def get_name(self) -> str:
        return "Orden alfabético"


class RecommendationEngine:
    # Registro de estrategias disponibles
    _strategies = {
        'best_rated': BestRatedFirstStrategy,
        'most_reviewed': MostReviewedFirstStrategy,
        'balanced': BalancedRecommendationStrategy,
        'alphabetical': AlphabeticalStrategy,
    }
    
    def __init__(self, strategy_name: str = 'best_rated'):
        # Inicializa el motor con una estrategia.
        
        self.set_strategy(strategy_name)
    
    def set_strategy(self, strategy_name: str):
        # Cambia la estrategia de recomendación en tiempo de ejecución.

        strategy_class = self._strategies.get(strategy_name)
        if not strategy_class:
            raise ValueError(
                f"Estrategia '{strategy_name}' no existe. "
                f"Disponibles: {list(self._strategies.keys())}"
            )
        self._strategy = strategy_class()
    
    def recommend(self, queryset: QuerySet) -> QuerySet:
        # estrategia actual al queryset de profesores.
        
        return self._strategy.apply(queryset)
    
    def get_current_strategy_name(self) -> str:
        # Retorna el nombre de la estrategia actual
        return self._strategy.get_name()
    
    @classmethod
    def get_available_strategies(cls) -> dict:
        # Retorna las estrategias disponibles.
        
        return {
            key: cls._strategies[key]().get_name()
            for key in cls._strategies.keys()
        }
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class):
        # registrar nuevas estrategias dinámicamente.

        if not issubclass(strategy_class, RecommendationStrategy):
            raise TypeError("La estrategia debe heredar de RecommendationStrategy")
        cls._strategies[name] = strategy_class
