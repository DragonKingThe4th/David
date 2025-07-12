import nltk
import random
from nltk.chat.util import Chat, reflections
import speech_recognition as sr


text = pairs = [
    [
        r"hi|hello|in your command",
        ["Hello!", "Hi there!", "Hey! How can I help you today?"]
    ],
    [
        r"how are you ?",
        ["I'm doing well, thank you!", "I'm good, thanks for asking.", "All good here!"]
    ],
    [
        r"what is your name ?",
        ["You can call me David.", "I'm a simple chatbot named DDavid", "I don't have a name but they call me david"]
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
        r"weather", # Pattern: matches if "weather" is in the input
        ["I don't have access to real-time weather data.", "I'm not equipped to tell you the weather.", "You can check a weather app for that!"]

    ],
    [
        r"German",
        ["FUCK YOU SCHLAMPE","Halt die Fresse","Leck mich am Arsch"]

    ],
    [
        r"(.*)", # Default response for anything not matched
        ["I'm not sure how to respond to that.", "Could you please rephrase that?", "Hmm, I don't understand."]
    ]
]
david = Chat(pairs, reflections)
def chat_with_voice_input():
    r = sr.Recognizer() # Initialize the recognizer
    print("Hi! I'm a simple chatbot named David. Speak 'bye' to exit.")

    while True:
        with sr.Microphone() as source:
            print("Listening...")
            r.adjust_for_ambient_noise(source) # Adjust for ambient noise
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5) # Listen for audio
                print("Processing...")
                # Use Google Web Speech API for recognition (requires internet)
                user_input = r.recognize_google(audio)
                print(f"You: {user_input}")

                if user_input.lower() == 'bye':
                    print("David: Goodbye! Have a great day.")
                    break

                response = david.respond(user_input)
                print(f"David: {response}")

            except sr.WaitTimeoutError:
                print("No speech detected. Please speak up.")
            except sr.UnknownValueError:
                print("Could not understand audio. Please try again.")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

# Run the chatbot with voice input
if __name__ == "__main__":
    chat_with_voice_input()