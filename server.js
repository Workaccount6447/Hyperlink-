
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const axios = require('axios');

const app = express();
const port = process.env.PORT || 3000;
const API_KEY = process.env.PUTER_API_KEY || 'your-puter-api-key';
const API_BASE_URL = 'https://api.puter.ai';

app.use(cors());
app.use(bodyParser.json());

app.post('/chat', async (req, res) => {
  const { prompt, model = 'gpt-3.5-turbo', system = '', messages = [] } = req.body;

  try {
    const response = await axios.post(`${API_BASE_URL}/v1/chat/completions`, {
      model,
      messages: messages.length ? messages : [{ role: 'user', content: prompt }],
      ...(system ? { system } : {})
    }, {
      headers: { Authorization: `Bearer ${API_KEY}` }
    });

    res.json({ result: response.data.choices[0].message.content });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/image', async (req, res) => {
  const { prompt } = req.body;

  try {
    const response = await axios.post(`${API_BASE_URL}/v1/images/generations`, {
      model: 'dalle-3',
      prompt
    }, {
      headers: { Authorization: `Bearer ${API_KEY}` }
    });

    res.json({ image: response.data.data[0].url });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
