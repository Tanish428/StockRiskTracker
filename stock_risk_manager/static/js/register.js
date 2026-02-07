document.getElementById("registerForm").addEventListener("submit", function(e) {
    e.preventDefault();

    let username = document.getElementById("username");
    let email = document.getElementById("email");
    let password = document.getElementById("password");
    let confirmPassword = document.getElementById("confirmPassword");

    let valid = true;

    clearErrors();

    if (username.value.trim() === "") {
        showError(username, "Username required");
        valid = false;
    }

    if (email.value.trim() === "") {
        showError(email, "Email required");
        valid = false;
    }

    if (password.value.length < 6) {
        showError(password, "Minimum 6 characters");
        valid = false;
    }

    if (password.value !== confirmPassword.value) {
        showError(confirmPassword, "Passwords do not match");
        valid = false;
    }

    if (valid) {
        // Redirect to Risk Quiz page
        window.location.href = "risk_quiz.html";
    }
});

function showError(input, message) {
    input.parentElement.querySelector(".error").innerText = message;
}

function clearErrors() {
    document.querySelectorAll(".error").forEach(err => err.innerText = "");
}
