from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('studio/', views.studio, name='studio'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # User profile
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # Designs
    path('design/<int:design_id>/', views.design_detail, name='design_detail'),
    path('design/<int:design_id>/edit/', views.design_edit, name='design_edit'),
    path('design/<int:design_id>/delete/', views.design_delete, name='design_delete'),
    path('design/create/', views.design_create, name='design_create'),
    
    # AI Inpainting endpoints
    path('api/inpaint/', views.inpaint_image, name='inpaint_image'),
    path('api/upload-for-inpainting/', views.upload_for_inpainting, name='upload_for_inpainting'),
    path('api/ai-status/', views.check_ai_status, name='check_ai_status'),
    
    # Debug (geçici)
    path('debug/', views.debug, name='debug'),
] 