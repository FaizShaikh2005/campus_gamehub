#games urls 
from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_list, name='game_list'),
    path('<int:pk>/', views.game_detail, name='game_detail'),
    path('add/', views.add_game, name='add_game'),
    path('edit/<int:pk>/', views.edit_game, name='edit_game'),
    path('delete/<int:pk>/', views.delete_game, name='delete_game'),
]
