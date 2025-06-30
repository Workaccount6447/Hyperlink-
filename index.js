
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Root route
app.get('/', (req, res) => {
  res.send('🌐 API Server is running.');
});

// Example POST route for receiving messages from your bot
app.post('/api/message', (req, res) => {
  const { chat_id, message } = req.body;

  if (!chat_id || !message) {
    return res.status(400).json({ error: "chat_id and message required." });
  }

  console.log(`📩 Message received from ${chat_id}: ${message}`);
  // You can add database logic, third-party calls, etc. here

  res.json({ status: 'ok', reply: `Received: ${message}` });
});

// Start the server
app.listen(PORT, () => {
  console.log(`✅ Server listening on port ${PORT}`);
});
