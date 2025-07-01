from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile, Design, Like, Comment, Follow, DesignView, ContactMessage
from django.db.models import Q, Count
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import F
import os
import json
import uuid
from PIL import Image
import logging
import requests

# Initialize logger
logger = logging.getLogger(__name__)

# AI model imports
try:
    from .ai_models import get_inpainting_model
    AI_AVAILABLE = True
    logger.info("AI models configured successfully for API usage")
except ImportError as e:
    logger.warning(f"AI models not available: {e}")
    AI_AVAILABLE = False
except Exception as e:
    logger.error(f"AI models failed to configure: {e}")
    AI_AVAILABLE = False

# Force debug mode to ensure static files load correctly
settings.DEBUG = True

# Create your views here.

def home(request):
    # Trending tasarımları göster (en çok beğenilen son 7 günün tasarımları)
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    
    trending_designs = Design.objects.filter(
        status='published',
        created_at__gte=week_ago
    ).annotate(
        engagement_score=F('likes_count') + F('views_count') + F('comments_count')
    ).order_by('-engagement_score', '-created_at')[:6]
    
    # Eğer trend bulunamazsa son tasarımları göster
    if not trending_designs:
        trending_designs = Design.objects.filter(status='published').order_by('-created_at')[:6]
    
    # Son eklenen tasarımlar
    latest_designs = Design.objects.filter(status='published').order_by('-created_at')[:6]
    
    # Toplam istatistikler
    total_designs = Design.objects.filter(status='published').count()
    total_users = User.objects.count()
    total_likes = Like.objects.count()
    
    context = {
        'title': 'triX - Creativity Platform',
        'trending_designs': trending_designs,
        'latest_designs': latest_designs,
        'stats': {
            'total_designs': total_designs,
            'total_users': total_users,
            'total_likes': total_likes,
        }
    }
    return render(request, 'home.html', context)

def simple_home(request):
    return render(request, 'simple.html')

def about(request):
    context = {
        'title': 'About triX'
    }
    return render(request, 'about.html', context)

def gallery(request):
    # Filtreler
    style = request.GET.get('style', '')
    search = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'latest')  # latest, popular, trending
    
    designs = Design.objects.filter(status='published')
    
    if style:
        designs = designs.filter(style=style)
    
    if search:
        designs = designs.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(prompt__icontains=search) |
            Q(tags__icontains=search)
        )
    
    # Sıralama
    if sort_by == 'popular':
        designs = designs.order_by('-likes_count', '-views_count')
    elif sort_by == 'trending':
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        designs = designs.filter(created_at__gte=week_ago).annotate(
            engagement_score=F('likes_count') + F('views_count') + F('comments_count')
        ).order_by('-engagement_score')
    else:  # latest
        designs = designs.order_by('-created_at')
    
    # Sayfalama eklenebilir burada
    
    context = {
        'title': 'triX Gallery',
        'designs': designs,
        'style_filter': style,
        'search_query': search,
        'sort_by': sort_by,
        'available_styles': Design.objects.filter(status='published').values_list('style', flat=True).distinct()
    }
    return render(request, 'gallery.html', context)

def contact(request):
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_content = request.POST.get('message', '').strip()
        
        # Validasyon
        if not all([name, email, subject, message_content]):
            messages.error(request, 'Lütfen tüm alanları doldurun.')
            return render(request, 'contact.html', {
                'title': 'Contact triX',
                'form_data': {
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'message': message_content
                }
            })
        
        try:
            # Veritabanına kaydet
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message_content
            )
            
            # Email gönder (admin'e)
            try:
                admin_email = settings.DEFAULT_FROM_EMAIL or 'admin@trixweb.com'
                
                email_subject = f'triX Contact Form: {subject}'
                email_message = f"""
Yeni iletişim formu mesajı:

İsim: {name}
Email: {email}
Konu: {subject}

Mesaj:
{message_content}

---
Bu mesaj triX iletişim formundan gönderilmiştir.
Mesaj ID: {contact_message.id}
Tarih: {contact_message.created_at.strftime('%d/%m/%Y %H:%M')}
                """
                
                send_mail(
                    email_subject,
                    email_message,
                    email,  # From email
                    [admin_email],  # To email
                    fail_silently=False,
                )
                
                # Kullanıcıya teşekkür emaili gönder
                thank_you_subject = 'triX - Mesajınız alındı'
                thank_you_message = f"""
Merhaba {name},

triX iletişim formundan gönderdiğiniz mesajınız başarıyla alınmıştır.

Konu: {subject}

En kısa sürede size geri dönüş yapacağız.

Teşekkürler,
triX Ekibi
                """
                
                send_mail(
                    thank_you_subject,
                    thank_you_message,
                    admin_email,
                    [email],
                    fail_silently=True,  # Kullanıcı emaili başarısız olursa ana işlemi etkilemesin
                )
                
                messages.success(request, 'Mesajınız başarıyla gönderildi! En kısa sürede size geri dönüş yapacağız.')
                
            except Exception as e:
                logger.error(f"Contact form email failed: {e}")
                messages.success(request, 'Mesajınız kaydedildi! En kısa sürede size geri dönüş yapacağız.')
            
            return redirect('core:contact')
            
        except Exception as e:
            logger.error(f"Contact form save failed: {e}")
            messages.error(request, 'Mesaj gönderilirken bir hata oluştu. Lütfen tekrar deneyin.')
    
    context = {
        'title': 'Contact triX'
    }
    return render(request, 'contact.html', context)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Kayıt başarılı! triX'e hoş geldiniz!")
            return redirect('core:home')
        messages.error(request, "Kayıt başarısız. Lütfen hataları düzeltin.")
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Hoş geldiniz, {username}!")
                
                # Check if there's a next parameter
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('core:home')
            else:
                messages.error(request, "Geçersiz kullanıcı adı veya şifre.")
        else:
            messages.error(request, "Geçersiz kullanıcı adı veya şifre.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Başarıyla çıkış yaptınız!")
    return redirect('core:home')

@login_required(login_url='/login/')
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    
    # Ensure user has a profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Kullanıcının kendi profili ise veya tasarım yayınladıysa göster
    if request.user == user:
        designs = Design.objects.filter(user=user).order_by('-created_at')
    else:
        designs = Design.objects.filter(user=user, status='published').order_by('-created_at')
    
    context = {
        'user': user,
        'designs': designs,
        'profile': profile,
    }
    return render(request, 'auth/profile.html', context)

@login_required(login_url='/login/')
def profile_edit(request):
    """Enhanced profile edit with all new fields"""
    try:
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            # Kullanıcı bilgilerini güncelle
            user = request.user
            user.username = request.POST.get('username', user.username)
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', user.email)
            user.save()
            
            # Profil bilgilerini güncelle
            profile.bio = request.POST.get('bio', '')
            profile.website = request.POST.get('website', '')
            profile.location = request.POST.get('location', '')
            
            # Birth date işleme
            birth_date = request.POST.get('birth_date')
            if birth_date:
                try:
                    from datetime import datetime
                    profile.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                except ValueError:
                    profile.birth_date = None
            
            # Avatar işleme
            if 'avatar' in request.FILES:
                if profile.avatar:
                    # Eski avatarı sil
                    try:
                        if os.path.isfile(profile.avatar.path):
                            os.remove(profile.avatar.path)
                    except:
                        pass  # File might not exist
                profile.avatar = request.FILES['avatar']
            
            # Avatar silme işlemi
            if request.POST.get('remove_avatar') == 'on' and profile.avatar:
                try:
                    if os.path.isfile(profile.avatar.path):
                        os.remove(profile.avatar.path)
                except:
                    pass
                profile.avatar = None
            
            profile.save()
            
            messages.success(request, "Profil başarıyla güncellendi!")
            return redirect('core:profile', username=user.username)
            
    except Exception as e:
        logger.error(f"Profile edit error: {e}")
        messages.error(request, "Profil güncellenirken bir hata oluştu.")
    
    return render(request, 'auth/profile_edit.html', {
        'user': request.user,
        'profile': request.user.profile
    })

def design_detail(request, design_id):
    design = get_object_or_404(Design, id=design_id)
    
    # Eğer tasarım yayınlanmadıysa ve mevcut kullanıcı sahibi değilse erişimi engelle
    if design.status != 'published' and request.user != design.user:
        return HttpResponseForbidden("Bu tasarımı görüntüleme izniniz yok.")
    
    # View tracking (her ziyaret için sayaç artır)
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    
    # Eğer bu IP'den bu tasarımı daha önce görmediyse view kaydet
    design_view, created = DesignView.objects.get_or_create(
        user=request.user if request.user.is_authenticated else None,
        design=design,
        ip_address=ip_address,
        defaults={'user_agent': user_agent}
    )
    
    if created:
        # View count'u artır
        design.views_count = F('views_count') + 1
        design.save(update_fields=['views_count'])
        design.refresh_from_db()
    
    # Kullanıcının bu tasarımı beğenip beğenmediğini kontrol et
    is_liked = False
    is_following = False
    if request.user.is_authenticated:
        is_liked = design.is_liked_by(request.user)
        is_following = Follow.objects.filter(
            follower=request.user, 
            following=design.user
        ).exists()
    
    # Yorumları al
    comments = Comment.objects.filter(
        design=design, 
        parent=None
    ).select_related('user', 'user__profile').order_by('-created_at')
    
    # Benzer tasarımları bul
    related_designs = Design.objects.filter(
        status='published', 
        style=design.style
    ).exclude(id=design.id)[:4]
    
    context = {
        'design': design,
        'related_designs': related_designs,
        'comments': comments,
        'is_liked': is_liked,
        'is_following': is_following,
    }
    return render(request, 'design_detail.html', context)

@login_required(login_url='/login/')
def design_edit(request, design_id):
    design = get_object_or_404(Design, id=design_id)
    
    # Sadece sahibi düzenleyebilir
    if request.user != design.user:
        return HttpResponseForbidden("Bu tasarımı düzenleme izniniz yok.")
    
    if request.method == 'POST':
        design.title = request.POST.get('title')
        design.description = request.POST.get('description')
        design.status = request.POST.get('status')
        design.style = request.POST.get('style')
        design.model_used = request.POST.get('model_used')
        design.prompt = request.POST.get('prompt')
        
        if 'image' in request.FILES:
            # Eski resmi sil
            if os.path.isfile(design.image.path):
                os.remove(design.image.path)
            design.image = request.FILES['image']
        
        design.save()
        messages.success(request, "Tasarım başarıyla güncellendi!")
        return redirect('core:design_detail', design_id=design.id)
    
    context = {
        'design': design,
    }
    return render(request, 'design_edit.html', context)

@login_required(login_url='/login/')
def design_create(request):
    if request.method == 'POST':
        new_design = Design(
            user=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            status=request.POST.get('status', 'draft'),
            style=request.POST.get('style', ''),
            model_used=request.POST.get('model_used', ''),
            prompt=request.POST.get('prompt', '')
        )
        
        if 'image' in request.FILES:
            new_design.image = request.FILES['image']
            new_design.save()
            messages.success(request, "Tasarım başarıyla oluşturuldu!")
            return redirect('core:design_detail', design_id=new_design.id)
        else:
            messages.error(request, "Tasarım için bir görsel yüklemelisiniz.")
    
    return render(request, 'design_create.html')

@login_required(login_url='/login/')
def design_delete(request, design_id):
    design = get_object_or_404(Design, id=design_id)
    
    # Sadece sahibi silebilir
    if request.user != design.user:
        return HttpResponseForbidden("Bu tasarımı silme izniniz yok.")
    
    if request.method == 'POST':
        # Görsel dosyasını sil
        if design.image and os.path.isfile(design.image.path):
            os.remove(design.image.path)
        
        design.delete()
        messages.success(request, "Tasarım başarıyla silindi!")
        return redirect('core:profile', username=request.user.username)
    
    return redirect('core:design_detail', design_id=design.id)

@login_required(login_url='/login/')
def studio(request):
    context = {
        'title': 'triX Studio - Image Design',
        'user': request.user,
        'designs': Design.objects.filter(user=request.user).order_by('-created_at')[:5]
    }
    return render(request, 'studio.html', context)

@login_required(login_url='/login/')
@csrf_exempt
@require_http_methods(["POST"])
def inpaint_image(request):
    """
    Endpoint for inpainting functionality using Hugging Face API
    """
    if not AI_AVAILABLE:
        return JsonResponse({
            'success': False, 
            'error': 'AI functionality not available. Please check configuration.'
        })
    
    try:
        # Parse request data
        data = json.loads(request.body)
        
        # Get parameters
        image_path = data.get('image_path')
        mask_data = data.get('mask_data')
        prompt = data.get('prompt', '')
        negative_prompt = data.get('negative_prompt', '')
        num_inference_steps = int(data.get('num_inference_steps', 50))
        guidance_scale = float(data.get('guidance_scale', 7.5))
        strength = float(data.get('strength', 1.0))
        
        if not image_path or not mask_data:
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters: image_path or mask_data'
            })
        
        # Convert relative path to absolute
        if not os.path.isabs(image_path):
            image_path = os.path.join(settings.MEDIA_ROOT, image_path)
        
        if not os.path.exists(image_path):
            return JsonResponse({
                'success': False,
                'error': 'Image file not found'
            })
        
        logger.info(f"Starting API inpainting for user {request.user.username}")
        
        # Get inpainting model (API client)
        model = get_inpainting_model()
        
        # Perform inpainting via API
        result_image = model.inpaint(
            image_path=image_path,
            mask_data=mask_data,
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            strength=strength
        )
        
        # Save result image
        result_filename = f"inpainted_{uuid.uuid4().hex}.png"
        result_path = os.path.join(settings.MEDIA_ROOT, 'inpainted', result_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        
        # Save the result
        result_image.save(result_path, format='PNG')
        
        # Get relative URL for the result
        result_url = f"{settings.MEDIA_URL}inpainted/{result_filename}"
        
        logger.info(f"API inpainting completed successfully for user {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'result_url': result_url,
            'message': 'Inpainting completed successfully via API!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"API inpainting error: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Inpainting failed: {str(e)}'
        })

@login_required(login_url='/login/')
@csrf_exempt
@require_http_methods(["POST"])
def upload_for_inpainting(request):
    """
    Upload image for inpainting processing
    """
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No image file provided'
            })
        
        image_file = request.FILES['image']
        
        # Validate file type
        if not image_file.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type. Please upload an image.'
            })
        
        # Generate unique filename
        filename = f"upload_{uuid.uuid4().hex}_{image_file.name}"
        
        # Save file
        file_path = default_storage.save(
            os.path.join('uploads', filename), 
            ContentFile(image_file.read())
        )
        
        # Get full URL
        file_url = f"{settings.MEDIA_URL}{file_path}"
        
        return JsonResponse({
            'success': True,
            'file_path': file_path,
            'file_url': file_url,
            'message': 'Image uploaded successfully!'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        })

@login_required(login_url='/login/')
def check_ai_status(request):
    """
    Check if AI functionality is available via Hugging Face API
    """
    if not AI_AVAILABLE:
        return JsonResponse({
            'available': False,
            'message': 'AI functionality not available. Please check configuration.',
            'device': None
        })
    
    try:
        model = get_inpainting_model()
        api_token = os.environ.get('HUGGINGFACE_API_TOKEN')
        
        return JsonResponse({
            'available': True,
            'message': 'AI functionality available via Hugging Face API',
            'device': 'Hugging Face API',
            'model_loaded': bool(api_token),
            'api_configured': bool(api_token)
        })
    except Exception as e:
        return JsonResponse({
            'available': False,
            'message': f'AI functionality error: {str(e)}',
            'device': None
        })

def debug(request):
    """Debug view to check if static files are loading properly."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Static Files</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #8b5cf6; }
            .test-box { border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>Static Files Debug Page</h1>
        
        <div class="test-box">
            <h2>CSS Test</h2>
            <div id="css-test">Testing CSS...</div>
        </div>
        
        <div class="test-box">
            <h2>JavaScript Test</h2>
            <div id="js-test">Testing JavaScript...</div>
        </div>
        
        <div class="test-box">
            <h2>Image Test</h2>
            <img src="/static/images/test-image.jpg" alt="Test Image" id="image-test" style="max-width:200px">
        </div>
        
        <script>
            // Test loading CSS
            fetch('/static/css/style.css')
                .then(response => {
                    if (response.ok) {
                        document.getElementById('css-test').innerHTML = '<span class="success">CSS file loaded successfully!</span>';
                    } else {
                        document.getElementById('css-test').innerHTML = '<span class="error">Failed to load CSS file. Status: ' + response.status + '</span>';
                    }
                })
                .catch(error => {
                    document.getElementById('css-test').innerHTML = '<span class="error">Error loading CSS file: ' + error + '</span>';
                });
                
            // Test loading JavaScript
            fetch('/static/js/main.js')
                .then(response => {
                    if (response.ok) {
                        document.getElementById('js-test').innerHTML = '<span class="success">JavaScript file loaded successfully!</span>';
                    } else {
                        document.getElementById('js-test').innerHTML = '<span class="error">Failed to load JavaScript file. Status: ' + response.status + '</span>';
                    }
                })
                .catch(error => {
                    document.getElementById('js-test').innerHTML = '<span class="error">Error loading JavaScript file: ' + error + '</span>';
                });
                
            // Test image loading
            document.getElementById('image-test').onload = function() {
                document.getElementById('image-test').insertAdjacentHTML('afterend', '<p class="success">Image loaded successfully!</p>');
            };
            
            document.getElementById('image-test').onerror = function() {
                document.getElementById('image-test').insertAdjacentHTML('afterend', '<p class="error">Failed to load image.</p>');
            };
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)

@login_required(login_url='/login/')
def test_ai_model(request):
    """
    Simple test endpoint for AI model functionality
    """
    if not AI_AVAILABLE:
        return JsonResponse({
            'success': False,
            'error': 'AI functionality not available'
        })
    
    try:
        # Test with a free, publicly available model first
        api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        
        # Try without token first (some models are public)
        test_payload = {
            "inputs": "a beautiful sunset landscape, high quality, detailed"
        }
        
        logger.info("Testing AI model with free public model...")
        
        # First try without authentication
        response = requests.post(
            api_url,
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return JsonResponse({
                'success': True,
                'message': 'AI model test successful! Using public model (Stable Diffusion v1.5)',
                'status_code': response.status_code,
                'api_url': api_url,
                'note': 'Using free public model - your LoRA model may need updated token'
            })
        
        # If public doesn't work, try with token
        headers = {
            "Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_TOKEN', '')}"
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            # Now try the LoRA model
            lora_api_url = "https://api-inference.huggingface.co/models/meryemarpaci/sd2base-inpainting-lora"
            lora_response = requests.post(
                lora_api_url,
                headers=headers,
                json=test_payload,
                timeout=30
            )
            
            if lora_response.status_code == 200:
                return JsonResponse({
                    'success': True,
                    'message': 'Perfect! Both base model and your LoRA model are working!',
                    'status_code': lora_response.status_code,
                    'api_url': lora_api_url
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f'Base model works, but LoRA model failed (Status {lora_response.status_code}). Token may need Inference API permissions.',
                    'status_code': response.status_code,
                    'api_url': api_url,
                    'lora_error': lora_response.text[:200]
                })
        else:
            return JsonResponse({
                'success': False,
                'error': f'API test failed. Status: {response.status_code}. Response: {response.text[:200]}',
                'status_code': response.status_code,
                'suggestion': 'Check if HUGGINGFACE_API_TOKEN is set correctly in Render.com environment variables'
            })
            
    except Exception as e:
        logger.error(f"AI model test failed: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Test failed: {str(e)}',
            'suggestion': 'Check network connection and API availability'
        })

# Social Features
@login_required(login_url='/login/')
@csrf_exempt
@require_http_methods(["POST"])
def toggle_like(request, design_id):
    """Toggle like for a design"""
    design = get_object_or_404(Design, id=design_id)
    
    try:
        like, created = Like.objects.get_or_create(
            user=request.user,
            design=design
        )
        
        if created:
            # Like eklendi
            action = 'liked'
            liked = True
        else:
            # Like kaldırıldı
            like.delete()
            action = 'unliked'
            liked = False
        
        # Güncel like sayısını al
        design.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'liked': liked,
            'likes_count': design.likes_count
        })
        
    except Exception as e:
        logger.error(f"Toggle like failed: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Like işlemi başarısız oldu'
        })

@login_required(login_url='/login/')
@csrf_exempt
@require_http_methods(["POST"])
def toggle_follow(request, username):
    """Toggle follow for a user"""
    target_user = get_object_or_404(User, username=username)
    
    if request.user == target_user:
        return JsonResponse({
            'success': False,
            'error': 'Kendinizi takip edemezsiniz'
        })
    
    try:
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target_user
        )
        
        if created:
            # Follow eklendi
            action = 'followed'
            following = True
        else:
            # Follow kaldırıldı
            follow.delete()
            action = 'unfollowed'
            following = False
        
        # Güncel follower sayısını al
        target_user.profile.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'following': following,
            'followers_count': target_user.profile.followers_count
        })
        
    except Exception as e:
        logger.error(f"Toggle follow failed: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Takip işlemi başarısız oldu'
        })

@login_required(login_url='/login/')
@csrf_exempt
@require_http_methods(["POST"])
def add_comment(request, design_id):
    """Add comment to a design"""
    design = get_object_or_404(Design, id=design_id)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Yorum içeriği boş olamaz'
            })
        
        # Parent comment kontrolü
        parent = None
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id, design=design)
        
        # Yorum oluştur
        comment = Comment.objects.create(
            user=request.user,
            design=design,
            content=content,
            parent=parent
        )
        
        # Response data
        response_data = {
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'user': {
                    'username': comment.user.username,
                    'full_name': comment.user.get_full_name() or comment.user.username,
                    'avatar': comment.user.profile.avatar.url if comment.user.profile.avatar else None
                },
                'created_at': comment.created_at.strftime('%d %b %Y, %H:%M'),
                'parent_id': parent.id if parent else None
            },
            'comments_count': design.comments_count
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Add comment failed: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Yorum eklenirken hata oluştu'
        })

def search(request):
    """Search designs, users, and tags"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all')  # all, designs, users, tags
    
    context = {
        'title': 'Search Results',
        'query': query,
        'category': category
    }
    
    if not query:
        return render(request, 'search.html', context)
    
    # Tasarım araması
    if category in ['all', 'designs']:
        designs = Design.objects.filter(
            status='published'
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(prompt__icontains=query) |
            Q(tags__icontains=query) |
            Q(user__username__icontains=query)
        ).distinct().order_by('-likes_count', '-created_at')
        
        context['designs'] = designs
    
    # Kullanıcı araması
    if category in ['all', 'users']:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__bio__icontains=query)
        ).select_related('profile').order_by('-profile__followers_count')
        
        context['users'] = users
    
    # Tag araması
    if category in ['all', 'tags']:
        # Tag'leri içeren tasarımları bul
        tag_designs = Design.objects.filter(
            status='published',
            tags__icontains=query
        ).order_by('-likes_count')
        
        # Benzersiz tag'leri bul
        all_tags = []
        for design in Design.objects.filter(status='published').exclude(tags=''):
            tags = design.get_tags_list()
            for tag in tags:
                if query.lower() in tag.lower() and tag not in all_tags:
                    all_tags.append(tag)
        
        context['tag_designs'] = tag_designs
        context['tags'] = all_tags[:10]  # İlk 10 tag
    
    return render(request, 'search.html', context)

def trending(request):
    """Trending designs page"""
    from datetime import datetime, timedelta
    
    # Son 7 günün trend tasarımları
    week_ago = datetime.now() - timedelta(days=7)
    
    trending_designs = Design.objects.filter(
        status='published',
        created_at__gte=week_ago
    ).annotate(
        engagement_score=F('likes_count') + F('views_count') + F('comments_count')
    ).order_by('-engagement_score', '-created_at')
    
    # Son 30 günün popüler tasarımları
    month_ago = datetime.now() - timedelta(days=30)
    popular_designs = Design.objects.filter(
        status='published',
        created_at__gte=month_ago
    ).order_by('-likes_count', '-views_count')[:12]
    
    # En aktif kullanıcılar
    top_creators = User.objects.filter(
        designs__status='published',
        designs__created_at__gte=week_ago
    ).annotate(
        recent_designs=Count('designs')
    ).order_by('-recent_designs', '-profile__followers_count')[:8]
    
    context = {
        'title': 'Trending - triX',
        'trending_designs': trending_designs,
        'popular_designs': popular_designs,
        'top_creators': top_creators,
    }
    
    return render(request, 'trending.html', context)

def designs_by_tag(request, tag):
    """Show designs filtered by tag"""
    designs = Design.objects.filter(
        status='published',
        tags__icontains=tag
    ).order_by('-created_at')
    
    # İlgili tag'ler
    related_tags = []
    for design in designs[:20]:  # İlk 20 tasarımdan tag topla
        tags = design.get_tags_list()
        for t in tags:
            if t != tag and t not in related_tags:
                related_tags.append(t)
    
    context = {
        'title': f'#{tag} - triX',
        'tag': tag,
        'designs': designs,
        'related_tags': related_tags[:10],  # İlk 10 ilgili tag
        'designs_count': designs.count()
    }
    
    return render(request, 'designs_by_tag.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def track_design_view(request, design_id):
    """Track design view (AJAX endpoint)"""
    design = get_object_or_404(Design, id=design_id)
    
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    try:
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = get_client_ip(request)
        
        # View kaydı oluştur
        design_view, created = DesignView.objects.get_or_create(
            user=request.user if request.user.is_authenticated else None,
            design=design,
            ip_address=ip_address,
            defaults={'user_agent': user_agent}
        )
        
        if created:
            # View count'u artır
            design.views_count = F('views_count') + 1
            design.save(update_fields=['views_count'])
            design.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'views_count': design.views_count
        })
        
    except Exception as e:
        logger.error(f"Track design view failed: {e}")
        return JsonResponse({
            'success': False,
            'error': 'View tracking failed'
        })
