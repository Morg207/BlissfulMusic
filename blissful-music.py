import pygame
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from ttkthemes import ThemedTk
import os

pygame.mixer.init()

class MusicPlayer:
    def __init__(self):
        self.window = ThemedTk()
        self.window.title("Blissful Music 1.0")
        self.window.config(background="white")
        right_frame, track_info_frame, options_frame = self.create_frames()
        MusicPlayer.style_player()
        self.create_welcome_message()
        self.create_song_label(track_info_frame)
        self.create_buttons(track_info_frame, options_frame)
        options_frame.pack(padx=(10,10),pady=(20,20))
        self.create_volume_slider()
        self.window_frame.pack(padx=20,pady=20)
        self.left_frame.pack(side="left",padx=(0,0))
        self.create_track_info(right_frame)
        right_frame.pack(padx=(10,0),pady=(20,0))
        self.muted = False
        self.filenames = []
        self.pathnames = []
        self.volume = 1.0

    def create_frames(self):
        self.window_frame = tk.Frame(self.window, background="white")
        self.left_frame = ttk.Frame(self.window_frame, style="config.TFrame")
        right_frame = ttk.Frame(self.window_frame, style="config.TFrame")
        track_info_frame = ttk.Frame(self.left_frame)
        options_frame = ttk.Frame(self.left_frame)
        return right_frame, track_info_frame, options_frame

    def run_player(self):
        self.window.mainloop()
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

    def create_welcome_message(self):
        welcome_message = ttk.Label(self.window_frame,text="Welcome to blissful music",anchor="center",width=23,foreground="white",background="green",font=("Arial",14))
        welcome_message.pack(ipady=6)

    def create_song_label(self, track_info_frame):
        self.song_label = ttk.Label(track_info_frame, text="Song title...", font=("Arial", 12), justify=tk.CENTER,
                                    foreground="black", wraplength=170)
        self.song_label.pack(side="left", padx=(20, 0))

    def create_track_info(self, right_frame):
        self.track_number = ttk.Label(right_frame,text="Tracks: 0")
        track_frame = ttk.LabelFrame(right_frame,text="Tracks")
        self.track_list = tk.Listbox(track_frame,width=40, height=20,selectmode=tk.SINGLE,activestyle="none",font=("Arial",10))
        self.track_list.bind("<<ListboxSelect>>", self.mouse_select)
        self.track_list.pack()
        scrollbar_y = ttk.Scrollbar(right_frame,orient=tk.VERTICAL,command=self.track_list.yview)
        self.track_list.config(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right",fill="y")
        scrollbar_x = ttk.Scrollbar(track_frame,orient=tk.HORIZONTAL, command=self.track_list.xview)
        self.track_list.config(xscrollcommand=scrollbar_x.set)
        scrollbar_x.pack(side="bottom", fill="x")
        track_frame.pack()
        self.track_number.pack(pady=(0,3),padx=(3,0),side="left")

    def create_volume_slider(self):
        frame = ttk.Frame(self.left_frame)
        volume_slider = ttk.Scale(frame,from_=0, to=10,orient=tk.HORIZONTAL,length=120, command=self.change_volume, value=10)
        volume_slider.pack(side="left",padx=(0,10))
        self.loop_var = tk.IntVar(value=1)
        loop_checkbox = ttk.Checkbutton(frame,text="Loop",variable=self.loop_var)
        loop_checkbox.pack(side="right")
        frame.pack(pady=(0,20))

    def create_buttons(self, track_info_frame, options_frame):
        track_button = ttk.Button(track_info_frame,text="Load tracks",command=self.load_tracks)
        track_button.pack(side="right",padx=(10,0),anchor="s")
        track_info_frame.pack(pady=(20,0))
        self.create_control_buttons(options_frame)

    def create_control_buttons(self, options_frame):
        self.play_button = ttk.Button(options_frame, text="Play", command=self.play, width=4)
        stop_button = ttk.Button(options_frame, text="Stop", command=self.stop, width=4)
        pause_button = ttk.Button(options_frame, text="Pause", command=MusicPlayer.pause, width=6)
        unpause_button = ttk.Button(options_frame, text="Unpause", command=MusicPlayer.unpause, width=8)
        mute_button = ttk.Button(options_frame, text="Mute", command=self.mute, width=4)
        self.play_button.pack(side="left", padx=(0, 1))
        stop_button.pack(side="left", padx=(0, 1))
        pause_button.pack(side="left", padx=(0, 1))
        unpause_button.pack(side="left", padx=(0, 1))
        mute_button.pack(side="left")

    @staticmethod
    def style_player():
        style = ttk.Style()
        style.theme_use("radiance")
        style.configure("config.TFrame",relief=tk.RAISED)
        style.configure("style.TFrame", background="white")
        style.configure("style.TLabel", relief=tk.RAISED)
        style.configure("TButton",font=("Arial",7))
        style.configure("TCheckbutton",font=("Arial",11), indicatorsize=16)

    def change_volume(self,current_volume):
        self.volume = float(current_volume) / 10.0
        pygame.mixer.music.set_volume(self.volume)

    def load_tracks(self):
        filetypes = [("Mp3", "*.mp3"),("Wav","*.wav"),("Ogg","*.ogg")]
        pathnames = filedialog.askopenfilenames(filetypes=filetypes)
        if pathnames:
            self.filenames.clear()
            for pathname in pathnames:
                filename = os.path.basename(pathname)
                self.filenames.append(filename)
            self.pathnames = pathnames
            self.track_list.delete(0, tk.END)
            self.track_list.insert(tk.END,*self.filenames)
            self.select_first_track()
            pygame.mixer.music.unload()
            pygame.mixer.music.load(self.pathnames[0])

    def play(self):
        try:
           if self.loop_var.get():
               pygame.mixer.music.play(loops=-1)
           else:
               pygame.mixer.music.play()
           self.play_button.config(state="disabled")
        except pygame.error:
            pass

    def stop(self):
        try:
            pygame.mixer.music.stop()
            self.play_button.config(state="enabled")
        except pygame.error:
            pass

    @staticmethod
    def pause():
        try:
            pygame.mixer.music.pause()
        except pygame.error:
            pass
        
    @staticmethod
    def unpause():
        try:
            pygame.mixer.music.unpause()
        except pygame.error:
            pass

    def mute(self):
        try:
            self.muted = not self.muted
            if self.muted:
                pygame.mixer.music.set_volume(0.0)
            else:
                pygame.mixer.music.set_volume(self.volume)
        except pygame.error:
            pass

    def mouse_select(self, event=None):
        if self.track_list.size() > 0:
            self.play_button.config(state="enabled")
            selected_index = self.track_list.curselection()[0]
            self.select_track(selected_index)

    def select_track(self, selected_index):
        pathname = self.pathnames[selected_index]
        track_name = self.filenames[selected_index]
        self.song_label.config(text=track_name)
        try:
            pygame.mixer.music.unload()
            pygame.mixer.music.load(pathname)
        except pygame.error:
            pass
        self.track_list.selection_set(selected_index)

    def select_first_track(self):
        self.track_list.selection_set(0)
        self.song_label.config(text=self.filenames[0])
        self.track_number.config(text=f"Tracks: {self.track_list.size()}")
        self.play_button.config(state="enabled")
               
if __name__ == "__main__":
    music_player = MusicPlayer()
    music_player.run_player()
