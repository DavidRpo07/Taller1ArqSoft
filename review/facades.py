# review/facades.py
"""
Implementación del patrón Facade para el sistema de comentarios.
Simplifica las operaciones complejas relacionadas con la creación, edición y 
eliminación de comentarios, coordinando múltiples subsistemas.
"""

from django.contrib import messages
from .models import Comentario
from account.models import UserProfile
from django.db import transaction
from collections import Counter, defaultdict


class ComentarioFacade:
    """
    Fachada que simplifica las operaciones complejas del sistema de comentarios.
    Coordina: validación de permisos (State), aprobación IA, persistencia y estadísticas.
    
    Este patrón oculta la complejidad de múltiples subsistemas detrás de una
    interfaz simple y unificada.
    """
    
    def __init__(self, aprobador_strategy=None):
        """
        Inicializa la fachada con una estrategia de aprobación.
        
        Args:
            aprobador_strategy: Instancia de ComentarioAprobador (IA o Manual).
                               Si no se proporciona, usa ComentarioAprobadorIA por defecto.
        """
        # Import here to avoid circular dependency
        from review.views import ComentarioAprobadorIA
        self.aprobador = aprobador_strategy or ComentarioAprobadorIA()
    
    def puede_usuario_comentar(self, user):
        """
        Verifica si el usuario tiene permisos para comentar.
        Utiliza el patrón State existente en UserProfile.
        
        Args:
            user: Usuario de Django
            
        Returns:
            tuple: (puede_comentar: bool, mensaje: str)
        """
        try:
            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            
            if not user_profile.puede_acceder():
                mensaje = user_profile.mensaje_estado() + ' No puedes agregar comentarios.'
                return False, mensaje
            
            return True, "Puede comentar"
        except Exception as e:
            return False, f"Error al verificar permisos: {str(e)}"
    
    @transaction.atomic
    def crear_comentario(self, form_data, profesor, usuario, es_anonimo=False):
        """
        Crea y procesa un comentario completo (validación + aprobación + guardado).
        Usa transacciones atómicas para garantizar consistencia.
        
        Args:
            form_data (dict): Datos del formulario validado con keys:
                             'contenido', 'rating', 'fecha', 'materia' (opcional)
            profesor: Instancia del profesor
            usuario: Usuario que comenta
            es_anonimo (bool): Si el comentario es anónimo
            
        Returns:
            tuple: (exito: bool, comentario: Comentario|None, mensaje: str)
        """
        # 1. Verificar permisos usando patrón State
        puede_comentar, mensaje_permiso = self.puede_usuario_comentar(usuario)
        if not puede_comentar:
            return False, None, mensaje_permiso
        
        try:
            # 2. Crear instancia sin guardar
            comentario = Comentario(
                profesor=profesor,
                usuario=usuario,
                contenido=form_data['contenido'],
                rating=form_data['rating'],
                fecha=form_data['fecha'],
                materia=form_data.get('materia'),
                anonimo=es_anonimo
            )
            
            # 3. Aprobar con IA (Strategy pattern)
            aprobado = self.aprobador.aprobar(comentario.contenido)
            
            if aprobado:
                comentario.aprobado_por_ia = True
                comentario.save()
                # Los signals de Django actualizan automáticamente las estadísticas
                return True, comentario, 'Tu comentario ha sido aprobado y publicado.'
            else:
                return False, None, 'Tu comentario ha sido rechazado por no cumplir con las normas.'
                
        except Exception as e:
            return False, None, f'Error al crear comentario: {str(e)}'
    
    @transaction.atomic
    def editar_comentario(self, comentario_id, usuario, nuevos_datos, re_aprobar=True):
        """
        Edita un comentario existente con validaciones.
        
        Args:
            comentario_id (int): ID del comentario a editar
            usuario: Usuario que edita
            nuevos_datos (dict): Nuevos datos para el comentario
            re_aprobar (bool): Si debe re-aprobar con IA cuando cambie el contenido
            
        Returns:
            tuple: (exito: bool, comentario: Comentario|None, mensaje: str)
        """
        try:
            comentario = Comentario.objects.get(id=comentario_id)
        except Comentario.DoesNotExist:
            return False, None, 'Comentario no encontrado.'
        
        # Verificar permisos de edición
        if comentario.usuario != usuario and not usuario.is_staff:
            return False, None, 'No tienes permisos para editar este comentario.'
        
        try:
            # Actualizar campos si están presentes en nuevos_datos
            contenido_cambio = False
            if 'contenido' in nuevos_datos:
                comentario.contenido = nuevos_datos['contenido']
                contenido_cambio = True
            
            if 'rating' in nuevos_datos:
                comentario.rating = nuevos_datos['rating']
            
            if 'fecha' in nuevos_datos:
                comentario.fecha = nuevos_datos['fecha']
            
            if 'materia' in nuevos_datos:
                comentario.materia = nuevos_datos['materia']
            
            # Re-aprobar si cambió el contenido
            if contenido_cambio and re_aprobar:
                aprobado = self.aprobador.aprobar(comentario.contenido)
                if not aprobado:
                    return False, None, 'El contenido editado no cumple las normas.'
                comentario.aprobado_por_ia = True
            
            comentario.save()
            # Los signals actualizan automáticamente las estadísticas
            return True, comentario, 'Comentario actualizado exitosamente.'
            
        except Exception as e:
            return False, None, f'Error al editar comentario: {str(e)}'
    
    @transaction.atomic
    def eliminar_comentario(self, comentario_id, usuario):
        """
        Elimina un comentario con validaciones.
        
        Args:
            comentario_id (int): ID del comentario a eliminar
            usuario: Usuario que elimina
            
        Returns:
            tuple: (exito: bool, profesor_id: int|None, mensaje: str)
        """
        try:
            comentario = Comentario.objects.get(id=comentario_id)
        except Comentario.DoesNotExist:
            return False, None, 'Comentario no encontrado.'
        
        # Verificar permisos
        if comentario.usuario != usuario and not usuario.is_staff:
            return False, None, 'No tienes permisos para eliminar este comentario.'
        
        try:
            profesor_id = comentario.profesor.id
            comentario.delete()
            # Los signals actualizan automáticamente las estadísticas del profesor
            return True, profesor_id, 'Comentario eliminado exitosamente.'
        except Exception as e:
            return False, None, f'Error al eliminar comentario: {str(e)}'
    
    def obtener_estadisticas_profesor(self, profesor):
        """
        Obtiene estadísticas consolidadas de un profesor.
        
        Args:
            profesor: Instancia del profesor
            
        Returns:
            dict: Estadísticas del profesor con keys:
                  - total_comentarios
                  - calificacion_promedio
                  - comentarios_por_semestre
                  - distribucion_ratings
        """
        try:
            comentarios = Comentario.objects.filter(profesor=profesor, aprobado_por_ia=True)
            
            return {
                'total_comentarios': comentarios.count(),
                'calificacion_promedio': profesor.calificacion_media,
                'comentarios_por_semestre': self._agrupar_por_semestre(comentarios),
                'distribucion_ratings': self._contar_ratings(comentarios),
            }
        except Exception as e:
            return {
                'total_comentarios': 0,
                'calificacion_promedio': 0.0,
                'comentarios_por_semestre': {},
                'distribucion_ratings': {},
                'error': str(e)
            }
    
    def obtener_comentarios_usuario(self, usuario, incluir_no_aprobados=False):
        """
        Obtiene todos los comentarios de un usuario.
        
        Args:
            usuario: Usuario de Django
            incluir_no_aprobados (bool): Si incluir comentarios rechazados
            
        Returns:
            QuerySet: Comentarios del usuario
        """
        comentarios = Comentario.objects.filter(usuario=usuario)
        
        if not incluir_no_aprobados:
            comentarios = comentarios.filter(aprobado_por_ia=True)
        
        return comentarios.order_by('-fecha')
    
    def validar_datos_comentario(self, contenido, rating):
        """
        Valida los datos básicos de un comentario.
        
        Args:
            contenido (str): Contenido del comentario
            rating (int): Calificación (1-5)
            
        Returns:
            tuple: (valido: bool, mensaje: str)
        """
        if not contenido or len(contenido.strip()) < 10:
            return False, 'El comentario debe tener al menos 10 caracteres.'
        
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return False, 'La calificación debe estar entre 1 y 5.'
        
        if len(contenido) > 1000:
            return False, 'El comentario no puede exceder 1000 caracteres.'
        
        return True, 'Datos válidos'
    
    # Métodos privados auxiliares
    
    def _agrupar_por_semestre(self, comentarios):
        """
        Agrupa comentarios por semestre.
        
        Args:
            comentarios (QuerySet): Comentarios a agrupar
            
        Returns:
            dict: Semestre -> [ratings]
        """
        agrupados = defaultdict(list)
        for c in comentarios:
            agrupados[c.fecha].append(c.rating)
        return dict(agrupados)
    
    def _contar_ratings(self, comentarios):
        """
        Cuenta la distribución de ratings.
        
        Args:
            comentarios (QuerySet): Comentarios a contar
            
        Returns:
            dict: Rating -> Frecuencia
        """
        ratings = [c.rating for c in comentarios]
        return dict(Counter(ratings))
    
    def cambiar_aprobador(self, nuevo_aprobador):
        """
        Cambia la estrategia de aprobación en tiempo de ejecución.
        
        Args:
            nuevo_aprobador: Nueva instancia de ComentarioAprobador
        """
        self.aprobador = nuevo_aprobador
