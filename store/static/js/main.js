tailwind.config = {
    theme: {
        extend: {
        colors: {
            primary: '#00ADB5',
            secondary: '#222831',
            accent: '#393E46'
        }
        }
    }
}
setTimeout(() => {
    document.querySelectorAll('.z-50 > div').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(-10px)';
        setTimeout(() => el.remove(), 500);
    });
    }, 3000);