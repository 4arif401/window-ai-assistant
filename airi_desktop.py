import tkinter as tk
from PIL import Image, ImageTk
import time
import threading
import random
from ai_voice_interface import listen_until_name, listen, speak, process_input, load_memory, load_chat_history, save_chat_history, load_web_shortcuts, pending_dangerous
import os
import pyautogui

# === CONFIG ===
IDLE_IMG = "airi_state/airi_idle.png"
WALK_IMG = "airi_state/airi_walk.png"
SLEEP_IMG = "airi_state/airi_sleep.png"
POPCORN_IMG1 = "airi_state/airi_popcorn1.png"
POPCORN_IMG2 = "airi_state/airi_popcorn2.png"
SCALE_WIDTH = 225
SCALE_HEIGHT = 225
IDLE_TIMEOUT = 60  # seconds

class AiriApp:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "#0000FF")
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.x = random.randint(100, self.screen_width - SCALE_WIDTH)
        taskbar_height = 48  # Adjust if needed
        self.y = self.screen_height - SCALE_HEIGHT - taskbar_height

        transparent_color = "#0000FF"
        self.canvas = tk.Canvas(root, width=screen_w, height=screen_h, bg=transparent_color, highlightthickness=0)
        self.root.wm_attributes("-transparentcolor", transparent_color)

        self.canvas.pack()

        walk_right = self.load_scaled_image(WALK_IMG)
        walk_left = self.load_scaled_image(WALK_IMG, flip=True)

        self.frames = {
            "idle": self.load_scaled_image(IDLE_IMG),
            "walk_right": walk_right,
            "walk_left": walk_left,
            "sleep": self.load_scaled_image(SLEEP_IMG),
            "popcorn1": self.load_scaled_image(POPCORN_IMG1),
            "popcorn2": self.load_scaled_image(POPCORN_IMG2)
        }

        self.sprite = self.canvas.create_image(self.x, self.y, anchor="nw", image=self.frames["idle"])
        self.canvas.coords(self.sprite, self.x, self.y)
        self.state = "idle"
        self.last_active = time.time()
        self.sleep_start_time = None
        self.SLEEP_DURATION = 120  # seconds until she wakes up on her own
        self.is_interacting = False  # Lock movement when interacting

        self.screen_width = self.root.winfo_screenwidth()
        self.dx = 4

        #self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        #self.canvas.coords(self.sprite, self.x, self.y)

        #MODE
        self.movie_mode = False
        self.movie_frame = 0
        self.type_mode = False 

        #AI UPLOAD
        self.memory = load_memory()
        self.chat_history = load_chat_history()
        self.web_shortcuts = load_web_shortcuts()
        self.voice_enabled = True
        threading.Thread(target=self.voice_loop, daemon=True).start()

        threading.Thread(target=self.update_behavior, daemon=True).start()

    def load_scaled_image(self, file_path, flip=False):
        img = Image.open(file_path).convert("RGBA")
        if flip:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        return ImageTk.PhotoImage(img.resize((SCALE_WIDTH, SCALE_HEIGHT), Image.NEAREST))

    def spam_typing_loop(self):
        import pyautogui
        while self.type_mode:
            pyautogui.write("d a ", interval=0.001)  # 🟢 Ultra fast
            # Optional short pause to reduce CPU spike:
            time.sleep(0.001)

    def update_behavior(self):
        while True:
            time.sleep(0.1)
            
            if self.movie_mode:
                # Move Airi to bottom-right corner
                self.x = self.screen_width - SCALE_WIDTH
                self.y = self.screen_height - SCALE_HEIGHT - 40  # Adjust for taskbar
                self.canvas.coords(self.sprite, self.x, self.y)

                # Toggle frames every half second
                self.state = "popcorn1" if self.movie_frame % 2 == 0 else "popcorn2"
                self.update_sprite()
                self.movie_frame += 1
                time.sleep(0.5)
                continue  # Skip normal behavior

            # === TYPE MODE ===
            if self.type_mode:
                while True:
                    user_input = listen()
                    if user_input and "stop" in user_input.lower():
                        self.type_mode = False
                        speak("Stopped typing.")
                        break
                    #pyautogui.write("d a", interval=0.01)  # 🟡 Typing spam
                self.is_interacting = False
                self.last_active = time.time()
                continue
            
            if self.is_interacting:
                continue  # ❌ Don't update state if interacting

            elapsed = time.time() - self.last_active

            if elapsed > IDLE_TIMEOUT:
                if self.state != "sleep":
                    self.state = "sleep"
                    self.sleep_start_time = time.time()
            else:
                self.sleep_start_time = None
                self.state = "walk" if random.random() < 0.8 else "idle"

            self.update_sprite()

            if self.state == "walk":
                self.x += self.dx
                if self.x <= 0 or self.x + SCALE_WIDTH >= self.screen_width:
                    self.dx *= -1
                    self.x += self.dx
                self.canvas.coords(self.sprite, self.x, self.y)

    def update_sprite(self):
        if self.state == "walk":
            direction = "right" if self.dx > 0 else "left"
            self.canvas.itemconfig(self.sprite, image=self.frames[f"walk_{direction}"])
        else:
            self.canvas.itemconfig(self.sprite, image=self.frames[self.state])

    def wake_up(self):
        self.last_active = time.time()
        self.state = "idle"
        self.update_sprite()

    def voice_loop(self):
        while True:
            
            if self.movie_mode:
                user_input = listen()
                if user_input and "movie end" in user_input.lower():
                    self.movie_mode = False
                    self.state = "idle"
                    self.last_active = time.time()  # ✅ Restart activity timer
                    speak("That is a good movie.")
                    self.is_interacting = False 
                    #self.x = random.randint(100, self.screen_width - SCALE_WIDTH)
                    #self.y = self.screen_height - SCALE_HEIGHT - 40
                    #self.canvas.coords(self.sprite, self.x, self.y)
                    self.update_sprite()
                    continue
                else:
                    continue  # stay in movie mode and listen again
     
            if not listen_until_name(name="hey"):
                continue

            self.is_interacting = True  # 🧠 Lock behavior
            self.state = "idle"
            self.update_sprite()
            self.wake_up()  # update timer too

            speak("Yes?")
            user_input = listen()
            if not user_input:
                self.is_interacting = False
                continue

            response = process_input(user_input, self.memory, self.chat_history, self.web_shortcuts)
            
            #Movie
            if response == "__toggle_movie_mode__":
                self.movie_mode = not self.movie_mode
                if self.movie_mode:
                    self.state = "popcorn1"
                else:
                    self.state = "idle"
                    self.x = random.randint(100, self.screen_width - SCALE_WIDTH)
                    self.y = self.screen_height - SCALE_HEIGHT - 40
                    self.canvas.coords(self.sprite, self.x, self.y)
                continue
            
            #Type Loop
            # === TYPE MODE TOGGLE ===
            if response == "__toggle_type_mode__":
                self.type_mode = not self.type_mode
                if self.type_mode:
                    speak("Typing mode started.")
                    threading.Thread(target=self.spam_typing_loop, daemon=True).start()
                else:
                    speak("Typing mode stopped.")
                continue

            #Terminate
            if response == "__exit__":
                speak("Goodbye!")
                self.root.quit()
                os._exit(0)  # ⛔ Forcefully terminate all threads and close the app
                return
                
            print("Airi:", response)
            speak(response)
            self.chat_history.append({"user": user_input, "ai": response})
            save_chat_history(self.chat_history)
            self.state = "idle"
            self.update_sprite()

            self.last_active = time.time()
            self.is_interacting = False  # 🔓 Unlock after done

if __name__ == "__main__":
    root = tk.Tk()
    app = AiriApp(root)
    root.mainloop()
