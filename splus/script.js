
document.addEventListener("DOMContentLoaded", () => {
    const loginButton = document.querySelector(".btn");

    if (loginButton) {
        loginButton.addEventListener("click", () => {
            loginButton.textContent = "در حال ورود...";
        });
    }

    console.log("%c NEXORA ", 
        "background:#39ff57;color:#000;padding:8px;font-weight:bold;"
    );
});
