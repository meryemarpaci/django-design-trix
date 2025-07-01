from django.contrib import admin
from .models import UserProfile, Design, TokenMetadata

# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')

@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'token_id', 'created_at')
    list_filter = ('status', 'created_at', 'style', 'model_used')
    search_fields = ('title', 'description', 'user__username', 'prompt', 'token_id')
    readonly_fields = ('token_id', 'token_created_at')
    prepopulated_fields = {'title': ('title',)}
    date_hierarchy = 'created_at'

@admin.register(TokenMetadata)
class TokenMetadataAdmin(admin.ModelAdmin):
    list_display = ('design', 'token_id_short', 'creation_timestamp', 'blockchain_verified')
    list_filter = ('blockchain_verified', 'creation_timestamp', 'hash_algorithm')
    search_fields = ('token_id', 'design__title')
    readonly_fields = ('token_id', 'creation_timestamp')
    
    def token_id_short(self, obj):
        """Token ID'nin kısa versiyonunu gösterir"""
        if obj.token_id:
            return f"{obj.token_id[:8]}...{obj.token_id[-8:]}"
        return "-"
    
    token_id_short.short_description = 'Token ID'
