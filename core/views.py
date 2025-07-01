from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile, Design
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
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
    # Son eklenen 6 tasarımı göster
    latest_designs = Design.objects.filter(status='published').order_by('-created_at')[:6]
    
    context = {
        'title': 'triX - Creativity Platform',
        'latest_designs': latest_designs,
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
    
    designs = Design.objects.filter(status='published')
    
    if style:
        designs = designs.filter(style=style)
    
    if search:
        designs = designs.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(prompt__icontains=search)
        )
    
    context = {
        'title': 'triX Gallery',
        'designs': designs,
        'style_filter': style,
        'search_query': search,
    }
    return render(request, 'gallery.html', context)

def contact(request):
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
    
    # Kullanıcının kendi profili ise veya tasarım yayınladıysa göster
    if request.user == user:
        designs = Design.objects.filter(user=user)
    else:
        designs = Design.objects.filter(user=user, status='published')
    
    context = {
        'user': user,
        'designs': designs,
    }
    return render(request, 'auth/profile.html', context)

@login_required(login_url='/login/')
def profile_edit(request):
    if request.method == 'POST':
        # Kullanıcı bilgilerini güncelle
        user = request.user
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        
        # Profil bilgilerini güncelle
        profile = user.profile
        profile.bio = request.POST.get('bio')
        profile.website = request.POST.get('website')
        
        # Avatar işleme
        if 'avatar' in request.FILES:
            if profile.avatar:
                # Eski avatarı sil
                if os.path.isfile(profile.avatar.path):
                    os.remove(profile.avatar.path)
            profile.avatar = request.FILES['avatar']
        
        # Avatar silme işlemi
        if request.POST.get('remove_avatar') == 'on' and profile.avatar:
            if os.path.isfile(profile.avatar.path):
                os.remove(profile.avatar.path)
            profile.avatar = None
        
        profile.save()
        
        messages.success(request, "Profil başarıyla güncellendi!")
        return redirect('core:profile', username=user.username)
    
    return render(request, 'auth/profile_edit.html', {'user': request.user})

@login_required(login_url='/login/')
def design_detail(request, design_id):
    design = get_object_or_404(Design, id=design_id)
    
    # Eğer tasarım yayınlanmadıysa ve mevcut kullanıcı sahibi değilse erişimi engelle
    if design.status != 'published' and request.user != design.user:
        return HttpResponseForbidden("Bu tasarımı görüntüleme izniniz yok.")
    
    # Benzer tasarımları bul
    related_designs = Design.objects.filter(
        status='published', 
        style=design.style
    ).exclude(id=design.id)[:4]
    
    context = {
        'design': design,
        'related_designs': related_designs,
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
