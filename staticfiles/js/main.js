// Main JavaScript for triX - Enhanced with better loading animations

window.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded - initializing components');
    
    // TriX navbar'ı başlat
    initTrixNavbar();
    
    // Skills bölümünü başlat
    setupSkillsSection();
    
    // Diğer bileşenleri başlat
    initMobileMenu();
    initScrollAnimations();
    applyGlassEffects();
    initDynamicContent();
    createScrollProgressBar();
    initSmoothScroll();
    initTimelineAnimations();
    initScrollAnimationDemo(); // Scroll animasyon demosunu başlat
    
    // ThreeJS bileşenini başlat
    if (typeof THREE !== 'undefined') {
        initThreeJS();
    }
    
    // Ek bileşenler
    createParticles();
    preloadImages();
});

// TriX navbar'ı başlat
function initTrixNavbar() {
    console.log('Initializing trix navbar');
    const trixNavbar = document.querySelector('.trix-navbar');
    
    if (!trixNavbar) {
        console.error('TriX navbar element not found!');
        return;
    }
    
    // Get all navigation items
    const navItems = document.querySelectorAll('.trix-nav-item');
    
    // Add active class on click
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Remove active class from all items
            navItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            item.classList.add('active');
        });
    });
    
    // Set initial state
    let isScrolled = window.scrollY > 100;
    updateNavbarState(isScrolled);
    
    // Use requestAnimationFrame for smooth scroll handling
    let lastScrollY = window.scrollY;
    let ticking = false;
    
    window.addEventListener('scroll', () => {
        lastScrollY = window.scrollY;
        
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const shouldBeScrolled = lastScrollY > 100;
                
                if (isScrolled !== shouldBeScrolled) {
                    isScrolled = shouldBeScrolled;
                    updateNavbarState(isScrolled);
                }
                
                ticking = false;
            });
            
            ticking = true;
        }
    }, { passive: true });
    
    // Handle resize
    window.addEventListener('resize', () => {
        updateNavbarState(isScrolled);
    });
    
    // Update navbar state function with improved animation
    function updateNavbarState(scrolled) {
        // Don't add the transitioning class if it's already in the state we want
        const isCurrentlyScrolled = trixNavbar.classList.contains('scrolled');
        if (isCurrentlyScrolled === scrolled) return;
        
        // Add a class to prevent hover effects during transition
        trixNavbar.classList.add('transitioning');
        
        // Force a reflow to ensure CSS transitions work properly
        void trixNavbar.offsetWidth;
        
        if (scrolled) {
            // Scrolled state - expanded navbar
            trixNavbar.classList.add('scrolled');
        } else {
            // Top state - circular navbar
            trixNavbar.classList.remove('scrolled');
        }
        
        // Remove the transitioning class after animation completes
        setTimeout(() => {
            trixNavbar.classList.remove('transitioning');
        }, 600); // Slightly longer than the CSS transition duration for safety
    }
}

// Skills bölümünü ayarla ve ilerleme çubuklarını oluştur
function setupSkillsSection() {
    console.log('Setting up skills section');
    const skillsSection = document.querySelector('#skills');
    
    if (!skillsSection) {
        console.error('Skills section not found!');
        return;
    }
    
    console.log('Skills section found');
    
    // Mevcut içeriği temizle
    skillsSection.innerHTML = '';
    
    // Skills container oluştur
    const container = document.createElement('div');
    container.className = 'skills-container';
    
    // Skill verileri
    const skills = [
        { 
            name: '3D Modelleme', 
            percentage: 90,
            description: 'Karmaşık 3D nesneleri modelleme ve düzenleme'
        },
        { 
            name: 'Yapay Zeka', 
            percentage: 85,
            description: 'AI destekli 3D tasarım araçlarını kullanma'
        },
        { 
            name: 'UI/UX Tasarım', 
            percentage: 80,
            description: 'Kullanıcı arayüzü ve deneyimi tasarımı'
        },
        { 
            name: 'Görselleştirme', 
            percentage: 95,
            description: 'Gerçekçi render ve görselleştirme teknikleri'
        }
    ];
    
    // Her skill için bir kart oluştur
    skills.forEach((skill, index) => {
        const skillItem = document.createElement('div');
        skillItem.className = 'skill-item fade-in';
        
        skillItem.innerHTML = `
            <div class="flex justify-between mb-2">
                <div class="skill-name">${skill.name}</div>
                <div class="skill-value">${skill.percentage}%</div>
            </div>
            <div class="skill-bar">
                <div class="skill-progress" data-width="${skill.percentage}%" style="width: 0"></div>
            </div>
            <div class="skill-description">${skill.description}</div>
        `;
        
        container.appendChild(skillItem);
        
        // Gecikme ile animasyon ekle
        setTimeout(() => {
            const progressBar = skillItem.querySelector('.skill-progress');
            if (progressBar) {
                progressBar.style.width = `${skill.percentage}%`;
                console.log(`Setting progress width for ${skill.name}: ${skill.percentage}%`);
            }
        }, 500 + (index * 150));
    });
    
    // Skills container'ı skills section'a ekle
    skillsSection.appendChild(container);
    console.log('Skills container added with', skills.length, 'items');
    
    // Görünürlük gözlemcisi ekle
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                console.log('Skills section is now visible');
                
                // Tüm progress barları animasyonla doldur
                const progressBars = skillsSection.querySelectorAll('.skill-progress');
                progressBars.forEach((bar, index) => {
                    setTimeout(() => {
                        const targetWidth = bar.getAttribute('data-width');
                        bar.style.width = targetWidth;
                    }, 300 + (index * 150));
                });
                
                // Gözlemlemeyi durdur
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });
    
    // Skills section'ı gözlemle
    observer.observe(skillsSection);
}

// Initialize mobile menu toggle
function initMobileMenu() {
    const menuToggle = document.getElementById('menu-toggle');
    const menuClose = document.getElementById('menu-close');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuToggle && menuClose && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.remove('hidden');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
            
            // Animate menu items with staggered delay
            const menuItems = mobileMenu.querySelectorAll('a');
            menuItems.forEach((item, index) => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    item.style.transition = 'all 0.4s ease';
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, 100 + (index * 80));
            });
        });
        
        menuClose.addEventListener('click', () => {
            mobileMenu.classList.add('hidden');
            document.body.style.overflow = ''; // Restore scrolling
        });
    }
}

// Smooth scroll to section when clicking on navigation links
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Offset for navbar
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Create scroll progress bar that shows loading progress as user scrolls
function createScrollProgressBar() {
    // Create container
    const progressContainer = document.createElement('div');
    progressContainer.className = 'scroll-progress-container';
    
    // Create the progress bar
    const progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress-bar';
    
    // Add to DOM
    progressContainer.appendChild(progressBar);
    document.body.appendChild(progressContainer);
    
    // Update progress bar width on scroll
    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrollProgress = (scrollTop / scrollHeight) * 100;
        
        progressBar.style.width = `${scrollProgress}%`;
        
        // Load more content when near bottom of page
        if (scrollProgress > 70) {
            document.querySelectorAll('.dynamic-content-container:not(.loaded)').forEach(container => {
                if (!container.classList.contains('loading')) {
                    loadDynamicContent(container);
                    container.classList.add('loaded');
                }
            });
        }
    });
}

// Initialize scroll-based animations
function initScrollAnimations() {
    // Animate navbar on scroll
    const navbar = document.querySelector('.curved-navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    // Change background based on scroll position
    function updateBackgroundBasedOnScroll() {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrollPercentage = (scrollTop / height) * 100;
        
        // Remove all scroll classes first
        document.body.classList.remove('scroll-1', 'scroll-2', 'scroll-3', 'scroll-4', 'scroll-5');
        
        // Add appropriate class based on scroll position
        if (scrollPercentage < 20) {
            document.body.classList.add('scroll-1');
        } else if (scrollPercentage < 40) {
            document.body.classList.add('scroll-2');
        } else if (scrollPercentage < 60) {
            document.body.classList.add('scroll-3');
        } else if (scrollPercentage < 80) {
            document.body.classList.add('scroll-4');
        } else {
            document.body.classList.add('scroll-5');
        }
    }
    
    // Initial call to set initial background
    updateBackgroundBasedOnScroll();
    
    // Add event listener for scroll
    window.addEventListener('scroll', updateBackgroundBasedOnScroll);
    
    // Create intersection observer for fade-in elements
    const fadeInObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                
                // Add special animation for cards
                if (entry.target.classList.contains('glass-card')) {
                    entry.target.style.animationDelay = entry.target.dataset.delay || '0s';
                    entry.target.classList.add('animate-in');
                }
                
                // Stop observing after animation
                fadeInObserver.unobserve(entry.target);
            }
        });
    }, { 
        threshold: 0.15,
        rootMargin: '0px 0px -10% 0px' // Trigger a bit earlier
    });
    
    // Observe all fade-in elements with staggered delay
    document.querySelectorAll('.fade-in').forEach((el, index) => {
        // Add staggered delay for siblings
        const parent = el.parentElement;
        const siblings = Array.from(parent.children).filter(child => 
            child.classList.contains('fade-in')
        );
        
        const siblingIndex = siblings.indexOf(el);
        if (siblingIndex !== -1) {
            el.dataset.delay = `${siblingIndex * 0.15}s`;
        }
        
        fadeInObserver.observe(el);
    });
    
    // Initialize reveal animations
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.reveal-animation').forEach(el => {
        revealObserver.observe(el);
    });
}

// Initialize timeline animations
function initTimelineAnimations() {
    const timelineObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Delay animation based on timeline item number
                const itemNumber = parseInt(entry.target.id.split('-')[1]) || 1;
                
                setTimeout(() => {
                    entry.target.classList.add('visible');
                    
                    // Animate the number with a shiny effect
                    const numberEl = entry.target.querySelector('.timeline-number');
                    if (numberEl) {
                        numberEl.classList.add('pulse-animation');
                    }
                    
                    // If this is the last timeline item observed
                    if (itemNumber === document.querySelectorAll('.timeline-item').length) {
                        const timelineTrack = document.querySelector('.timeline-track');
                        if (timelineTrack) {
                            timelineTrack.classList.add('timeline-track-complete');
                        }
                    }
                }, (itemNumber - 1) * 600);
            }
        });
    }, { 
        threshold: 0.2,
        rootMargin: '0px 0px -10% 0px'
    });
    
    document.querySelectorAll('.timeline-item').forEach(item => {
        timelineObserver.observe(item);
    });
}

// Apply glass effects to elements
function applyGlassEffects() {
    // Add diamond shine effect to cards
    document.querySelectorAll('.glass-card').forEach(card => {
        card.classList.add('diamond-shine');
        
        // Add mouse-follow shine effect
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left; // x position within the element
            const y = e.clientY - rect.top; // y position within the element
            
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
            card.classList.add('mouse-hover');
        });
        
        card.addEventListener('mouseleave', () => {
            card.classList.remove('mouse-hover');
        });
    });
    
    // Add floating animation to elements
    document.querySelectorAll('.hero h1, .webgl-container, .btn').forEach((el, index) => {
        el.classList.add('floating');
        el.style.animationDelay = `${index * 0.2}s`;
    });
    
    // Initialize 3D card effect if library exists
    if (typeof VanillaTilt !== 'undefined') {
        VanillaTilt.init(document.querySelectorAll('.card-3d'), {
            max: 8,
            speed: 400,
            glare: true,
            "max-glare": 0.3,
            scale: 1.03
        });
    }
}

// Handle dynamic content loading with beautiful animations
function initDynamicContent() {
    // Load content when container enters viewport
    const contentObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.classList.contains('loaded')) {
                loadDynamicContent(entry.target);
                entry.target.classList.add('loaded');
                contentObserver.unobserve(entry.target);
            }
        });
    }, { 
        threshold: 0.1,
        rootMargin: '0px 0px 200px 0px' // Load earlier for smoother experience
    });
    
    // Observe all dynamic content containers
    document.querySelectorAll('.dynamic-content-container').forEach(container => {
        contentObserver.observe(container);
    });
}

// Load dynamic content with animation
function loadDynamicContent(container) {
    // Add loading animation
    container.classList.add('loading');
    
    // Create progress bar to show loading progress
    const progressBar = document.createElement('div');
    progressBar.className = 'load-more-progress';
    container.appendChild(progressBar);
    
    // Simulate loading delay (remove in production and replace with actual API call)
    setTimeout(() => {
        // Create content items - in production, this would be fetched from an API
        const projects = [
            {
                title: '3D Modelleme Sanatı',
                description: 'Kompleks geometrilerle oluşturulmuş yaratıcı 3D model tasarımı.',
                image: '/static/images/project1.jpg',
                categories: ['3D Model', 'Tasarım']
            },
            {
                title: 'Dijital Mimari',
                description: 'Yapay zeka destekli mimari tasarım ve 3D modelleme projesi.',
                image: '/static/images/project2.jpg',
                categories: ['Mimari', 'AI']
            },
            {
                title: 'Kristal Dünyalar',
                description: 'Şeffaf ve parlak yüzeylerle oluşturulmuş fantastik ortamlar.',
                image: '/static/images/project3.jpg',
                categories: ['Görselleştirme', 'Sanat']
            }
        ];
        
        // Remove loading state
        container.classList.remove('loading');
        container.innerHTML = '';
        
        // Create grid for items
        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 md:grid-cols-3 gap-8';
        container.appendChild(grid);
        
        // Add items with staggered animation
        projects.forEach((project, index) => {
            const card = createProjectCard(project, index);
            grid.appendChild(card);
        });
        
        // Add load more button
        setTimeout(() => {
            const loadMoreBtn = document.createElement('div');
            loadMoreBtn.className = 'text-center mt-12';
            loadMoreBtn.innerHTML = `
                <button class="btn py-3 px-8 glass diamond-shine rounded-full font-medium">
                    Daha Fazla Göster
                </button>
            `;
            
            loadMoreBtn.querySelector('button').addEventListener('click', () => {
                // Add loading progress bar when button is clicked
                const progressBar = document.createElement('div');
                progressBar.className = 'load-more-progress';
                loadMoreBtn.appendChild(progressBar);
                
                // Disable button during loading
                const button = loadMoreBtn.querySelector('button');
                button.disabled = true;
                button.textContent = 'Yükleniyor...';
                
                // Simulate loading delay
                setTimeout(() => {
                    loadMoreProjects(grid);
                    // Remove progress bar and restore button
                    progressBar.remove();
                    button.disabled = false;
                    button.textContent = 'Daha Fazla Göster';
                }, 1500);
            });
            
            container.appendChild(loadMoreBtn);
        }, 500);
    }, 800);
}

// Create a project card with image and details
function createProjectCard(project, index) {
    const card = document.createElement('div');
    card.className = 'glass-card fade-in card-3d overflow-hidden';
    card.style.opacity = '0';
    card.style.transform = 'translateY(40px)';
    
    // Create placeholder for image to avoid layout shift
    const imageHtml = project.image ? 
        `<img src="${project.image}" alt="${project.title}" class="w-full h-56 object-cover transition-transform hover:scale-105">` :
        `<div class="w-full h-56 bg-gradient-to-br from-purple-600/30 to-pink-600/30 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
        </div>`;
    
    // Create categories badges
    const categoriesHtml = project.categories ? 
        project.categories.map(cat => `<span class="inline-block bg-purple-600/20 rounded-full px-3 py-1 text-sm text-white mr-2">${cat}</span>`).join('') :
        '';
    
    card.innerHTML = `
        <div class="overflow-hidden">
            ${imageHtml}
        </div>
        <div class="p-6">
            <div class="flex items-center justify-between mb-3">
                <h3 class="text-xl font-bold gradient-text">${project.title}</h3>
                <div class="flex space-x-1">
                    <span class="w-2 h-2 rounded-full bg-purple-500"></span>
                    <span class="w-2 h-2 rounded-full bg-indigo-500"></span>
                    <span class="w-2 h-2 rounded-full bg-pink-500"></span>
                </div>
            </div>
            <div class="gradient-divider"></div>
            <p class="text-gray-600 mb-4">${project.description}</p>
            <div class="flex flex-wrap mt-4">
                ${categoriesHtml}
            </div>
        </div>
    `;
    
    // Animate in with staggered delay
    setTimeout(() => {
        card.style.transition = 'all 0.6s cubic-bezier(0.22, 1, 0.36, 1)';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
    }, 100 + (index * 150));
    
    return card;
}

// Load more projects when "load more" is clicked
function loadMoreProjects(container) {
    // New projects to load - in production, fetch from API
    const moreProjects = [
        {
            title: 'Elmas Mühendisliği',
            description: 'Parlak yüzeylerin simülasyonu ve ışık etkileşimi çalışması.',
            image: '/static/images/project4.jpg',
            categories: ['Simülasyon', 'Işık']
        },
        {
            title: 'Organik Formlar',
            description: 'Doğadan ilham alan organik 3D form tasarımları ve analizleri.',
            image: '/static/images/project5.jpg', 
            categories: ['Organik', 'Tasarım']
        },
        {
            title: 'Dijital Mücevher',
            description: 'Dijital ortamda oluşturulmuş detaylı mücevher tasarımları.',
            image: '/static/images/project6.jpg',
            categories: ['Mücevher', 'Detay']
        }
    ];
    
    // Add items with staggered animation
    moreProjects.forEach((project, index) => {
        const card = createProjectCard(project, index);
        container.appendChild(card);
    });
}

// Initialize 3D scene with Three.js
function initThreeJS() {
    // Check if container exists
    const container = document.getElementById('webgl-container');
    if (!container) return;

    // Set up scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true 
    });

    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2);
    directionalLight.position.set(1, 2, 3);
    scene.add(directionalLight);

    // Add point lights for color
    const purpleLight = new THREE.PointLight(0x9333ea, 2, 10);
    purpleLight.position.set(2, 1, 2);
    scene.add(purpleLight);

    const pinkLight = new THREE.PointLight(0xec4899, 2, 10);
    pinkLight.position.set(-2, -1, -2);
    scene.add(pinkLight);

    const blueLight = new THREE.PointLight(0x06b6d4, 2, 10);
    blueLight.position.set(0, 2, -3);
    scene.add(blueLight);

    // Create a group for the 3D object
    const objectGroup = new THREE.Group();
    scene.add(objectGroup);
    
    // Create a stylized 3D avatar instead of gem
    create3DAvatar();
    
    // Create triX text with handwriting animation
    createTriXText();
    
    // Position camera
    camera.position.z = 5;
    camera.position.y = 1.2;

    // Animation loop
    const clock = new THREE.Clock();

    function animate() {
        const elapsedTime = clock.getElapsedTime();
        
        // Rotate the avatar slowly
        objectGroup.rotation.y = Math.sin(elapsedTime * 0.2) * 0.2 + 0.3;
        
        // Make the avatar float up and down slightly
        objectGroup.position.y = Math.sin(elapsedTime * 0.5) * 0.2;
        
        // Animate crystals and other elements
        objectGroup.children.forEach(child => {
            if (child.userData && child.userData.radius) {
                // This is a crystal or particle
                const userData = child.userData;
                
                // Update angle for orbital movement
                userData.angle += userData.speed * 0.01;
                
                // Calculate new position
                child.position.x = Math.cos(userData.angle) * userData.radius;
                child.position.z = Math.sin(userData.angle) * userData.radius;
                
                // Add a slight vertical bounce
                child.position.y = userData.initialY + Math.sin(elapsedTime * userData.verticalSpeed) * 0.1;
                
                // Rotate the crystal
                child.rotation.x += userData.rotationSpeed.x;
                child.rotation.y += userData.rotationSpeed.y;
                child.rotation.z += userData.rotationSpeed.z;
            }
            
            // Animate sparkles
            if (child.geometry && child.geometry.type === 'SphereGeometry' && child.geometry.parameters.radius < 0.1) {
                child.position.y = child.userData.initialY + Math.sin(elapsedTime * child.userData.floatSpeed) * 0.1;
                
                // Pulse opacity
                if (child.material) {
                    child.material.opacity = 0.5 + Math.sin(elapsedTime * 2 + child.userData.angle) * 0.3;
                }
                
                // Move in small circles
                const sparkleAngle = elapsedTime * 0.5 + child.userData.angle;
                child.position.x += Math.cos(sparkleAngle) * 0.002;
                child.position.z += Math.sin(sparkleAngle) * 0.002;
            }
        });
        
        // Move lights in circular pattern
        purpleLight.position.x = Math.sin(elapsedTime * 0.3) * 3;
        purpleLight.position.z = Math.cos(elapsedTime * 0.3) * 3;
        
        pinkLight.position.x = Math.sin(elapsedTime * 0.4 + Math.PI) * 3;
        pinkLight.position.z = Math.cos(elapsedTime * 0.4 + Math.PI) * 3;
        
        blueLight.position.x = Math.sin(elapsedTime * 0.5 + Math.PI / 2) * 3;
        blueLight.position.z = Math.cos(elapsedTime * 0.5 + Math.PI / 2) * 3;
        
        renderer.render(scene, camera);
        requestAnimationFrame(animate);
    }
    
    animate();
    
    // Mouse interaction - make the avatar follow the mouse slightly
    document.addEventListener('mousemove', (event) => {
        const x = (event.clientX / window.innerWidth) - 0.5;
        const y = (event.clientY / window.innerHeight) - 0.5;
        
        // Make object turn slightly to follow mouse
        const targetRotationY = x * 0.5 + 0.3;
        const targetRotationX = -y * 0.3 - 0.2;
        
        // Apply with damping for smooth movement
        objectGroup.rotation.y += (targetRotationY - objectGroup.rotation.y) * 0.05;
        objectGroup.rotation.x += (targetRotationX - objectGroup.rotation.x) * 0.05;
    });
    
    // Handle resize
    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
    
    function createTriXText() {
        // Create a simple 3D text for "triX"
        const textMaterial = new THREE.MeshPhongMaterial({
            color: 0xff33cc,
            emissive: 0xff33cc,
            emissiveIntensity: 0.5,
            specular: 0xffffff,
            shininess: 100
        });
        
        // Load font and create text
        const loader = new THREE.FontLoader();
        
        // Create a simple placeholder text while font loads
        const geometry = new THREE.PlaneGeometry(2, 0.5);
        const material = new THREE.MeshBasicMaterial({
            color: 0xff33cc,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
        });
        
        const textMesh = new THREE.Mesh(geometry, material);
        textMesh.position.set(0, 1.5, 0);
        objectGroup.add(textMesh);
        
        // Create sparkles around the text
        for (let i = 0; i < 20; i++) {
            const sparkle = new THREE.Mesh(
                new THREE.SphereGeometry(0.03 + Math.random() * 0.02, 8, 8),
                new THREE.MeshBasicMaterial({
                    color: 0xff33cc,
                    transparent: true,
                    opacity: 0.7,
                    blending: THREE.AdditiveBlending
                })
            );
            
            const angle = Math.random() * Math.PI * 2;
            const radius = 0.5 + Math.random() * 1;
            sparkle.position.set(
                Math.cos(angle) * radius,
                1.5 + (Math.random() - 0.5) * 0.5,
                Math.sin(angle) * radius
            );
            
            sparkle.userData = {
                initialY: sparkle.position.y,
                floatSpeed: 0.5 + Math.random() * 1,
                angle: Math.random() * Math.PI * 2,
                radius: 0.1 + Math.random() * 0.2,
                rotationSpeed: {
                    x: (Math.random() - 0.5) * 0.02,
                    y: (Math.random() - 0.5) * 0.02,
                    z: (Math.random() - 0.5) * 0.02
                }
            };
            
            objectGroup.add(sparkle);
        }
        
        // Create a canvas for the text
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 128;
        const ctx = canvas.getContext('2d');
        
        // Draw text on canvas
        ctx.fillStyle = 'transparent';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.font = 'bold 80px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#FF3366');
        gradient.addColorStop(0.5, '#9933FF');
        gradient.addColorStop(1, '#33CCFF');
        
        ctx.fillStyle = gradient;
        ctx.fillText('triX', canvas.width / 2, canvas.height / 2);
        
        // Add glow
        ctx.shadowColor = '#FF33CC';
        ctx.shadowBlur = 15;
        ctx.fillText('triX', canvas.width / 2, canvas.height / 2);
        
        // Create texture from canvas
        const texture = new THREE.CanvasTexture(canvas);
        
        // Create a plane with the texture
        const textPlane = new THREE.Mesh(
            new THREE.PlaneGeometry(2, 1),
            new THREE.MeshBasicMaterial({
                map: texture,
                transparent: true,
                side: THREE.DoubleSide,
                blending: THREE.AdditiveBlending
            })
        );
        
        textPlane.position.set(0, 1.5, 0);
        objectGroup.add(textPlane);
    }
    
    function create3DAvatar() {
        // Avatar materials with glossy appearance
        const purpleMaterial = new THREE.MeshPhysicalMaterial({
            color: 0x9333ea,
            metalness: 0.2,
            roughness: 0.3,
            transparent: true,
            opacity: 0.9
        });
        
        const pinkMaterial = new THREE.MeshPhysicalMaterial({
            color: 0xec4899,
            metalness: 0.3,
            roughness: 0.3,
            transparent: true,
            opacity: 0.9
        });
        
        const blueMaterial = new THREE.MeshPhysicalMaterial({
            color: 0x06b6d4,
            metalness: 0.25,
            roughness: 0.3,
            transparent: true,
            opacity: 0.9
        });
        
        const whiteMaterial = new THREE.MeshPhysicalMaterial({
            color: 0xffffff,
            metalness: 0.3,
            roughness: 0.2,
            transparent: true,
            opacity: 0.95
        });
        
        // Create head
        const head = new THREE.Mesh(
            new THREE.SphereGeometry(0.8, 32, 32),
            whiteMaterial
        );
        head.position.y = 1.2;
        objectGroup.add(head);
        
        // Create eyes
        const leftEye = new THREE.Mesh(
            new THREE.SphereGeometry(0.12, 16, 16),
            purpleMaterial
        );
        leftEye.position.set(-0.25, 1.3, 0.65);
        objectGroup.add(leftEye);
        
        const rightEye = new THREE.Mesh(
            new THREE.SphereGeometry(0.12, 16, 16),
            purpleMaterial
        );
        rightEye.position.set(0.25, 1.3, 0.65);
        objectGroup.add(rightEye);
        
        // Create body
        const body = new THREE.Mesh(
            new THREE.CylinderGeometry(0.7, 0.5, 1.5, 32),
            pinkMaterial
        );
        body.position.y = 0;
        objectGroup.add(body);
        
        // Create arms
        const leftArm = new THREE.Mesh(
            new THREE.CapsuleGeometry(0.2, 0.7, 8, 8),
            blueMaterial
        );
        leftArm.position.set(-0.9, 0.2, 0);
        leftArm.rotation.z = Math.PI / 6;
        objectGroup.add(leftArm);
        
        const rightArm = new THREE.Mesh(
            new THREE.CapsuleGeometry(0.2, 0.7, 8, 8),
            blueMaterial
        );
        rightArm.position.set(0.9, 0.2, 0);
        rightArm.rotation.z = -Math.PI / 6;
        objectGroup.add(rightArm);
        
        // Create an ice crystal halo around the avatar
        const haloParticleCount = 30;
        
        for (let i = 0; i < haloParticleCount; i++) {
            const angle = (i / haloParticleCount) * Math.PI * 2;
            const radius = 1.5 + Math.random() * 0.5;
            const height = 0.5 + Math.random() * 1.5;
            
            const crystalGeometry = new THREE.TetrahedronGeometry(0.1 + Math.random() * 0.15, 0);
            const crystalMaterial = i % 3 === 0 ? purpleMaterial : i % 3 === 1 ? pinkMaterial : blueMaterial;
            
            const crystal = new THREE.Mesh(crystalGeometry, crystalMaterial);
            crystal.position.x = Math.cos(angle) * radius;
            crystal.position.y = height;
            crystal.position.z = Math.sin(angle) * radius;
            crystal.rotation.x = Math.random() * Math.PI;
            crystal.rotation.z = Math.random() * Math.PI;
            
            // Add animation data
            crystal.userData = {
                initialX: crystal.position.x,
                initialZ: crystal.position.z,
                initialY: crystal.position.y,
                radius: radius,
                angle: angle,
                speed: 0.2 + Math.random() * 0.3,
                verticalSpeed: 0.5 + Math.random() * 0.5,
                rotationSpeed: {
                    x: (Math.random() - 0.5) * 0.02,
                    y: (Math.random() - 0.5) * 0.02,
                    z: (Math.random() - 0.5) * 0.02
                }
            };
            
            objectGroup.add(crystal);
        }
        
        // Add a circular platform beneath the avatar
        const platform = new THREE.Mesh(
            new THREE.CylinderGeometry(1.2, 1.2, 0.1, 32),
            new THREE.MeshPhysicalMaterial({
                color: 0xffffff,
                metalness: 0.5,
                roughness: 0.1,
                transparent: true,
                opacity: 0.7
            })
        );
        platform.position.y = -0.8;
        objectGroup.add(platform);
        
        // Position avatar
        objectGroup.rotation.x = -0.2;
        objectGroup.rotation.y = 0.3;
    }
}

// Create animated particles
function createParticles() {
    const footer = document.querySelector('footer');
    if (!footer) return;
    
    // Create container for particles
    const particleContainer = document.createElement('div');
    particleContainer.className = 'absolute inset-0 pointer-events-none overflow-hidden';
    
    // Create particles (fewer for lighter animation)
    for (let i = 0; i < 6; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Random position
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        
        // Random size (smaller for lighter effect)
        const size = Math.random() * 60 + 20;
        
        // Apply styles
        particle.style.left = `${x}%`;
        particle.style.top = `${y}%`;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        
        // Random animation delay
        particle.style.animationDelay = `${i * 0.8}s`;
        
        particleContainer.appendChild(particle);
    }
    
    footer.appendChild(particleContainer);
}

// Preload images for smoother experience
function preloadImages() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        // Add loading state
        img.classList.add('image-loading');
        
        const src = img.getAttribute('src');
        if (src) {
            const newImg = new Image();
            newImg.onload = () => {
                // Remove loading state when image is loaded
                img.classList.remove('image-loading');
            };
            newImg.src = src;
        }
    });
}

// Scroll animasyon demosunu başlat
function initScrollAnimationDemo() {
    console.log('Initializing scroll animation demo');
    const scrollAnimationDemo = document.getElementById('scroll-animation-demo');
    
    if (!scrollAnimationDemo) {
        console.error('Scroll animation demo container not found!');
        return;
    }
    
    // Başlık içeriği
    const titleHtml = `
        <h1 class="text-4xl font-semibold text-black dark:text-white">
            triX ile oluşturuldu <br />
        </h1>
    `;
    
    // İçerik - bir görsel ekleyelim
    const contentHtml = `
        <img 
            src="static/images/madesign1.png" 
            alt="3D Design" 
            class="mx-auto rounded-2xl object-cover h-full object-center"
            draggable="false"
        />
    `;
    
    // Scroll animasyonu oluştur
    createScrollAnimation('scroll-animation-demo', titleHtml, contentHtml);
} 