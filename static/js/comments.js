document.addEventListener('DOMContentLoaded', function () {
    const toggleButtons = document.querySelectorAll('.comment-reply-toggle');
    const cancelButtons = document.querySelectorAll('.comment-reply-cancel');

    function closeAllReplyForms() {
        document.querySelectorAll('.comment-reply-form').forEach(function (form) {
            form.classList.add('is-hidden');
        });
    }

    toggleButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            const targetId = button.getAttribute('data-target');
            const targetForm = document.getElementById(targetId);
            if (!targetForm) {
                return;
            }

            const willOpen = targetForm.classList.contains('is-hidden');
            closeAllReplyForms();
            if (willOpen) {
                targetForm.classList.remove('is-hidden');
                const firstInput = targetForm.querySelector('input, textarea');
                if (firstInput) {
                    firstInput.focus();
                }
            }
        });
    });

    cancelButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            const form = button.closest('.comment-reply-form');
            if (form) {
                form.classList.add('is-hidden');
            }
        });
    });
});
