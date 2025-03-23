import telebot
import ollama
import re
import json
import time
import random
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API Key
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
bot = telebot.TeleBot(TELEGRAM_API_KEY)

# User state tracking
user_state = {}
conversation_history = {}
MAX_HISTORY = 5

# Smart replies for more natural conversation
GREETINGS = ["Hi", "Hello", "Hey", "Greetings", "Hi there"]
THINKING_MESSAGES = [
    "Thinking about that recipe...", 
    "Searching through my cookbook...",
    "Checking what we can make with those ingredients...",
    "Looking for something delicious...",
    "Stirring up some ideas..."
]

def query_gemma(prompt, chat_id=None, with_history=False):
    """Send a request to the Gemma 3 model via Ollama and return the response."""
    try:
        messages = []
        
        # Add conversation history if requested
        if with_history and chat_id in conversation_history:
            messages = conversation_history[chat_id][-MAX_HISTORY:]
        
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})
        
        print(f"Querying Gemma with prompt: {prompt}")  # Debugging
        response = ollama.chat(model='gemma3:4b', messages=messages)
        
        # Extract message content correctly
        if 'message' in response and 'content' in response['message']:
            result = response['message']['content'].strip()
        else:
            result = "Sorry, I couldn't generate a response."

        # Update conversation history
        if chat_id is not None:
            if chat_id not in conversation_history:
                conversation_history[chat_id] = []
            conversation_history[chat_id].append({"role": "user", "content": prompt})
            conversation_history[chat_id].append({"role": "assistant", "content": result})

        print(f"Gemma response: {result}")  # Debugging
        return result
    except Exception as e:
        print(f"Error querying Gemma: {e}")
        return "An error occurred while processing your request. Please try again later."

def safe_send_message(chat_id, text, parse_mode=None):
    """Safely send messages with fallback for markdown issues"""
    try:
        if parse_mode == 'MarkdownV2':
            bot.send_message(chat_id, escape_markdown(text), parse_mode='MarkdownV2')
        else:
            bot.send_message(chat_id, text, parse_mode=parse_mode)
    except Exception as e:
        print(f"Error sending message: {e}")
        # Fallback without markdown
        bot.send_message(chat_id, text)

def escape_markdown(text):
    """Escape MarkdownV2 special characters"""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def send_typing_action(chat_id, duration=1.5):
    """Send typing action to make the bot feel more human"""
    bot.send_chat_action(chat_id, 'typing')
    time.sleep(duration)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_message = (
        f"👋 Hello, {user_name}! I'm your personal Recipe Assistant!\n\n"
        "I can help you with recipes, meal planning, nutrition info, and more.\n\n"
        "Try asking me things like:\n"
        "• What can I make with chicken and potatoes?\n"
        "• I need a quick vegetarian dinner idea\n"
        "• Help me plan meals for the week\n"
        "• What's a good breakfast with eggs?\n\n"
        "Or type /help to see all commands!"
    )
    safe_send_message(message.chat.id, welcome_message)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🍽 *Recipe Assistant Help* 🍽\n\n"
        "*Smart Conversations:*\n"
        "Simply chat with me about food, ingredients, or meal ideas!\n\n"
        "*Commands:*\n"
        "• /recipe \\- Enter ingredients to find recipes\n"
        "• /plan \\- Create a weekly meal plan\n"
        "• /nutrition \\- Get nutritional information\n"
        "• /history \\- View your recent recipe searches\n"
        "• /clear \\- Clear your conversation history\n\n"
        "*Examples:*\n"
        "\"What can I make with eggs and spinach?\"\n"
        "\"I need a keto dinner idea\"\n"
        "\"Plan meals for my vegetarian diet\"\n"
    )
    safe_send_message(message.chat.id, help_text, parse_mode='MarkdownV2')

@bot.message_handler(commands=['recipe'])
def handle_recipe(message):
    safe_send_message(message.chat.id, "What ingredients do you have? (separate by commas if you'd like)")
    user_state[message.chat.id] = {'step': 'waiting_for_ingredients'}

@bot.message_handler(commands=['plan'])
def handle_meal_plan(message):
    safe_send_message(message.chat.id, "Tell me about your dietary preferences or restrictions (if any):")
    user_state[message.chat.id] = {'step': 'waiting_for_plan'}

@bot.message_handler(commands=['nutrition'])
def handle_nutrition(message):
    try:
        recipe_name = ' '.join(message.text.split()[1:])
        if recipe_name:
            send_typing_action(message.chat.id, 2)
            bot.send_message(message.chat.id, random.choice(THINKING_MESSAGES))
            prompt = f"Provide detailed nutritional information for {recipe_name}. Include calories, macronutrients, and any health benefits. Format as a clear, organized report."
            response_text = query_gemma(prompt, message.chat.id, with_history=True)
            safe_send_message(message.chat.id, response_text)
        else:
            safe_send_message(message.chat.id, "Please tell me which recipe you'd like nutrition information for. For example: /nutrition chicken parmesan")
    except IndexError:
        safe_send_message(message.chat.id, "Please tell me which recipe you'd like nutrition information for. For example: /nutrition chicken parmesan")

@bot.message_handler(commands=['history'])
def handle_history(message):
    chat_id = message.chat.id
    if chat_id in conversation_history and len(conversation_history[chat_id]) > 0:
        history = []
        for item in conversation_history[chat_id]:
            if item["role"] == "user":
                history.append(f"You: {item['content'][:50]}..." if len(item['content']) > 50 else f"You: {item['content']}")
        
        if history:
            safe_send_message(chat_id, "Your recent queries:\n\n" + "\n".join(history[-10:]))
        else:
            safe_send_message(chat_id, "No history found.")
    else:
        safe_send_message(chat_id, "You haven't asked me anything yet!")

@bot.message_handler(commands=['clear'])
def handle_clear(message):
    chat_id = message.chat.id
    if chat_id in conversation_history:
        conversation_history[chat_id] = []
    if chat_id in user_state:
        user_state.pop(chat_id)
    safe_send_message(chat_id, "Your conversation history has been cleared!")

def detect_ingredients(text):
    """Detect if the message contains food ingredients"""
    common_ingredients = ['chicken', 'beef', 'pork', 'fish', 'egg', 'pasta', 'rice', 'potato', 
                         'tomato', 'onion', 'garlic', 'cheese', 'milk', 'flour', 'butter', 
                         'vegetable', 'fruit', 'bean', 'lentil', 'tofu']
    
    # Check if any common ingredient is mentioned
    for ingredient in common_ingredients:
        if ingredient in text.lower():
            return True
            
    # Check for lists (comma-separated items)
    if ',' in text and len(text.split(',')) >= 2:
        return True
        
    return False

def detect_recipe_request(text):
    """Detect if the message is asking for recipe suggestions"""
    recipe_phrases = ['recipe', 'make with', 'cook with', 'dish with', 'meal with', 
                     'what can i make', 'what can i cook', 'how to cook', 'how to make',
                     'dinner idea', 'lunch idea', 'breakfast idea', 'meal idea']
    
    text_lower = text.lower()
    for phrase in recipe_phrases:
        if phrase in text_lower:
            return True
    
    return False

def detect_meal_plan_request(text):
    """Detect if the message is asking for meal planning"""
    plan_phrases = ['meal plan', 'weekly plan', 'plan for the week', 'diet plan',
                   'plan meals', 'week of meals', 'plan my meals']
    
    text_lower = text.lower()
    for phrase in plan_phrases:
        if phrase in text_lower:
            return True
    
    return False

def detect_nutrition_request(text):
    """Detect if the message is asking for nutritional information"""
    nutrition_phrases = ['nutrition', 'nutritional', 'calories', 'healthy', 'protein', 
                        'carbs', 'fat content', 'vitamins', 'minerals']
    
    text_lower = text.lower()
    for phrase in nutrition_phrases:
        if phrase in text_lower:
            return True
    
    return False

def get_time_based_greeting():
    """Return a greeting appropriate for the time of day"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

@bot.message_handler(func=lambda msg: True)
def handle_conversation(message):
    chat_id = message.chat.id
    text = message.text.strip()
    user_data = user_state.get(chat_id, {})

    # Handle guided flows first
    if user_data.get('step') == 'waiting_for_ingredients':
        user_state[chat_id] = {'step': 'waiting_for_preferences', 'ingredients': text}
        safe_send_message(chat_id, "Any dietary preferences or restrictions? (or just say 'none')")
        return
    
    elif user_data.get('step') == 'waiting_for_preferences':
        ingredients = user_data['ingredients']
        preference = text.lower()
        
        # Show typing indicator
        send_typing_action(chat_id, 2)
        safe_send_message(chat_id, random.choice(THINKING_MESSAGES))
        
        # Generate recipe via Gemma 3
        prompt = (
            f"Generate a detailed recipe using these ingredients: {ingredients}. "
            f"Dietary preference: {preference}. Include: 1) Recipe name with emoji, "
            f"2) Ingredients with measurements, 3) Step-by-step instructions, "
            f"4) Cooking time, 5) Nutritional highlights, 6) Chef's tip"
        )
        recipe_response = query_gemma(prompt, chat_id, with_history=True)
        
        # Send the response
        safe_send_message(chat_id, recipe_response)
        
        # Ask follow-up question
        time.sleep(1)
        safe_send_message(chat_id, "Would you like me to suggest substitutions for any ingredients?")
        
        user_state.pop(chat_id, None)
        return
    
    elif user_data.get('step') == 'waiting_for_plan':
        preference = text.lower()
        
        # Show typing indicator
        send_typing_action(chat_id, 3)
        safe_send_message(chat_id, "Creating your personalized meal plan... This might take a moment.")
        
        # Generate meal plan via Gemma 3
        prompt = (
            f"Create a detailed 7-day meal plan for a {preference} diet. "
            f"For each day, include breakfast, lunch, dinner, and a snack. "
            f"Add variety, balance nutrition, and include one special weekend meal. "
            f"Format clearly with days as headers and meals with brief descriptions."
        )
        meal_plan = query_gemma(prompt, chat_id, with_history=True)
        
        safe_send_message(chat_id, meal_plan)
        
        # Follow up
        time.sleep(1)
        safe_send_message(chat_id, "Would you like recipes for any specific meals in this plan?")
        
        user_state.pop(chat_id, None)
        return
    
    # Smart conversation detection
    if detect_recipe_request(text) or detect_ingredients(text):
        # Show thinking
        send_typing_action(chat_id, 2)
        safe_send_message(chat_id, random.choice(THINKING_MESSAGES))
        
        # Generate recipe
        if detect_recipe_request(text):
            prompt = f"The user is asking for recipe ideas with this request: '{text}'. Generate a detailed recipe that matches their request. Include: 1) Recipe name with emoji, 2) Ingredients with measurements, 3) Step-by-step instructions, 4) Cooking time, 5) Chef's tip"
        else:
            prompt = f"Generate a creative recipe using these ingredients or food items mentioned: '{text}'. Include: 1) Recipe name with emoji, 2) Complete ingredients list with measurements, 3) Step-by-step instructions, 4) Cooking time, 5) Chef's tip"
        
        recipe = query_gemma(prompt, chat_id, with_history=True)
        safe_send_message(chat_id, recipe)
        
    elif detect_meal_plan_request(text):
        # Show thinking
        send_typing_action(chat_id, 2.5)
        safe_send_message(chat_id, "Planning your meals for the week... Let me create something balanced and delicious!")
        
        prompt = f"Create a personalized 7-day meal plan based on this request: '{text}'. Include breakfast, lunch, dinner for each day. Format clearly with days as headers. Add variety and balance nutrition."
        meal_plan = query_gemma(prompt, chat_id, with_history=True)
        safe_send_message(chat_id, meal_plan)
        
    elif detect_nutrition_request(text):
        # Show thinking
        send_typing_action(chat_id, 2)
        safe_send_message(chat_id, "Analyzing nutritional information...")
        
        prompt = f"Provide detailed nutritional information about: '{text}'. Include calories, macronutrients, and health benefits if applicable."
        nutrition_info = query_gemma(prompt, chat_id, with_history=True)
        safe_send_message(chat_id, nutrition_info)
        
    else:
        # General conversation
        send_typing_action(chat_id)
        
        # Add user message to history
        if chat_id not in conversation_history:
            conversation_history[chat_id] = []
            # Add system message for context
            conversation_history[chat_id].append({
                "role": "system", 
                "content": "You are a helpful cooking assistant. Respond to culinary questions with expertise and enthusiasm."
            })
        
        # Create prompt with enhanced instructions
        prompt = (
            f"The user sent this message: '{text}'. "
            f"If it's related to food, cooking, ingredients, recipes, meal planning, or nutrition, "
            f"respond with helpful, enthusiastic information as a cooking expert. "
            f"If it's a greeting, respond warmly. If it's unrelated to food, "
            f"gently guide the conversation back to cooking topics. Keep responses concise and friendly."
        )
        
        response = query_gemma(prompt, chat_id, with_history=True)
        safe_send_message(chat_id, response)

if __name__ == "__main__":
    print("Recipe Bot is starting...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Bot polling error: {e}")