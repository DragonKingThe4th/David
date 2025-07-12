import nltk
import random
from nltk.chat.util import Chat, reflections
from gtts import gTTS  
import os
import pygame


pairs = [
    [
        r"hi|hello|in your command|hey",
        ["Hello!", "Hi there!", "Hey! How can I help you today?"]
    ],
    [
        r"how are you ?",
        ["I'm doing well, thank you!", "I'm good, thanks for asking.", "All good here!"]
    ],
    [
        r"what is your name ?",
        ["You can call me David.", "I'm a simple chatbot named David.", "I don't have a name, but they call me David."]
    ],
    [
        r"what can you do ?",
        ["I can answer your questions and have a chat.", "I can provide information and engage in conversation."]
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


def chat_with_text_input_and_voice_output():
    print("Hi! I'm a simple chatbot. Type 'bye' to exit.")
    speak_text("Hi! I'm a simple chatbot. Type 'bye' to exit.")

    while True:
        
        user_input = input("You: ")

        if user_input.lower() == 'bye':
            speak_text("Goodbye! Have a great day.")
            print("Chatbot: Goodbye! Have a great day.")
            break

        
        response = david.respond(user_input)
        print(f"Chatbot: {response}")

        
        speak_text(response)


if __name__ == "__main__":
    chat_with_text_input_and_voice_output()