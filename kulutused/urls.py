from django.urls import path

from . import views


app_name = 'kulutused'
urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='signup'),
    path('logout', views.logout, name='logout'),
    path('groups/', views.index, name='index'),
    path('groups/choose', views.choose_group, name='choose-group'),
    path('groups/<int:group_id>/send_transaction', views.send_transaction, name='send-transaction'),
    path('groups/<int:group_id>/summary', views.summary , name='summary'),
    path('groups/<int:group_id>/dashboard', views.dashboard , name='dashboard'),
    path('groups/<int:group_id>/join', views.join , name='join'),
    path('groups/create', views.create_group , name='create-group'),
    path('groups/<int:group_id>/share', views.share_group , name='share-group'),


]