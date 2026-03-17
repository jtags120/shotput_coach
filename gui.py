from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QLineEdit, QSlider, QWidget, QSplitter, QStackedWidget, QVBoxLayout, QListWidget, QLabel, 
    QHBoxLayout, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, Slot, QCoreApplication, Signal
from PySide6.QtGui import QImage, QPixmap
import numpy as np
import cv2 as cv

class HoverSidebar(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.collapsed_ratio = 0.10
        self.expanded_ratio = 0.40

        
        self.setMaximumWidth(50)
        self.setMinimumWidth(50)
        
        self.anim = QPropertyAnimation(self, b"maximumWidth")
        self.anim.setDuration(150)

    def parent_width(self):
        if self.parentWidget():
            return self.parentWidget().width() # type: ignore
        return 800

    def collapsed_width(self):
        return max(50, int(self.parent_width() * self.collapsed_ratio))

    def expanded_width(self):
        return int(self.parent_width() * self.expanded_ratio)

    def enterEvent(self, event):
        self.animate(self.expanded_width())

    def leaveEvent(self, event):
        self.animate(self.collapsed_width())

    def animate(self, width):
        self.anim.stop()
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(width)
        self.anim.start()



class HomeScreen(QWidget):
    clicked = Signal(QWidget)
    def __init__(self, main_obj, stack):
        super().__init__()
        self.stack = stack

        self.main_obj = main_obj

        main_layout = QVBoxLayout(self)

        main_layout.addStretch(35)
        main_button_row = QHBoxLayout()
        main_button_row.setSpacing(40)

        self.image_button = QPushButton("Image")
        self.video_button = QPushButton("Video")
        self.livestream_button = QPushButton("Livestream")

        
        self.image_button.clicked.connect(lambda: self.start("image"))
        self.video_button.clicked.connect(lambda: self.start("video"))
        self.livestream_button.clicked.connect(lambda: self.start("livestream"))

        for btn in (self.image_button, self.video_button, self.livestream_button):
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # type: ignore
            btn.setMinimumHeight(100)

        main_button_row.addWidget(self.image_button)
        main_button_row.addWidget(self.video_button)
        main_button_row.addWidget(self.livestream_button)

        main_layout.addLayout(main_button_row)
        main_layout.addStretch(50)

        exit_layout = QHBoxLayout()
        self.exit_button = QPushButton("Exit")
        self.exit_button.setMinimumSize(150, 60)
        self.exit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) # type: ignore
        exit_layout.addStretch(1)
        exit_layout.addWidget(self.exit_button)
        exit_layout.addStretch(1)
        main_layout.addLayout(exit_layout)
        main_layout.addStretch(30)

        self.exit_button.clicked.connect(QCoreApplication.instance().quit) # type: ignore
        
    def start(self, str):
        self.main_obj.set_process(str)
        self.stack.setCurrentIndex(1)

class InputScreen(QWidget):
    image_path = Signal(str)
    mode_signal = Signal(str)
    def __init__(self, main_obj, stack):
        super().__init__()
        self.stack = stack
        self.main_obj = main_obj

        self.main_layout = QVBoxLayout(self)
        self.mode = ""

        
        self.mode_label = QLabel("Mode:")
        self.image_btn = QPushButton("Image")
        self.video_btn = QPushButton("Video")
        self.livestream_btn = QPushButton("Livestream")

        mode_row = QHBoxLayout()
        mode_row.addWidget(self.mode_label)
        mode_row.addWidget(self.image_btn)
        mode_row.addWidget(self.video_btn)
        mode_row.addWidget(self.livestream_btn)

        self.main_layout.addLayout(mode_row)

        
        self.file_label = QLabel("File:")
        self.file_input = QLineEdit()
        self.file_browse = QPushButton("Browse")
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_label)
        file_row.addWidget(self.file_input)
        file_row.addWidget(self.file_browse)
        self.main_layout.addLayout(file_row)

        
        self.save_annotated = QCheckBox("Save annotated media")
        self.save_annotated.setChecked(True)
        self.save_raw = QCheckBox("Save raw livestream")
        self.main_layout.addWidget(self.save_annotated)
        self.main_layout.addWidget(self.save_raw)
        
        self.raw_label = QLabel("Raw livestream: ")
        self.raw_input = QLineEdit()
        self.raw_browse = QPushButton("Browse")
        raw_row = QHBoxLayout()
        raw_row.addWidget(self.raw_label)
        raw_row.addWidget(self.raw_input)
        raw_row.addWidget(self.raw_browse)
        self.main_layout.addLayout(raw_row)
        
        self.output_label = QLabel("Output folder:")
        self.output_input = QLineEdit()
        self.output_browse = QPushButton("Browse")
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_label)
        output_row.addWidget(self.output_input)
        output_row.addWidget(self.output_browse)
        self.main_layout.addLayout(output_row)

        
        self.start_btn = QPushButton("Start")
        self.main_layout.addWidget(self.start_btn)

        
        self.image_btn.clicked.connect(lambda: (self.set_mode("image"), self.mode_signal.emit("image")))
        self.video_btn.clicked.connect(lambda: (self.set_mode("video"), self.mode_signal.emit("video")))
        self.livestream_btn.clicked.connect(lambda: (self.set_mode("livestream"), self.mode_signal.emit("livestream")))
        self.file_browse.clicked.connect(self.browse_file)
        self.output_browse.clicked.connect(self.browse_output)
        self.raw_browse.clicked.connect(self.browse_output)
        self.start_btn.clicked.connect(self.start_processing)
        
        self.file_label.hide()
        self.file_browse.hide()
        self.file_input.hide()
        self.save_annotated.hide()
        self.output_browse.hide()
        self.output_input.hide()
        self.output_label.hide()
        self.save_raw.hide()
        self.raw_label.hide()
        self.raw_input.hide()
        self.raw_browse.hide()
        
        self.save_raw.stateChanged.connect(self.on_save_raw)
        self.save_annotated.stateChanged.connect(self.on_save_annotations)
    
        
    def set_mode(self, mode):
        self.mode = mode
        self.main_obj.set_process(mode)
        
        self.output_browse.show()
        self.output_input.show()
        self.output_label.show()
        
        if mode == "image":
            self.save_raw.hide()
            self.file_label.setText("Image file:")
            self.file_label.show()
            self.file_browse.show()
            self.file_input.show()
            
        elif mode == "video":
            self.save_raw.hide()
            self.file_label.setText("Video file:")
            self.file_label.show()
            self.file_browse.show()
            self.file_input.show()
           
        elif mode == "livestream":
            self.save_raw.show()
            self.file_label.hide()
            self.file_browse.hide()
            self.file_input.hide()
        self.save_annotated.show()

    @Slot(bool)
    def on_save_raw(self, checked):
        if checked:
            self.raw_label.show()
            self.raw_input.show()
            self.raw_browse.show()
        else:
            self.raw_label.hide()
            self.raw_input.hide()
            self.raw_browse.hide()
            
    @Slot(bool)
    def on_save_annotations(self, checked):
        if(checked):
            self.output_label.setText("Select where to save the annotated file")
            self.output_input.show()
            self.output_browse.show()
            self.output_label.show()
        else:
            self.output_input.hide()
            self.output_browse.hide()
            self.output_label.hide()
        
        
    def browse_file(self):
        if self.mode in ("image", "video"):
            file, _ = QFileDialog.getOpenFileName(self, "Select file")
            if file:
                self.file_input.setText(file)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_input.setText(folder)
        
    def start_processing(self):
        file_path = self.file_input.text()
        
        output_folder = False
        save_annotated = self.save_annotated.isChecked()
        if(save_annotated):    
            output_folder = self.output_input.text()
        
        raw_stream = False
        save_raw = self.save_raw.isChecked() if self.mode == "livestream" else False
        if(save_raw):
                    raw_stream = self.raw_input.text()
                    
        # Pass options to Main
        self.main_obj.fetch(
            mode=self.mode,
            file=file_path,
            output=output_folder,
            save_annotated=save_annotated,
            save_raw=save_raw,
            raw_stream = raw_stream
        )
        self.main_obj.start_processing_threads()
        
        if self.mode == "image":
            self.image_path.emit(file_path)
        
        self.stack.setCurrentIndex(2)
        
class ProcessingScreen(QWidget):
    def __init__(self, main_obj, stack):
        super().__init__()
        self.user_scrubbing = False
        self.frame_index = 0
        self.buffer = {}
        self.timestamps = []
        self.stack = stack
        self.main_obj = main_obj
        self.main_layout = QVBoxLayout(self)

        
        self.video_label = QLabel("Waiting for frames...")
        self.video_label.setAlignment(Qt.AlignCenter) # type: ignore
        self.video_label.setStyleSheet("background-color: black;")
        self.main_layout.addWidget(self.video_label, stretch=1)

        
        controls_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.slider = QSlider(Qt.Horizontal) # type: ignore
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.slider)
        self.main_layout.addLayout(controls_layout)

        
        self.back_btn = QPushButton("Back")
        self.main_layout.addWidget(self.back_btn)

        self.slider.sliderPressed.connect(self.start_scrub)
        self.slider.sliderReleased.connect(self.end_scrub)
        self.slider.sliderMoved.connect(self.scrub_to)
        self.playing = True
        
        
        self.play_btn.clicked.connect(self.toggle_play)
        self.back_btn.clicked.connect(self.go_back)
        
    @Slot(np.ndarray, int)
    def update_buffer(self, frame, timestamp):
        
        self.buffer[self.frame_index] = {"frame": frame, "timestamp": timestamp}
        
        if not self.timestamps or timestamp > self.timestamps[-1]:
            self.timestamps.append(timestamp)
        self.display_frame(frame, timestamp)
        self.frame_index += 1
        
        
    @Slot(str)
    def get_mode(self, mode):
        self.mode = mode
        print(self.mode)
        if self.mode == "image":
            self.slider.hide()
            self.play_btn.hide()
            self.playing = False
            self.slider.setValue(0)
        elif self.mode == "video":
            self.slider.show()
            self.play_btn.show()
            self.playing = True
    
    
    @Slot()
    def set_total_frames(self):
        self.slider.setRange(1, len(self.buffer))
        
    @Slot()
    def start_scrub(self):
        self.user_scrubbing = True
        self.playing = False
        self.play_btn.setText("Play")

    @Slot()
    def end_scrub(self):
        frame_index = self.slider.value()
        print(f"end_scrub called, frame_index={frame_index}, in_buffer={frame_index in self.buffer}")
        self.user_scrubbing = False
        self.play_btn.setText("Pause" if self.playing else "Play")
        
        
        if frame_index in self.buffer:
            timestamp = self.buffer[frame_index]["timestamp"]
            frame = self.buffer[frame_index]["frame"]
            self.display_frame(frame, timestamp, True)
            
            self.main_obj.capture_worker.seek_signal.emit(frame_index)
            

    @Slot(int)
    def scrub_to(self, frame_number):
        if self.user_scrubbing:
            self.main_obj.capture_worker.seek_signal.emit(frame_number)
    
    def toggle_play(self):
        self.playing = not self.playing
        self.play_btn.setText("Pause" if self.playing else "Play")
    
    @Slot(np.ndarray, int)
    def display_frame(self, frame: np.ndarray, timestamp: int, force = False):
        if frame is None:
            return
        if self.playing or self.mode == "image":
            rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888) # type: ignore
            pix = QPixmap.fromImage(img).scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation # type: ignore
            )
            self.video_label.setPixmap(pix)

        if not self.user_scrubbing and self.playing:
            self.slider.setValue(timestamp)

    def go_back(self):
        self.playing = False
        self.video_label.clear()
        self.video_label.setText("Waiting for frames...")
        self.stack.setCurrentIndex(0)

class ResultsScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Results Screen"))

class GUI(QWidget):
    def __init__(self, main_obj):
        super().__init__()
        self.setWindowTitle("Landmark Estimation")
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)

    
        self.splitter = QSplitter(Qt.Horizontal) # type: ignore

    
        self.sidebar = HoverSidebar()
        self.sidebar.addItems(["Home", "Input", "Processing", "Results"])
        self.workspace = QStackedWidget()
        self.home_screen = HomeScreen(main_obj, self.workspace)
        self.input_screen = InputScreen(main_obj, self.workspace)
        self.processing_screen = ProcessingScreen(main_obj, self.workspace)
      
        
        self.workspace.addWidget(self.home_screen)
        self.workspace.addWidget(self.input_screen)
        self.workspace.addWidget(self.processing_screen)
        self.workspace.addWidget(ResultsScreen())

      
        self.sidebar.currentRowChanged.connect(self.workspace.setCurrentIndex)

       
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.workspace)

        layout.addWidget(self.splitter)
        self.input_screen.mode_signal.connect(self.processing_screen.get_mode)
 
    def showEvent(self, event):
        super().showEvent(event)
        init_sidebar_width = self.sidebar.collapsed_width()
        self.sidebar.setMaximumWidth(init_sidebar_width)
        self.sidebar.setMinimumWidth(init_sidebar_width)
        self.splitter.setSizes([init_sidebar_width, int(self.width()*0.50)])
