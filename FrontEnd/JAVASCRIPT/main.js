


//funzione utile a inizializzare la mappa, utilizzeremo Leaflet.js,
//  una libreria open source di mappa interattiva
let map = null;
function initMap() {
  if (map) return;
  // Centro sul Sud Italia (avvia la vista verso Napoli / Campania)
  map = L.map("map").setView([40.9, 14.2], 7);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
}




//funzione che renderizza le stazioni sulla mappa e nella sidebar a destra
let stationListDiv = null;
function renderStazioni(stazioni) {
  // pulisco la lista laterale
  if (!stationListDiv) stationListDiv = document.getElementById("station-list");
  stationListDiv.innerHTML = "";

  stazioni.forEach((s) => {

    let coords = { lat: s.latitudine, lng: s.longitudine }; 

    // Marker verde sulla mappa
    const marker = L.circle([coords.lat, coords.lng], {
      radius: 200,
      color: "#22c55e",
      weight: 2,
      fillColor: "#22c55e",
      fillOpacity: 0.25,
    }).addTo(map);

    // se si clicca sul marker, mostra i dettagli in un popup
    let popupHtml = `<strong>${s.nome_stazione}</strong><br/>
      ${s.citta || ""} ${s.regione ? "(" + s.regione + ")" : ""}<br/>`;

    if (s.ultimo_dato) {
      popupHtml += `<small>Ultimo dato: ${s.ultimo_dato}</small><br/><br/>`;
    } else {
      popupHtml += `<small>Nessun dato disponibile</small><br/><br/>`;
    }

    if (s.dati && Object.keys(s.dati).length > 0) {
      popupHtml += "<strong>Dati recenti:</strong><br/>";
      for (const [chiave, valore] of Object.entries(s.dati)) {
        popupHtml += `${chiave}: ${valore}<br/>`;
      }
    }marker.bindPopup(popupHtml);

    // creiamo la card nella sidebar a destra
    const card = document.createElement("div");
    card.className = "station-card";
    card.innerHTML = `
      <div class="station-title-row">
        <div class="station-title">${s.nome_stazione}</div>
        <div class="station-chip">${s.citta || ""}</div>
      </div>
      <div class="station-location">
        ${s.citta || ""} ${s.regione ? "(" + s.regione + ")" : ""} • ${s.paese || ""}
      </div>
      <div class="station-data">
        <div class="pill">
          <span class="pill-dot"></span>
          ${s.ultimo_dato
        ? "Ultimo dato: " + s.ultimo_dato
        : "Nessun dato disponibile"
      }
        </div>
        ${s.dati && Object.keys(s.dati).length > 0
        ? Object.entries(s.dati)
          .map(
            ([k, v]) => `
          <div class="data-line">
            <span class="data-key">${k}</span>
            <span class="data-value">${v}</span>
          </div>`
          )
          .join("")
        : `<div class="data-line">
                 <span class="data-key">Dati</span>
                 <span class="data-value">Nessun dato</span>
               </div>`
      }
      </div>
    `;

    // Click sulla card → centra la mappa e apre il popup
    card.addEventListener("click", () => {
      map.setView([coords.lat, coords.lng], 15); // zooma sulla stazione quando si clicca sulla card
      marker.openPopup();
    });

    stationListDiv.appendChild(card);
  });
}





//funzione usata per caricare su un file json tutte le stazioni presenti sul db
async function caricaStazioni() {
  try {
    // visto che index.html viene servito da Flask su http://127.0.0.1:5000/
    // possiamo usare un path relativo:
    const response = await fetch("/api/public/stazioni");

    if (!response.ok) {
      throw new Error("Risposta non OK dal server");
    }

    const stazioni = await response.json();
    renderStazioni(stazioni);
  } catch (err) {
    console.error("Errore nel caricamento delle stazioni:", err);
    stationListDiv.innerHTML =
      '<div style="font-size:0.85rem;color:#fca5a5;">Errore nel caricamento dei dati. Verifica che il server Flask (app.py) sia in esecuzione.</div>';
  }
}





async function checkLoginStatus() {
  const userPanel = document.getElementById("user-panel");
  if (!userPanel) return; // Se non siamo nella home o manca l'elemento

  try {
    const response = await fetch("/api/auth/status");
    const data = await response.json();

    if (data.logged_in) {
      // UTENTE LOGGATO: Mostra Benvenuto e Logout
      userPanel.innerHTML = `
        <span style="font-weight:bold; color:#333;">Ciao, ${data.nickname}</span>

        <button onclick="vaiAlleStazioni()"; class="btn-stazioni" style="cursor:pointer; background:#ef4444; border:none; color:white; padding: 0.5rem 1rem; border-radius:4px;">Vai alle stazioni</button>
        
        <button onclick="doLogout()" class="btn-login" style="cursor:pointer; background:#ef4444; border:none; color:white; padding: 0.5rem 1rem; border-radius:4px;">Logout</button>
      `;
    } else {
      // UTENTE NON LOGGATO: Mostra Login e Registrati
      userPanel.innerHTML = `
        <div class="header-right">Vista pubblica • Solo lettura</div>
        <a href="/login" class="btn-login" style="text-decoration: none; text-align: center;">Login</a>
        <a href="/registrazione" class="btn-register" style="text-decoration: none; text-align: center;">Registrati</a>
      `;
    }
  } catch (e) {
    console.error("Errore check sessione:", e);
  }
}






// Funzione per il Logout
async function doLogout() {
  await fetch("/api/auth/logout");
  window.location.reload(); // Ricarica la pagina per resettare la vista
}




//funzione che riporta una volta cliccato al file delle stazioni 
function vaiAlleStazioni() {
  window.location.href = "/stazioni"; // Reindirizza alla pagina di gestione delle stazioni
}



function ricaricaMappa() {
  if (map) {
    map.setView([40.9, 14.2], 7); // Centro e zoom iniziali
  }
}


// Avvia subito il caricamento quando la pagina è pronta
document.addEventListener("DOMContentLoaded", () => {
  // elemento della sidebar
  stationListDiv = document.getElementById("station-list");

  // inizializza la mappa e carica i dati
  initMap();
  caricaStazioni();
  checkLoginStatus();
});


