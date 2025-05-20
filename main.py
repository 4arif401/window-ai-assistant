import os
import json
import subprocess
import speech_recognition as sr
import pyttsx3
from datetime import datetime
import requests
import webbrowser
import re

# ===== GLOBAL =====
input_mode = "text"  # default input method

# ===== CHECK URL =====
def is_url(text):
    return re.match(r"^(https?:\/\/)?(www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}", text)

# ===== CHAT HISTORY =====
HISTORY_FILE = "chat_history.json"

def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_chat_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# ===== MEMORY =====
def load_memory():
    try:
        with open("memory.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_memory(memory):
    with open("memory.json", "w") as f:
        json.dump(memory, f, indent=2)

# ===== LOAD WEB SHORTCUTS =====
def load_web_shortcuts():
    try:
        with open("web_shortcuts.json", "r") as f:
            return json.load(f)
    except:
        return {}

# ===== VOICE IO =====
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            print(f"You (voice): {text}")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""

def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.say(text)
    engine.runAndWait()

# ===== OPEN APP =====
def open_app(name, memory, web_shortcuts):
    name = name.lower().strip()
    if name in memory:
        name = memory[name]

    apps = {
        "vlc": "start vlc",
        "chrome": "start chrome",
        "notepad": "start notepad",
        "opera gx": os.path.expandvars(r'start "" "%LOCALAPPDATA%\\Programs\\Opera GX\\opera.exe"'),
        "spotify": os.path.expandvars(r'start "" "%APPDATA%\\Spotify\\Spotify.exe"'),
    }
    if name in apps:
        command = apps[name]
        if callable(command):
            command()
        else:
            os.system(command)
        return f"Opening {name}..."
    
    elif name in web_shortcuts:
        webbrowser.open(web_shortcuts[name])
        return f"Opening {name}..."

    return f"Sorry, I don’t know how to open {name}."

# ===== CLOSE APP =====
def close_app(name, memory):
    name = name.lower().strip()
    if name in memory:
        name = memory[name]

    processes = {
        "vlc": "vlc.exe",
        "chrome": "chrome.exe",
        "notepad": "notepad.exe",
        "opera gx": "opera.exe",
        "spotify": "spotify.exe"
    }
    if name in processes:
        try:
            subprocess.run(["taskkill", "/f", "/im", processes[name]], check=True)
            return f"Closed {name}."
        except subprocess.CalledProcessError:
            return f"Failed to close {name}. Maybe it's not running?"
    return f"I don’t know how to close {name}."

# ===== CALL LM STUDIO =====
def call_lm_studio(prompt):
    try:
        response = requests.post(
            "http://localhost:1234/v1/completions",
            headers={"Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "max_tokens": 150,
                "temperature": 0.7,
                "stop": ["Human:", "AI:"]
            }
        )
        return response.json()["choices"][0]["text"].strip()
    except Exception as e:
        return f"Error talking to local model: {e}"

# ===== PROCESS INPUT =====
def process_input(user_input, memory, chat_history, web_shortcuts):
    user_input = user_input.lower().strip()

    if "remember that" in user_input:
        try:
            key, value = user_input.split("remember that")[1].strip().split(" is ")
            key = key.strip()
            value = value.strip()

            # If it's a web URL
            if is_url(value):
                # If it doesn't already have http, add it
                if not value.startswith("http"):
                    value = "https://" + value
                web_shortcuts[key] = value
                with open("web_shortcuts.json", "w") as f:
                    json.dump(web_shortcuts, f, indent=2)
                return f"Got it! I'll remember that '{key}' is {value}."

            # If it's a general memory fact
            memory[key] = value
            save_memory(memory)
            return f"Got it! I'll remember that {key} is {value}."

        except:
            return "Hmm, I didn’t understand that format. Try: remember that X is Y"

    elif any(k in user_input for k in ["open", "start", "run", "launch"]):
        for k in ["open", "start", "run", "launch"]:
            if k in user_input:
                app = user_input.split(k)[-1].strip()
                return open_app(app, memory, web_shortcuts)

    elif any(k in user_input for k in ["close", "stop", "exit app"]):
        for k in ["close", "stop", "exit app"]:
            if k in user_input:
                app = user_input.split(k)[-1].strip()
                return close_app(app, memory)

    elif user_input.startswith("play"):
        possible_name = user_input.replace("play", "").strip()
        if possible_name in memory:
            url = memory[possible_name]
            os.system(f'start {url}')
            return f"Playing {possible_name} on Spotify..."
        for key in memory:
            if possible_name in key and ("playlist" in key or "mix" in key):
                url = memory[key]
                os.system(f'start {url}')
                return f"Playing {key} on Spotify..."
        return "I don't know that playlist yet. Try teaching me first!"

    elif user_input in ["what playlists do you know", "what playlists do you know?", "list playlists"]:
        playlists = [key for key in memory if "playlist" in key or "mix" in key]
        if playlists:
            return "🎶 I know these playlists:\n- " + "\n- ".join(playlists)
        else:
            return "I don't know any playlists yet. Try teaching me one!"

    elif "what is today's date" in user_input or "what's today's date" in user_input:
        today = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {today}."

    elif "what time is it" in user_input or "current time" in user_input or "what time is now" in user_input:
        now = datetime.now().strftime("%I:%M %p")
        return f"The current time is {now}."
    
    elif user_input.startswith("search for ") or user_input.startswith("google "):
        query = user_input.replace("search for", "").replace("google", "").strip()
        if query:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching Google for '{query}'..."
        else:
            return "What do you want me to search for?"

    # ===== Fallback to local LLM =====
    # Build last 5 lines of memory
    memory_prompt = "\n".join(
        [f"Human: {h['user']}\nAisi: {h['ai']}" for h in chat_history[-5:]]
    )

    prompt = f"I am Aisi, your personal AI assistant.\nHuman: {user_input}\nAisi:"
    response = call_lm_studio(prompt)
    return response


# ===== MAIN CHAT LOOP =====
def run_chat():
    global input_mode
    memory = load_memory()
    chat_history = load_chat_history()
    web_shortcuts = load_web_shortcuts()
    print("🤖 Hello! I'm your AI. Say 'exit' to quit.")
    print("💡 You can say 'switch to voice' or 'switch to text' anytime.")

    while True:
        if input_mode == "voice":
            user_input = listen()
            if not user_input:
                continue
        else:
            user_input = input("You: ")

        user_input = user_input.lower().strip()

        if user_input in ["switch to voice", "change to voice", "voice mode"]:
            input_mode = "voice"
            print("🎤 Switched to VOICE mode.")
            speak("Switched to voice mode.")
            continue

        elif user_input in ["switch to text", "change to text", "text mode"]:
            input_mode = "text"
            print("⌨️ Switched to TEXT mode.")
            speak("Switched to text mode.")
            continue

        elif user_input in ["exit", "quit"]:
            print("👋 Bye!")
            speak("Goodbye!")
            break

        response = process_input(user_input, memory, chat_history, web_shortcuts)
        print("Aisi:", response)
        speak(response)
        chat_history.append({"user": user_input, "ai": response})
        save_chat_history(chat_history)

# ===== RUN =====
if __name__ == "__main__":
    run_chat()
