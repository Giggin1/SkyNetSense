"use strict";

// ==============================
// 1. Inizializza mappa in modo robusto (ritardato)
//    per evitare che la mappa non venga renderizzata su mobile
// ==============================

let map = null;

function initMap() {
  if (map) return;
  // Centro sul Sud Italia (avvia la vista verso Napoli / Campania)
  map = L.map("map").setView([40.5, 14.0], 6);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  // Dopo un breve delay, invalida la size per forzare il render corretto
  setTimeout(() => {
    try {
      map.invalidateSize();
    } catch (e) {
      // ignora
    }
  }, 200);

  // Ricalcola dimensione su resize/orientation
  window.addEventListener("resize", () => {
    try {
      map.invalidateSize();
    } catch (e) {}
  });
  window.addEventListener("orientationchange", () => {
    // piccolo delay per permettere al browser di aggiornare layout
    setTimeout(() => {
      try {
        map.invalidateSize();
      } catch (e) {}
    }, 200);
  });
}

// Mappa città -> coordinate approssimative
const cityCoords = {
  Milano: { lat: 45.4642, lng: 9.19 },
  Viterbo: { lat: 42.42, lng: 12.11 },
  Roma: { lat: 41.9028, lng: 12.4964 },
  Napoli: { lat: 40.8518, lng: 14.2681 },
};

function getCoordsForCity(citta) {
  if (cityCoords[citta]) {
    return cityCoords[citta];
  }
  // fallback: centro Italia
  return { lat: 41.8719, lng: 12.5674 };
}

let stationListDiv = null;


// ==============================
// 2. Funzione che disegna stazioni su mappa + sidebar
// ==============================

function renderStazioni(stazioni) {
  // pulisco la lista laterale
  if (!stationListDiv) stationListDiv = document.getElementById("station-list");
  stationListDiv.innerHTML = "";

  stazioni.forEach((s) => {
    const coords = getCoordsForCity(s.citta);

    // Marker verde sulla mappa
    const marker = L.circleMarker([coords.lat, coords.lng], {
      radius: 8,
      color: "#22c55e",
      weight: 2,
      fillColor: "#22c55e",
      fillOpacity: 0.9,
    }).addTo(map);

    // Popup sulla mappa
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
    }

    marker.bindPopup(popupHtml);

    // Card nella sidebar
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
          ${
            s.ultimo_dato
              ? "Ultimo dato: " + s.ultimo_dato
              : "Nessun dato disponibile"
          }
        </div>
        ${
          s.dati && Object.keys(s.dati).length > 0
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
      map.setView([coords.lat, coords.lng], 11);
      marker.openPopup();
    });

    stationListDiv.appendChild(card);
  });

    // Assicuriamoci che la mappa ricalcoli le dimensioni dopo aver inserito i marker
    if (map) {
      try {
        map.invalidateSize();
      } catch (e) {}
    }
}

// ==============================
// 3. Chiama il backend per caricare le stazioni
// ==============================

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

// Avvia subito il caricamento quando la pagina è pronta
document.addEventListener("DOMContentLoaded", () => {
  // elemento della sidebar
  stationListDiv = document.getElementById("station-list");

  // inizializza la mappa e carica i dati
  initMap();
  caricaStazioni();
});
