document.addEventListener("DOMContentLoaded", () => {
  console.log("login.js caricato correttamente");

  const form = document.getElementById("login-form");
  const messageBox = document.getElementById("login-message");
  const submitBtn = document.querySelector("button[type='submit']");

  if (!form || !messageBox || !submitBtn) {
    console.error("ERRORE: elementi del form mancanti");
    return;
  }

  //semplice blocco per eventuali attacchi di forza bruta
  const MAX_ATTEMPTS = 5;          // dopo 5 errori...
  const LOCK_TIME_MS = 10 * 1000;  // ...blocca per 10 secondi
  let failedAttempts = 0;
  let lockUntil = 0;
  const defaultBtnLabel = submitBtn.textContent || "Login";

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    console.log("Pulsante premuto. Inizio procedura di Login...");

    // Controllo se siamo in "lock"
    const now = Date.now();
    if (now < lockUntil) {
      const secondsLeft = Math.ceil((lockUntil - now) / 1000);
      showMessage(
        `Troppi tentativi falliti. Riprova tra ${secondsLeft} secondi.`,
        "error"
      );
      return;
    }




    const emailInput = document.getElementById("login-email");
    const passwordInput = document.getElementById("login-password");

    const email = emailInput ? emailInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value : "";

    if (!email || !password) {
      showMessage("Inserisci email e password.", "error");
      return;
    }

    const payload = { email, password };
    console.log("Payload pronto per l'invio:", payload);

    // Disabilito il bottone mentre invio la richiesta
    submitBtn.disabled = true;
    submitBtn.textContent = "Accesso in corso...";
    messageBox.style.display = "none";

    try {
      const response = await fetch("/api/public/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      console.log("Risposta server status:", response.status);

      let result = {};
      try {
        result = await response.json();
      } catch (e) {
        result = {};
      }

      if (!response.ok) {
        // 401 / 403 = credenziali errate
        if (response.status === 401 || response.status === 403) {
          handleFailedAttempt(result.error);
        } else {
          showMessage(
            result.error || "Errore del server. Riprova più tardi.",
            "error"
          );
        }

        submitBtn.disabled = false;
        submitBtn.textContent = defaultBtnLabel;
        return;
      }

      // Se arrivo qui, login OK
      failedAttempts = 0;
      lockUntil = 0;

      showMessage("Login completato! Reindirizzamento...", "success");
      console.log("Login effettuato con successo:", result);

      form.reset();

      setTimeout(() => {
        window.location.href = "/";
      });
    } catch (error) {
      console.error("Errore CATCH:", error);
      showMessage(
        "dati errati.",
        "error"
      );

      submitBtn.disabled = false;
      submitBtn.textContent = defaultBtnLabel;
    }
  });

  
  // Mostra messaggi usando il box in alto
  function showMessage(text, type) {
    messageBox.textContent = text;
    messageBox.className = `login-message ${type}`;
    messageBox.style.display = "block";
    // I colori li gestisce il CSS (login-message.error / .success)
  }
});


