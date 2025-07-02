from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('studio/', views.studio, name='studio'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # User profiles - IMPORTANT: Keep specific routes BEFORE dynamic routes
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/settings/', views.profile_edit, name='profile_settings'), # Alternative URL
    path('profile/<str:username>/', views.profile_view, name='profile'),
    
    # Designs
    path('design/<int:design_id>/', views.design_detail, name='design_detail'),
    path('design/<int:design_id>/edit/', views.design_edit, name='design_edit'),
    path('design/<int:design_id>/delete/', views.design_delete, name='design_delete'),
    path('design/create/', views.design_create, name='design_create'),
    
    # Social features - AJAX endpoints
    path('api/like/<int:design_id>/', views.toggle_like, name='toggle_like'),
    path('api/follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('api/comment/<int:design_id>/', views.add_comment, name='add_comment'),
    path('api/design/<int:design_id>/view/', views.track_design_view, name='track_design_view'),
    
    # Search and discovery
    path('search/', views.search, name='search'),
    path('trending/', views.trending, name='trending'),
    path('tag/<str:tag>/', views.designs_by_tag, name='designs_by_tag'),
    
    # AI Inpainting endpoints
    path('api/inpaint/', views.inpaint_image, name='inpaint_image'),
    path('api/upload-for-inpainting/', views.upload_for_inpainting, name='upload_for_inpainting'),
    path('api/ai-status/', views.check_ai_status, name='check_ai_status'),
    path('api/test-ai/', views.test_ai_model, name='test_ai_model'),
    
    # Debug (geçici)
    path('debug/', views.debug, name='debug'),
] 