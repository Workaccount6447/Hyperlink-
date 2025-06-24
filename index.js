
const express = require('express');
const puppeteer = require('puppeteer');
const app = express();
const PORT = process.env.PORT || 3000;

let browser, page;

async function init() {
    browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    page = await browser.newPage();
    await page.goto('https://js.puter.com/v2/', {waitUntil: 'networkidle2'});
    await page.addScriptTag({ url: 'https://js.puter.com/v2/' });
}

app.get('/chat', async (req, res) => {
    const prompt = req.query.prompt || 'Hello';
    const model = req.query.model || 'gpt-4o';

    try {
        const result = await page.evaluate(async (userPrompt, modelName) => {
            const res = await puter.ai.chat(userPrompt, { model: modelName });
            return res;
        }, prompt, model);

        res.json({ response: result });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/image', async (req, res) => {
    const prompt = req.query.prompt || 'a cat wearing sunglasses';
    const model = req.query.model || 'dalle-3';

    try {
        const imageUrl = await page.evaluate(async (userPrompt, modelName) => {
            const res = await puter.ai.txt2img(userPrompt, { model: modelName });
            return res;
        }, prompt, model);

        res.json({ image: imageUrl });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

init().then(() => {
    app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
    });
});
