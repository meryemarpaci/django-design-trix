// Inpainting functionality
class InpaintingApp {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.maskCanvas = null;
        this.maskCtx = null;
        this.originalImage = null;
        this.isDrawing = false;
        this.brushSize = 20;
        this.currentImagePath = null;
        this.currentTool = 'brush'; // 'brush' or 'bbox'
        this.bboxStart = null;
        this.bboxEnd = null;
        this.isSelectingBbox = false;
        
        this.init();
    }
    
    init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.checkAIStatus();
    }
    
    setupCanvas() {
        this.canvas = document.getElementById('inpainting-canvas');
        this.maskCanvas = document.getElementById('mask-canvas');
        
        if (!this.canvas || !this.maskCanvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.maskCtx = this.maskCanvas.getContext('2d');
        
        // Set canvas size
        this.canvas.width = 512;
        this.canvas.height = 512;
        this.maskCanvas.width = 512;
        this.maskCanvas.height = 512;
        
        // Setup mask canvas styles
        this.maskCtx.globalCompositeOperation = 'source-over';
        this.maskCtx.strokeStyle = 'rgba(255, 0, 0, 0.7)';
        this.maskCtx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        this.maskCtx.lineWidth = this.brushSize;
        this.maskCtx.lineCap = 'round';
        this.maskCtx.lineJoin = 'round';
    }
    
    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('inpainting-image-input');
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileUpload.bind(this));
        }
        
        // Canvas drawing events
        if (this.maskCanvas) {
            this.maskCanvas.addEventListener('mousedown', this.startDrawing.bind(this));
            this.maskCanvas.addEventListener('mousemove', this.draw.bind(this));
            this.maskCanvas.addEventListener('mouseup', this.stopDrawing.bind(this));
            this.maskCanvas.addEventListener('mouseout', this.stopDrawing.bind(this));
        }
        
        // Tool selection
        const toolButtons = document.querySelectorAll('.tool-btn');
        toolButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectTool(e.target.dataset.tool);
            });
        });
        
        // Clear mask
        const clearBtn = document.getElementById('clear-mask-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', this.clearMask.bind(this));
        }
        
        // Brush size
        const brushSizeSlider = document.getElementById('brush-size');
        if (brushSizeSlider) {
            brushSizeSlider.addEventListener('input', (e) => {
                this.brushSize = parseInt(e.target.value);
                this.maskCtx.lineWidth = this.brushSize;
                document.getElementById('brush-size-value').textContent = this.brushSize;
            });
        }
        
        // Generate button
        const generateBtn = document.getElementById('inpainting-generate-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', this.generateInpainting.bind(this));
        }
    }
    
    async checkAIStatus() {
        try {
            const response = await fetch('/api/ai-status/');
            const data = await response.json();
            
            const statusElement = document.getElementById('ai-status');
            if (statusElement) {
                if (data.available) {
                    statusElement.innerHTML = `
                        <span class="status-success">✓ AI Ready</span>
                        <small>Device: ${data.device}</small>
                    `;
                } else {
                    statusElement.innerHTML = `
                        <span class="status-error">✗ AI Unavailable</span>
                        <small>${data.message}</small>
                    `;
                }
            }
        } catch (error) {
            console.error('Failed to check AI status:', error);
        }
    }
    
    selectTool(tool) {
        this.currentTool = tool;
        
        // Update UI
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tool="${tool}"]`).classList.add('active');
        
        // Update cursor
        if (tool === 'brush') {
            this.maskCanvas.style.cursor = 'crosshair';
        } else if (tool === 'bbox') {
            this.maskCanvas.style.cursor = 'crosshair';
        }
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Show loading
        this.showLoading('Uploading image...');
        
        try {
            const formData = new FormData();
            formData.append('image', file);
            
            const response = await fetch('/api/upload-for-inpainting/', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentImagePath = data.file_path;
                await this.loadImageToCanvas(data.file_url);
                this.hideLoading();
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        }
    }
    
    async loadImageToCanvas(imageUrl) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                // Calculate dimensions to fit in canvas
                const maxWidth = this.canvas.width;
                const maxHeight = this.canvas.height;
                
                let { width, height } = img;
                
                if (width > maxWidth || height > maxHeight) {
                    const ratio = Math.min(maxWidth / width, maxHeight / height);
                    width *= ratio;
                    height *= ratio;
                }
                
                // Clear canvas and draw image
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                this.ctx.drawImage(img, 
                    (this.canvas.width - width) / 2, 
                    (this.canvas.height - height) / 2, 
                    width, height
                );
                
                this.originalImage = img;
                resolve();
            };
            img.onerror = reject;
            img.src = imageUrl;
        });
    }
    
    getMousePos(e) {
        const rect = this.maskCanvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
    
    startDrawing(e) {
        const pos = this.getMousePos(e);
        
        if (this.currentTool === 'brush') {
            this.isDrawing = true;
            this.maskCtx.beginPath();
            this.maskCtx.moveTo(pos.x, pos.y);
        } else if (this.currentTool === 'bbox') {
            this.isSelectingBbox = true;
            this.bboxStart = pos;
        }
    }
    
    draw(e) {
        const pos = this.getMousePos(e);
        
        if (this.currentTool === 'brush' && this.isDrawing) {
            this.maskCtx.lineTo(pos.x, pos.y);
            this.maskCtx.stroke();
        } else if (this.currentTool === 'bbox' && this.isSelectingBbox) {
            // Clear and redraw bbox
            this.maskCtx.clearRect(0, 0, this.maskCanvas.width, this.maskCanvas.height);
            
            const width = pos.x - this.bboxStart.x;
            const height = pos.y - this.bboxStart.y;
            
            this.maskCtx.strokeRect(this.bboxStart.x, this.bboxStart.y, width, height);
            this.maskCtx.fillRect(this.bboxStart.x, this.bboxStart.y, width, height);
        }
    }
    
    stopDrawing(e) {
        if (this.currentTool === 'brush') {
            this.isDrawing = false;
        } else if (this.currentTool === 'bbox' && this.isSelectingBbox) {
            this.isSelectingBbox = false;
            const pos = this.getMousePos(e);
            this.bboxEnd = pos;
        }
    }
    
    clearMask() {
        this.maskCtx.clearRect(0, 0, this.maskCanvas.width, this.maskCanvas.height);
        this.bboxStart = null;
        this.bboxEnd = null;
    }
    
    async generateInpainting() {
        if (!this.currentImagePath) {
            this.showError('Please upload an image first');
            return;
        }
        
        const prompt = document.getElementById('inpainting-prompt').value.trim();
        if (!prompt) {
            this.showError('Please enter a prompt');
            return;
        }
        
        // Prepare mask data
        let maskData;
        if (this.currentTool === 'bbox' && this.bboxStart && this.bboxEnd) {
            const x = Math.min(this.bboxStart.x, this.bboxEnd.x);
            const y = Math.min(this.bboxStart.y, this.bboxEnd.y);
            const width = Math.abs(this.bboxEnd.x - this.bboxStart.x);
            const height = Math.abs(this.bboxEnd.y - this.bboxStart.y);
            
            maskData = {
                type: 'bbox',
                bbox: [x, y, width, height]
            };
        } else if (this.currentTool === 'brush') {
            // For brush tool, we need to send stroke data
            // This is a simplified implementation
            maskData = {
                type: 'brush',
                strokes: [] // Would need to track actual stroke paths
            };
        } else {
            this.showError('Please create a mask by drawing or selecting an area');
            return;
        }
        
        const requestData = {
            image_path: this.currentImagePath,
            mask_data: maskData,
            prompt: prompt,
            negative_prompt: document.getElementById('negative-prompt').value || '',
            num_inference_steps: parseInt(document.getElementById('inference-steps').value) || 50,
            guidance_scale: parseFloat(document.getElementById('guidance-scale').value) || 7.5,
            strength: parseFloat(document.getElementById('strength').value) || 1.0
        };
        
        this.showLoading('Generating inpainting...');
        
        try {
            const response = await fetch('/api/inpaint/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showResult(data.result_url);
                this.hideLoading();
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Generation failed: ' + error.message);
        }
    }
    
    showResult(imageUrl) {
        const resultContainer = document.getElementById('inpainting-result');
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="result-image">
                    <img src="${imageUrl}" alt="Inpainting Result" />
                    <div class="result-actions">
                        <button class="btn btn-primary" onclick="inpaintingApp.downloadResult('${imageUrl}')">
                            Download
                        </button>
                        <button class="btn btn-secondary" onclick="inpaintingApp.saveAsDesign('${imageUrl}')">
                            Save as Design
                        </button>
                    </div>
                </div>
            `;
        }
    }
    
    downloadResult(imageUrl) {
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = 'inpainted_result.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    saveAsDesign(imageUrl) {
        // This would redirect to design creation with the result image
        const prompt = document.getElementById('inpainting-prompt').value;
        
        // Create a form and submit it
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/design/create/';
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        form.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
            <input type="hidden" name="title" value="Inpainted Design">
            <input type="hidden" name="prompt" value="${prompt}">
            <input type="hidden" name="style" value="AI Inpainting">
            <input type="hidden" name="model_used" value="LoRA Inpainting">
            <input type="hidden" name="result_url" value="${imageUrl}">
        `;
        
        document.body.appendChild(form);
        form.submit();
    }
    
    showLoading(message) {
        const loadingElement = document.getElementById('inpainting-loading');
        if (loadingElement) {
            loadingElement.innerHTML = `<div class="loading-spinner"></div><p>${message}</p>`;
            loadingElement.style.display = 'flex';
        }
    }
    
    hideLoading() {
        const loadingElement = document.getElementById('inpainting-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    showError(message) {
        this.hideLoading();
        
        const errorElement = document.getElementById('inpainting-error');
        if (errorElement) {
            errorElement.innerHTML = `<p class="error-message">${message}</p>`;
            errorElement.style.display = 'block';
            
            // Hide error after 5 seconds
            setTimeout(() => {
                errorElement.style.display = 'none';
            }, 5000);
        } else {
            alert(message);
        }
    }
}

// Initialize the inpainting app when the page loads
let inpaintingApp;
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('inpainting-canvas')) {
        inpaintingApp = new InpaintingApp();
    }
}); 