function showNewsForm() {
    document.getElementById('newsForm').style.display = 'block';
    document.getElementById('applicationsForm').style.display = 'none';
    document.getElementById('linkForm').style.display = 'none';
    document.getElementById('subscriptionsForm').style.display = 'none';
    document.getElementById('notificationsForm').style.display = 'none';
}

function showApplicationsForm() {
    document.getElementById('newsForm').style.display = 'none';
    document.getElementById('applicationsForm').style.display = 'block';
    document.getElementById('linkForm').style.display = 'none';
    document.getElementById('subscriptionsForm').style.display = 'none';
    document.getElementById('notificationsForm').style.display = 'none';
}

function showNotificationForm() {
    document.getElementById('newsForm').style.display = 'none';
    document.getElementById('applicationsForm').style.display = 'none';
    document.getElementById('linkForm').style.display = 'none';
    document.getElementById('subscriptionsForm').style.display = 'none';
    document.getElementById('notificationsForm').style.display = 'block';
}

function showLinkForm() {
    document.getElementById('newsForm').style.display = 'none';
    document.getElementById('applicationsForm').style.display = 'none';
    document.getElementById('linkForm').style.display = 'block';
    document.getElementById('subscriptionsForm').style.display = 'none';
    document.getElementById('notificationsForm').style.display = 'none';
}

function showSubscriptionsForm() {
    document.getElementById('newsForm').style.display = 'none';
    document.getElementById('applicationsForm').style.display = 'none';
    document.getElementById('linkForm').style.display = 'none';
    document.getElementById('subscriptionsForm').style.display = 'block';
    document.getElementById('notificationsForm').style.display = 'none';
}
function showAssignSubscriptionForm() {
    document.getElementById('assignSubscriptionForm').style.display = 'block';
    document.getElementById('newsForm').style.display = 'none';
    document.getElementById('applicationsForm').style.display = 'none';
    document.getElementById('linkForm').style.display = 'none';
    document.getElementById('subscriptionsForm').style.display = 'none';
    document.getElementById('notificationsForm').style.display = 'none';
}
document.querySelector('form').addEventListener('submit', (e) => {
    const userId = document.getElementById('user_id').value;
    if (!userId) {
        e.preventDefault();
        alert('Пользователь не выбран!');
    }
    console.log(`user_id: ${userId}`);
});
