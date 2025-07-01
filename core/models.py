from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import hashlib
import time
from datetime import datetime

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Token ID özelliği - benzersiz ve değişmez olacak
    token_id = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    token_created_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

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
