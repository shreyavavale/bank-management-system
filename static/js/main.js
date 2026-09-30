// Sidebar toggle for small screens
document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.getElementById("sidebarToggle");
  var sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () { sidebar.classList.toggle("open"); });
  }

  // Delete confirmation popup: every .btn-delete opens the same Bootstrap modal
  var modalEl = document.getElementById("deleteModal");
  if (modalEl && window.bootstrap) {
    var modal = new bootstrap.Modal(modalEl);
    document.querySelectorAll(".btn-delete").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.getElementById("deleteForm").action = btn.dataset.url;
        document.getElementById("deleteName").textContent = btn.dataset.name;
        modal.show();
      });
    });
  }

  // Auto-hide success alerts after 5 seconds
  setTimeout(function () {
    document.querySelectorAll(".alert-success").forEach(function (el) {
      if (window.bootstrap) { bootstrap.Alert.getOrCreateInstance(el).close(); }
    });
  }, 5000);
});
