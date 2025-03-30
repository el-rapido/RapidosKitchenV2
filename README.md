# Recipebot V2

This project is a **Telegram Recipe Bot** that leverages **Gemma 3**, an AI model integrated via **Ollama**, to provide users with personalized recipes, meal planning, and nutritional information. The bot interacts with users through Telegram messages, allowing them to request recipes based on available ingredients, create weekly meal plans, and inquire about nutritional data. It enhances the user experience with smart conversation features like greeting messages and natural-sounding responses.

## Key Features:
- **Recipe Suggestions**: Users can ask the bot to generate recipes based on available ingredients.
- **Meal Planning**: The bot helps create a personalized weekly meal plan, considering dietary preferences and restrictions.
- **Nutritional Information**: The bot provides detailed nutritional information, including calories, macronutrients, and health benefits, for any recipe or dish.
- **History Tracking**: The bot maintains conversation history and offers users the option to view or clear their recent searches.
- **Smart Conversations**: The bot tracks user conversations and responds accordingly, with the ability to handle common meal-related requests and maintain a friendly tone.

## Linking to Recipebot

In the earlier version of this project, the **Spoonacular API** was used to fetch recipes, nutritional data, and meal plans. With the integration of **Gemma 3** via **Ollama**, the bot now generates all this information on the fly based on natural language processing, providing a more flexible and intelligent interaction with the user. This AI-powered approach allows for better customization of recipe suggestions and meal plans, adapting to individual user needs more effectively than the API-driven model.

This move aligns with the goal of making the bot smarter and more interactive, leveraging advanced AI capabilities to offer a richer user experience.

## Deployment Instructions

To deploy this Recipe Bot, follow these steps:

### 1. Set Up Environment Variables:
- Create a `.env` file in the root directory of your project.
- Add the following line to store your **Telegram API key**:
  ```plaintext
  TELEGRAM_API_KEY=your_telegram_api_key_here
  ```

### 2. Install Dependencies:
- Install the required Python packages:
  ```bash
  pip install -r requirements.txt
  ```

### 3. Run the Bot Locally:
- Start the bot by running the script:
  ```bash
  python app.py
  ```
- The bot will start polling and will respond to user messages in the Telegram app.

### 4. Deploy to a Cloud Service (Optional):
If you'd like to deploy your bot to a cloud service (e.g., Heroku, AWS, or DigitalOcean), follow these steps:
  
#### Heroku:
- Create a **Heroku app** and push your repository:
  ```bash
  git push heroku main
  ```
- Make sure to set your environment variables on Heroku for `TELEGRAM_API_KEY`.

#### AWS or DigitalOcean:
- Set up a server with Python installed.
- Clone your GitHub repository to the server and set up the environment variables.
- Run the bot using `python app.py` in the background (e.g., using `nohup` or `screen`).

### 5. Make Sure the Bot Keeps Running:
- You may want to use a process manager like **PM2** or **Supervisor** to keep the bot running even after a system reboot.

---


