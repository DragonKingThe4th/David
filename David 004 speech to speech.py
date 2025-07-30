import nltk
import random
from nltk.chat.util import Chat,reflections
import speech_recognition as sr
from gtts import gTTS  
import os
import pygame


pairs = [
    [
        r"hi|hello|in my command|hey", 
        ["Hello! How may I assist you", "Hi there! How can I be of help", "Hey! How can I help you today?"]
    ],
    [
        r"how are you ?|How you doing?|How is life?",
        ["I'm doing well, thank you! What about You", "I'm good, thanks for asking. What about You", "All good here!What about You"]
    ],
    [
        r"what is your name ?|What do they call you",
        ["You can call me David.", "I'm a simple chatbot named David.", "I don't have a name, but they call me David."]
    ],
    [
        r"what can you do ?",
        ["I can answer your questions and have a chat.", "I can provide information and engage in conversation.","I can assist you any task"]
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
        r"German",
        ["I am not programmed to use offensive language. Please rephrase your query.", "I cannot respond to that in German. Is there anything else I can help you with?"]
    ],
    [
        r"(.*)", 
        ["I'm not sure how to respond to that.", "Could you please rephrase that?", "Hmm, I don't understand."]
    ]
]

david = Chat(pairs, reflections)


audio_file = "chatbot_response.mp3" 

def speak_text(text):
    """Converts text to speech and plays it using pygame."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(audio_file) 

        pygame.mixer.init() 
        pygame.mixer.music.load(audio_file) 
        pygame.mixer.music.play() 

        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10) 

        pygame.mixer.quit() 
        os.remove(audio_file) 

    except Exception as e:
        print(f"Error speaking: {e}")
        print(f"Chatbot (text fallback): {text}") 

def chat_with_voice_input():
    r = sr.Recognizer()  
    print("Hi! I'm David,a simple chatbot.I can help with you as much I am programmed too.For exit type 'terminate'")
    speak_text("Hi! I'm David,a simple chatbot.I can help with you as much I am programmed too.For exit type 'terminate'") 

    while True:
        with sr.Microphone() as source:
            print("Listening...")
            try:
                r.adjust_for_ambient_noise(source, duration=1) 
                audio = r.listen(source, timeout=7, phrase_time_limit=7) 
                print("Processing...")
                user_input = r.recognize_google(audio)
                print(f"You said: {user_input}")

                if user_input.lower() == 'bye':
                    speak_text("Goodbye! Have a great day.")
                    print("Chatbot: Goodbye! Have a great day.") 
                    break

                response = david.respond(user_input)
                print(f"Chatbot: {response}")
                speak_text(response)

            except sr.WaitTimeoutError:
                print("No speech detected. Please speak up.")
                speak_text("I didn't hear anything. Please speak up.")
            except sr.UnknownValueError:
                print("Could not understand audio. Please try again.")
                speak_text("I'm sorry, I didn't understand that. Could you please repeat?")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                speak_text(f"I'm having trouble connecting to the speech service. Error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                speak_text(f"An unexpected error occurred: {e}. Please check the console.")


if __name__ == "__main__":
    chat_with_voice_input()