document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();
  initLogout();

  try {
    const res  = await API.getMe();
    const user = res.data;
    Auth.setUser(user);

    setText("profileName",          user.name);
    setText("profileGreeting",      `Hello, ${user.name.split(" ")[0]}!`);
    setText("profileRole",          formatRole(user.role));
    setText("profileCourseSection", user.course_section || "—");
    setText("profileStudentId",     user.student_id    || "—");
    setText("profileEmail",         user.email);

  } catch (err) {
    console.error("Failed to load profile:", err);
  }
});

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function formatRole(role) {
  return { superadmin: "Super Admin", admin: "Admin / Teacher", student: "Student" }[role] || role;
}

function initLogout() {
  document.querySelectorAll(".logout-btn").forEach(btn => {
    btn.addEventListener("click", () => API.logout());
  });
}