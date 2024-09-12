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
    path('profesor/<int:profesor_id>/', reviewViews.detalle_profesor, name='detalle_profesor'),
    path('profesor/<int:profesor_id>/comentar/', reviewViews.agregar_comentario, name='agregar_comentario'),
    
    # Nuevas rutas para "Mis Comentarios", editar y eliminar reseñas
    path('mis_comentarios/', reviewViews.mis_comentarios, name='mis_comentarios'),
    path('edit_review/<int:comentario_id>/', reviewViews.edit_review, name='edit_review'),
    path('delete_own_review/<int:comentario_id>/', reviewViews.delete_own_review, name='delete_own_review'),
    path('delete_review/<int:comentario_id>/', reviewViews.delete_review, name='delete_review'),
    path('review/manage_reviews/', reviewViews.manage_reviews, name='manage_reviews'),

    # Rutas de autenticación
    path('profile/', accountViews.user_profile, name='profile'),
    path('login/', LoginView.as_view(template_name='registro/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', accountViews.register, name='register'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
