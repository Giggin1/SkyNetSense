"use strict";

// ==============================
// 1. Inizializza mappa
// ==============================

const map = L.map("map").setView([41.8719, 12.5674], 5); // Italia centrata

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

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

// ==============================
// 2. Dati finti delle stazioni
//    (più avanti li prenderai dal backend)
// ==============================
const stazioni = [
  {
    cf_utente: "RSSMRA99A01H501X",
    nome_stazione: "Skynetsense_Casa",
    paese: "Italia",
    regione: "Lombardia",
    citta: "Milano",
    ultimo_dato: "2025-11-18 10:15:00",
    dati: {
      Temperatura: "22.0 °C",
      Umidità: "44 %",
      "PM2.5": "8.4 µg/m³",
    },
  },
  {
    cf_utente: "RSSMRA99A01H501X",
    nome_stazione: "Skynetsense_Tetto",
    paese: "Italia",
    regione: "Lombardia",
    citta: "Milano",
    ultimo_dato: "2025-11-18 10:20:00",
    dati: {
      Temperatura: "19.3 °C",
      Velocità_Vento: "3.2 m/s",
    },
  },
  {
    cf_utente: "BNCLNZ01B45F205Y",
    nome_stazione: "Skynetsense_Campagna",
    paese: "Italia",
    regione: "Lazio",
    citta: "Viterbo",
    ultimo_dato: "2025-11-18 09:50:00",
    dati: {
      Temperatura: "16.8 °C",
      Umidità: "61.5 %",
      PM10: "12.1 µg/m³",
    },
  },
];

const stationListDiv = document.getElementById("station-list");

// ==============================
// 3. Disegna marker + card laterali
// ==============================

stazioni.forEach((s) => {
  const coords = getCoordsForCity(s.citta);

  const marker = L.circleMarker([coords.lat, coords.lng], {
    radius: 8,
    color: "#22c55e",
    weight: 2,
    fillColor: "#22c55e",
    fillOpacity: 0.9,
  }).addTo(map);

  let popupHtml = `<strong>${s.nome_stazione}</strong><br/>
    ${s.citta} (${s.regione})<br/>
    <small>Ultimo dato: ${s.ultimo_dato}</small><br/><br/>`;

  popupHtml += "<strong>Dati recenti:</strong><br/>";
  for (const [chiave, valore] of Object.entries(s.dati)) {
    popupHtml += `${chiave}: ${valore}<br/>`;
  }

  marker.bindPopup(popupHtml);

  const card = document.createElement("div");
  card.className = "station-card";
  card.innerHTML = `
    <div class="station-title-row">
      <div class="station-title">${s.nome_stazione}</div>
      <div class="station-chip">${s.citta}</div>
    </div>
    <div class="station-location">${s.citta} (${s.regione}) • ${s.paese}</div>
    <div class="station-data">
      <div class="pill">
        <span class="pill-dot"></span>
        Ultimo dato: ${s.ultimo_dato}
      </div>
      ${Object.entries(s.dati)
        .map(
          ([k, v]) => `
        <div class="data-line">
          <span class="data-key">${k}</span>
          <span class="data-value">${v}</span>
        </div>`
        )
        .join("")}
    </div>
  `;

  card.addEventListener("click", () => {
    map.setView([coords.lat, coords.lng], 11);
    marker.openPopup();
  });

  stationListDiv.appendChild(card);
});

// In futuro: sostituisci l'array "stazioni" con una fetch al backend, es:
// fetch('/api/public/stazioni').then(res => res.json()).then(stazioni => { ... });
