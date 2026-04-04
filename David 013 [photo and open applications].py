import cv2
import nltk
import random
from nltk.chat.util import Chat, reflections
import os
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import pyaudio
import pygame
import pywhatkit as py
import threading
import time
from datetime import datetime
import re
import requests
import wikipedia
import sys

GOOGLE_API_KEY = "AIzaSyAdVYpa29xf1Yo6dg4MZkohF70dx8Fexk0"
WEATHER_API_KEY = "a4bae7f0035feb339118116941e34c2f"

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set it before running the script.")
    sys.exit()

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
        r"who are you ?",
        ["I am David, a helpful AI assistant.", "My name is David."]
    ],
    [
        r"what can you do ?",
        ["I can answer your questions, generate text, and have conversations.", "I can provide information on a wide range of topics."]
    ],
    [
        r"bye|goodbye|exit|stop",
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
        r"what is the weather in (.*)|weather in (.*)|how is the weather in (.*)",
        ["weather_query_city"]
    ],
    [
        r"weather|current weather",
        ["weather_query_default"]
    ],
    [
        r"play music|play a song|start music",
        ["Sure, I can play some music. What song or genre would you like?", "Alright, let's get some tunes going! What should I play?"]
    ],
    [
        r"play (.*) by (.*)",
        ["Playing %1 by %2 now. Enjoy!", "Here's %1 by %2 coming right up!"]
    ],
    [
        r"play (.*) song",
        ["Playing %1 now. Enjoy!", "Here's %1 coming right up!"]
    ],
    [
        r"stop music|pause music",
        ["Okay, pausing the music.", "Music stopped.", "Pausing now."]
    ],
    [
        r"resume music|continue music",
        ["Resuming music.", "Music continued."]
    ],
    [
        r"next song",
        ["Playing the next song.", "Skipping to the next track."]
    ],
    [
        r"what's playing",
        ["I'm not currently set up to tell you the song name once it's playing, but I can play something new if you like!"]
    ],
    [
        r"play (.*) on youtube",
        ["Playing %1 on YouTube.", "Okay, looking for %1 on YouTube."]
    ],
    [
        r"search (.*) on google",
        ["Searching Google for %1.", "Looking up %1 on Google."]
    ],
    [
        r"what is the date today|what day is it|what's the date",
        ["Sure, let me check the current date for you."]
    ],
    [
        r"what time is it|tell me the time|current time",
        ["Checking the current time for you."]
    ],
    [
        r"who is Sudarshan|who is Sudarshan Raj Bhattarai|who is your creator|who created you",
        ["Sudarshan(DragonKingThe4th), known as sudarshan_.1715 on Instagram, is a Student. He is a random guy"]
    ],
    [
        r"who is (.*)",
        ["Searching Wikipedia for %1.", "Let me find information about %1."]
    ],
    [
        r"open chrome",
        ["Opening Chrome."]
    ],
    [
        r"open brave",
        ["opening Brave."]
    ],
    [
        r"open code|open vs code|open vs",
        ["Opening VS Code."]
    ],
    [
        r"open VPN",
        ["Connecting to VPN."]
    ],
    [
        r"click photo|take a picture",
        ["Okay, capturing your photo."]
    ]
]

nltk_chatbot = Chat(pairs, reflections)

engine = pyttsx3.init()
david_voice_id = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0"

try:
    engine.setProperty('voice', david_voice_id)
except Exception as e:
    print(f"Error setting voice to {david_voice_id}: {e}. Falling back to default.")
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[0].id)

stop_speaking_flag = threading.Event()

def speak_text(message):
    global engine
    engine.say(message)
    try:
        engine.runAndWait()
    except Exception as e:
        print(f"Error during pyttsx3 runAndWait: {e}")

pygame.mixer.init()

MUSIC_FOLDER = "Music"
current_playlist = []
current_song_index = -1
music_thread = None
stop_music_flag = threading.Event()

def get_music_files():
    music_files = []
    if os.path.exists(MUSIC_FOLDER):
        for file in os.listdir(MUSIC_FOLDER):
            if file.lower().endswith((".mp3", ".wav", ".ogg")):
                music_files.append(os.path.join(MUSIC_FOLDER, file))
    return music_files

def play_music_local(song_name=None):
    global current_playlist, current_song_index, music_thread, stop_music_flag

    stop_music_internal()
    stop_music_flag.clear()

    music_files = get_music_files()

    if not music_files:
        speak_text("I can't find any music files in the 'music' folder. Please add some.")
        return

    selected_song_path = None
    if song_name:
        for music_path in music_files:
            if song_name.lower() in os.path.basename(music_path).lower():
                selected_song_path = music_path
                break

    if selected_song_path:
        current_playlist = [selected_song_path]
        current_song_index = 0
    else:
        if song_name:
            speak_text(f"Sorry, I couldn't find a local song called {song_name}. Playing a random local track instead.")
        current_playlist = random.sample(music_files, len(music_files))
        current_song_index = 0
        selected_song_path = current_playlist[current_song_index]

    speak_text(f"Now playing {os.path.basename(selected_song_path).replace('.mp3', '').replace('.wav', '')}.")

    def load_and_play_local():
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(selected_song_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not stop_music_flag.is_set():
                pygame.time.Clock().tick(10)
            if stop_music_flag.is_set():
                pygame.mixer.music.stop()
        except Exception as e:
            print(f"Error playing local audio: {e}")
            speak_text("Sorry, I had trouble playing that local song.")

    music_thread = threading.Thread(target=load_and_play_local)
    music_thread.start()

def play_youtube_video(query):
    speak_text(f"Playing {query} on YouTube.")
    py.playonyt(query)

def search_google(query):
    speak_text(f"Searching Google for {query}.")
    py.search(query)

def stop_music_internal():
    global music_thread, stop_music_flag
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy() or (music_thread and music_thread.is_alive()):
        stop_music_flag.set()
        if music_thread:
            music_thread.join(timeout=2)
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    stop_music_flag.clear()

def stop_music():
    stop_music_internal()
    speak_text("Music stopped.")

def pause_music():
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        speak_text("Music paused.")
    else:
        speak_text("No music is currently playing to pause.")

def resume_music():
    if pygame.mixer.get_init() and pygame.mixer.music.get_pos() != -1 and not pygame.mixer.music.get_busy():
        pygame.mixer.music.unpause()
        speak_text("Resuming music.")
    else:
        speak_text("No music paused to resume.")

def next_song():
    global current_playlist, current_song_index, music_thread, stop_music_flag

    stop_music_internal()
    stop_music_flag.clear()

    if not current_playlist:
        local_files = get_music_files()
        if local_files:
            current_playlist = random.sample(local_files, len(local_files))
            current_song_index = 0
            speak_text("Populating playlist with local music.")
        else:
            speak_text("There's no playlist and no local music to advance.")
            return

    current_song_index += 1
    if current_song_index >= len(current_playlist):
        current_song_index = 0

    selected_song_path = current_playlist[current_song_index]
    speak_text(f"Playing next: {os.path.basename(selected_song_path).replace('.mp3', '').replace('.wav', '')}.")

    def load_and_play_local():
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(selected_song_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not stop_music_flag.is_set():
                pygame.time.Clock().tick(10)
            if stop_music_flag.is_set():
                pygame.mixer.music.stop()
        except Exception as e:
            print(f"Error playing local audio: {e}")
            speak_text("Sorry, I had trouble playing that local song.")

    music_thread = threading.Thread(target=load_and_play_local)
    music_thread.start()

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

def get_weather(city="Kathmandu"):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data["cod"] != 200:
            return f"Sorry, I couldn't fetch the weather for {city}. The city might not be found or there was another issue: {data.get('message', 'Unknown error')}."

        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        return f"The current weather in {city} is {weather} with a temperature of {temp}°C. It feels like {feels_like}°C."

    except requests.exceptions.ConnectionError:
        return "I'm having trouble connecting to the internet to get weather data."
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return "Sorry, I couldn't retrieve the weather at the moment due to an unexpected error."

def capture_photo():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)

    photo_taken = False
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
        # The line below, which drew the blue rectangle, has been removed.
        cv2.imshow('Capturing Photo', frame)

        if not photo_taken and len(faces) > 0:
            filename = f"captured_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
            speak_text("Photo clicked and saved.")
            photo_taken = True

        if cv2.waitKey(1) == ord('q') or photo_taken:
            break

    cap.release()
    cv2.destroyAllWindows()

def chat_with_llm_and_voice_output():
    print("Hi! I'm David, an AI assistant. Type 'bye' or say 'goodbye' to exit.")
    speak_text("Hi! I'm David, an AI assistant. Type 'bye' or say 'goodbye' to exit.")

    last_input_time = time.time()

    while True:
        if time.time() - last_input_time > 50:
            speak_text("No input detected. Exiting now. Goodbye!")
            print("David: No input detected. Exiting now. Goodbye!")
            break

        user_input = get_audio_input()

        if user_input:
            last_input_time = time.time()
            user_input_lower = user_input.lower()

            if "shut up" in user_input_lower or "stop talking" in user_input_lower:
                stop_speaking_flag.set()
                print("David: (speech interrupted)")
                continue

        if not user_input:
            continue

        user_input_lower = user_input.lower()

        if user_input_lower in ['bye', 'goodbye', 'exit', 'stop']:
            stop_music_internal()
            speak_text("Goodbye! Have a great day.")
            print("Chatbot: Goodbye! Have a great day.")
            break

        if "click photo" in user_input_lower or "take a picture" in user_input_lower:
            speak_text("Okay, capturing your photo.")
            capture_photo()
            continue

        if "what's the time" in user_input_lower or "tell me the time" in user_input_lower or "current time" in user_input_lower:
            now = datetime.now()
            formatted_time = now.strftime("The current time is %I:%M %S %p.")
            speak_text(formatted_time)
            print(f"Chatbot: {formatted_time}")
            continue

        if "what is the date today" in user_input_lower or "what day is it" in user_input_lower or "what's the date" in user_input_lower:
            today = datetime.now()
            formatted_date = today.strftime("Today is %A, %B %d, %Y.")
            speak_text(formatted_date)
            print(f"Chatbot: {formatted_date}")
            continue

        if "who created you" in user_input_lower or "who is your creator" in user_input_lower:
            info = ("Sudarshan(DragonKingThe4th), known as sudarshan_.1715 on Instagram, is a Student. He is a random guy")
            speak_text(info)
            print(f"David: {info}")
            continue

        if "who is" in user_input_lower:
            person = user_input_lower.replace("who is", "").strip()
            try:
                info = wikipedia.summary(person, sentences=1)
                speak_text(info)
                print(f"David: {info}")
            except wikipedia.exceptions.PageError:
                speak_text("Sorry, I couldn't find information about that person on Wikipedia.")
                print("David: Sorry, I couldn't find information about that person on Wikipedia.")
            except Exception as e:
                speak_text("Sorry, I encountered an error while searching for that information.")
                print(f"David: Sorry, I encountered an error while searching for that information: {e}")
            continue

        if "open chrome" in user_input_lower:
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if os.path.exists(chrome_path):
                speak_text("Opening Chrome.")
                print("David: Opening Chrome.")
                os.startfile(chrome_path)
            else:
                speak_text("Chrome path not found.")
                print("David: Chrome path not found.")
            continue
        if "open brave" in user_input_lower:
            brave_path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            if os.path.exists(brave_path):
                speak_text("Opening Brave.")
                print("David: Opening Brave.")
                os.startfile(brave_path)
            else:
                speak_text("Brave path not found.")
                print("David: brave path not found.")
            continue
        if "open vpn" in user_input_lower or "open proton" in user_input_lower:
            vpn_path = "C:\\Program Files\\Proton\\VPN\\ProtonVPN.Launcher.exe"
            if os.path.exists(vpn_path):
                speak_text("Opening VPN And Connecting")
                print("David: Opening VPN And Connecting")
                os.startfile(vpn_path)
            else:
                speak_text("VPN path not found.")
                print("David: VPN path not found.")
            continue

        if "open code" in user_input_lower or "open vs" in user_input_lower:
            speak_text("Opening VS Code.")
            print("David: Opening VS Code.")
            os.system("code")
            continue

        response_text = ""
        for pattern, responses in pairs:
            if isinstance(responses, list) and (responses[0] == "weather_query_city" or responses[0] == "weather_query_default"):
                match = re.search(pattern, user_input_lower)
                if match:
                    if responses[0] == "weather_query_city":
                        city_match = None
                        if "what is the weather in (.*)" in pattern:
                            city_match = re.search(r"what is the weather in (.*)", user_input_lower)
                        elif "weather in (.*)" in pattern:
                            city_match = re.search(r"weather in (.*)", user_input_lower)
                        elif "how is the weather in (.*)" in pattern:
                            city_match = re.search(r"how is the weather in (.*)", user_input_lower)

                        city = city_match.group(1).strip() if city_match else "Kathmandu"
                        response_text = get_weather(city)
                    elif responses[0] == "weather_query_default":
                        response_text = get_weather("Kathmandu")
                    break

        if response_text:
            print(f"David: {response_text}")
            speak_text(response_text)
            continue

        yt_match_song = re.search(r"play (.*) on youtube", user_input_lower)
        Google_Search_match = re.search(r"search (.*) on google", user_input_lower)

        if yt_match_song:
            song_query = yt_match_song.group(1).strip()
            speak_text(f"Playing {song_query} on YouTube.")
            py.playonyt(song_query)
            continue
        elif Google_Search_match:
            search_query = Google_Search_match.group(1).strip()
            search_google(search_query)
            continue
        elif "play music" in user_input_lower or "play a song" in user_input_lower or "start music" in user_input_lower:
            match_play_song = re.search(r"play (.*) by (.*)", user_input_lower)
            if match_play_song:
                song = match_play_song.group(1).strip()
                play_music_local(song)
                continue

            match_play_song_simple = re.search(r"play (.*) song", user_input_lower)
            if match_play_song_simple:
                song = match_play_song_simple.group(1).strip()
                play_music_local(song)
                continue

            play_music_local()
            continue

        elif "stop music" in user_input_lower:
            stop_music()
            continue
        elif "pause music" in user_input_lower:
            pause_music()
            continue
        elif "resume music" in user_input_lower or "continue music" in user_input_lower:
            resume_music()
            continue
        elif "next song" in user_input_lower:
            next_song()
            continue
        elif "what's playing" in user_input_lower:
            speak_text("I'm not currently set up to tell you the song name once it's playing, but I can play something new if you like!")
            continue

        nltk_response = nltk_chatbot.respond(user_input)
        if nltk_response and nltk_response not in ["I'm not sure how to respond to that.", "Could you please rephrase that?", "Hmm, I don't understand."]:
            response = nltk_response
        else:
            response = get_llm_response(user_input)
        print(f"David: {response}")
        speak_text(response)

if __name__ == "__main__":
    pygame.mixer.init()

    try:
        chat_with_llm_and_voice_output()
    finally:
        if engine:
            try:
                engine.stop()
            except RuntimeError as e:
                print(f"Error stopping pyttsx3 engine cleanly: {e}")

        stop_music_internal()

        if pygame.mixer.get_init():
            pygame.mixer.quit()

        print("David session ended and resources released.")