import nltk
import random
from nltk.chat.util import Chat, reflections


pairs = [
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
        ["You can call me Chatbot.", "I'm a simple chatbot.", "I don't have a name."]
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
        r"(.*) weather (.*)", # Pattern: matches if "weather" is in the input
        ["I don't have access to real-time weather data.", "I'm not equipped to tell you the weather.", "You can check a weather app for that!"]

    ],
    [
        r"(.*)", # Default response for anything not matched
        ["I'm not sure how to respond to that.", "Could you please rephrase that?", "Hmm, I don't understand."]
    ]
]


chatbot = Chat(pairs, reflections)

def chat_with_user():
    print("Hi! I'm a simple chatbot. Type 'bye' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'bye':
            print("Chatbot: Goodbye! Have a great day.")
            break
        response = chatbot.respond(user_input)
        print(f"Chatbot: {response}")


if __name__ == "__main__":
    chat_with_user()