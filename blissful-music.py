import pygame
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from ttkthemes import ThemedTk
import random
import os
import av
import threading

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
pygame.mixer.init()

def write_wav_file(audio_data, wav_output):
    try:
        input_stream = audio_data.streams.audio[0]
        output_stream = wav_output.add_stream("pcm_s16le", rate=input_stream.rate)
        resampler = av.AudioResampler("s16", "stereo", rate=input_stream.rate)
        for frame in audio_data.decode(input_stream):
            resampled = resampler.resample(frame)
            for resampled_frame in resampled:
                for packet in output_stream.encode(resampled_frame):
                    wav_output.mux(packet)
        for resampled_frame in resampler.resample(None):
            for packet in output_stream.encode(resampled_frame):
                wav_output.mux(packet)
        write_success = True
    except Exception:
        write_success = False
    finally:
        audio_data.close()
        wav_output.close()
    return write_success

class ConvertProgress:
    def __init__(self, window, total_files):
        self.wavs_written = 0
        self.total_files = total_files
        self.window = window
        self.top_window = tk.Toplevel(self.window)
        self.top_window.title("Convert Progress")
        self.top_window.transient(self.window)
        self.top_window.focus_force()
        frame = tk.Frame(self.top_window)
        self.progress_label = tk.Label(frame, text="Progress: 0%", font=("Arial",13))
        self.progress_label.pack(pady=(0,10))
        self.progress_bar = ttk.Progressbar(frame, length=150, mode="determinate", orient=tk.HORIZONTAL)
        self.progress_bar.pack()
        frame.pack(padx=(25, 25), pady=(25,25))
        self.top_window.update_idletasks()
        half_window_width = self.top_window.winfo_width() // 2
        half_window_height = self.top_window.winfo_height() // 2
        self.top_window.geometry(
            f"+{(self.window.winfo_x() + self.window.winfo_width() // 2) \
                - half_window_width}+{(window.winfo_y() + window.winfo_height() // 2) - half_window_height}")

    def _update(self):
        if not self.top_window.winfo_exists():
            return
        self.wavs_written+=1
        progress = int(self.wavs_written / self.total_files * 100)
        self.progress_bar["value"] = progress
        self.progress_label.config(text=f"Progress: {progress}%")

    def update_progress(self):
        self.window.after(0, self._update) #Never update gui components in a separate thread with tkinter.
                                           #After runs this code on the gui thread as soon as possible.
    def destroy_window(self, millis=0):
        self.window.after(millis, self._destroy_window) 

    def _destroy_window(self):
        if self.top_window.winfo_exists():
            self.top_window.destroy()

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
        self.window_frame.pack(padx=20,pady=(20, 25))
        self.left_frame.pack(side="left",padx=(0,0))
        self.create_track_info(right_frame)
        self.create_audio_converter(right_frame)
        right_frame.pack(padx=(10,0),pady=(20,0))
        self.muted = False
        self.playing = False
        self.filenames = []
        self.pathnames = []
        self.volume = 1.0
        self.selected_index = 0
        self.output_directory = ""
        self.play_next()
        self.convert_progress = None

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
        self.track_number.pack(pady=(3,3),padx=(3,0),side="left")

    def create_audio_converter(self, right_frame):
        output_button = ttk.Button(right_frame, width=6, text="Folder", command=self.output_select)
        output_button.pack(side="right", padx=(0,10),pady=(6, 8))
        self.convert_button = ttk.Button(right_frame, state="disabled", width=10, text="Make Wavs", command=self.convert)
        self.convert_button.pack(side="right", padx=(0,5),pady=(6, 8))

    def show_conversion_error(self, failed_wavs):
        messagebox.showerror(
            title="Wav Conversion Error",
            message=f"{failed_wavs} Wav file(s) could not be written.",
            parent=self.window
        )

    def show_conversion_success(self):
        messagebox.showinfo(
            title="Operation Successful",
            message="Wavs written successfully.",
            parent=self.window
        )

    def show_overwrite_error(self):
        messagebox.showerror(
            title="Overwrite Error",
            message="Reading and writing the same wav file. Choose different files to convert.",
            parent=self.window)
        self.convert_button.config(state="enabled")

    @staticmethod
    def delete_corrupt_wav(wav_path): #Why opening a file for writing, it creates the file in the file system.
        if os.path.exists(wav_path): #Stops the user from having to delete corrupt files manually.
            try:
                os.remove(wav_path)
            except PermissionError:
                pass

    def check_same_file(self, pathname, wav_path):
        if os.path.exists(wav_path):
            if os.path.samefile(pathname, wav_path):
                self.convert_progress.destroy_window()
                self.window.after(0, self.show_overwrite_error)
                return True
        return False

    def create_wavs(self):
        failed_wavs = 0
        for i in range(len(self.pathnames)):
            pathname = self.pathnames[i]
            audio_data = av.open(pathname)
            filename = self.filenames[i]
            wav_filename = os.path.splitext(filename)[0] + ".wav"
            wav_path = os.path.join(self.output_directory, wav_filename)
            if self.check_same_file(pathname, wav_path):
                return
            wav_output = av.open(wav_path, mode="w")
            if not write_wav_file(audio_data, wav_output):
                failed_wavs+=1
                MusicPlayer.delete_corrupt_wav(wav_path)
            else:
                self.convert_progress.update_progress()
        self.convert_progress.destroy_window(50) #This deletes the progress bar window 50 milliseconds after conversion finishes.
        if failed_wavs > 0:                      #This is to allow the progress bar to update fully to 100%.
            self.window.after(0, self.show_conversion_error, failed_wavs)
        else:
            self.window.after(0, self.show_conversion_success)
        self.window.after(0, lambda: self.convert_button.config(state="enabled"))

    def convert(self):
        if self.output_directory != "":
            self.convert_button.config(state="disabled")
            self.convert_progress = ConvertProgress(self.window, self.track_list.size())
            convert_thread = threading.Thread(target=self.create_wavs)
            convert_thread.start()

    def output_select(self):
        directory = filedialog.askdirectory(title="Wav Output")
        if directory:
            self.output_directory = directory
            if self.track_list.size() > 0:
                self.convert_button.config(state="enabled")

    def create_volume_slider(self):
        frame = ttk.Frame(self.left_frame)
        volume_slider = ttk.Scale(frame,from_=0, to=10,orient=tk.HORIZONTAL,length=120, command=self.change_volume, value=10)
        volume_slider.pack(side="left",padx=(0,10))
        self.loop_var = tk.IntVar(value=1)
        loop_checkbox = ttk.Checkbutton(frame,text="Loop",variable=self.loop_var)
        loop_checkbox.pack(side="left", padx=(0,8))
        shuffle_button = ttk.Button(frame, text="Shuffle", command=self.shuffle, width=7)
        shuffle_button.pack(side="left")
        frame.pack(pady=(0,20))

    def create_buttons(self, track_info_frame, options_frame):
        track_button = ttk.Button(track_info_frame,text="Load tracks",command=self.load_tracks)
        track_button.pack(side="right",padx=(10,0),anchor="s")
        track_info_frame.pack(pady=(20,0))
        self.create_control_buttons(options_frame)

    def create_control_buttons(self, options_frame):
        self.play_button = ttk.Button(options_frame, text="Play", command=self.play, width=4)
        stop_button = ttk.Button(options_frame, text="Stop", command=self.stop, width=4)
        pause_button = ttk.Button(options_frame, text="Pause", command=self.pause, width=6)
        unpause_button = ttk.Button(options_frame, text="Unpause", command=self.unpause, width=8)
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

    def play_next(self):
        if not pygame.mixer.music.get_busy() and self.playing: #If loop is off, plays the playlist from start to finish.
            self.track_list.select_clear(self.selected_index)  #Loops back to the start when done.
            self.selected_index += 1
            if self.selected_index >= len(self.filenames):
                self.selected_index = 0
            pygame.mixer.music.load(self.pathnames[self.selected_index])
            if self.loop_var.get():
                pygame.mixer.music.play(loops=-1)
            else:
                pygame.mixer.music.play()
            self.track_list.selection_set(self.selected_index)
            self.song_label.config(text=self.filenames[self.selected_index])
        self.window.after(500, self.play_next)

    def shuffle(self):
        if self.pathnames:
            random.shuffle(self.pathnames) #A shuffle feature is really easy to implement.
            self.filenames.clear()         #Just uses the built in shuffle function.
            for pathname in self.pathnames:
                filename = os.path.basename(pathname)
                self.filenames.append(filename)
            self.playing = False
            self.populate_track_list()

    def load_tracks(self):
        filetypes = [("Mp3", "*.mp3"),("Wav","*.wav"),("Ogg","*.ogg"),("Flac","*.flac")]
        pathnames = list(filedialog.askopenfilenames(filetypes=filetypes))
        if pathnames:
            self.filenames.clear()
            for pathname in pathnames:
                filename = os.path.basename(pathname)
                self.filenames.append(filename)
            self.pathnames = pathnames
            self.populate_track_list()

    def populate_track_list(self):
        self.track_list.delete(0, tk.END)
        self.track_list.insert(tk.END, *self.filenames)
        self.select_first_track()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(self.pathnames[0])
        self.playing = False
        if self.output_directory != "":
            self.convert_button.config(state="enabled")

    def play(self):
        try:
           if self.loop_var.get():
               pygame.mixer.music.play(loops=-1)
           else:
               pygame.mixer.music.play()
           self.play_button.config(state="disabled")
           self.playing = True
        except pygame.error:
            pass

    def stop(self):
        try:
            pygame.mixer.music.stop()
            self.play_button.config(state="enabled")
            self.playing = False
        except pygame.error:
            pass

    def pause(self):
        try:
            pygame.mixer.music.pause()
            self.playing = False
        except pygame.error:
            pass

    def unpause(self):
        try:
            pygame.mixer.music.unpause()
            if self.play_button.cget("state") == "disabled":
              self.playing = True
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
            self.selected_index = self.track_list.curselection()[0]
            self.select_track(self.selected_index)
            self.playing = False

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
        self.selected_index = 0
        self.track_list.selection_set(self.selected_index)
        self.song_label.config(text=self.filenames[self.selected_index])
        self.track_number.config(text=f"Tracks: {self.track_list.size()}")
        self.play_button.config(state="enabled")
               
if __name__ == "__main__":
    music_player = MusicPlayer()
    music_player.run_player()
