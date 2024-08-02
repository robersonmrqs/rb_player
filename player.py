import customtkinter as ctk
import json
import io
import os
import random
import tkinter as tk
import vlc
from comtypes import CLSCTX_ALL
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageTk
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from tkinter.filedialog import askopenfilenames

vlc_path = r"C:\Program Files\VideoLAN\VLC"
os.add_dll_directory(vlc_path)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

CONFIG_FILE = "player_config.json"

class App(ctk.CTk):
    HEIGHT = 500
    WIDTH = 400

    def __init__(self):
        super().__init__()
        self.title("Rb player")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.resizable(False, False)

        self.playlist_button = ctk.CTkButton(self, image=ctk.CTkImage(Image.open('playlist.png'), size=(30, 30)), compound="left", width=35, height=35, corner_radius=0, text="", fg_color="#242424", bg_color="#242424", hover_color="#242424", hover=False, command=self.open_playlist)
        self.playlist_button.place(x=350, y=10)
        self.frame1 = ctk.CTkFrame(self)
        self.frame1.place(x=100, y=70)
        self.album_art_label = ctk.CTkLabel(self.frame1, width=200, height=150, text="")
        self.album_art_label.pack()
        self.backward_button = ctk.CTkButton(self, image=ctk.CTkImage(Image.open('backward.png'), size=(20, 20)), compound="left", width=35, height=35, corner_radius=0, text="", fg_color="#242424", hover_color="#242424", hover=False, command=self.previous_track)
        self.backward_button.place(x=30, y=330)
        self.play_button = ctk.CTkButton(self, image=ctk.CTkImage(Image.open('play.png'), size=(20, 20)), compound="left", width=35, height=35, corner_radius=0, text="", fg_color="#242424", hover_color="#242424", command=self.play_music)
        self.play_button.place(x=90, y=330)
        self.pause_button = ctk.CTkButton(self, image=ctk.CTkImage(Image.open('pause.png'), size=(20, 20)), compound="left", width=35, height=35, corner_radius=0, text="", fg_color="#242424", hover_color="#242424", command=self.pause_music)
        self.pause_button.place(x=150, y=330)
        self.stop_button = ctk.CTkButton(self, image=ctk.CTkImage(Image.open('stop.png'), size=(20, 20)), compound="left", width=35, height=35, corner_radius=0, text="", fg_color="#242424", hover_color="#242424", command=self.stop_music)
        self.stop_button.place(x=210, y=330)
        self.forward_button = ctk.CTkButton(self, image=ctk.CTkImage(Image.open('forward.png'), size=(20, 20)), compound="left", width=35, height=35, corner_radius=0, text="", fg_color="#242424", hover_color="#242424", command=self.next_track)
        self.forward_button.place(x=270, y=330)
        self.repeat_button = ctk.CTkButton(self, width=35, height=35, corner_radius=0, text="Off", text_color="#6495ED", fg_color="#242424", hover_color="#242424", command=self.toggle_repeat)
        self.repeat_button.place(x=330, y=330)
        self.current_time_label = ctk.CTkLabel(self, text="00:00")
        self.current_time_label.place(x=55, y=390)
        self.progressBar1 = ctk.CTkProgressBar(self, width=200)
        self.progressBar1.place(x=100, y=400)
        self.total_time_label = ctk.CTkLabel(self, text="00:00")
        self.total_time_label.place(x=310, y=390)
        self.volume_label = ctk.CTkLabel(self, text="Vol: 50")
        self.volume_label.place(x=350, y=280)
        self.volume_control = ctk.CTkSlider(self, from_=0, to=100, number_of_steps=100, orientation="vertical", command=self.set_volume)
        self.volume_control.place(x=365, y=70)
        self.musicname_label = ctk.CTkLabel(self, width=200, height=50, text="", anchor="center", justify="center")
        self.musicname_label.place(x=100, y=420)
        self.exit_button = ctk.CTkButton(self, text="Sair", width=50, height=30, fg_color="#ff4d4d", hover_color="#ff1a1a", command=self.quit)
        self.exit_button.place(x=0, y=470)
        self.player = vlc.MediaPlayer()
        self.playlist = []
        self.current_index = 0
        self.repeat_mode = 0
        self.load_state()
        self.system_volume_interface = self.get_system_volume_interface()
        initial_volume = self.get_current_system_volume()
        self.volume_control.set(initial_volume * 100)
        self.set_volume(initial_volume * 100)
        self.load_state()

    def get_system_volume_interface(self):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return interface.QueryInterface(IAudioEndpointVolume)

    def get_current_system_volume(self):
        volume_db = self.system_volume_interface.GetMasterVolumeLevel()
        min_volume, max_volume, _ = self.system_volume_interface.GetVolumeRange()
        volume_linear = (volume_db - min_volume) / (max_volume - min_volume)
        return max(0, min(volume_linear, 1))

    def open_playlist(self):
        files = askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac")])
        if files:
            self.playlist = list(files)
            self.current_index = 0
            self.play_music()
            self.save_state()

    def play_music(self):
        if self.playlist:
            self.player.stop()
            media = vlc.Media(self.playlist[self.current_index])
            self.player.set_media(media)
            self.player.play()
            self.update_music_name()
            self.monitor_progress()
            self.show_album_art()
            self.save_state()

    def pause_music(self):
        state = self.player.get_state()
        if state == vlc.State.Playing:
            self.player.pause()
        elif state == vlc.State.Paused:
            self.player.play()

    def stop_music(self):
        self.player.stop()

    def next_track(self):
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_music()

    def previous_track(self):
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_music()

    def update_music_name(self):
        if self.playlist:
            music_name = os.path.basename(self.playlist[self.current_index])
            music_name = music_name[:20] + ('...' if len(music_name) > 20 else '')
            self.musicname_label.configure(text=music_name)

    def monitor_progress(self):
        def update_progress():
            if self.player.get_state() in [vlc.State.Ended, vlc.State.Error]:
                if self.repeat_mode == 1:
                    self.play_music()
                elif self.repeat_mode == 2:
                    self.current_index = random.randint(0, len(self.playlist) - 1)
                    self.play_music()
                else:
                    self.next_track()
                return

            if self.player.get_length() > 0:
                progress = self.player.get_time() / self.player.get_length()
                self.progressBar1.set(progress)
                current_time = self.format_time(self.player.get_time() // 1000)
                total_time = self.format_time(self.player.get_length() // 1000)
                self.current_time_label.configure(text=current_time)
                self.total_time_label.configure(text=total_time)

            self.after(1000, update_progress)
        self.after(1000, update_progress)

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02}:{secs:02}"

    def set_volume(self, volume):
        volume = int(volume)
        self.player.audio_set_volume(volume)
        self.volume_label.configure(text=f"Vol: {volume}")
        min_volume, max_volume, _ = self.system_volume_interface.GetVolumeRange()
        volume_level = min_volume + (volume / 100 * (max_volume - min_volume))
        self.system_volume_interface.SetMasterVolumeLevel(volume_level, None)

    def toggle_repeat(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3
        repeat_text = ["Off", "Sequential", "Random"]
        self.repeat_button.configure(text=f"{repeat_text[self.repeat_mode]}")

    def save_state(self):
        state = {"playlist": self.playlist, "current_index": self.current_index}
        with open(CONFIG_FILE, "w") as file:
            json.dump(state, file)

    def load_state(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as file:
                state = json.load(file)
                self.playlist = state.get("playlist", [])
                self.current_index = state.get("current_index", 0)
                if self.playlist:
                    self.play_music()

    def show_album_art(self):
        try:
            audio = MP3(self.playlist[self.current_index], ID3=ID3)
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    image = Image.open(io.BytesIO(tag.data))
                    image = image.resize((200, 150), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.album_art_label.configure(image=photo)
                    self.album_art_label.image = photo
                    return
        except Exception as e:
            print(f"Erro ao carregar imagem do álbum: {e}")
            self.album_art_label.configure(image="")

if __name__ == "__main__":
    app = App()
    app.mainloop()