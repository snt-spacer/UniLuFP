window.HELP_IMPROVE_VIDEOJS = false;

// More Works Dropdown Functionality
function toggleMoreWorks() {
    const dropdown = document.getElementById('moreWorksDropdown');
    const button = document.querySelector('.more-works-btn');
    
    if (dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
        button.classList.remove('active');
    } else {
        dropdown.classList.add('show');
        button.classList.add('active');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const container = document.querySelector('.more-works-container');
    const dropdown = document.getElementById('moreWorksDropdown');
    const button = document.querySelector('.more-works-btn');
    
    if (container && !container.contains(event.target)) {
        dropdown.classList.remove('show');
        button.classList.remove('active');
    }
});

// Close dropdown on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const dropdown = document.getElementById('moreWorksDropdown');
        const button = document.querySelector('.more-works-btn');
        dropdown.classList.remove('show');
        button.classList.remove('active');
    }
});

// Copy BibTeX to clipboard
function copyBibTeX() {
    const bibtexElement = document.getElementById('bibtex-code');
    const button = document.querySelector('.copy-bibtex-btn');
    const copyText = button.querySelector('.copy-text');
    
    if (bibtexElement) {
        navigator.clipboard.writeText(bibtexElement.textContent).then(function() {
            // Success feedback
            button.classList.add('copied');
            copyText.textContent = 'Cop';
            
            setTimeout(function() {
                button.classList.remove('copied');
                copyText.textContent = 'Copy';
            }, 2000);
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = bibtexElement.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            button.classList.add('copied');
            copyText.textContent = 'Cop';
            setTimeout(function() {
                button.classList.remove('copied');
                copyText.textContent = 'Copy';
            }, 2000);
        });
    }
}

// Scroll to top functionality
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Show/hide scroll to top button
window.addEventListener('scroll', function() {
    const scrollButton = document.querySelector('.scroll-to-top');
    if (window.pageYOffset > 300) {
        scrollButton.classList.add('visible');
    } else {
        scrollButton.classList.remove('visible');
    }
});

// Video carousel autoplay when in view
function setupVideoCarouselAutoplay() {
    const carouselVideos = document.querySelectorAll('.results-carousel video');
    
    if (carouselVideos.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const video = entry.target;
            if (entry.isIntersecting) {
                // Video is in view, play it
                video.play().catch(e => {
                    // Autoplay failed, probably due to browser policy
                    console.log('Autoplay prevented:', e);
                });
            } else {
                // Video is out of view, pause it
                video.pause();
            }
        });
    }, {
        threshold: 0.5 // Trigger when 50% of the video is visible
    });
    
    carouselVideos.forEach(video => {
        observer.observe(video);
    });
}

// Image Lightbox/Zoom functionality
function setupImageLightbox() {
    // Create lightbox HTML structure
    const lightbox = document.createElement('div');
    lightbox.id = 'image-lightbox-modal';
    lightbox.innerHTML = `
        <span class="lightbox-close">&times;</span>
        <img class="lightbox-content" id="lightbox-img">
        <div id="lightbox-caption"></div>
    `;
    
    // Add styles dynamically
    const styles = document.createElement('style');
    styles.textContent = `
        #image-lightbox-modal {
            display: none;
            position: fixed;
            z-index: 99999;
            padding-top: 50px;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            align-items: center;
            justify-content: center;
            flex-direction: column;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        #image-lightbox-modal.show {
            display: flex;
            opacity: 1;
        }
        .lightbox-content {
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 80vh;
            border-radius: var(--border-radius-lg, 16px);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            transform: scale(0.95);
            transition: transform 0.3s ease;
            object-fit: contain;
        }
        #image-lightbox-modal.show .lightbox-content {
            transform: scale(1);
        }
        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 35px;
            color: #f1f5f9;
            font-size: 40px;
            font-weight: 300;
            transition: 0.3s;
            cursor: pointer;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
        }
        .lightbox-close:hover,
        .lightbox-close:focus {
            color: #ffffff;
            text-decoration: none;
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.05);
        }
        #lightbox-caption {
            margin: auto;
            display: block;
            width: 80%;
            max-width: 700px;
            text-align: center;
            color: #e2e8f0;
            padding: 15px 0;
            font-size: 1.1rem;
            font-weight: 500;
        }
        /* Add pointer cursor to zoomable images */
        img:not(.icon):not(#favicon):not(.lightbox-content) {
            cursor: zoom-in;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        img:not(.icon):not(#favicon):not(.lightbox-content):hover {
            transform: scale(1.015);
        }
    `;
    
    document.head.appendChild(styles);
    document.body.appendChild(lightbox);
    
    const lightboxImg = document.getElementById('lightbox-img');
    const captionText = document.getElementById('lightbox-caption');
    const closeBtn = document.querySelector('.lightbox-close');
    
    // Use Event Delegation to listen to all image clicks on the page dynamically
    document.addEventListener('click', function(e) {
        const img = e.target.closest('img');
        if (!img) return;
        
        // Skip lightbox image, small icons/logos, or items inside small classes
        if (
            img.classList.contains('icon') || 
            img.classList.contains('lightbox-content') || 
            img.id === 'favicon' || 
            img.closest('.lightbox-close') ||
            img.closest('.icon') ||
            (img.clientWidth > 0 && img.clientWidth < 100)
        ) {
            return;
        }
        
        lightbox.classList.add('show');
        lightboxImg.src = img.src;
        captionText.textContent = img.alt || img.title || '';
        document.body.style.overflow = 'hidden'; // Disable background scroll
    });
    
    function closeLightbox() {
        lightbox.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    closeBtn.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox || e.target === closeBtn) {
            closeLightbox();
        }
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && lightbox.classList.contains('show')) {
            closeLightbox();
        }
    });
}

// Call it immediately (the script is deferred, so document.body is ready)
setupImageLightbox();

$(document).ready(function() {
    // Check for click events on the navbar burger icon

    var options = {
		slidesToScroll: 1,
		slidesToShow: 1,
		loop: true,
		infinite: true,
		autoplay: true,
		autoplaySpeed: 5000,
    }

    try {
        // Initialize all div with carousel class
        var carousels = bulmaCarousel.attach('.carousel', options);
        bulmaSlider.attach();
    } catch(e) {
        console.warn("Bulma carousel/slider missing or failed to initialize:", e);
    }
    
    // Setup video autoplay for carousel
    setupVideoCarouselAutoplay();
})
