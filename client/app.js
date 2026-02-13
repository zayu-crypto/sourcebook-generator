// Use relative path for API calls (works in both local and deployed environments)
const API_BASE_URL = "/api";

let generatedCards = [];
let selectedCards = new Set();

// DOM Elements
const outcomeInput = document.getElementById("outcomeInput");
const generateBtn = document.getElementById("generateBtn");
const loadingMessage = document.getElementById("loadingMessage");
const errorMessage = document.getElementById("errorMessage");
const cardsSection = document.getElementById("cardsSection");
const cardsContainer = document.getElementById("cardsContainer");
const selectedCount = document.getElementById("selectedCount");
const exportPdfBtn = document.getElementById("exportPdfBtn");
const exportJsonBtn = document.getElementById("exportJsonBtn");

// Guide toggle
const guideToggle = document.getElementById("guideToggle");
const guideBody = document.getElementById("guideBody");
const guideArrow = document.getElementById("guideArrow");

guideToggle.addEventListener("click", () => {
  guideBody.classList.toggle("open");
  guideArrow.classList.toggle("open");
});

// Refine elements
const refineBtn = document.getElementById("refineBtn");
const refineMessage = document.getElementById("refineMessage");
const refineResult = document.getElementById("refineResult");
const refinePreview = document.getElementById("refinePreview");
const refineChanges = document.getElementById("refineChanges");
const applyRefineBtn = document.getElementById("applyRefineBtn");
const dismissRefineBtn = document.getElementById("dismissRefineBtn");

let refinedText = "";

refineBtn.addEventListener("click", refineOutcome);
applyRefineBtn.addEventListener("click", () => {
  outcomeInput.value = refinedText;
  refineResult.style.display = "none";
});
dismissRefineBtn.addEventListener("click", () => {
  refineResult.style.display = "none";
});

async function refineOutcome() {
  const draft = outcomeInput.value.trim();

  if (!draft) {
    showError("먼저 Learning Outcome 초안을 입력해주세요.");
    return;
  }

  refineBtn.disabled = true;
  refineMessage.style.display = "flex";
  refineResult.style.display = "none";
  errorMessage.style.display = "none";

  try {
    const response = await fetch(`${API_BASE_URL}/refine-outcome`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ draft }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "다듬기에 실패했습니다");
    }

    const data = await response.json();
    refinedText = data.refined || draft;

    refinePreview.textContent = refinedText;
    refineChanges.textContent = data.changes || "";
    refineResult.style.display = "block";
    refineResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (error) {
    showError(error.message);
  } finally {
    refineBtn.disabled = false;
    refineMessage.style.display = "none";
  }
}

// Event Listeners
generateBtn.addEventListener("click", generateCards);
exportPdfBtn.addEventListener("click", exportToPDF);
exportJsonBtn.addEventListener("click", exportToJSON);

// API Call to generate cards
async function generateCards() {
  const outcome = outcomeInput.value.trim();

  if (!outcome) {
    showError("Learning Outcome을 입력해주세요.");
    return;
  }

  generateBtn.disabled = true;
  loadingMessage.style.display = "flex";
  errorMessage.style.display = "none";

  try {
    const response = await fetch(`${API_BASE_URL}/generate-cards`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ outcome }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "서버 오류가 발생했습니다");
    }

    const data = await response.json();
    generatedCards = data.cards || [];

    if (generatedCards.length === 0) {
      throw new Error("카드가 생성되지 않았습니다");
    }

    displayCards();
    cardsSection.style.display = "block";
    cardsSection.scrollIntoView({ behavior: "smooth" });
    selectedCards.clear();
    updateSelectedCount();
  } catch (error) {
    showError(error.message);
  } finally {
    generateBtn.disabled = false;
    loadingMessage.style.display = "none";
  }
}

// Display generated cards
function displayCards() {
  cardsContainer.innerHTML = "";

  generatedCards.forEach((card, index) => {
    const cardEl = createCardElement(card, index + 1);
    cardsContainer.appendChild(cardEl);
  });
}

// Create card element
function createCardElement(card, cardNumber) {
  const div = document.createElement("div");
  div.className = "card";
  div.dataset.cardId = card.id;

  const searchCuesHTML = (card.searchCues || [])
    .map((cue) => `<span class="cue-tag">${escapeHtml(cue)}</span>`)
    .join("");

  // 핵심 자료 표시 (이미지 또는 텍스트)
  let coreImageHTML = "";
  if (card.coreImage) {
    const imageUrl = card.coreImage.url || "";
    const source = card.coreImage.source || "출처 미상";
    const caption = card.coreImage.caption || "";
    
    coreImageHTML = `
      <div class="card-image-container">
        ${imageUrl ? `<img src="${imageUrl}" alt="${caption}" class="card-image" loading="lazy" />` : '<div class="card-image-placeholder">이미지를 불러올 수 없습니다</div>'}
        <div class="card-section">
          <div class="card-label">핵심 자료 (Core Material)</div>
          ${caption ? `<div class="card-content">${escapeHtml(caption)}</div>` : ""}
          ${source ? `<div class="card-source">출처: ${escapeHtml(source)}</div>` : ""}
        </div>
      </div>
    `;
  } else if (card.primaryEvidence) {
    // 호환성을 위해 primaryEvidence도 지원
    coreImageHTML = `
      <div class="card-section">
        <div class="card-label">핵심 자료 (Core Material)</div>
        <div class="card-content">${escapeHtml(card.primaryEvidence)}</div>
      </div>
    `;
  }

  div.innerHTML = `
    <input type="checkbox" class="card-checkbox" data-card-id="${card.id}" />
    
    ${coreImageHTML}
    
    <div class="card-number">카드 ${cardNumber}</div>
    <div class="card-title">${escapeHtml(card.title)}</div>
    
    <div class="card-section">
      <div class="card-label">핵심질문 (Essential Question)</div>
      <div class="card-content">${escapeHtml(card.essentialQuestion)}</div>
    </div>
    
    <div class="card-section">
      <div class="card-label">탐색큐 (Search Cues)</div>
      <div class="search-cues">${searchCuesHTML}</div>
    </div>
  `;

  // Click handler for card selection
  const checkbox = div.querySelector(".card-checkbox");
  div.addEventListener("click", (e) => {
    if (e.target !== checkbox) {
      checkbox.checked = !checkbox.checked;
    }
    toggleCardSelection(checkbox);
  });

  checkbox.addEventListener("change", toggleCardSelection);

  return div;
}

// Toggle card selection
function toggleCardSelection(checkbox) {
  const cardId = checkbox.dataset.cardId;
  const cardEl = document.querySelector(`[data-card-id="${cardId}"]`);

  if (checkbox.checked) {
    selectedCards.add(cardId);
    cardEl.classList.add("selected");
  } else {
    selectedCards.delete(cardId);
    cardEl.classList.remove("selected");
  }

  updateSelectedCount();
}

// Update selected count
function updateSelectedCount() {
  const count = selectedCards.size;
  selectedCount.textContent = `선택된 카드: ${count}개`;

  exportPdfBtn.disabled = count === 0;
  exportJsonBtn.disabled = count === 0;
}

// Export to PDF
function exportToPDF() {
  if (selectedCards.size === 0) {
    showError("최소 1개 이상의 카드를 선택해주세요");
    return;
  }

  const selectedCardsData = generatedCards.filter((card) =>
    selectedCards.has(card.id.toString())
  );

  const element = document.createElement("div");
  element.innerHTML = generatePDFContent(selectedCardsData);

  const opt = {
    margin: 10,
    filename: `sourcebook_${new Date().getTime()}.pdf`,
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { orientation: "portrait", unit: "mm", format: "a4" },
  };

  html2pdf().set(opt).from(element).save();
}

// Generate PDF content HTML
function generatePDFContent(cards) {
  const outcome = outcomeInput.value;
  let html = `
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif; color: #222; }
      h1 { color: #222; border-bottom: 1px solid #ddd; padding-bottom: 10px; font-weight: 600; }
      .card { page-break-inside: avoid; border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 20px; border-radius: 6px; }
      .card-number { color: #999; font-size: 0.78em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; display: block; }
      .card-title { font-size: 1.1em; font-weight: 600; margin-bottom: 15px; color: #222; }
      .section { margin-bottom: 12px; }
      .label { font-size: 0.78em; font-weight: 600; color: #999; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
      .content { font-size: 0.9em; color: #555; line-height: 1.6; }
      .cues { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
      .cue-tag { background: #f5f5f5; color: #555; padding: 4px 10px; border-radius: 20px; font-size: 0.82em; border: 1px solid #e0e0e0; }
      .outcome { border-left: 2px solid #222; padding: 15px; margin-bottom: 30px; background: #fafafa; }
      .card-image { max-width: 100%; height: auto; border-radius: 4px; margin: 10px 0; }
      .card-source { font-size: 0.78em; color: #999; margin-top: 8px; }
    </style>
    <h1>Sourcebook</h1>
    <div class="outcome">
      <h3 style="margin-top: 0; color: #222; font-weight: 600;">Learning Outcome</h3>
      <p style="line-height: 1.6; white-space: pre-wrap;">${escapeHtml(outcome)}</p>
    </div>
  `;

  cards.forEach((card, index) => {
    const searchCuesHTML = (card.searchCues || [])
      .map((cue) => `<span class="cue-tag">${escapeHtml(cue)}</span>`)
      .join("");

    // 핵심 자료 표시
    let coreImageHTML = "";
    if (card.coreImage) {
      const imageUrl = card.coreImage.url || "";
      const source = card.coreImage.source || "출처 미상";
      const caption = card.coreImage.caption || "";
      
      coreImageHTML = `
        <div class="section">
          <div class="label">핵심 자료 (Core Material)</div>
          ${imageUrl ? `<img src="${imageUrl}" alt="${caption}" class="card-image" style="max-width: 100%; height: auto;"/>` : ""}
          ${caption ? `<div class="content">${escapeHtml(caption)}</div>` : ""}
          ${source ? `<div class="card-source">출처: ${escapeHtml(source)}</div>` : ""}
        </div>
      `;
    } else if (card.primaryEvidence) {
      // 호환성
      coreImageHTML = `
        <div class="section">
          <div class="label">핵심 자료 (Core Material)</div>
          <div class="content">${escapeHtml(card.primaryEvidence)}</div>
        </div>
      `;
    }

    html += `
      <div class="card">
        <div class="card-number">카드 ${index + 1}</div>
        <div class="card-title">${escapeHtml(card.title)}</div>
        
        ${coreImageHTML}
        
        <div class="section">
          <div class="label">핵심질문 (Essential Question)</div>
          <div class="content">${escapeHtml(card.essentialQuestion)}</div>
        </div>
        
        <div class="section">
          <div class="label">탐색큐 (Search Cues)</div>
          <div class="cues">${searchCuesHTML}</div>
        </div>
      </div>
    `;
  });

  return html;
}

// Export to JSON
function exportToJSON() {
  if (selectedCards.size === 0) {
    showError("최소 1개 이상의 카드를 선택해주세요");
    return;
  }

  const selectedCardsData = generatedCards.filter((card) =>
    selectedCards.has(card.id.toString())
  );

  const exportData = {
    outcome: outcomeInput.value,
    generatedAt: new Date().toISOString(),
    totalCards: selectedCardsData.length,
    cards: selectedCardsData,
  };

  const dataStr = JSON.stringify(exportData, null, 2);
  const dataBlob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `sourcebook_${new Date().getTime()}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

// Show error message
function showError(message) {
  errorMessage.textContent = message;
  errorMessage.style.display = "block";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Escape HTML special characters
function escapeHtml(text) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}
