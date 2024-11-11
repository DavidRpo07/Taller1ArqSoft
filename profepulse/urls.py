from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView

from review import views as reviewViews
from profesores import views as profesoresViews
from account import views as accountViews

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', reviewViews.home, name='home'),
    path('profesores/', profesoresViews.lista_profesores, name='lista_profesores'),
    path('profesor/<int:profesor_id>/', profesoresViews.detalle_profesor, name='detalle_profesor'),
    path('profesor/<int:profesor_id>/comentar/', reviewViews.agregar_comentario, name='agregar_comentario'),
    path('agregarprofesor/', profesoresViews.upload_csv, name='agregar_profesor'),
    path('profile/<int:user_id>/', accountViews.user_profile, name='user_profile'),
    path('eliminarprofesor/', profesoresViews.manage_profesor, name='manage_profesor'),
    path('eliminarprofesor/<int:profesor_id>/', profesoresViews.delete_profesor, name='eliminar_profesor'),
    path('editarprofesor/<int:profesor_id>/', profesoresViews.edit_profesor, name='editar_profesor'),
    path('agregar-materia/', profesoresViews.agregar_materia, name='agregar_materia'),

    
    # Nuevas rutas para "Mis Comentarios", editar y eliminar reseñas
    path('mis_comentarios/<int:user_id>/', reviewViews.mis_comentarios, name='mis_comentarios'),
    path('edit_review/<int:comentario_id>/', reviewViews.edit_review, name='edit_review'),
    path('delete_own_review/<int:comentario_id>/', reviewViews.delete_own_review, name='delete_own_review'),
    path('delete_review/<int:comentario_id>/', reviewViews.delete_review, name='delete_review'),
    path('review/manage_reviews/', reviewViews.manage_reviews, name='manage_reviews'),

    # Rutas de autenticación
    path('login/', LoginView.as_view(template_name='registro/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', accountViews.register, name='register'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
