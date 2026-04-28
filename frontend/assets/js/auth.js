document.addEventListener("DOMContentLoaded", () => {
  if (Auth.isLoggedIn()) {
    window.location.href = "dashboard.html";
    return;
  }

  // Toggle reg n log
  const loginSection    = document.getElementById("loginSection");
  const registerSection = document.getElementById("registerSection");
  const toRegisterLink  = document.getElementById("toRegister");
  const toLoginLink     = document.getElementById("toLogin");

  toRegisterLink.addEventListener("click", (e) => {
    e.preventDefault();
    loginSection.style.display    = "none";
    registerSection.style.display = "block";
    clearErrors();
  });

  toLoginLink.addEventListener("click", (e) => {
    e.preventDefault();
    registerSection.style.display = "none";
    loginSection.style.display    = "block";
    clearErrors();
  });

  // Log
  document.getElementById("loginBtn").addEventListener("click", async () => {
    clearErrors();
    const email    = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    if (!email || !password) {
      showError("loginError", "Email and password are required.");
      return;
    }

    setLoading("loginBtn", true);
    try {
      const res = await API.login(email, password);
      Auth.setToken(res.data.access_token);
      localStorage.setItem("plv_refresh_token", res.data.refresh_token);
      Auth.setUser(res.data.user);
      window.location.href = "dashboard.html";
    } catch (err) {
      showError("loginError", err.error || "Login failed. Please try again.");
    } finally {
      setLoading("loginBtn", false);
    }
  });

  // Reg
  document.getElementById("registerBtn").addEventListener("click", async () => {
    clearErrors();
    const payload = {
      name:           document.getElementById("regName").value.trim(),
      email:          document.getElementById("regEmail").value.trim(),
      student_id:     document.getElementById("regStudentId").value.trim(),
      course_section: document.getElementById("regCourseSection").value.trim(),
      password:       document.getElementById("regPassword").value,
    };

    const missing = [];
    if (!payload.name)           missing.push("Name");
    if (!payload.email)          missing.push("School Email");
    if (!payload.student_id)     missing.push("Student ID");
    if (!payload.course_section) missing.push("Course/Section");
    if (!payload.password)       missing.push("Password");

    if (missing.length) {
      showError("registerError", `Required: ${missing.join(", ")}`);
      return;
    }

    setLoading("registerBtn", true);
    try {
      await API.register(payload);
      
      const res = await API.login(payload.email, payload.password);
      Auth.setToken(res.data.access_token);
      localStorage.setItem("plv_refresh_token", res.data.refresh_token);
      Auth.setUser(res.data.user);
      window.location.href = "dashboard.html";
    } catch (err) {
      
      if (err.errors) {
        const msgs = Object.values(err.errors).join(" ");
        showError("registerError", msgs);
      } else {
        showError("registerError", err.error || "Registration failed.");
      }
    } finally {
      setLoading("registerBtn", false);
    }
  });

  function showError(id, msg) {
    const el = document.getElementById(id);
    if (el) { el.textContent = msg; el.style.display = "block"; }
  }

  function clearErrors() {
    document.querySelectorAll(".form-error").forEach(el => {
      el.textContent = "";
      el.style.display = "none";
    });
  }

  function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.disabled    = loading;
    btn.textContent = loading ? "Please wait…" : (btnId === "loginBtn" ? "Log in" : "Register");
  }
});