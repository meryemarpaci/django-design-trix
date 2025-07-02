from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
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
from django.urls import reverse
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
    # Sadece platform istatistikleri - tasarımları galeri'de gösterelim
    total_designs = Design.objects.filter(status='published').count()
    total_users = User.objects.count()
    total_likes = Like.objects.count()
    
    context = {
        'title': 'triX - Creativity Platform',
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
    
    # Ana sayfa için özel categoriler
    trending_designs = Design.objects.filter(status='published')
    latest_designs = Design.objects.filter(status='published').order_by('-created_at')[:12]
    
    if trending_designs.exists():
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        trending_designs = trending_designs.filter(created_at__gte=week_ago).annotate(
            engagement_score=F('likes_count') + F('views_count') + F('comments_count')
        ).order_by('-engagement_score')[:12]
        
        if not trending_designs:
            trending_designs = latest_designs[:12]
    
    context = {
        'title': 'triX Gallery',
        'designs': designs,
        'trending_designs': trending_designs,
        'latest_designs': latest_designs,
        'style_filter': style,
        'search_query': search,
        'sort_by': sort_by,
        'available_styles': Design.objects.filter(status='published').values_list('style', flat=True).distinct()
    }
    return render(request, 'gallery.html', context)

def contact(request):
    # Formspree handles email sending directly from frontend
    # This view handles success message display
    context = {
        'title': 'Contact triX - Send us a message'
    }
    
    # Check if form was successfully submitted via Formspree
    if request.GET.get('success') == '1':
        context['success_message'] = 'Message sent successfully! We\'ll get back to you soon.'
    
    return render(request, 'contact.html', context)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Ensure the user was saved properly
                user.refresh_from_db()
                logger.info(f"User {user.username} created successfully with ID: {user.id}")
                
                # Ensure profile is created
                profile, created = UserProfile.objects.get_or_create(user=user)
                if created:
                    logger.info(f"Profile created for user {user.username}")
                
                login(request, user)
                return redirect('core:home')
                
            except Exception as e:
                logger.error(f"Error creating user: {e}")
        else:
            # Log form errors for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    logger.error(f"Form error in {field}: {error}")
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    error_message = None
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request=request, username=username, password=password)
            
            if user is not None and user.is_active:
                login(request, user)
                # Başarılı giriş - redirect
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('core:home')
            else:
                error_message = "Kullanıcı adı veya şifre hatalı!"
        else:
            error_message = "Kullanıcı adı veya şifre hatalı!"
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/login.html', {
        'form': form,
        'error_message': error_message
    })

def logout_view(request):
    logout(request)
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
    
    # Check if current user is following this profile user
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(
            follower=request.user, 
            following=user
        ).exists()
    
    context = {
        'user': user,
        'designs': designs,
        'profile': profile,
        'is_following': is_following,
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
            
            return redirect('core:profile', username=user.username)
            
    except Exception as e:
        logger.error(f"Profile edit error: {e}")
    
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
            return redirect('core:design_detail', design_id=new_design.id)
    
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
        # Check if token is set
        api_token = os.environ.get('HUGGINGFACE_API_TOKEN')
        if not api_token:
            return JsonResponse({
                'success': False,
                'error': 'HUGGINGFACE_API_TOKEN environment variable not set',
                'suggestion': 'Please set HUGGINGFACE_API_TOKEN in your Render.com environment variables'
            })
        
        if not api_token.startswith('hf_'):
            return JsonResponse({
                'success': False,
                'error': 'Invalid HUGGINGFACE_API_TOKEN format',
                'suggestion': 'Token should start with "hf_" - please check your token'
            })

        headers = {
            "Authorization": f"Bearer {api_token}"
        }

        # Try the most common and accessible Stable Diffusion model
        api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        
        # Simple prompt for testing
        test_payload = {
            "inputs": "a cat",
            "parameters": {
                "num_inference_steps": 10,
                "guidance_scale": 7.5
            }
        }
        
        logger.info("Testing AI image generation with Stable Diffusion v1.5...")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=test_payload,
            timeout=60  # Longer timeout for image generation
        )
        
        logger.info(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if response contains image data
            if response.headers.get('content-type', '').startswith('image') or len(response.content) > 1000:
                return JsonResponse({
                    'success': True,
                    'message': '🎨 AI görüntü üretimi çalışıyor! Prompt ile görüntü oluşturabilirsiniz ✨',
                    'status_code': response.status_code,
                    'api_url': api_url,
                    'image_size': len(response.content),
                    'note': 'Stable Diffusion v1.5 modeli hazır!'
                })
            else:
                # Maybe it returned JSON with generated_text instead of image
                try:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return JsonResponse({
                            'success': True,
                            'message': 'AI modeli yanıt veriyor ancak görüntü formatı beklenmiyor',
                            'status_code': response.status_code,
                            'response_type': 'json',
                            'note': 'Model çalışıyor ama farklı format döndürüyor'
                        })
                except:
                    pass
                
                return JsonResponse({
                    'success': False,
                    'error': 'API yanıt verdi ancak görüntü verisi alınamadı',
                    'response_preview': response.text[:200],
                    'content_type': response.headers.get('content-type', 'unknown')
                })
                
        elif response.status_code == 503:
            return JsonResponse({
                'success': False,
                'error': '⏳ Model yükleniyor - bu normal! 1-2 dakika bekleyip tekrar deneyin',
                'status_code': response.status_code,
                'suggestion': 'İlk kullanımda modeller yüklenmesi 1-2 dakika sürebilir'
            })
            
        elif response.status_code == 401:
            return JsonResponse({
                'success': False,
                'error': '🔑 API token problemi - geçersiz veya süresi dolmuş',
                'status_code': response.status_code,
                'suggestion': 'Hugging Face token\'ınızı kontrol edin ve yenileyin'
            })
            
        elif response.status_code == 403:
            return JsonResponse({
                'success': False,
                'error': '⚠️ Token izninde problem - Write permission gerekebilir',
                'status_code': response.status_code,
                'suggestion': 'Hugging Face\'de token\'ı Write permission ile yeniden oluşturun'
            })
            
        elif response.status_code == 404:
            return JsonResponse({
                'success': False,
                'error': '❌ Model bulunamadı - farklı model deniyoruz',
                'status_code': response.status_code,
                'suggestion': 'Alternatif model deneyin veya daha sonra tekrar deneyin'
            })
            
        else:
            error_text = response.text[:200]
            return JsonResponse({
                'success': False,
                'error': f'API hatası. Status: {response.status_code}. Yanıt: {error_text}',
                'status_code': response.status_code,
                'suggestion': 'Token ve network bağlantısını kontrol edin'
            })
            
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': '⏰ Zaman aşımı - model yükleniyor olabilir',
            'suggestion': '1-2 dakika bekleyip tekrar deneyin'
        })
        
    except Exception as e:
        logger.error(f"AI model test failed: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Test hatası: {str(e)}',
            'suggestion': 'Network bağlantısını kontrol edin'
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

def test_urls(request):
    """Test URL reverse functionality"""
    output = []
    output.append("<h1>URL Test Page</h1>")
    
    try:
        # Test tasarım URL'leri
        designs = Design.objects.all()[:5]
        output.append(f"<h2>Found {designs.count()} designs:</h2>")
        output.append("<ul>")
        
        for design in designs:
            try:
                url = reverse('core:design_detail', kwargs={'design_id': design.id})
                output.append(f"<li>Design ID {design.id}: <a href='{url}'>{design.title}</a> - URL: {url}</li>")
            except Exception as e:
                output.append(f"<li>Design ID {design.id}: ERROR - {e}</li>")
        
        output.append("</ul>")
        
        # Test profile URL'leri  
        users = User.objects.all()[:3]
        output.append(f"<h2>Found {users.count()} users:</h2>")
        output.append("<ul>")
        
        for user in users:
            try:
                url = reverse('core:profile', kwargs={'username': user.username})
                output.append(f"<li>User {user.username}: <a href='{url}'>Profile</a> - URL: {url}</li>")
            except Exception as e:
                output.append(f"<li>User {user.username}: ERROR - {e}</li>")
        
        output.append("</ul>")
        
    except Exception as e:
        output.append(f"<p style='color: red;'>Error: {e}</p>")
    
    return HttpResponse("<br>".join(output))

@login_required(login_url='/login/')
@csrf_exempt
@require_http_methods(["POST"])
def generate_image_from_prompt(request):
    """
    Generate image from text prompt using Stable Diffusion
    """
    if not AI_AVAILABLE:
        return JsonResponse({
            'success': False,
            'error': 'AI functionality not available'
        })
    
    try:
        # Parse request data
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        style = data.get('style', 'digital art')
        
        if not prompt:
            return JsonResponse({
                'success': False,
                'error': 'Prompt boş olamaz'
            })
        
        # Check token
        api_token = os.environ.get('HUGGINGFACE_API_TOKEN')
        if not api_token:
            return JsonResponse({
                'success': False,
                'error': 'AI token yapılandırılmamış'
            })
        
        # Prepare full prompt with style
        if style and style != 'none':
            full_prompt = f"{prompt}, {style}, high quality, detailed"
        else:
            full_prompt = f"{prompt}, high quality, detailed"
        
        headers = {
            "Authorization": f"Bearer {api_token}"
        }
        
        # Use Stable Diffusion v1.5
        api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "num_inference_steps": 20,
                "guidance_scale": 7.5,
                "width": 512,
                "height": 512
            }
        }
        
        logger.info(f"Generating image with prompt: {full_prompt}")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=90  # Longer timeout for generation
        )
        
        if response.status_code == 200:
            # Save the generated image
            image_bytes = response.content
            if len(image_bytes) > 1000:  # Valid image
                # Create unique filename
                filename = f"ai_generated_{uuid.uuid4().hex[:8]}.png"
                file_path = f"media/designs/{filename}"
                
                # Save image to media folder
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Create Design object
                design = Design.objects.create(
                    title=f"AI: {prompt[:50]}{'...' if len(prompt) > 50 else ''}",
                    prompt=full_prompt,
                    style=style,
                    image=f"designs/{filename}",
                    user=request.user,
                    visibility='public'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Görüntü başarıyla oluşturuldu! 🎨',
                    'design_id': design.id,
                    'image_url': f"/media/designs/{filename}",
                    'prompt': prompt,
                    'full_prompt': full_prompt
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Geçersiz görüntü verisi alındı'
                })
                
        elif response.status_code == 503:
            return JsonResponse({
                'success': False,
                'error': 'Model yükleniyor, lütfen 1-2 dakika bekleyip tekrar deneyin',
                'status_code': response.status_code
            })
            
        elif response.status_code == 401:
            return JsonResponse({
                'success': False,
                'error': 'API token problemi',
                'status_code': response.status_code
            })
            
        elif response.status_code == 403:
            return JsonResponse({
                'success': False,
                'error': 'Token permission hatası - Write izni gerekebilir',
                'status_code': response.status_code
            })
            
        else:
            return JsonResponse({
                'success': False,
                'error': f'API hatası: {response.status_code}',
                'response': response.text[:200]
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Geçersiz JSON verisi'
        })
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Görüntü üretimi başarısız: {str(e)}'
        })


