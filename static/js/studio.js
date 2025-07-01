// Studio page functionality
document.addEventListener('DOMContentLoaded', () => {
    console.log('Studio page loaded');
    
    // Initialize studio components
    initToolSwitching();
    initStyleChips();
    initRangeInputs();
    setupGenerateButton();
    animateStudioElements();
    initRandomSeed();
});

// Initialize tool switching
function initToolSwitching() {
    const toolItems = document.querySelectorAll('.tool-item');
    const toolContents = document.querySelectorAll('.tool-content');
    
    toolItems.forEach(item => {
        item.addEventListener('click', () => {
            const toolId = item.getAttribute('data-tool');
            let targetContent;
            
            // Map tool IDs to content IDs
            if (toolId === 'text-to-image') {
                targetContent = document.getElementById('text-to-image-content');
            } else if (toolId === 'inpainting') {
                targetContent = document.getElementById('inpainting-content');
            }
            
            if (!targetContent) return;
            
            // Remove active class from all items and contents
            toolItems.forEach(t => t.classList.remove('active'));
            toolContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked item and corresponding content
            item.classList.add('active');
            targetContent.classList.add('active');
            
            // Reinitialize inpainting app if switching to inpainting tool
            if (toolId === 'inpainting' && window.inpaintingApp) {
                // Reinitialize canvas if needed
                setTimeout(() => {
                    if (window.inpaintingApp.setupCanvas) {
                        window.inpaintingApp.setupCanvas();
                    }
                }, 100);
            }
        });
    });
}

// Initialize style chip selection
function initStyleChips() {
    const styleChips = document.querySelectorAll('.style-chip');
    const promptInput = document.getElementById('prompt');
    
    styleChips.forEach(chip => {
        chip.addEventListener('click', () => {
            // Toggle active state
            chip.classList.toggle('active');
            
            // Update prompt with selected styles
            updatePromptWithStyles();
        });
    });
    
    function updatePromptWithStyles() {
        const activeChips = document.querySelectorAll('.style-chip.active');
        let styleText = '';
        
        if (activeChips.length > 0) {
            const styles = Array.from(activeChips).map(chip => chip.getAttribute('data-style'));
            styleText = `, Style: ${styles.join(', ')}`;
        }
        
        // Get current prompt text without previous style
        let currentPrompt = promptInput.value;
        if (currentPrompt.includes(', Style:')) {
            currentPrompt = currentPrompt.substring(0, currentPrompt.indexOf(', Style:'));
        }
        
        // Add new style text if there are active chips
        if (styleText) {
            promptInput.value = currentPrompt + styleText;
        } else {
            promptInput.value = currentPrompt;
        }
    }
}

// Initialize range inputs with value display
function initRangeInputs() {
    const rangeInputs = document.querySelectorAll('.studio-range');
    
    rangeInputs.forEach(input => {
        const valueDisplay = input.nextElementSibling;
        
        // Set initial value
        if (valueDisplay && valueDisplay.classList.contains('range-value')) {
            valueDisplay.textContent = input.value;
        }
        
        // Update value on change
        input.addEventListener('input', () => {
            if (valueDisplay) {
                valueDisplay.textContent = input.value;
            }
        });
    });
}

// Setup generate button
function setupGenerateButton() {
    const generateBtn = document.getElementById('generate-btn');
    const outputContainer = document.querySelector('.output-container');
    const outputPlaceholder = document.querySelector('.output-placeholder');
    const outputLoading = document.querySelector('.output-loading');
    const generatedImage = document.getElementById('generated-image');
    const outputActions = document.querySelector('.output-actions');
    const progressFill = document.querySelector('.progress-fill');
    
    if (!generateBtn) return;
    
    generateBtn.addEventListener('click', () => {
        // Show loading state
        outputPlaceholder.classList.add('hidden');
        generatedImage.classList.add('hidden');
        outputLoading.classList.remove('hidden');
        outputActions.classList.add('hidden');
        
        // Animate progress bar
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 1;
            if (progressFill) {
                progressFill.style.width = `${progress}%`;
            }
            
            if (progress >= 100) {
                clearInterval(progressInterval);
                
                // Simulate image generation completion after progress reaches 100%
                setTimeout(() => {
                    simulateImageGeneration();
                }, 500);
            }
        }, 30);
    });
    
    // Simulate image generation
    function simulateImageGeneration() {
        // Create a random colored gradient as a placeholder
        const colors = [
            '#9333ea', '#ec4899', '#06b6d4', '#8b5cf6', '#3b82f6', 
            '#ef4444', '#f59e0b', '#10b981'
        ];
        
        const color1 = colors[Math.floor(Math.random() * colors.length)];
        const color2 = colors[Math.floor(Math.random() * colors.length)];
        
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');
        
        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Add some random shapes
        for (let i = 0; i < 20; i++) {
            ctx.fillStyle = `rgba(255, 255, 255, ${Math.random() * 0.2})`;
            ctx.beginPath();
            ctx.arc(
                Math.random() * canvas.width,
                Math.random() * canvas.height,
                Math.random() * 50 + 10,
                0,
                Math.PI * 2
            );
            ctx.fill();
        }
        
        // Set the generated image
        generatedImage.src = canvas.toDataURL();
        
        // Hide loading and show image
        outputLoading.classList.add('hidden');
        generatedImage.classList.remove('hidden');
        outputActions.classList.remove('hidden');
    }
    
    // Setup action buttons
    setupActionButtons();
}

// Setup action buttons
function setupActionButtons() {
    const downloadBtn = document.querySelector('.download-btn');
    const copyBtn = document.querySelector('.copy-btn');
    const variationsBtn = document.querySelector('.variations-btn');
    const upscaleBtn = document.querySelector('.upscale-btn');
    const generatedImage = document.getElementById('generated-image');
    
    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            if (generatedImage.src) {
                const link = document.createElement('a');
                link.download = `trix-studio-${Date.now()}.png`;
                link.href = generatedImage.src;
                link.click();
            }
        });
    }
    
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            // Show copy feedback
            const originalText = copyBtn.querySelector('span').textContent;
            copyBtn.querySelector('span').textContent = 'Kopyalandı!';
            
            setTimeout(() => {
                copyBtn.querySelector('span').textContent = originalText;
            }, 2000);
        });
    }
    
    if (variationsBtn) {
        variationsBtn.addEventListener('click', () => {
            // Simulate generating variations
            const generateBtn = document.getElementById('generate-btn');
            if (generateBtn) {
                generateBtn.click();
            }
        });
    }
    
    if (upscaleBtn) {
        upscaleBtn.addEventListener('click', () => {
            // Show upscale feedback
            const originalText = upscaleBtn.querySelector('span').textContent;
            upscaleBtn.querySelector('span').textContent = 'İyileştiriliyor...';
            
            setTimeout(() => {
                upscaleBtn.querySelector('span').textContent = 'Tamamlandı!';
                
                setTimeout(() => {
                    upscaleBtn.querySelector('span').textContent = originalText;
                }, 2000);
            }, 1500);
        });
    }
}

// Initialize random seed button
function initRandomSeed() {
    const randomSeedBtn = document.querySelector('.random-seed-btn');
    const seedInput = document.getElementById('seed');
    
    if (randomSeedBtn && seedInput) {
        randomSeedBtn.addEventListener('click', () => {
            seedInput.value = Math.floor(Math.random() * 1000000);
        });
    }
}

// Animate studio elements
function animateStudioElements() {
    // Animate light beam with subtle movement
    const lightBeam = document.querySelector('.light-beam');
    if (lightBeam) {
        let beamAngle = 0;
        let intensity = 1;
        
        setInterval(() => {
            beamAngle += 0.005;
            
            // Create occasional subtle flicker effect
            if (Math.random() > 0.98) {
                intensity = 0.85 + Math.random() * 0.15;
            } else {
                intensity = 1;
            }
            
            const offsetX = Math.sin(beamAngle) * 5;
            lightBeam.style.transform = `translateX(calc(-50% + ${offsetX}px))`;
            lightBeam.style.opacity = 0.6 + (intensity * 0.2);
        }, 30);
    }
}

// Add shake animation for error feedback
document.head.insertAdjacentHTML('beforeend', `
    <style>
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-5px); }
            40%, 80% { transform: translateX(5px); }
        }
        
        .shake {
            animation: shake 0.5s ease-in-out;
        }
        
        .range-value {
            position: absolute;
            right: 0;
            top: 0;
            font-size: 0.75rem;
            color: var(--studio-accent-light);
            transition: all 0.2s ease;
        }
        
        .range-value.updating {
            transform: scale(1.2);
            color: var(--studio-accent);
        }
        
        .setting {
            position: relative;
        }
    </style>
`); 