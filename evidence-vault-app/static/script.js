// static/script.js

document.addEventListener("DOMContentLoaded", () => {

    // Smooth card hover glow
    const cards = document.querySelectorAll(".card");

    cards.forEach(card => {
        card.addEventListener("mouseenter", () => {
            card.style.transform = "translateY(-6px)";
            card.style.transition = "0.3s ease";
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "translateY(0px)";
        });
    });

    // Auto hide flash alerts
    const alerts = document.querySelectorAll(".flash-msg");

    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = "0";
            alert.style.transition = "0.5s";
            setTimeout(() => {
                alert.style.display = "none";
            }, 500);
        }, 3000);
    });

    // Confirm before PDF open
    const pdfLinks = document.querySelectorAll(".pdf-link");

    pdfLinks.forEach(link => {
        link.addEventListener("click", () => {
            console.log("Generating PDF report...");
        });
    });

});