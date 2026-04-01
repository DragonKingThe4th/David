import nltk
import random
from nltk.chat.util import Chat, reflections
from gtts import gTTS
import os
import pygame
import google.generativeai as genai 
import speech_recognition as sr 

GOOGLE_API_KEY = "AIzaSyAdVYpa29xf1Yo6dg4MZkohF70dx8Fexk0" 
PI_KEY = os.environ.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set it before running the script.")
    exit()


genai.configure(api_key= GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

pairs = [
    [
        r"hi|hello|in your command|hey",
        ["Hello! How can I help you today?", "Hi there! What's on your mind?"]
    ],
    [
        r"what is your name ?",
        ["You can call me David.", "I am David, a helpful AI assistant.", "My name is David."]
    ],
    [
        r"what can you do ?",
        ["I can answer your questions, generate text, and have conversations.", "I can provide information on a wide range of topics."]
    ],
    [
        r"bye|goodbye",
        ["Goodbye! Have a great day.", "See you later!", "Bye!"]
    ],
    [
        r"(.*) your age(.*)",
        ["I don't have an age, I'm a program.", "I wasn't born, I was created digitally."]
    ],
    [
        r"thank you|thanks",
        ["You're welcome!", "No problem!", "Glad to help!"]
    ],
    [
        r"weather",
        ["I don't have access to real-time weather data.", "I'm not equipped to tell you the weather.", "You can check a weather app for that!"]
    ],
    [
        r"what is my wife's name ?|what is baby's name ?|Who is my dumb koala?",
        ["Your Wife,Your dumb Koala is Nisha Sudarshan Raj Bhattarai"]
    ]
]

nltk_chatbot = Chat(pairs, reflections)

audio_file = "David_response.mp3"

def speak_text(text):
    """Converts text to speech and plays it using pygame."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(audio_file)

        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(2)

        pygame.mixer.quit()
        os.remove(audio_file)

    except Exception as e:
        print(f"Error speaking: {e}")
        print(f"Chatbot (text fallback): {text}")


def get_llm_response(prompt):
    """Gets a response from the Google Gemini LLM."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        return "I'm having trouble connecting to my knowledge base right now. Please try again later."


def get_audio_input():
    """Listens to the microphone and converts speech to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something...")
        r.pause_threshold = 1 # seconds of non-speaking audio before a phrase is considered complete
        r.energy_threshold = 300 # minimum audio energy to consider for recording

        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8) # Listen for up to 5 seconds, max phrase 8 seconds
            print("Recognizing...")
            # Use Google Web Speech API (online)
            text = r.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""
        except sr.WaitTimeoutError:
            print("No speech detected. Please try again.")
            return ""


def chat_with_llm_and_voice_output():
    print("Hi! I'm David, an AI assistant. Type 'bye' or say 'goodbye' to exit.")
    speak_text("Hi! I'm David, an AI assistant. Type 'bye' or say 'goodbye' to exit.")

    while True:
        user_input = ""
        # Get speech input
        user_input = get_audio_input()

        if not user_input: # If nothing was recognized, try again
            continue

        if user_input.lower() in ['bye', 'goodbye']:
            speak_text("Goodbye! Have a great day.")
            print("Chatbot: Goodbye! Have a great day.")
            break

        # --- Your existing response logic ---
        response = ""
        nltk_response = nltk_chatbot.respond(user_input)

        if nltk_response and nltk_response not in ["I'm not sure how to respond to that.", "Could you please rephrase that?", "Hmm, I don't understand."]:
            response = nltk_response
        else:
            response = get_llm_response(user_input)

        print(f"Chatbot: {response}")
        speak_text(response)


if __name__ == "__main__":
    chat_with_llm_and_voice_output()