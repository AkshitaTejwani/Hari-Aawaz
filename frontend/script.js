// Hari Awaaz – client-side logic for the "Get Help" flow
const USE_MOCK = false;

// 👇 PASTE YOUR COLAB TRYCLOUDFLARE URL HERE (keep /api/complaint at the end)
const DEFAULT_API = "https://fwd-vsnet-managed-rogers.trycloudflare.com/api/complaint";
const API_URL = new URLSearchParams(location.search).get("api") || DEFAULT_API;

// Grab the elements we need from the page
const button = document.querySelector("button:not(#micBtn)");
const textarea = document.querySelector("textarea");
const landmarkInput = document.querySelector("input"); // Grab your new landmark input
const languageSelect = document.querySelector("select"); // Grab your language dropdown
const wrap = document.querySelector(".wrap");

const mockResult = {
  category: "DUMMY CATEGORY",
  urgency: "DUMMY URGENCY",
  authority: "DUMMY AUTHORITY",
  how_to_submit: "DUMMY SUBMISSION METHOD",
  rule: "DUMMY RULE",
  source: "DUMMY SOURCE",
  letter:
    "DUMMY COMPLAINT LETTER\n\nDUMMY RECIPIENT\n\nDUMMY SUBJECT\n\nDUMMY COMPLAINT TEXT\n\nDUMMY CLOSING\nDUMMY NAME"
};

function showResult(data) {
  const old = document.querySelector(".result-card");
  if (old) old.remove();

  const urgencyClass =
    data.urgency.toLowerCase() === "high"
      ? "badge-high"
      : data.urgency.toLowerCase() === "medium"
        ? "badge-medium"
        : "badge-low";

  const card = document.createElement("div");
  card.className = "result-card";
  card.innerHTML = `
    <div class="result-row">
      <span class="badge badge-category">${data.category}</span>
      <span class="badge ${urgencyClass}">${data.urgency} urgency</span>
    </div>
    <p class="result-field"><strong>Authority to contact:</strong> ${data.authority}</p>
    <p class="result-field"><strong>How to submit:</strong> ${data.how_to_submit}</p>
    <p class="result-field"><strong>Relevant rule:</strong> ${data.rule}</p>
    <p class="result-field"><strong>Source:</strong> <a href="${data.source}" target="_blank" rel="noopener">${data.source}</a></p>
    <div class="letter-box">
      <div class="letter-head">
        <div class="letter-label">Drafted complaint letter</div>
        <button type="button" class="copy-btn">Copy</button>
      </div>
      <pre>${data.letter}</pre>
    </div>
  `;

  const footer = document.querySelector("footer");
  wrap.insertBefore(card, footer);

  const copyBtn = card.querySelector(".copy-btn");
  const letterPre = card.querySelector(".letter-box pre");
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(letterPre.textContent).then(() => {
      copyBtn.textContent = "Copied!";
      setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
    });
  });
}

function showError(message) {
  const old = document.querySelector(".result-card");
  if (old) old.remove();

  const msg = document.createElement("p");
  msg.className = "empty-message";
  msg.textContent = message;
  const footer = document.querySelector("footer");
  wrap.insertBefore(msg, footer);
}

async function fetchResult(complaintText, landmarkText, selectedLanguage, timestamp) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      complaint: complaintText,
      location: landmarkText,
      language: selectedLanguage,
      timestamp: timestamp
    })
  });

  if (!response.ok) {
    throw new Error("Server responded with status " + response.status);
  }

  const data = await response.json();

  if (data.error) {
    throw new Error(data.error);
  }

  return data;
}

button.addEventListener("click", () => {
  const oldMsg = document.querySelector(".empty-message");
  if (oldMsg) oldMsg.remove();

  if (textarea.value.trim() === "") {
    const msg = document.createElement("p");
    msg.className = "empty-message";
    msg.textContent =
      "Please type your complaint above before clicking Get Help. ऊपर अपनी शिकायत लिखें।";
    const footer = document.querySelector("footer");
    wrap.insertBefore(msg, footer);
    textarea.focus();
    return;
  }

  // Read landmark input and language dropdown
  const landmarkText = landmarkInput ? landmarkInput.value.trim() : "";
  const selectedLanguage = languageSelect
    ? languageSelect.value || languageSelect.options[languageSelect.selectedIndex].text
    : "English";

  // Capture live IST timestamp at submission
  const timestamp =
    new Date().toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
      timeZone: "Asia/Kolkata"
    }) + " IST";

  button.textContent = "Working...";
  button.disabled = true;

  if (USE_MOCK) {
    setTimeout(() => {
      showResult(mockResult);
      button.textContent = "Get Help";
      button.disabled = false;
    }, 600);
  } else {
    fetchResult(textarea.value.trim(), landmarkText, selectedLanguage, timestamp)
      .then((data) => {
        showResult(data);
      })
      .catch((err) => {
        showError(
          "Sorry, we couldn't process your complaint right now. Please try again later. " +
            "त्रुटि: " + err.message
        );
      })
      .finally(() => {
        button.textContent = "Get Help";
        button.disabled = false;
      });
  }
});
(function () {
  const micBtn = document.getElementById('micBtn');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!micBtn) return;
  if (!SR) { micBtn.parentElement.style.display = 'none'; return; }
  const rec = new SR();
  micBtn.onclick = () => {
    rec.lang = document.getElementById('micLang').value;
    try { rec.start(); } catch (e) {}
    micBtn.textContent = '🎙 Listening...';
  };
  rec.onresult = e => {
    const box = document.getElementById('complaint-input');
    box.value += (box.value ? ' ' : '') + e.results[0][0].transcript;
  };
  rec.onend = rec.onerror = () => { micBtn.textContent = '🎤 Speak'; };
})();
