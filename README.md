# Taller 1

## David Restrepo, Sebastián Acevedo y Juan Pablo Corena

## Solución Taller

# Actividad 2 — Revisión autocrítica

## Usabilidad

### Fortalezas
- Flujo de registro y login funcional con formularios claros.  
- Listados y detalles con información relevante (promedios, comentarios).  
- Mensajes básicos de éxito/error tras acciones (por ejemplo, al enviar formularios).  

### A mejorar
- **Búsqueda y filtrado**: añadir un botón “Limpiar” para los filtros y mostrar la cantidad de resultados obtenidos.  
- **Paginación**: activar en listados (24 ítems/página) con navegación accesible para manejar más profesores.

## Compatibilidad

### Fortalezas
- Proyecto configurado para Python 3.11+, una versión moderna, estable y compatible con la mayoría de las librerías actuales de Django, lo que garantiza seguridad y soporte prolongado.
- Permite ser usada en dispositivos moviles.
- Compatibilidad con múltiples navegadores modernos (Chrome, Firefox, Edge y Safari) al seguir estándares HTML5 y evitar librerías obsoletas o dependencias específicas de un navegador.


###  A mejorar
- **Versionado explícito**: fijar rangos estables para las versiones de las tecnologías ej: (`Django>=4.2,<5`).  


---

## Rendimiento

### Fortalezas
- Uso de agregaciones (`Avg`, `Count`) en consultas que reducen la necesidad de cálculos manuales.
- Separación de vistas y plantillas que permite aplicar cache.  

### A mejorar
- Usar `select_related` y `prefetch_related` para evitar consultas N+1, especialmente en las vistas de detalle con relaciones (profesor–comentarios).  
- Activar **paginación** en listados grandes para reducir la carga en memoria y el tiempo de renderizado.

---

## Seguridad

### Fortalezas
- CSRF habilitado por defecto protegiendo formularios ante ataques de falsificación de solicitudes.  
- Autenticación estándar de Django. 
- Verificación de dos pasos para el registro mediante código enviado al correo electrónico, reduciendo el riesgo de cuentas falsas.
- Uso de variables de entorno para credenciales.

### A mejorar 
- **BD**: excluir `db.sqlite3` del repositorio. 
- **Validación de archivos**: restringir tamaño, extensión y cabeceras en CSV.  
- **Autenticación**: limitar intentos de inicio de sesión.
---
## Aspectos donde se podría aplicar Inversion de Dependencias

### 1. Lógica de aprobación de comentarios por IA
- Extraer la lógica de aprobación a una interfaz (por ejemplo, ComentarioAprobador) y permitir inyectar diferentes implementaciones (manual, IA, etc.) en las vistas o servicios.

### 2. Gestión de envío de correos
- Crear una interfaz para el envío de emails (EmailSender) y usar diferentes implementaciones (SMTP, mock para pruebas, etc.), desacoplando la vista del método concreto.

### 3. Validación de formularios
- Definir una interfaz para validadores de formularios y permitir inyectar validadores personalizados según el tipo de usuario o contexto.

### 4. Acceso a datos de profesores/comentarios
- Usar repositorios o servicios para acceder a los modelos, permitiendo cambiar la fuente de datos (base de datos, API externa, etc.) sin modificar la lógica de negocio.

---

## Actividad 3 — Inversión de Dependencias

Se aplicó el principio de inversión de dependencias en la lógica de aprobación de comentarios:
- Se crearon las clases `ComentarioAprobador`, `ComentarioAprobadorManual` y `ComentarioAprobadorIA` en `review/views.py`.
- La vista `agregar_comentario` ahora utiliza una instancia de la clase aprobadora, permitiendo cambiar la lógica de aprobación fácilmente.
- Esto desacopla la lógica de negocio de la vista y facilita pruebas, mantenimiento y futuras extensiones (por ejemplo, agregar nuevas formas de aprobación).

**Ejemplo de uso en la vista:**
```python
aprobador = ComentarioAprobadorIA()  # se puede cambiar por ComentarioAprobadorManual()
aprobado = aprobador.aprobar(comentario.contenido)
```

## Actividad 4 — Aplicación de patrón de diseño Python: State

Se aplicó el patrón State en la gestión del estado de suspensión de usuarios (`UserProfile`).
- Se crearon las clases `ActivoState` y `SuspendidoState` para encapsular el comportamiento según el estado del usuario.
- El modelo `UserProfile` ahora delega el comportamiento a la clase de estado correspondiente usando los métodos `puede_acceder()` y `mensaje_estado()`.
- Las vistas, como `user_profile` y `agregar_comentario`, utilizan estos métodos para mostrar mensajes y bloquear funcionalidades según el estado del usuario.

**Ventajas:**
- El código es más limpio y desacoplado.
- Es fácil agregar nuevos estados o modificar reglas sin cambiar la lógica principal.
- Se mejora la escalabilidad y mantenibilidad del sistema.

**Ejemplo de uso en la vista:**
```python
if not user_profile.puede_acceder():
    messages.error(request, user_profile.mensaje_estado() + ' No puedes agregar comentarios.')
    return redirect('detalle_profesor', profesor.id)
```

## Actividad 5 — Patrones de Diseño

### Patrón Factory

Se aplicó el patrón Factory en la generación de gráficas estadísticas del sistema.

**Problema identificado:**
- En views.py se que generaban diferentes tipos de gráficas (barras, líneas, dispersión, frecuencia).
- Cada función repetía la misma lógica de configurar matplotlib, crear buffers IO, codificar a base64 y cerrar recursos.

**Implementación:**
- Se creó chart_factory.py con una jerarquía de clases:
  - `ChartGenerator` (clase base abstracta) define la interfaz común.
  - Generadores concretos: `BarChartGenerator`, `LineChartGenerator`, `ScatterChartGenerator`, `FrequencyDistributionChartGenerator`, `SemesterLineChartGenerator`.
  - `ChartFactory` actúa como factory que crea y genera gráficas según el tipo solicitado.
- Las vistas ahora usan `ChartFactory.create_chart(tipo, datos)` en lugar de funciones individuales.

**Ventajas:**
- Reducción de líneas de código en views.py.
- Eliminación de código duplicado.
- Cada generador es testeable de forma independiente.

**Ejemplo de uso en la vista:**
```python
# ANTES:
grafica_barras = generar_grafica_barras(ratings_grafica)
grafica_por_semestre = grafica_calificaciones_semestre(comentarios_grafica)

# DESPUÉS:
grafica_barras = ChartFactory.create_chart('bar', ratings_grafica)
grafica_por_semestre = ChartFactory.create_chart('line', comentarios_grafica)
```

---

### Patrón Facade

Se aplicó el patrón Facade para simplificar el complejo subsistema de gestión de comentarios.

**Problema identificado:**
- La vista `agregar_comentario` en views.py tenía múltiples responsabilidades mezcladas:
  - Validar permisos del usuario.
  - Aprobar contenido con IA.
  - Guardar en base de datos.
  - Coordinar actualización de estadísticas (usando Signals/Observer).
- Lógica mezclada con lógica de presentación.
- Código difícil de testear y reutilizar en otras vistas.

**Implementación:**
- Se creó facades.py con la clase `ComentarioFacade` que actúa como punto único de acceso al subsistema de comentarios.
- Métodos principales:
  - `puede_usuario_comentar()`: Verifica permisos..
  - `crear_comentario()`: Coordina validación, aprobación IA y persistencia.
  - `editar_comentario()`: Maneja edición con re-aprobación si cambia el contenido.
  - `eliminar_comentario()`: Elimina con validaciones y actualización de estadísticas.
  - `obtener_estadisticas_profesor()`: Proporciona estadísticas consolidadas.
- La fachada coordina múltiples patrones: State, Strategy, Observer.
- 
**Ventajas:**
- Simplificación en las vistas: código más legible y mantenible.
- Separación de responsabilidades: vistas solo manejan presentación, fachada maneja lógica de negocio.
- La lógica está centralizada y puede usarse desde cualquier vista.
- Uso de transacciones atómicas garantizando consistencia de datos.

**Ejemplo de uso en la vista:**
```python
# ANTES (33 líneas):
user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
if not user_profile.puede_acceder():
    messages.error(request, user_profile.mensaje_estado() + ' No puedes agregar comentarios.')
    return redirect('detalle_profesor', profesor_id=profesor.id)
# ... 20+ líneas más de lógica ...

# DESPUÉS (10 líneas):
facade = ComentarioFacade()
puede_comentar, mensaje = facade.puede_usuario_comentar(request.user)
if not puede_comentar:
    messages.error(request, mensaje)
    return redirect('detalle_profesor', profesor_id=profesor.id)

exito, comentario, mensaje = facade.crear_comentario(
    form_data=form.cleaned_data,
    profesor=profesor,
    usuario=request.user,
    es_anonimo=es_anonimo
)
```

---

## Bono — Funcionalidad nueva desde cero

### Patrón Strategy (Sistema de Recomendación)

Se implementó un sistema de recomendación completamente nuevo utilizando el patrón Strategy para ordenar profesores según diferentes criterios.

**Problema identificado:**
- La vista `lista_profesores` en views.py contenía múltiples bloques `if/elif` para manejar diferentes criterios de ordenamiento.
- Agregar un nuevo criterio requería modificar directamente la función.
- La lógica de ordenamiento estaba mezclada con los filtros de búsqueda.

**Implementación:**
- Se creó recommendation_strategies.py con una jerarquía de estrategias:
- Registro dinámico de estrategias permite agregar nuevas sin modificar código existente.
- Por defecto, los profesores mejor calificados aparecen primero automáticamente.

**Ventajas:**
- Eliminación total de condicionales `if/elif` en la vista.
- Agregar nueva estrategia solo requiere crear una clase nueva.
- Permite cambiar el algoritmo de ordenamiento en tiempo de ejecución.
- Estrategia "balanceada" implementa lógica compleja imposible con simple `order_by()`.
- Código más limpio y mantenible.

**Ejemplo de uso en la vista:**
```python
# ANTES (16 líneas con if/elif):
if orden_field:
    if orden_field == 'mayor_rating':
        profesores = profesores.order_by('-calificacion_media')
    elif orden_field == 'menor_rating':
        profesores = profesores.order_by('calificacion_media')
    elif orden_field == 'mayor_comentarios':
        profesores = profesores.order_by('-numcomentarios')
    elif orden_field == 'menor_comentarios':
        profesores = profesores.order_by('numcomentarios')

# DESPUÉS (6 líneas sin condicionales):
strategy_map = {
    'mayor_rating': 'best_rated',
    'mayor_comentarios': 'most_reviewed',
    'recomendado': 'balanced'
}
recommendation_engine = RecommendationEngine(strategy_map.get(orden_field, 'best_rated'))
profesores = recommendation_engine.recommend(profesores)
```

**Funcionalidad nueva:**
- Sistema de recomendación automático: por defecto muestra los mejores profesores primero.
- Estrategia balanceada inteligente: requiere mínimo 3 reseñas para considerarse confiable.
- Mejora significativa en la experiencia del usuario al navegar por la lista de profesores.

---
### En el archivo setup.txt se encuentra el paso a paso para ejecutar el proyecto.

