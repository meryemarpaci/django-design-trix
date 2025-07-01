// Main JavaScript for triX - Enhanced with better loading animations

window.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded - initializing components');
    
    // Orb menüyü başlat
    initOrbMenu();
    
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
    
    // ThreeJS bileşenini başlat
    if (typeof THREE !== 'undefined') {
        initThreeJS();
    }
    
    // Ek bileşenler
    createParticles();
    preloadImages();
});

// Orb menüyü başlat
function initOrbMenu() {
    console.log('Initializing orb menu');
    const orbMenu = document.getElementById('orb-menu');
    
    if (!orbMenu) {
        console.error('Orb menu element not found!');
        return;
    }
    
    console.log('Orb menu found:', orbMenu);
    
    // Başlangıç durumunu ayarla - orb menu görünür hale getir
    setTimeout(() => {
        orbMenu.style.transform = 'translateY(-55px)';
        console.log('Initial transform applied to orb menu');
    }, 100);
    
    // Toggle düğmesini ayarla
    const orbToggle = document.getElementById('orb-toggle');
    if (orbToggle) {
        console.log('Orb toggle found');
        
        orbToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Orb toggle clicked');
            orbMenu.classList.toggle('open');
        });
    } else {
        console.error('Orb toggle not found!');
    }
    
    // Hover işlevselliği ekle
    orbMenu.addEventListener('mouseenter', () => {
        console.log('Mouse entered orb menu');
        orbMenu.classList.add('open');
    });
    
    orbMenu.addEventListener('mouseleave', () => {
        console.log('Mouse left orb menu');
        orbMenu.classList.remove('open');
    });
    

    orbNavItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            item.style.transform = 'translateY(-5px) scale(1.1)';
            item.style.boxShadow = 'var(--ice-glow)';
        });
        
        item.addEventListener('mouseleave', () => {
            item.style.transform = '';
            item.style.boxShadow = '';
        });
    });
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

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(2, 2, 2);
    scene.add(directionalLight);

    // Add point lights for color
    const purpleLight = new THREE.PointLight(0x9333ea, 1, 10);
    purpleLight.position.set(2, 2, 2);
    scene.add(purpleLight);

    const pinkLight = new THREE.PointLight(0xec4899, 1, 10);
    pinkLight.position.set(-2, -2, -2);
    scene.add(pinkLight);

    // Create main geometric shape
    const geometry = new THREE.TorusKnotGeometry(1, 0.4, 64, 16);
    const material = new THREE.MeshStandardMaterial({
        color: 0x9333ea,
        metalness: 0.8,
        roughness: 0.2,
        emissive: 0x330066,
        emissiveIntensity: 0.1
    });

    const torusKnot = new THREE.Mesh(geometry, material);
    scene.add(torusKnot);

    // Add small floating elements
    const smallGeometries = [
        new THREE.TetrahedronGeometry(0.2),
        new THREE.OctahedronGeometry(0.2),
        new THREE.IcosahedronGeometry(0.2)
    ];

    const smallGroup = new THREE.Group();
    
    for (let i = 0; i < 6; i++) {
        const geometry = smallGeometries[Math.floor(Math.random() * smallGeometries.length)];
        const material = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            metalness: 0.8,
            roughness: 0.2
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        
        // Position around the torus knot
        const angle = Math.random() * Math.PI * 2;
        const radius = 2 + Math.random();
        mesh.position.x = Math.cos(angle) * radius;
        mesh.position.z = Math.sin(angle) * radius;
        mesh.position.y = (Math.random() - 0.5) * 2;
        
        smallGroup.add(mesh);
    }
    
    scene.add(smallGroup);

    // Position camera
    camera.position.z = 4;

    // Animation loop
    const clock = new THREE.Clock();

    function animate() {
        const elapsedTime = clock.getElapsedTime();
        
        // Rotate the torus knot (slower for lighter animation)
        torusKnot.rotation.x = elapsedTime * 0.2;
        torusKnot.rotation.y = elapsedTime * 0.3;
        
        // Move lights
        purpleLight.position.x = Math.sin(elapsedTime * 0.3) * 3;
        purpleLight.position.z = Math.cos(elapsedTime * 0.3) * 3;
        
        pinkLight.position.x = Math.sin(elapsedTime * 0.3 + Math.PI) * 3;
        pinkLight.position.z = Math.cos(elapsedTime * 0.3 + Math.PI) * 3;
        
        // Rotate small objects (slower for lighter animation)
        smallGroup.children.forEach((obj, i) => {
            const speed = 0.1 + (i * 0.03);
            const radius = 2 + (i * 0.2);
            
            obj.position.x = Math.cos(elapsedTime * speed) * radius;
            obj.position.z = Math.sin(elapsedTime * speed) * radius;
            
            obj.rotation.x += 0.005;
            obj.rotation.y += 0.005;
        });
        
        renderer.render(scene, camera);
        requestAnimationFrame(animate);
    }
    
    animate();
    
    // Mouse interaction (reduced sensitivity for lighter effect)
    document.addEventListener('mousemove', (event) => {
        const x = (event.clientX / window.innerWidth) - 0.5;
        const y = (event.clientY / window.innerHeight) - 0.5;
        
        torusKnot.rotation.x += y * 0.005;
        torusKnot.rotation.y += x * 0.005;
    });
    
    // Handle resize
    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
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