const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(bodyParser.json());

const PORT = process.env.PORT || 3000;

app.post('/chat', async (req, res) => {
    const { userId, model, mode, message } = req.body;
    console.log(`Received from ${userId}: ${message} (Model: ${model}, Mode: ${mode})`);
    const response = `🧠 [${model} - ${mode}] says: This is a response to "${message}"`;
    res.json({ response });
});

app.listen(PORT, () => {
    console.log(`puter.js API running on http://localhost:${PORT}`);
});
