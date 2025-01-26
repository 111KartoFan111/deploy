function toggleForm(formId) {
    // Скрываем все формы
    const forms = document.querySelectorAll('.form-section');
    forms.forEach(form => form.style.display = 'none');

    // Показываем выбранную форму
    const selectedForm = document.getElementById(formId);
    if (selectedForm) {
        selectedForm.style.display = 'block';

        // Сохраняем выбранную форму в localStorage
        localStorage.setItem('activeForm', formId);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Восстановить последнюю активную форму из localStorage
    const savedForm = localStorage.getItem('activeForm') || 'newsForm';
    toggleForm(savedForm);

    // Активировать соответствующую радио-кнопку
    const radio = document.querySelector(`input[value="${savedForm}"]`);
    if (radio) {
        radio.checked = true;
    }
});
document.querySelector('form').addEventListener('submit', (e) => {
    const userId = document.getElementById('user_id').value;
    if (!userId) {
        e.preventDefault();
        alert('Пользователь не выбран!');
    }
    console.log(`user_id: ${userId}`);
});