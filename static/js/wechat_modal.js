document.addEventListener('DOMContentLoaded', function () {
    const trigger = document.getElementById('wechat-modal-trigger');
    const modal = document.getElementById('wechat-modal');
    
    if (trigger && modal) {
        const closeBtn = modal.querySelector('.modal-close');

        // Function to open the modal
        const openModal = (e) => {
            e.preventDefault();
            modal.classList.add('active');
        };

        // Function to close the modal
        const closeModal = () => {
            modal.classList.remove('active');
        };

        // Event listeners
        trigger.addEventListener('click', openModal);
        
        if(closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }

        // Close modal when clicking on the overlay
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Close modal with the Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === "Escape" && modal.classList.contains('active')) {
                closeModal();
            }
        });
    }
}); 