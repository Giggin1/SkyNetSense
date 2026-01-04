function ritornoAllaHome() {
   window.location.href = "/";
} 

async function caricaStazioni() {
  try {
    console.log("Caricamento stazioni...");
    const response = await fetch("/api/auth/my-stations");

    if (!response.ok) {
      throw new Error("Errore nella risposta dal server");
    }

    const stazioni = await response.json();
    mostraStazioni(stazioni);

  } catch (err) {
    console.error("Errore:", err);
    document.getElementById("station-list").innerHTML =
      "<p style='color:red;'>Errore nel caricamento dei dati.</p>";
  }
}

function mostraStazioni(stazioni) {
  const div = document.getElementById("station-list");

  div.innerHTML = stazioni
    .map(
      (s) => `
        <div style="border:1px solid #fa0000ff; padding:10px; margin:10px 0;">
          <strong>${s.nome_stazione}</strong><br>
        </div>
      `
    )
    .join("");
}

caricaStazioni();

function mostraForm(){
const formBox = document.getElementById("visualizzazioneModale");

formBox.style.display="flex";
}
function nascondiForm(){
const formBox = document.getElementById("visualizzazioneModale");

formBox.style.display="none";
}