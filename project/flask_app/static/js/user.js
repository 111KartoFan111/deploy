function startEdit(button) {
    const li = button.closest('li');
    li.querySelector('.app-name').style.display = 'none';
    li.querySelector('a').style.display = 'none';
    button.style.display = 'none';
    li.querySelector('.edit-form').style.display = 'block';
}

function cancelEdit(button) {
    const li = button.closest('li');
    li.querySelector('.app-name').style.display = '';
    li.querySelector('a').style.display = '';
    li.querySelector('button[onclick="startEdit(this)"]').style.display = '';
    li.querySelector('.edit-form').style.display = 'none';
}

function saveEdit(button) {
    const li = button.closest('li');
    const newAppName = li.querySelector('input').value;
    const link = li.dataset.link;

    fetch('/update_app_name', {
        method: 'POST',
        body: JSON.stringify({ link, newAppName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            li.querySelector('.app-name').textContent = newAppName;
            cancelEdit(button);
        } else {
            alert('Ошибка при сохранении');
        }
    });
}