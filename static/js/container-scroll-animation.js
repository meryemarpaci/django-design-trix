// Container Scroll Animation Component
// Converted from React to Vanilla JS

// Initialize the component when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  initContainerScrollAnimation();
});

function initContainerScrollAnimation() {
  // Check if the container exists
  const containerElement = document.getElementById('scroll-animation-container');
  if (!containerElement) return;

  // Initialize mobile detection
  let isMobile = window.innerWidth <= 768;
  
  // Add resize listener
  window.addEventListener('resize', function() {
    isMobile = window.innerWidth <= 768;
    updateAnimation();
  });

  // Get elements
  const titleElement = document.getElementById('scroll-animation-title');
  const cardElement = document.getElementById('scroll-animation-card');
  const contentElement = document.getElementById('scroll-animation-content');
  
  // Set up scroll listener
  let scrollYProgress = 0;
  
  function updateAnimation() {
    // Calculate scroll progress (0 to 1)
    const containerRect = containerElement.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    
    // Calculate progress based on container position
    if (containerRect.top <= windowHeight && containerRect.bottom >= 0) {
      // Container is in view
      const totalScrollDistance = windowHeight + containerRect.height;
      const scrolledDistance = windowHeight - containerRect.top;
      scrollYProgress = Math.min(Math.max(scrolledDistance / totalScrollDistance, 0), 1);
      
      // Apply transformations based on scroll progress
      const rotate = 20 - (scrollYProgress * 20); // 20 to 0 degrees
      const scale = isMobile ? 
        0.7 + (scrollYProgress * 0.2) : // 0.7 to 0.9 for mobile
        1.05 - (scrollYProgress * 0.05); // 1.05 to 1 for desktop
      const translate = -scrollYProgress * 100; // 0 to -100px
      
      // Apply transforms
      if (titleElement) {
        titleElement.style.transform = `translateY(${translate}px)`;
      }
      
      if (cardElement) {
        cardElement.style.transform = `rotateX(${rotate}deg) scale(${scale})`;
        cardElement.style.boxShadow = 
          "0 0 #0000004d, 0 9px 20px #0000004a, 0 37px 37px #00000042, 0 84px 50px #00000026, 0 149px 60px #0000000a, 0 233px 65px #00000003";
      }
    }
  }
  
  // Add scroll event listener
  window.addEventListener('scroll', updateAnimation);
  
  // Initial update
  updateAnimation();
}

// Function to create the container scroll animation HTML structure
function createScrollAnimation(containerId, titleHtml, contentHtml) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // Create the HTML structure
  container.innerHTML = `
    <div id="scroll-animation-container" class="h-[60rem] md:h-[80rem] flex items-center justify-center relative p-2 md:p-20">
      <div class="py-10 md:py-40 w-full relative" style="perspective: 1000px;">
        <div id="scroll-animation-title" class="max-w-5xl mx-auto text-center">
          ${titleHtml}
        </div>
        <div id="scroll-animation-card" class="max-w-5xl -mt-12 mx-auto h-[30rem] md:h-[40rem] w-full border-4 border-[#6C6C6C] p-2 md:p-6 bg-[#222222] rounded-[30px] shadow-2xl">
          <div id="scroll-animation-content" class="h-full w-full overflow-hidden rounded-2xl bg-gray-100 dark:bg-zinc-900 md:rounded-2xl md:p-4">
            ${contentHtml}
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Initialize the animation
  initContainerScrollAnimation();
} 