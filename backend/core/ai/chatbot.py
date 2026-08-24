import os
import google.generativeai as genai
from google.api_core.exceptions import PermissionDenied
from .prompts import get_system_prompt
from .context import get_customer_context

def init_ai():
    api_key = os.environ.get("AI_API_KEY")
    if not api_key:
        return False
    genai.configure(api_key=api_key)
    return True

def handle_chat_message(customer_username, message_text, history=None):
    """
    Handles a customer chat message using the AI model and context.
    Returns the AI's response text.
    """
    if not init_ai():
        return "I'm sorry, the AI assistant is currently unavailable (API key not configured)."

    # Retrieve context
    context_data = get_customer_context(customer_username)
    if not context_data:
        return "I'm sorry, I couldn't retrieve your account details."

    system_prompt = get_system_prompt(context_data)

    try:
        # Allow configuring the model via environment variable.
        model_name = os.environ.get("AI_MODEL_NAME", "gemini-3.6-flash")
        
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.4,
            )
        )
        
        chat = model.start_chat(history=history if history else [])
        response = chat.send_message(message_text)
        return response.text
    except PermissionDenied:
        print("AI Chat Error: Gemini project access denied")
        return "The AI assistant is temporarily unavailable because this Gemini project is not authorized. Please configure an active Gemini API key."
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
