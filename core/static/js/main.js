document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Khởi tạo các biểu tượng Lucide
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 2. Điều khiển Modal (Bật/Tắt)
    const modal = document.getElementById('detailsModal');
    const openBtn = document.getElementById('btn-open-modal');
    const closeBtn = document.getElementById('btn-close-modal');

    if (openBtn && modal) {
        openBtn.addEventListener('click', () => {
            modal.classList.remove('hidden');
        });
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });
    }

    // 3. Tự động gửi Form khi đổi Ổ đĩa hoặc Sắp xếp
    const autoSubmitElements = document.querySelectorAll('.auto-submit');
    autoSubmitElements.forEach(el => {
        el.addEventListener('change', function() {
            this.form.submit();
        });
    });

    // Đóng modal khi nhấn ra ngoài vùng trắng
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
});