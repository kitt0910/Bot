// Load environment variables from the .env file in the backend directory
require('dotenv').config({ path: './backend/.env' });
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const { Configuration, OpenAIApi } = require('openai');

const app = express();
const port = process.env.PORT || 5000;

app.use(bodyParser.json());
app.use(cors());

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});

const openai = new OpenAIApi(configuration);

app.post('/api/generate', async (req, res) => {
  const { prompt } = req.body;
  try {
    const response = await openai.createChatCompletion({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 150,
    });
    res.json({ text: response.data.choices[0].message.content });
  } catch (error) {
    console.error('Error generating response:', error);
    res.status(500).json({ error: 'Failed to generate response' });
  }
});

app.post('/api/generate-workflow', async (req, res) => {
  const { topic } = req.body;
  try {
    const prompt = `Generate a daily workflow for learning the topic: ${topic}. Include tasks for each day with specific steps.`;
    const response = await openai.createChatCompletion({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 300,
    });
    const workflow = response.data.choices[0].message.content;
    res.json({ workflow });
  } catch (error) {
    console.error('Error generating workflow:', error);
    res.status(500).json({ error: 'Failed to generate workflow' });
  }
});

app.post('/api/schedule-workflow', async (req, res) => {
  const { workflow, start_time, end_time } = req.body;
  try {
    // Integrate with Google Calendar API to schedule the workflow tasks
    // This is a placeholder for the actual implementation
    // Example: Use a library like googleapis to create calendar events

    res.json({ success: true });
  } catch (error) {
    console.error('Error scheduling workflow:', error);
    res.status(500).json({ error: 'Failed to schedule workflow' });
  }
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
