document.addEventListener("DOMContentLoaded", () => {
  console.log("registrazione.js caricato correttamente");

  const form = document.getElementById("registration-form");
  const messageBox = document.getElementById("reg-message");
  const submitBtn = document.querySelector("button[type='submit']");

  if (!form) {
    console.error("ERRORE: Impossibile trovare il form con id 'registration-form'");
    return;
  }

  form.addEventListener("submit", async (e) => {
    // 1. BLOCCA il ricaricamento della pagina standard
    e.preventDefault();
    console.log("Pulsante premuto. Inizio procedura...");

    // 2. Recupera i valori
    const nickname = document.getElementById("reg-nickname").value.trim();
    const nome = document.getElementById("reg-name").value.trim();
    const cognome = document.getElementById("reg-surname").value.trim();
    const codice = document.getElementById("reg-codice").value.trim().toUpperCase();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;

    // 3. Controllo validità lato client
    if (!nickname || !nome || !cognome || !codice || !email || !password) {
      showMessage("Compila tutti i campi.", "error");
      return;
    }

    if (codice.length !== 16) {
      showMessage("Il Codice Fiscale deve essere di 16 caratteri.", "error");
      return;
    }

    // 4. Prepara i dati (Payload)
    const payload = {
      nickname: nickname,
      nome: nome,
      cognome: cognome,
      codice_fiscale: codice,
      email: email,
      password: password
    };

    console.log("Payload pronto per l'invio:", payload);

    // Disabilita il bottone per evitare doppi click
    submitBtn.disabled = true;
    submitBtn.textContent = "Invio in corso...";
    messageBox.style.display = "none";

    try {
      // 5. Chiamata al server (Fetch)
      console.log("Invio richiesta POST a /api/public/register...");
      
      const response = await fetch('/api/public/register', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify(payload)
      });

      console.log("Risposta server status:", response.status);

      const result = await response.json();
      console.log("Dati ricevuti dal server:", result);

      if (!response.ok) {
        // Se c'è un errore (es. email già usata o errore server)
        throw new Error(result.error || "Errore sconosciuto durante la registrazione");
      }

      // 6. Successo
      showMessage("Registrazione completata! Reindirizzamento...", "success");
      
      // Pulisci il form
      form.reset();

      // Torna alla home dopo 2 secondi
      setTimeout(() => {
        window.location.href = "/";
      }, 2000);

    } catch (error) {
      console.error("Errore CATCH:", error);
      showMessage(error.message, "error");
      submitBtn.disabled = false;
      submitBtn.textContent = "Registrati";
    }
  });

  // Funzione helper per mostrare messaggi
  function showMessage(text, type) {
    messageBox.textContent = text;
    messageBox.className = `register-message ${type}`;
    messageBox.style.display = "block";
  }
});