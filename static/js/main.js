document.querySelectorAll("form").forEach(f => {
  f.addEventListener("submit", () => {
    const b = f.querySelector("button");
    b.innerText = "Processing...";
    b.disabled = true;
  });
});

const adminLink = document.getElementById("adminLink");

if (adminLink) {
    adminLink.addEventListener("click", function (e) {
        e.preventDefault();

        const password = prompt("Enter admin password:");
        if (!password) return;

        // Redirect to admin panel with key
        window.location.href = `/admin?key=${encodeURIComponent(password)}`;
    });
}