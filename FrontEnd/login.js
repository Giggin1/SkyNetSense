document.addEventListener("DOMContentLoaded", () => {
  console.log("login.js caricato correttamente");

  const form = document.getElementById("login-form");
  const messageBox = document.getElementById("login-message");
  const submitBtn = document.querySelector("button[type='submit']");

  if (!form) {
    console.error("ERRORE: Impossibile trovare il form con id 'login-form'");
    return;
  }

  form.addEventListener("submit", async (e) => {
    // 1. BLOCCA il ricaricamento della pagina standard
    e.preventDefault();
    console.log("Pulsante premuto. Inizio procedura di Login...");

    // 2. Recupera i valori (SOLO Email e Password per il login)
    const emailInput = document.getElementById("login-email");
    const passwordInput = document.getElementById("login-password");

    const email = emailInput ? emailInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value : "";

    // 3. Controllo validità lato client
    if (!email || !password) {
      showMessage("Inserisci email e password.", "error");
      return;
    }

    // 4. Prepara i dati (Payload)
    const payload = {
      email: email,
      password: password
    };

    console.log("Payload pronto per l'invio:", payload);

    // Disabilita il bottone per evitare doppi click
    submitBtn.disabled = true;
    submitBtn.textContent = "Accesso in corso...";
    messageBox.style.display = "none";

    try {
      // 5. Chiamata al server (Fetch)
      // Assicurati che l'endpoint backend gestisca il POST a questo indirizzo
      const response = await fetch('/api/public/login', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify(payload)
      });

      console.log("Risposta server status:", response.status);

      const result = await response.json();

      if (!response.ok) {
        // Se c'è un errore (es. credenziali errate)
        throw new Error(result.error || "Credenziali non valide o errore server");
      }

      // 6. Successo
      // Salva il token se il server lo restituisce (opzionale, dipende dal tuo backend)
    

      showMessage("Login completato! Reindirizzamento...", "success");
        console.log("Login effettuato con successo:", result);
      
      // Pulisci il form
      form.reset();

      // Torna alla home dopo 1.5 secondi
      setTimeout(() => {
        window.location.href = "/";
      }, 1500);

    } catch (error) {
      console.error("Errore CATCH:", error);
      showMessage(error.message, "error");
      
      // Riabilita il bottone
      submitBtn.disabled = false;
      submitBtn.textContent = "Login aaaaaaaa";
    }
  });

  // Funzione helper per mostrare messaggi
  function showMessage(text, type) {
    messageBox.textContent = text;
    // Se nel CSS hai classi specifiche per success/error bene, 
    // altrimenti usa colori inline o assicurati che il CSS gestisca queste classi
    messageBox.className = `login-message ${type}`; 
    messageBox.style.display = "block";
    
    // Aggiunta opzionale per rendere il messaggio più visibile in base al tipo
    if(type === 'error') messageBox.style.color = 'red';
    if(type === 'success') messageBox.style.color = 'green';
  }
});
