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

pygame.mixer.init()

MUSIC_FOLDER = "Music"
current_playlist = []
current_song_index = -1

def get_music_files():
    music_files = []
    if os.path.exists(MUSIC_FOLDER):
        for file in os.listdir(MUSIC_FOLDER):
            if file.endswith((".mp3", ".wav", ".ogg",)):
                music_files.append(os.path.join(MUSIC_FOLDER, file))
    return music_files

def play_music(song_name=None):
    global current_playlist, current_song_index
    music_files = get_music_files()

    if not music_files:
        speak_text("I can't find any music files in the 'music' folder. Please add some.", voice_id=david_voice_id)
        return

    if song_name:
        found_song = None
        for music_path in music_files:
            if song_name.lower() in os.path.basename(music_path).lower():
                found_song = music_path
                break
        
        if found_song:
            current_playlist = [found_song]
            current_song_index = 0
            pygame.mixer.music.load(current_playlist[current_song_index])
            pygame.mixer.music.play()
            speak_text(f"Now playing {os.path.basename(found_song).replace('.mp3', '')}.", voice_id=david_voice_id)
        else:
            speak_text(f"Sorry, I couldn't find a song called {song_name}. Playing a random track instead.", voice_id=david_voice_id)
            current_playlist = random.sample(music_files, len(music_files))
            current_song_index = 0
            pygame.mixer.music.load(current_playlist[current_song_index])
            pygame.mixer.music.play()
            speak_text(f"Now playing {os.path.basename(current_playlist[current_song_index]).replace('.mp3', '')}.", voice_id=david_voice_id)
    else:
        current_playlist = random.sample(music_files, len(music_files))
        current_song_index = 0
        pygame.mixer.music.load(current_playlist[current_song_index])
        pygame.mixer.music.play()
        speak_text(f"Now playing {os.path.basename(current_playlist[current_song_index]).replace('.mp3', '')}.", voice_id=david_voice_id)

def stop_music():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        speak_text("Music stopped.", voice_id=david_voice_id)
    else:
        speak_text("No music is currently playing.", voice_id=david_voice_id)

def pause_music():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        speak_text("Music paused.", voice_id=david_voice_id)
    else:
        speak_text("No music is currently playing to pause.", voice_id=david_voice_id)

def resume_music():
    if pygame.mixer.music.get_pos() != -1 and not pygame.mixer.music.get_busy():
        pygame.mixer.music.unpause()
        speak_text("Resuming music.", voice_id=david_voice_id)
    else:
        speak_text("No music paused to resume.", voice_id=david_voice_id)

def next_song():
    global current_playlist, current_song_index
    if not current_playlist:
        speak_text("There's no playlist to advance.", voice_id=david_voice_id)
        return

    current_song_index += 1
    if current_song_index >= len(current_playlist):
        current_song_index = 0

    pygame.mixer.music.load(current_playlist[current_song_index])
    pygame.mixer.music.play()
    speak_text(f"Playing next: {os.path.basename(current_playlist[current_song_index]).replace('.mp3', '')}.", voice_id=david_voice_id)

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
            stop_music()
            speak_text("Goodbye! Have a great day.", voice_id=david_voice_id)
            print("Chatbot: Goodbye! Have a great day.")
            break

        if "play music" in user_input.lower() or "play a song" in user_input.lower() or "start music" in user_input.lower():
            match_play_song = nltk.re.search(r"play (.*) by (.*)", user_input.lower())
            if match_play_song:
                song = match_play_song.group(1).strip()
                artist = match_play_song.group(2).strip()
                play_music(song)
                continue
            
            match_play_song_simple = nltk.re.search(r"play (.*) song", user_input.lower())
            if match_play_song_simple:
                song = match_play_song_simple.group(1).strip()
                play_music(song)
                continue

            play_music()
            continue

        elif "stop music" in user_input.lower():
            stop_music()
            continue
        elif "pause music" in user_input.lower():
            pause_music()
            continue
        elif "resume music" in user_input.lower() or "continue music" in user_input.lower():
            resume_music()
            continue
        elif "next song" in user_input.lower():
            next_song()
            continue
        elif "what's playing" in user_input.lower():
            pass

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
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        print("Chatbot session ended and resources released.")