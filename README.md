# ProfePulse

## David Restrepo, Sebastián Castaño & Miguel Arcila

## How to install? 
# Download python version 3.11
# Download git
### Download as a zip file or with git clone the repository with this command:
### git clone https://github.com/Miguel107/ProfePulse.git
### Create a file named keys.env in the main project folder. It should look like this
 OPENAI_API_KEY = 'your_openai_api_key'
 
 EMAIL_HOST= 'smtp.gmail.com'
 
 EMAIL_HOST_USER= 'your_gmail'
 
 EMAIL_HOST_PASSWORD= 'your_password_app'


## How to run it?
### 1. Go to the directory
### 2. pip install -r requirements.txt
### 3. python manage.py makemigrations
### 4. python manage.py migrate
### 5. python manage.py runserver
### Open your web browser and go to http://127.0.0.1:8000/


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
- Verificación de dos pasos** para el registro mediante código enviado al correo electrónico, reduciendo el riesgo de cuentas falsas.
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
### Patron Factory

En la app de profesores en `views.py` hay múltiples funciones que generan gráficas (barras, dispersión, líneas por semestre).  Cada una cofigura matplotlib, crear buffers, codifica a base64.
La idea de factory es generar con base a la interfaz común diferentes tipos de gráficas y no repetir la logica de la configuración.


### Patron Facade
En la app `review/views.py` la vista agregar_comentario tenía múltiples responsabilidades validar permisos, aprobar con IA, guardar, actualizar estadísticas. Necesitabamos simplificar la interaccion con el subsistemas de los comentarios, en teoría las vistas solo deberian preocuparse por la presentación y no la logica.

## Bono — Funcionalidad nueva desde cero
### Patron Strategy

En la app pofesores en `views.py/lista_profesores` tenía múltiples if/elif para ordenar profesores, la logica de ordenamiento estaba mezclada con los filtros y agregar un nuevo criterio requería modificar la función.
Strategy es mas flexible, elimina condicionales y permite cambiar el comportamiento en runtime sin modificar el cliente.



