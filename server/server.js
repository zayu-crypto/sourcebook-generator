const express = require("express");
const cors = require("cors");
require("dotenv").config();

const { generateCards } = require("./gemini");

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.post("/api/generate-cards", async (req, res) => {
  try {
    const { outcome } = req.body;

    if (!outcome || outcome.trim() === "") {
      return res.status(400).json({ error: "Learning Outcome이 필요합니다" });
    }

    console.log("Generating cards for outcome:", outcome);
    const cards = await generateCards(outcome);

    res.json(cards);
  } catch (error) {
    console.error("Server error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get("/api/health", (req, res) => {
  res.json({ status: "Server is running" });
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
  if (!process.env.GOOGLE_GEMINI_API_KEY) {
    console.warn("⚠️  Warning: GOOGLE_GEMINI_API_KEY is not set");
  }
});
