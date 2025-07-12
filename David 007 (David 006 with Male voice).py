import nltk
import random
from nltk.chat.util import Chat, reflections
import os
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import pyaudio
import pygame

GOOGLE_API_KEY = "AIzaSyAdVYpa29xf1Yo6dg4MZkohF70dx8Fexk0"
PI_KEY = os.environ.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set it before running the script.")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)

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
        ["Your Wife, Your dumb Koala is Nisha Sudarshan Raj Bhattarai"]
    ]
]

nltk_chatbot = Chat(pairs, reflections)

engine = pyttsx3.init()

david_voice_id = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0"

def speak_text(message, voice_id=None):
    if voice_id:
        try:
            current_voice = engine.getProperty('voice')
            if current_voice != voice_id:
                engine.setProperty('voice', voice_id)
                print(f"Set voice to: {voice_id}")
        except Exception as e:
            print(f"Error setting voice to {voice_id}: {e}. Falling back to default.")
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)
                print(f"Fallback to voice: {voices[0].name}")
    else:
        print("No specific voice ID provided. Using current engine default.")

    engine.say(message)
    engine.runAndWait()

def get_llm_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        return "I'm having trouble connecting to my knowledge base right now. Please try again later."

def get_audio_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something...")
        r.pause_threshold = 1
        r.energy_threshold = 300

        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            print("Recognizing...")
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
    speak_text("Hi! I'm David, an AI assistant. Type 'bye' or say 'goodbye' to exit.", voice_id=david_voice_id)

    while True:
        user_input = ""
        user_input = get_audio_input()

        if not user_input:
            continue

        if user_input.lower() in ['bye', 'goodbye']:
            speak_text("Goodbye! Have a great day.", voice_id=david_voice_id)
            print("Chatbot: Goodbye! Have a great day.")
            break

        response = ""
        nltk_response = nltk_chatbot.respond(user_input)

        if nltk_response and nltk_response not in ["I'm not sure how to respond to that.", "Could you please rephrase that?", "Hmm, I don't understand."]:
            response = nltk_response
        else:
            response = get_llm_response(user_input)

        print(f"Chatbot: {response}")
        speak_text(response, voice_id=david_voice_id)

if __name__ == "__main__":
    try:
        chat_with_llm_and_voice_output()
    finally:
        if 'engine' in locals() and engine._inLoop:
            engine.stop()
        print("Chatbot session ended and resources released.")