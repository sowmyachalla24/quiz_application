// === REGISTER FORM ===
const registerForm = document.getElementById("registerForm");
if (registerForm) {
    registerForm.addEventListener("submit", function(event) {
        event.preventDefault();
        
        const name = document.getElementById("name").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const dob = document.getElementById("date").value;
        const male = document.getElementById("male").checked;
        const female = document.getElementById("female").checked;
        
        let gender = "";
        if (male) gender = "male";
        else if (female) gender = "female";

        if (!name || !email || !password || !dob || !gender) {
            alert("Please fill all the fields");
            return;
        }

        fetch("/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password, dob, gender })
        })
        .then(response => response.json().then(data => ({ status: response.status, data })))
        .then(({ status, data }) => {
            alert(data.message);
            if (status === 201) {
                window.location.href = "/login";
            }
        })
        .catch(err => console.error("Registration error:", err));
    });
}

// === LOGIN FORM ===
const loginForm = document.getElementById("loginForm");
if (loginForm) {
    loginForm.addEventListener("submit", function(event) {
        event.preventDefault();
        
        const email = document.getElementById("loginEmail").value;
        const password = document.getElementById("loginPassword").value;

        if (!email || !password) {
            alert("Please fill all the fields");
            return;
        }

        fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        })
        .then(response => response.json().then(data => ({ status: response.status, data })))
        .then(({ status, data }) => {
            alert(data.message);
            if (status === 200) {
                window.location.href = "/quiz";
            }
        })
        .catch(err => console.error("Login error:", err));
    });
}

// === QUIZ FORM ===
const quizForm = document.getElementById('quiz-form');
if (quizForm) {
    quizForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        let answers = []; // Fixed: Added missing empty array brackets
        
        for (let [key, value] of formData.entries()) {
            answers.push({ question: key, answer: value });
        }

        fetch('/api/quiz', {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answers: answers })
        })
        .then(response => {
            if (response.ok) {
                window.location.href = '/results';
            } else {
                alert("Submission failed. Make sure you are logged in.");
            }
        })
        .catch(err => console.error("Quiz submission error:", err));
    });
}

// === RESULTS PRESENTATION ===
const resultsDiv = document.getElementById("results");
if (resultsDiv) {
    fetch("/api/results", { method: "GET" })
        .then(response => response.json())
        .then(data => {
            resultsDiv.innerHTML = "";
            if (data.courses && data.courses.length > 0) {
                data.courses.forEach((course, index) => {
                    let p = document.createElement("p");
                    p.textContent = `Recommended Course ${index + 1}: ${course}`;
                    resultsDiv.appendChild(p);
                });
            } else {
                resultsDiv.innerHTML = "<p>No course recommendations found. Try retaking the quiz!</p>";
            }
        })
        .catch(err => console.error("Error fetching results:", err));
}






