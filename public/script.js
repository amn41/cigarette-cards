document.addEventListener('DOMContentLoaded', function() {
    // Carousel functionality
    const carousel = document.querySelector('.carousel');
    const items = document.querySelectorAll('.carousel-item');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    
    let currentIndex = 0;
    const itemWidth = items[0].offsetWidth + 24; // width + margin
    const maxIndex = items.length - 1;
    
    // Handle window resize and adjust visible items based on screen width
    function calculateVisibleItems() {
        if (window.innerWidth < 768) {
            return 1;
        } else if (window.innerWidth < 1024) {
            return 2;
        } else {
            return 3;
        }
    }
    
    let visibleItems = calculateVisibleItems();
    
    function updateCarousel() {
        carousel.style.transform = `translateX(-${currentIndex * itemWidth}px)`;
        
        // Update button states
        prevBtn.disabled = currentIndex === 0;
        prevBtn.style.opacity = currentIndex === 0 ? '0.5' : '1';
        nextBtn.disabled = currentIndex >= maxIndex - visibleItems + 1;
        nextBtn.style.opacity = currentIndex >= maxIndex - visibleItems + 1 ? '0.5' : '1';
    }
    
    nextBtn.addEventListener('click', function() {
        if (currentIndex < maxIndex - visibleItems + 1) {
            currentIndex++;
            updateCarousel();
        }
    });
    
    prevBtn.addEventListener('click', function() {
        if (currentIndex > 0) {
            currentIndex--;
            updateCarousel();
        }
    });
    
    // Auto-advance carousel
    let autoAdvance = setInterval(function() {
        if (currentIndex < maxIndex - visibleItems + 1) {
            currentIndex++;
        } else {
            currentIndex = 0;
        }
        updateCarousel();
    }, 5000);
    
    // Pause auto-advance on hover
    carousel.addEventListener('mouseenter', function() {
        clearInterval(autoAdvance);
    });
    
    carousel.addEventListener('mouseleave', function() {
        autoAdvance = setInterval(function() {
            if (currentIndex < maxIndex - visibleItems + 1) {
                currentIndex++;
            } else {
                currentIndex = 0;
            }
            updateCarousel();
        }, 5000);
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        const newVisibleItems = calculateVisibleItems();
        if (newVisibleItems !== visibleItems) {
            visibleItems = newVisibleItems;
            // Adjust currentIndex if needed
            if (currentIndex > maxIndex - visibleItems + 1) {
                currentIndex = maxIndex - visibleItems + 1;
            }
            updateCarousel();
        }
    });
    
    // Initialize carousel
    updateCarousel();
    
    // Handle subscription form
    const subscribeForm = document.getElementById('subscribe-form');
    const subscribeButton = document.getElementById('subscribe-button');
    const formMessage = document.getElementById('form-message');
    
    if (subscribeForm) {
        subscribeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Disable button and show loading state
            subscribeButton.disabled = true;
            subscribeButton.innerText = 'Subscribing...';
            formMessage.innerText = 'Processing...';
            
            // Get form data
            const formData = new FormData(subscribeForm);
            const email = formData.get('email');
            
            // Submit form using fetch API
            fetch('/.netlify/functions/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            })
            .then(response => {
                if (response.ok) {
                    // If the function returns a redirect, follow it
                    if (response.redirected) {
                        window.location.href = response.url;
                        return;
                    }
                    
                    // Otherwise show success message
                    subscribeButton.innerText = 'Subscribed!';
                    formMessage.innerText = 'Subscription confirmed. Check your inbox.';
                    subscribeForm.reset();
                    
                    // Redirect to thank you page
                    setTimeout(() => {
                        window.location.href = '/thank-you.html';
                    }, 1500);
                } else {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Subscription failed');
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                subscribeButton.innerText = 'Subscribe';
                subscribeButton.disabled = false;
                formMessage.innerText = `Error: ${error.message}. Please try again.`;
            });
        });
    }
});