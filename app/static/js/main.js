// AI Stratejist - Modern JavaScript Dosyası

// === UTILITY FUNCTIONS ===
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// === SMOOTH SCROLLING ===
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// === NAVBAR SCROLL EFFECT ===
function initNavbarScrollEffect() {
    const header = document.querySelector('.main-header');
    
    const handleScroll = debounce(() => {
        if (window.scrollY > 100) {
            header.style.background = 'rgba(15, 27, 60, 0.98)';
            header.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
        } else {
            header.style.background = 'rgba(15, 27, 60, 0.95)';
            header.style.boxShadow = 'none';
        }
    }, 10);
    
    window.addEventListener('scroll', handleScroll);
}

// === PARALLAX EFFECTS ===
function initParallaxEffects() {
    const floatingElements = document.querySelectorAll('.floating-element');
    const heroVisual = document.querySelector('.hero-visual');
    
    const handleScroll = debounce(() => {
        const scrollY = window.scrollY;
        const rate = scrollY * -0.5;
        
        if (heroVisual) {
            heroVisual.style.transform = `translateY(${rate * 0.3}px)`;
        }
        
        floatingElements.forEach((element, index) => {
            const speed = 0.2 + (index * 0.1);
            element.style.transform = `translateY(${scrollY * speed}px)`;
        });
    }, 10);
    
    window.addEventListener('scroll', handleScroll);
}

// === INTERSECTION OBSERVER FOR ANIMATIONS ===
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Animate service cards
    document.querySelectorAll('.service-card').forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.6s ease ${index * 0.1}s`;
        observer.observe(card);
    });
    
    // Animate section headers
    document.querySelectorAll('.section-header').forEach(header => {
        header.style.opacity = '0';
        header.style.transform = 'translateY(20px)';
        header.style.transition = 'all 0.6s ease';
        observer.observe(header);
    });
}

// === TYPING ANIMATION ===
function initTypingAnimation() {
    const heroTitle = document.querySelector('.hero-title');
    if (!heroTitle) return;
    
    // Metni parçalara ayır
    const firstLine = 'Satışlarınızı';
    const secondLine = 'AI ile Güçlendirin';
    
    // Başlangıçta boş yap
    heroTitle.innerHTML = '';
    heroTitle.style.opacity = '1';
    
    let currentPhase = 1; // 1: ilk satır, 2: ikinci satır
    let index = 0;
    const speed = 80;
    
    function typeWriter() {
        if (currentPhase === 1) {
            // İlk satırı yaz
            if (index < firstLine.length) {
                heroTitle.innerHTML = firstLine.substring(0, index + 1);
                index++;
                setTimeout(typeWriter, speed);
            } else {
                // İlk satır tamamlandı, <br> ekle ve ikinci faza geç
                heroTitle.innerHTML = firstLine + '<br>';
                currentPhase = 2;
                index = 0;
                setTimeout(typeWriter, speed * 2); // Kısa bir duraklama
            }
        } else if (currentPhase === 2) {
            // İkinci satırı gradient ile yaz
            if (index < secondLine.length) {
                const currentText = secondLine.substring(0, index + 1);
                heroTitle.innerHTML = firstLine + '<br><span class="gradient-text">' + currentText + '</span>';
                index++;
                setTimeout(typeWriter, speed);
            }
            // Animasyon tamamlandı
        }
    }
    
    setTimeout(typeWriter, 500);
}

// === MODAL FUNCTIONS ===
function showLogin() {
    const modal = document.getElementById('loginModal');
    if (modal) {
        modal.style.display = 'block';
        setTimeout(() => {
            modal.style.opacity = '1';
            modal.querySelector('.modal-content').style.transform = 'scale(1)';
        }, 10);
    }
}

function showRegister() {
    const modal = document.getElementById('registerModal');
    if (modal) {
        modal.style.display = 'block';
        setTimeout(() => {
            modal.style.opacity = '1';
            modal.querySelector('.modal-content').style.transform = 'scale(1)';
        }, 10);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.opacity = '0';
        modal.querySelector('.modal-content').style.transform = 'scale(0.9)';
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

function showDemoVideo() {
    showNotification('Demo video yakında eklenecek!', 'info');
}

// === MODAL STYLING ===
function initModalStyling() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.style.opacity = '0';
        modal.style.transition = 'opacity 0.3s ease';
        
        const content = modal.querySelector('.modal-content');
        if (content) {
            content.style.transform = 'scale(0.9)';
            content.style.transition = 'transform 0.3s ease';
        }
    });
}

// Modal dışına tıklandığında kapat
window.onclick = function(event) {
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    
    if (event.target === loginModal) {
        closeModal('loginModal');
    }
    if (event.target === registerModal) {
        closeModal('registerModal');
    }
}

// === BUTTON RIPPLE EFFECT ===
function initButtonRippleEffect() {
    document.querySelectorAll('button, .btn-primary, .btn-secondary-nav, .btn-primary-nav').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                transform: scale(0);
                animation: ripple-effect 0.6s linear;
                left: ${x}px;
                top: ${y}px;
                width: ${size}px;
                height: ${size}px;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// === STATS COUNTER ANIMATION ===
function initStatsAnimation() {
    const stats = document.querySelectorAll('.stat-number');
    
    const animateValue = (element, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const currentValue = Math.floor(progress * (end - start) + start);
            
            if (element.textContent.includes('%')) {
                element.textContent = `%${currentValue}`;
            } else if (element.textContent.includes('+')) {
                element.textContent = `${currentValue}+`;
            } else {
                element.textContent = currentValue;
            }
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const text = element.textContent;
                
                if (text.includes('500+')) {
                    animateValue(element, 0, 500, 2000);
                } else if (text.includes('%40')) {
                    animateValue(element, 0, 40, 2000);
                } else if (text.includes('24/7')) {
                    element.textContent = '24/7';
                }
                
                observer.unobserve(element);
            }
        });
    });
    
    stats.forEach(stat => observer.observe(stat));
}

// API Base URL
const API_BASE_URL = '/api/v1';

// Utility functions
function showNotification(message, type = 'info') {
    // Basit notification sistemi
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Stil ekle
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
    `;
    
    // Tip'e göre renk
    switch(type) {
        case 'success':
            notification.style.background = '#27ae60';
            break;
        case 'error':
            notification.style.background = '#e74c3c';
            break;
        case 'warning':
            notification.style.background = '#f39c12';
            break;
        default:
            notification.style.background = '#3498db';
    }
    
    document.body.appendChild(notification);
    
    // 3 saniye sonra kaldır
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Login form handler
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('username', loginForm.querySelector('input[type="text"]').value);
            formData.append('password', loginForm.querySelector('input[type="password"]').value);
            
            try {
                const response = await fetch(`${API_BASE_URL}/auth/token`, {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('access_token', data.access_token);
                    showNotification('Giriş başarılı! Yönlendiriliyorsunuz...', 'success');
                    
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                } else {
                    const error = await response.json();
                    showNotification(error.detail || 'Giriş başarısız!', 'error');
                }
            } catch (error) {
                showNotification('Bağlantı hatası!', 'error');
            }
        });
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const userData = {
                email: registerForm.querySelector('input[type="email"]').value,
                username: registerForm.querySelectorAll('input[type="text"]')[0].value,
                full_name: registerForm.querySelectorAll('input[type="text"]')[1].value,
                password: registerForm.querySelector('input[type="password"]').value
            };
            
            try {
                const response = await fetch(`${API_BASE_URL}/auth/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(userData)
                });
                
                if (response.ok) {
                    showNotification('Kayıt başarılı! Giriş yapabilirsiniz.', 'success');
                    closeModal('registerModal');
                    showLogin();
                } else {
                    const error = await response.json();
                    showNotification(error.detail || 'Kayıt başarısız!', 'error');
                }
            } catch (error) {
                showNotification('Bağlantı hatası!', 'error');
            }
        });
    }
});

// Token kontrol fonksiyonu
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Authenticated API çağrısı için utility
async function authenticatedFetch(url, options = {}) {
    const token = getAuthToken();
    
    if (!token) {
        showNotification('Lütfen giriş yapın!', 'warning');
        showLogin();
        return null;
    }
    
    const defaultHeaders = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, config);
        
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            showNotification('Oturum süresi doldu, tekrar giriş yapın!', 'warning');
            showLogin();
            return null;
        }
        
        return response;
    } catch (error) {
        showNotification('Bağlantı hatası!', 'error');
        return null;
    }
}

// === MAIN INITIALIZATION ===
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all effects and animations
    initSmoothScrolling();
    initNavbarScrollEffect();
    initParallaxEffects();
    initScrollAnimations();
    initModalStyling();
    initButtonRippleEffect();
    initStatsAnimation();
    
    // Initialize typing animation after a small delay
    setTimeout(() => {
        initTypingAnimation();
    }, 1000);
    
    // Initialize existing form handlers
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginSubmit);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegisterSubmit);
    }
    
    // Add loading animation on page load
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);
});

// === FORM HANDLERS ===
async function handleLoginSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('username', e.target.querySelector('input[type="text"]').value);
    formData.append('password', e.target.querySelector('input[type="password"]').value);
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            showNotification('Giriş başarılı! Yönlendiriliyorsunuz...', 'success');
            
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Giriş başarısız!', 'error');
        }
    } catch (error) {
        showNotification('Bağlantı hatası!', 'error');
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    
    const userData = {
        email: e.target.querySelector('input[type="email"]').value,
        username: e.target.querySelectorAll('input[type="text"]')[0].value,
        full_name: e.target.querySelectorAll('input[type="text"]')[1].value,
        password: e.target.querySelector('input[type="password"]').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        if (response.ok) {
            showNotification('Kayıt başarılı! Giriş yapabilirsiniz.', 'success');
            closeModal('registerModal');
            showLogin();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Kayıt başarısız!', 'error');
        }
    } catch (error) {
        showNotification('Bağlantı hatası!', 'error');
    }
}

// === KEYBOARD NAVIGATION ===
document.addEventListener('keydown', function(e) {
    // ESC key to close modals
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal[style*="block"]');
        openModals.forEach(modal => {
            closeModal(modal.id);
        });
    }
});

// === CSS ANIMATIONS ===
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes ripple-effect {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
    
    @keyframes float {
        0%, 100% {
            transform: translateY(0px);
        }
        50% {
            transform: translateY(-10px);
        }
    }
    
    .notification {
        animation: slideIn 0.3s ease;
    }
    
    .loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    .floating-animation {
        animation: float 3s ease-in-out infinite;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 27, 60, 0.3);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #00D4FF, #00BCD4);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #00BCD4, #1DE9B6);
    }
    
    /* Selection styles */
    ::selection {
        background: rgba(0, 212, 255, 0.3);
        color: white;
    }
    
    ::-moz-selection {
        background: rgba(0, 212, 255, 0.3);
        color: white;
    }
`;
document.head.appendChild(style); 