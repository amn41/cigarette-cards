document.addEventListener('DOMContentLoaded', function() {
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