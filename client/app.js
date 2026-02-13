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
          ${source ? `<div class="card-source">📸 출처: ${escapeHtml(source)}</div>` : ""}
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
      body { font-family: Arial, sans-serif; color: #333; }
      h1 { color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; }
      h2 { color: #333; margin-top: 30px; margin-bottom: 15px; }
      .card { page-break-inside: avoid; border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 8px; }
      .card-number { background: #f3f4f6; color: #667eea; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 600; margin-bottom: 12px; display: inline-block; }
      .card-title { font-size: 1.2em; font-weight: bold; margin-bottom: 15px; }
      .section { margin-bottom: 12px; }
      .label { font-size: 0.9em; font-weight: bold; color: #667eea; text-transform: uppercase; margin-bottom: 4px; }
      .content { font-size: 0.95em; color: #666; line-height: 1.5; }
      .cues { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
      .cue-tag { background: #f3f4f6; color: #555; padding: 4px 10px; border-radius: 20px; font-size: 0.85em; }
      .outcome { background: #f0f4ff; border-left: 4px solid #667eea; padding: 15px; margin-bottom: 30px; }
      .card-image { max-width: 100%; height: auto; border-radius: 6px; margin: 10px 0; }
      .card-source { font-size: 0.85em; color: #666; margin-top: 8px; font-style: italic; }
    </style>
    <h1>📚 Sourcebook</h1>
    <div class="outcome">
      <h3 style="margin-top: 0; color: #667eea;">Learning Outcome</h3>
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
          ${source ? `<div class="card-source">📸 출처: ${escapeHtml(source)}</div>` : ""}
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
