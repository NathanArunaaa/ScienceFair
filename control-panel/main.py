
import customtkinter
import threading
import sys
import cv2
from PIL import Image, ImageTk
from tkinter import messagebox
import os

from web_interface.app import start_flask
from functions import (
    change_scaling_event, 
    sys_shutdown, 
    sys_restart, 
    get_local_ip,
    play_buzzer
)

customtkinter.set_appearance_mode("light")  
customtkinter.set_default_color_theme("blue") 

class TextWidgetStream:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.after(0, self._write, message)
    
    def _write(self, message):
        self.text_widget.insert("end", message)
        self.text_widget.yview("end")  

    def flush(self):
        pass

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        #------inits------- 
        self.title("HASTE CONTROL PANEL")
        self.config(cursor="none")
        self.cap = cv2.VideoCapture(0) 
         

        self.attributes("-fullscreen", True)
        self.config(cursor="none")
        self.change_scaling_event("130%")

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        #------Sidebar------- 
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0, fg_color="white")
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="HASTE", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Start", hover_color="#3b8ed0", command=self.buzzer_thread)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_1.configure(cursor="none")

        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, text="System Calibration", hover_color="#3b8ed0", command=self.buzzer_thread)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_2.configure(cursor="none")

        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, text="Load Sample", hover_color="#3b8ed0", command=self.buzzer_thread)
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        self.sidebar_button_3.configure(cursor="none")
        
        self.sidebar_button_6 = customtkinter.CTkButton(self.sidebar_frame, text="Flush System", hover_color="#3b8ed0", )
        self.sidebar_button_6.grid(row=4, column=0, padx=20, pady=10)
        self.sidebar_button_6.configure(cursor="none")

        self.sidebar_button_4 = customtkinter.CTkButton(self.sidebar_frame, text="System Restart", hover_color="#3b8ed0", command=self.sys_restart)
        self.sidebar_button_4.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.sidebar_button_4.configure(cursor="none")

        self.sidebar_button_5 = customtkinter.CTkButton(self.sidebar_frame, text="Shut Down", hover_color="#3b8ed0", command=self.sys_shutdown)
        self.sidebar_button_5.grid(row=7 , column=0, padx=20, pady=(10, 10))
        self.sidebar_button_5.configure(cursor="none")
        
      
        

        local_ip = get_local_ip() 
        self.local_ip_label = customtkinter.CTkLabel(self.sidebar_frame, text=f"{local_ip}:5000", anchor="w")
        self.local_ip_label.grid(row=8, column=0, padx=20, pady=(10, 20))



        #------Video Feeds-------
        self.video_feeds_frame = customtkinter.CTkFrame(self, fg_color="white")
        self.video_feeds_frame.grid(row=1, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.video_feeds_frame.grid_columnconfigure(0, weight=1)
        self.video_feeds_frame.grid_rowconfigure(4, weight=1)
        self.textbox = customtkinter.CTkTextbox(self, width=250)

        self.cam_buttons = customtkinter.CTkSegmentedButton(
            self.video_feeds_frame, 
            values=["Microscope", "CAM-1", "CAM-2"],
            command=self.on_camera_change 
        )
        self.cam_buttons.grid(row=0, column=0, padx=20, pady=10)
        
        self.video_frame = customtkinter.CTkFrame(self.video_feeds_frame, fg_color="white")
        self.video_frame.grid(row=1, column=0, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.video_label = customtkinter.CTkLabel(self.video_frame, text="")
        self.video_label.grid(row=0, column=0, padx=20, pady=20) 
        
    

        self.update_video_feed()


        #------Console log-------
        self.textbox.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.textbox.configure(cursor="none") 

        sys.stdout = TextWidgetStream(self.textbox)
        sys.stderr = TextWidgetStream(self.textbox)
        
        #------Tabs-------
        self.tabview = customtkinter.CTkTabview(self, fg_color="white", width=250)
        self.tabview.grid(row=0, column=2, padx=(20, 0), pady=(0, 0), sticky="nsew")
        self.tabview.add("Blade")
        self.tabview.add("Sensors")
        self.tabview.add("Steppers")

        #------Blades-------
        self.blade_health = customtkinter.CTkLabel(self.tabview.tab("Blade"), text="Blade Health:")
        self.blade_health.grid(row=0, column=0, padx=20, pady=20)
        self.blade_cylce = customtkinter.CTkLabel(self.tabview.tab("Blade"), text="Blade Cylces: 182")
        self.blade_cylce.grid(row=1, column=0, padx=20, pady=20)
        self.blade_progressbar_1 = customtkinter.CTkProgressBar(self.tabview.tab("Blade"))
        self.blade_progressbar_1.grid(row=2, column=0, padx=20, pady=20)

        #------Sensors-------
        self.label_tab_2 = customtkinter.CTkLabel(self.tabview.tab("Sensors"), text="Sensor info here")
        self.label_tab_2.grid(row=0, column=0, padx=20, pady=20)
        
        #------Steppers-------
        self.up_button = customtkinter.CTkButton(self.tabview.tab("Steppers"), text="↑", width=20)
        self.up_button.grid(row=0, column=1, padx=10, pady=10)

        self.left_button = customtkinter.CTkButton(self.tabview.tab("Steppers"), text="←", width=20)
        self.left_button.grid(row=1, column=0, padx=10, pady=10)
        
        self.left_button = customtkinter.CTkButton(self.tabview.tab("Steppers"), text="O", width=20)
        self.left_button.grid(row=1, column=1, padx=10, pady=10)

        self.right_button = customtkinter.CTkButton(self.tabview.tab("Steppers"), text="→", width=20)
        self.right_button.grid(row=1, column=2, padx=10, pady=10)

        self.down_button = customtkinter.CTkButton(self.tabview.tab("Steppers"), text="↓", width=20)
        self.down_button.grid(row=2, column=1, padx=10, pady=10)
        
        
        #------Switch buttons-------
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self, fg_color="white", label_text="Active Indicators")
        self.scrollable_frame.grid(row=1, column=2, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame_switches = []
        for i in range(4):
            switch = customtkinter.CTkSwitch(master=self.scrollable_frame, text=f"Indicator {i}")
            switch.grid(row=i, column=0, padx=10, pady=(0, 20))
            self.scrollable_frame_switches.append(switch)
            
            
        #------Default values-------
        self.textbox.insert("0.0", "Developed By: Nathan Aruna & Arielle Benarroch\n\n" + "Console Log:\n\n" )
        self.cam_buttons.set("Microscope")
        
  
    #------Functions-------
    def buzzer_thread(self):
        buzzer_thread = threading.Thread(target=play_buzzer)
        buzzer_thread.daemon = True
        buzzer_thread.start()  
        
    def show_confirmation_dialog(self, action):
        response = messagebox.askyesno("Confirm Action", f"Are you sure you want to {action}?")
        return response
    

    def on_camera_change(self, event):
        selected_camera = self.cam_buttons.get()
        print(f"Selected camera: {selected_camera}")  
        camera_index = 0  

        if selected_camera == "CAM-1":
            camera_index = 0  
        elif selected_camera == "CAM-2":
            camera_index = 1  
        elif selected_camera == "Microscope":
            camera_index = 2 
        
        self.cap.release() 
        self.cap = cv2.VideoCapture(camera_index)  
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Unable to access camera: {camera_index}")
   
    def change_scaling_event(self, new_scaling: str):
        change_scaling_event(new_scaling)

    def sys_shutdown(self):
        if self.show_confirmation_dialog("Shut Down"):
           sys_shutdown()
           
    def sys_restart(self):
        if self.show_confirmation_dialog("Restart"):
           sys_restart()

    def update_video_feed(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
            img = Image.fromarray(frame)  
            imgtk = ImageTk.PhotoImage(image=img) 
            self.video_label.configure(image=imgtk)
            self.video_label.imgtk = imgtk  

        self.after(10, self.update_video_feed)

    def on_closing(self, event=0):
        self.cap.release()  
        self.destroy()
    
 

if __name__ == "__main__":
    print(os.getcwd())
    app = App()
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()
    app.mainloop()
