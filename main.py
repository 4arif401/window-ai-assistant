import os
import json
import subprocess
import speech_recognition as sr
import pyttsx3
from datetime import datetime
import requests
import webbrowser
import re
import psutil
import platform
import socket
import shutil
try:
    import GPUtil
except:
    GPUtil = None
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import time
from dangerous_commands import dangerous_commands
import threading

# ===== GLOBAL =====
input_mode = "voice"  # default input method

# ===== TIME TRACKER FOR COMMAND =====
pending_dangerous = {"command": None, "timer": None}

# ===== CLICK IMAGE =====
def click_image_on_screen(target_img_path, confidence=0.8, click=True):
    try:
        # Take screenshot
        screenshot = ImageGrab.grab()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Load target image
        target = cv2.imread(target_img_path)
        result = cv2.matchTemplate(screenshot, target, cv2.TM_CCOEFF_NORMED)

        # Find locations where the match is above threshold
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val >= confidence:
            target_height, target_width = target.shape[:2]
            center_x = max_loc[0] + target_width // 2
            center_y = max_loc[1] + target_height // 2
            pyautogui.moveTo(center_x, center_y, duration=0.2)
            if click:
                pyautogui.click()
            return f"Clicked the image"
        else:
            return "Couldn’t find the image on screen."
    except Exception as e:
        return f"Error: {e}"

# ===== CHECK URL =====
def is_url(text):
    return re.match(r"^(https?:\/\/)?(www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}", text)

# ===== WAKE CALL FOR VOICE =====
def listen_until_name(name="hey"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"🎧 Say '{name}' to wake me up...")
        while True:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=4)
                command = recognizer.recognize_google(audio).lower()
                print(f"👂 Heard: {command}")
                if name in command:
                    return True
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                print("⚠️ Could not connect to speech service.")
                return False

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
        
#XTTS IMPORT AND OTHER
# === XTTSv2 (custom voice) setup ===
import torch
from torch.serialization import add_safe_globals

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig

add_safe_globals([
    XttsConfig,
    XttsAudioConfig,
    XttsArgs,
    BaseDatasetConfig
])

from TTS.api import TTS
xtts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
xtts.to("cuda" if torch.cuda.is_available() else "cpu")  # ✅ Auto GPU fallback

# Your trained voice clips (relative path)
speaker_wavs = [
    "my_voice_dataset/clips/001_cleaned.wav",
    "my_voice_dataset/clips/002_cleaned.wav",
    "my_voice_dataset/clips/003_cleaned.wav",
    "my_voice_dataset/clips/004_cleaned.wav",
    "my_voice_dataset/clips/005_cleaned.wav",
    "my_voice_dataset/clips/006_cleaned.wav",
    "my_voice_dataset/clips/007_cleaned.wav",
    "my_voice_dataset/clips/008_cleaned.wav",
    "my_voice_dataset/clips/009_cleaned.wav",
    "my_voice_dataset/clips/010_cleaned.wav"
]

import pygame
def speak(text):
    output_path = "airi_voice.wav"  # ✅ Change to WAV

    # Ensure pygame isn't using the file
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        pygame.mixer.quit()

    # Generate speech with XTTS
    xtts.tts_to_file(
        text=text,
        speaker_wav=speaker_wavs,
        language="en",
        file_path=output_path
    )

    # Wait a moment to ensure file is written
    time.sleep(0.1)

    # ✅ Play the clean .wav file
    pygame.mixer.init()
    pygame.mixer.music.load(output_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    
    pygame.mixer.quit()  # Release file for next use

def speak2(text):
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
        "spotify": lambda: subprocess.Popen(
            r'"C:\Users\4arif\OneDrive\Desktop\Shortcut Other\Spotify.lnk"', shell=True
        ),

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

def extract_url(text):
    # Try to match common URL formats
    match = re.search(r"(https?://\S+|www\.\S+|\b[a-zA-Z0-9\-]+\.[a-z]{2,}\S*)", text)
    if match:
        url = match.group(0)
        # If no scheme, add https://
        if not url.startswith("http"):
            url = "https://" + url
        return url
    return None

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
        return f"Error talking to local model"

# ===== PROCESS INPUT =====
def process_input(user_input, memory, chat_history, web_shortcuts):
    user_input = user_input.lower().strip()

    if user_input in ["exit", "quit"]:
        return "__exit__"

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

    elif any(user_input.startswith(k + " ") for k in ["open", "start", "run", "launch"]):
        for k in ["open", "start", "run", "launch"]:
            if user_input.startswith(k + " "):
                app = user_input[len(k):].strip()
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

    elif "what is today's date" in user_input or "today's date" in user_input:
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
    
    elif user_input.startswith("search youtube for ") or user_input.startswith("youtube "):
        query = user_input.replace("search youtube for", "").replace("youtube", "").strip()
        if query:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Searching Youtube for '{query}'..."
        else:
            return "What do you want me to search for?"

    elif "battery" in user_input:
        battery = psutil.sensors_battery()
        if battery:
            return f"Battery level is at {battery.percent}%. {'Charging' if battery.power_plugged else 'Not charging'}."
        else:
            return "I couldn't access battery info on your device."
    
    elif "how much ram" in user_input or "total ram" in user_input:
        total_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        return f"Your PC has {total_gb} GB of RAM."

    elif "ram used" in user_input or "ram usage" in user_input:
        ram = psutil.virtual_memory()
        used_gb = round((ram.total - ram.available) / (1024**3), 2)
        return f"You're currently using about {used_gb} GB of RAM."

    elif "disk" in user_input or "storage" in user_input:
        partitions = psutil.disk_partitions()
        output = "Storage Report:\n"

        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total = round(usage.total / (1024**3), 2)
                used = round(usage.used / (1024**3), 2)
                free = round(usage.free / (1024**3), 2)
                percent = usage.percent

                output += (
                    f"• {partition.device}\n"
                    f"  {total} GB Total \n  {used} GB Used \n  {free} GB Free ({percent}%)\n"
                )
            except:
                continue  # Some partitions might not be accessible

        return output.strip()

    elif "cpu" in user_input and "usage" in user_input:
        cpu_percent = psutil.cpu_percent(interval=1)
        return f"Your CPU is currently using {cpu_percent}%."

    elif "cpu" in user_input and "have" in user_input:
        return f"You're using this CPU: {platform.processor()}"

    elif "gpu" in user_input and "have" in user_input:
        if GPUtil:
            gpus = GPUtil.getGPUs()
            if gpus:
                return f"You're using this GPU: {gpus[0].name}"
            else:
                return "I couldn't detect any GPU on your system."
        else:
            return "GPU info not available. Try: pip install gputil"

    elif "ip" in user_input:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return f"Your local IP address is {ip_address}."
    
    elif "gpu usage" in user_input or "gpu temperature" in user_input:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            load = round(gpu.load * 100, 2)
            temp = gpu.temperature
            return (
                f" GPU Status:\n"
                f"• Name: {gpu.name}\n"
                f"• Usage: {load}%\n"
                f"• Temperature: {temp}°C"
            )
        else:
            return "I couldn't detect any GPU usage or temperature data."
        
    elif "click play" in user_input:
        return click_image_on_screen("images/play_button.png")

    elif "click pause" in user_input:
        return click_image_on_screen("images/pause_button.png")
    
    elif user_input in dangerous_commands:
        cmd_info = dangerous_commands[user_input]
        pending_dangerous["command"] = user_input
        return f"⚠️ That will {cmd_info['description']}. Are you sure? (yes/no)"

    elif pending_dangerous["command"]:
        if user_input in ["yes", "yeah", "sure"]:
            cmd = dangerous_commands[pending_dangerous["command"]]["command"]
            pending_dangerous["command"] = None
            os.system(cmd)
            return f"🛑 Executing command..."
        else:
            pending_dangerous["command"] = None
            return "❌ Cancelled the dangerous command."
    
    elif "movie" in user_input:
        return "__toggle_movie_mode__"

    # ===== Fallback to local LLM =====
    # Build last 5 lines of memory
    memory_prompt = "\n".join(
        [f"Human: {h['user']}\nAiri: {h['ai']}" for h in chat_history[-5:]]
    )

    prompt = f"I am Airi, your personal AI assistant.\nHuman: {user_input}\nAiri:"
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
            # Skip wake word if waiting for yes/no confirmation
            if pending_dangerous["command"]:
                user_input = listen()
            else:
                if not listen_until_name(name="hey"):
                    continue
                speak("Yes?")
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
        print("Airi:", response)
        speak(response)
        chat_history.append({"user": user_input, "ai": response})
        save_chat_history(chat_history)

# ===== RUN =====
if __name__ == "__main__":
    run_chat()
