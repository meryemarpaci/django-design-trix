from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
import hashlib
import time
from datetime import datetime
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Social stats
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    designs_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def get_absolute_url(self):
        return reverse('core:profile', kwargs={'username': self.user.username})

class Follow(models.Model):
    """User following system"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class Design(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('private', 'Private'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='designs')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='designs/')
    prompt = models.TextField(blank=True)
    style = models.CharField(max_length=50, blank=True)
    model_used = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Social features
    likes_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    
    # SEO and sharing
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Token ID özelliği - benzersiz ve değişmez olacak
    token_id = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    token_created_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('core:design_detail', kwargs={'design_id': self.id})
    
    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def is_liked_by(self, user):
        if user.is_authenticated:
            return Like.objects.filter(user=user, design=self).exists()
        return False
    
    def generate_token_id(self):
        """
        Benzersiz bir token ID oluşturur.
        SHA-256 ile resim dosyası içeriği, kullanıcı bilgisi ve zaman bilgisini birleştirerek hash oluşturur.
        """
        if self.token_id:  # Eğer zaten bir token ID varsa, değiştirme
            return self.token_id
        
        # Şu anki zaman bilgisi (mikrosan cinsinden)
        timestamp = str(time.time())
        
        # Kullanıcı bilgisi
        user_info = f"{self.user.id}:{self.user.username}"
        
        # Resim bilgisi (dosya yolu ve içerik)
        image_info = f"{self.image.name}:{self.image.size}"
        
        # Diğer meta veriler
        metadata = f"{self.title}:{self.created_at}:{self.style}:{self.model_used}"
        
        # Tüm veriyi birleştir
        data = f"{user_info}|{image_info}|{timestamp}|{metadata}"
        
        # SHA-256 hash oluştur
        hash_object = hashlib.sha256(data.encode())
        hex_dig = hash_object.hexdigest()
        
        return hex_dig
    
    def save_token_id(self):
        """Token ID'yi kaydeder ve tarih atar"""
        if not self.token_id:
            self.token_id = self.generate_token_id()
            self.token_created_at = datetime.now()

class Like(models.Model):
    """Design likes system"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'design')
    
    def __str__(self):
        return f"{self.user.username} liked {self.design.title}"

class Comment(models.Model):
    """Comments on designs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.design.title}"

class DesignView(models.Model):
    """Track design views for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name='design_views')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'design', 'ip_address')

class ContactMessage(models.Model):
    """Contact form submissions"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

class TokenMetadata(models.Model):
    """
    Token ID ile ilgili ek meta verileri saklamak için model.
    Daha fazla veri saklanabilir ve sorgulanabilir.
    """
    design = models.OneToOneField(Design, on_delete=models.CASCADE, related_name='token_metadata')
    token_id = models.CharField(max_length=64, unique=True)
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    blockchain_verified = models.BooleanField(default=False)
    hash_algorithm = models.CharField(max_length=20, default='SHA-256')
    
    def __str__(self):
        return f"Token {self.token_id[:8]}... for {self.design.title}"

# Signal handlers
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            profile, profile_created = UserProfile.objects.get_or_create(user=instance)
            if profile_created:
                logger.info(f"Profile created successfully for user: {instance.username} (ID: {instance.id})")
            else:
                logger.info(f"Profile already exists for user: {instance.username} (ID: {instance.id})")
        except Exception as e:
            logger.error(f"Error creating profile for user {instance.username}: {e}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # If profile doesn't exist, create it
            UserProfile.objects.get_or_create(user=instance)
            logger.info(f"Profile created for existing user: {instance.username}")
    except Exception as e:
        logger.error(f"Error saving profile for user {instance.username}: {e}")

@receiver(post_save, sender=Like)
def update_design_likes_count(sender, instance, created, **kwargs):
    if created:
        instance.design.likes_count = instance.design.likes.count()
        instance.design.save(update_fields=['likes_count'])

@receiver(post_save, sender=Comment)
def update_design_comments_count(sender, instance, created, **kwargs):
    if created:
        instance.design.comments_count = instance.design.comments.count()
        instance.design.save(update_fields=['comments_count'])

@receiver(post_save, sender=Follow)
def update_follow_counts(sender, instance, created, **kwargs):
    if created:
        # Update follower count
        instance.following.profile.followers_count = instance.following.followers.count()
        instance.following.profile.save(update_fields=['followers_count'])
        
        # Update following count
        instance.follower.profile.following_count = instance.follower.following.count()
        instance.follower.profile.save(update_fields=['following_count'])

@receiver(post_save, sender=Design)
def update_user_designs_count(sender, instance, created, **kwargs):
    if created:
        instance.user.profile.designs_count = instance.user.designs.filter(status='published').count()
        instance.user.profile.save(update_fields=['designs_count'])

@receiver(pre_save, sender=Design)
def ensure_token_id(sender, instance, **kwargs):
    """
    Tasarım kaydedilmeden önce token ID'nin atandığından emin olur.
    Token ID sadece bir kez oluşturulur ve değiştirilemez.
    """
    if not instance.token_id:
        # Yeni kayıt, token ID oluştur
        instance.save_token_id()
    elif Design.objects.filter(pk=instance.pk).exists():
        # Mevcut kayıt güncelleniyor, token ID'yi değiştirme
        original = Design.objects.get(pk=instance.pk)
        instance.token_id = original.token_id
        instance.token_created_at = original.token_created_at

@receiver(post_save, sender=Design)
def create_token_metadata(sender, instance, created, **kwargs):
    """Tasarım kaydedildiğinde TokenMetadata oluşturur veya günceller"""
    if created:
        # Yeni kayıt için metadata oluştur
        TokenMetadata.objects.create(
            design=instance,
            token_id=instance.token_id
        )
    else:
        # Varolan kayıt güncelleniyor, metadata'yı güncelle
        try:
            metadata = instance.token_metadata
            if metadata.token_id != instance.token_id:
                metadata.token_id = instance.token_id
                metadata.save()
        except TokenMetadata.DoesNotExist:
            # Metadata kaydı yoksa oluştur
            TokenMetadata.objects.create(
                design=instance,
                token_id=instance.token_id
            )
