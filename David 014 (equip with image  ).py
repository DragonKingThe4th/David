import os
import sys
import re
import time
import signal
import atexit
import threading
import random
import logging
from datetime import datetime
import pygame
import pyttsx3
import speech_recognition as sr
import pywhatkit as py
import requests
import wikipedia
import cv2
import nltk
from nltk.chat.util import Chat, reflections
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import hashlib

try:
    from google import genai as ggenai
    from google.genai import types as gtypes
except Exception:
    ggenai = None
    gtypes = None

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAdVYpa29xf1Yo6dg4MZkohF70dx8Fexk0")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "a4bae7f0035feb339118116941e34c2f")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Kathmandu")
MUSIC_FOLDER = os.getenv("MUSIC_FOLDER", "Music")
IDLE_TIMEOUT_SECONDS = int(os.getenv("IDLE_TIMEOUT_SECONDS", "50"))
VOICE_ID_DAVID = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0"
IMAGE_MODEL_ID = os.getenv("IMAGE_MODEL_ID", "gemini-2.0-flash-preview-image-generation")

logging.basicConfig(level=logging.INFO,format="[%(asctime)s] [%(levelname)s] %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("david")

if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not set. LLM/image features will be limited.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

MODEL = None
if GOOGLE_API_KEY:
    try:
        MODEL = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    except Exception as e:
        logger.error("Failed to initialize Gemini model: %s", e)
        MODEL = None

engine = pyttsx3.init()
try:
    engine.setProperty('voice', VOICE_ID_DAVID)
except Exception as e:
    logger.warning("Could not set David voice: %s. Falling back to default.", e)
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[0].id)

def speak_text(message: str):
    try:
        engine.say(message)
        engine.runAndWait()
    except Exception as e:
        logger.error("TTS error: %s", e)

def get_audio_input() -> str:
    r = sr.Recognizer()
    try:
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
            except sr.RequestError as e:
                print(f"Speech Recognition service error: {e}")
            except sr.WaitTimeoutError:
                print("No speech detected. Please try again.")
    except OSError:
        try:
            return input("Mic unavailable. Type your command: ").strip()
        except EOFError:
            return ""
    return ""

class MusicPlayer:
    def __init__(self, folder: str):
        self.folder = folder
        self.current_playlist = []
        self.current_index = -1
        self.thread = None
        self.stop_flag = threading.Event()
        self.lock = threading.Lock()
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def _get_music_files(self):
        if not os.path.exists(self.folder):
            return []
        return [os.path.join(self.folder, f) for f in os.listdir(self.folder) if f.lower().endswith((".mp3", ".wav", ".ogg"))]

    def _play_path(self, path: str):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self.stop_flag.is_set():
                pygame.time.Clock().tick(10)
            if self.stop_flag.is_set():
                pygame.mixer.music.stop()
        except Exception as e:
            logger.error("Error playing %s: %s", path, e)
            speak_text("Sorry, I had trouble playing that song.")

    def _start_thread(self, path: str):
        self.thread = threading.Thread(target=self._play_path, args=(path,), daemon=True)
        self.thread.start()

    def play(self, name: str | None = None):
        with self.lock:
            self.stop()
            self.stop_flag.clear()
            music_files = self._get_music_files()
            if not music_files:
                speak_text("I can't find any music files in the 'Music' folder. Please add some.")
                return
            selected = None
            if name:
                for p in music_files:
                    if name.lower() in os.path.basename(p).lower():
                        selected = p
                        break
            if selected:
                self.current_playlist = [selected]
                self.current_index = 0
            else:
                if name:
                    speak_text(f"Sorry, I couldn't find {name}. Playing a random local track instead.")
                self.current_playlist = random.sample(music_files, len(music_files))
                self.current_index = 0
                selected = self.current_playlist[self.current_index]
            speak_text(f"Now playing {os.path.basename(selected).rsplit('.', 1)[0]}.")
            self._start_thread(selected)

    def stop(self):
        with self.lock:
            if pygame.mixer.get_init() and (pygame.mixer.music.get_busy() or (self.thread and self.thread.is_alive())):
                self.stop_flag.set()
                if self.thread:
                    self.thread.join(timeout=2)
                pygame.mixer.music.stop()
            self.stop_flag.clear()

    def pause(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            speak_text("Music paused.")
        else:
            speak_text("No music is currently playing to pause.")

    def resume(self):
        if pygame.mixer.get_init() and not pygame.mixer.music.get_busy() and pygame.mixer.music.get_pos() != -1:
            pygame.mixer.music.unpause()
            speak_text("Resuming music.")
        else:
            speak_text("No music paused to resume.")

    def next(self):
        with self.lock:
            self.stop()
            self.stop_flag.clear()
            if not self.current_playlist:
                files = self._get_music_files()
                if not files:
                    speak_text("There's no playlist and no local music to advance.")
                    return
                self.current_playlist = random.sample(files, len(files))
                self.current_index = 0
                speak_text("Populating playlist with local music.")
            else:
                self.current_index += 1
                if self.current_index >= len(self.current_playlist):
                    self.current_index = 0
            path = self.current_playlist[self.current_index]
            speak_text(f"Playing next: {os.path.basename(path).rsplit('.', 1)[0]}.")
            self._start_thread(path)

music_player = MusicPlayer(MUSIC_FOLDER)

def get_weather(city: str = DEFAULT_CITY) -> str:
    if not WEATHER_API_KEY:
        return "Weather API key not set. Set WEATHER_API_KEY environment variable."
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("cod") != 200:
            return f"Sorry, I couldn't fetch the weather for {city}: {data.get('message', 'Unknown error')}"
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        return f"The current weather in {city} is {weather} with a temperature of {temp}°C. It feels like {feels_like}°C."
    except requests.exceptions.RequestException:
        return "I'm having trouble connecting to the internet to get weather data."
    except Exception as e:
        logger.error("Weather error: %s", e)
        return "Sorry, I couldn't retrieve the weather right now."

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

def llm(prompt: str) -> str:
    if not MODEL:
        return "I'm having trouble connecting to my knowledge base right now. Please try again later."
    try:
        response = MODEL.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error("LLM error: %s", e)
        return "I'm having trouble connecting to my knowledge base right now. Please try again later."

def generate_image(prompt: str, base_filename: str | None = None) -> None:
    if not GOOGLE_API_KEY:
        msg = "Google API key not set. Set GOOGLE_API_KEY to enable image generation."
        speak_text(msg)
        print(msg)
        return
    if ggenai is None or gtypes is None:
        msg = "google.genai SDK is not available. Please install and import it to use image generation."
        speak_text(msg)
        print(msg)
        return
    try:
        client = ggenai.Client(api_key=GOOGLE_API_KEY)
        chat = client.chats.create(model=IMAGE_MODEL_ID, config=gtypes.GenerateContentConfig(response_modalities=['Text', 'Image']))
        response = chat.send_message(prompt)
        if not response.candidates:
            print("No candidates returned in the response.")
            speak_text("No image was generated.")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()[:8]
        saved_any = False
        for i, part in enumerate(response.candidates[0].content.parts):
            if getattr(part, 'text', None) is not None:
                print(f"Text Part {i}: {part.text}")
            elif getattr(part, 'inline_data', None) is not None:
                try:
                    image = Image.open(BytesIO(part.inline_data.data))
                    if base_filename:
                        base_filename_clean = base_filename.rsplit('.', 1)[0] if '.' in base_filename else base_filename
                        current_filename = f"{base_filename_clean}_{timestamp}_{prompt_hash}_{i}.png"
                    else:
                        current_filename = f"image_{timestamp}_{prompt_hash}_{i}.png"
                    image.save(current_filename)
                    print(f"Image saved as: {current_filename}")
                    saved_any = True
                except Exception as e:
                    print(f"Error processing image part: {e}")
            else:
                print(f"Unknown part type at index {i}: {part}")
        if saved_any:
            speak_text("Your image has been generated and saved.")
        else:
            speak_text("I couldn't save any images from the response.")
    except Exception as e:
        print(f"An error occurred: {e}")
        if "API_KEY_INVALID" in str(e):
            print("Please check your GOOGLE_API_KEY. It might be invalid or improperly configured.")
        elif "RESOURCE_EXHAUSTED" in str(e):
            print("You might have exceeded your quota. Please check your usage.")

pairs = [
    [r"hi|hello|hey", ["Hello! How can I help you today?", "Hi there! What's on your mind?"]],
    [r"what is your name ?", ["You can call me David.", "I am David, a helpful AI assistant.", "My name is David."]],
    [r"who are you ?", ["I am David, a helpful AI assistant.", "My name is David."]],
    [r"what can you do ?", ["I can answer your questions, generate text, and have conversations.", "I can provide information on a wide range of topics."]],
    [r"bye|goodbye|exit|stop", ["Goodbye! Have a great day.", "See you later!", "Bye!"]],
    [r"(.*) your age(.*)", ["I don't have an age, I'm a program.", "I wasn't born, I was created digitally."]],
    [r"thank you|thanks", ["You're welcome!", "No problem!", "Glad to help!"]]
]

nltk_chatbot = Chat(pairs, reflections)

class Command:
    def __init__(self, pattern, handler):
        self.regex = re.compile(pattern, re.IGNORECASE)
        self.handler = handler

def handle_exit(_):
    music_player.stop()
    speak_text("Goodbye! Have a great day.")
    print("David: Goodbye! Have a great day.")
    return "__EXIT__"

def handle_time(_):
    now = datetime.now()
    msg = now.strftime("The current time is %I:%M %p.")
    speak_text(msg)
    print(f"David: {msg}")

def handle_date(_):
    today = datetime.now()
    msg = today.strftime("Today is %A, %B %d, %Y.")
    speak_text(msg)
    print(f"David: {msg}")

def handle_creator(_):
    info = "Sudarshan(DragonKingThe4th), known as sudarshan_.1715 on Instagram, is a Student. He is a random guy"
    speak_text(info)
    print(f"David: {info}")

def handle_who_is(text: str):
    person = re.sub(r"^who is", "", text, flags=re.IGNORECASE).strip()
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

def handle_open_chrome(_):
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        speak_text("Opening Chrome.")
        print("David: Opening Chrome.")
        os.startfile(chrome_path)
    else:
        speak_text("Chrome path not found.")
        print("David: Chrome path not found.")

def handle_open_brave(_):
    brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    if os.path.exists(brave_path):
        speak_text("Opening Brave.")
        print("David: Opening Brave.")
        os.startfile(brave_path)
    else:
        speak_text("Brave path not found.")
        print("David: Brave path not found.")

def handle_open_vpn(_):
    vpn_path = r"C:\Program Files\Proton\VPN\ProtonVPN.Launcher.exe"
    if os.path.exists(vpn_path):
        speak_text("Opening VPN And Connecting")
        print("David: Opening VPN And Connecting")
        os.startfile(vpn_path)
    else:
        speak_text("VPN path not found.")
        print("David: VPN path not found.")

def handle_open_code(_):
    speak_text("Opening VS Code.")
    print("David: Opening VS Code.")
    os.system("code")

def handle_click_photo(_):
    speak_text("Okay, capturing your photo.")
    capture_photo()

def handle_weather_city(text: str):
    m = re.search(r"weather (?:in|for) (.*)", text, re.IGNORECASE)
    city = m.group(1).strip() if m else DEFAULT_CITY
    resp = get_weather(city)
    print(f"David: {resp}")
    speak_text(resp)

def handle_weather_default(_):
    resp = get_weather(DEFAULT_CITY)
    print(f"David: {resp}")
    speak_text(resp)

def handle_play_youtube(text: str):
    m = re.search(r"play (.*) on youtube", text, re.IGNORECASE)
    if m:
        q = m.group(1).strip()
        speak_text(f"Playing {q} on YouTube.")
        py.playonyt(q)

def handle_google_search(text: str):
    m = re.search(r"search (.*) on google", text, re.IGNORECASE)
    if m:
        q = m.group(1).strip()
        speak_text(f"Searching Google for {q}.")
        py.search(q)

def handle_play_music(text: str):
    m1 = re.search(r"play (.*) by (.*)", text, re.IGNORECASE)
    m2 = re.search(r"play (.*) song", text, re.IGNORECASE)
    if m1:
        song = m1.group(1).strip()
        music_player.play(song)
    elif m2:
        song = m2.group(1).strip()
        music_player.play(song)
    else:
        music_player.play()

def handle_stop_music(_):
    music_player.stop()
    speak_text("Music stopped.")

def handle_pause_music(_):
    music_player.pause()

def handle_resume_music(_):
    music_player.resume()

def handle_next_song(_):
    music_player.next()

def handle_whats_playing(_):
    speak_text("I'm not currently set up to tell you the song name once it's playing, but I can play something new if you like!")

def handle_generate_image(text: str):
    m = re.search(r"(?:generate|create|make) (?:an |a )?image of (.*)", text, re.IGNORECASE)
    prompt = m.group(1).strip() if m else text
    generate_image(prompt)

COMMANDS = [
    Command(r"^(bye|goodbye|exit|stop)$", handle_exit),
    Command(r"^(what's the time|tell me the time|current time)$", handle_time),
    Command(r"^(what is the date today|what day is it|what's the date)$", handle_date),
    Command(r"^(who created you|who is your creator)$", handle_creator),
    Command(r"^who is .*", handle_who_is),
    Command(r"^open chrome$", handle_open_chrome),
    Command(r"^open brave$", handle_open_brave),
    Command(r"^(open vpn|open proton)$", handle_open_vpn),
    Command(r"^(open code|open vs|open vs code)$", handle_open_code),
    Command(r"^(click photo|take a picture)$", handle_click_photo),
    Command(r"^(what is the weather in .+|weather in .+|how is the weather in .+)$", handle_weather_city),
    Command(r"^(weather|current weather)$", handle_weather_default),
    Command(r"^play .* on youtube$", handle_play_youtube),
    Command(r"^search .* on google$", handle_google_search),
    Command(r"^(play music|play a song|start music|play .+ by .+|play .+ song)$", handle_play_music),
    Command(r"^stop music$", handle_stop_music),
    Command(r"^pause music$", handle_pause_music),
    Command(r"^(resume music|continue music)$", handle_resume_music),
    Command(r"^next song$", handle_next_song),
    Command(r"^what's playing$", handle_whats_playing),
    Command(r"^(generate|create|make) (an |a )?image of .+$", handle_generate_image),
]

def dispatch(user_input: str):
    text = user_input.strip()
    for cmd in COMMANDS:
        if cmd.regex.search(text):
            result = cmd.handler(text)
            return result
    nltk_response = nltk_chatbot.respond(text)
    if nltk_response:
        speak_text(nltk_response)
        print(f"David: {nltk_response}")
        return
    reply = llm(text)
    speak_text(reply)
    print(f"David: {reply}")

def chat_loop():
    print("Hi! I'm David, an AI assistant. Say 'bye' or 'goodbye' to exit.")
    speak_text("Hi! I'm David, an AI assistant. Say 'bye' or 'goodbye' to exit.")
    last_input_time = time.time()
    while True:
        if time.time() - last_input_time > IDLE_TIMEOUT_SECONDS:
            speak_text("No input detected. Exiting now. Goodbye!")
            print("David: No input detected. Exiting now. Goodbye!")
            break
        user_input = get_audio_input()
        if not user_input:
            continue
        last_input_time = time.time()
        result = dispatch(user_input.lower())
        if result == "__EXIT__":
            break

def cleanup():
    try:
        engine.stop()
    except Exception:
        pass
    try:
        music_player.stop()
    except Exception:
        pass
    if pygame.mixer.get_init():
        try:
            pygame.mixer.quit()
        except Exception:
            pass
    print("David session ended and resources released.")

atexit.register(cleanup)
signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

if __name__ == "__main__":
    pygame.mixer.init()
    chat_loop()
