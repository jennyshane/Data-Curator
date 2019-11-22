import sys
import time
from Dataset import *

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class Player(QMainWindow):
    def __init__(self, data, *args, **kwargs):
        super(Player, self).__init__(*args, **kwargs)

        self.data=Dataset(data)
        self.file_list=[]
        for f in self.data.get_files():
            self.file_list.append(f.split("/")[-1])
        #self.file_list=self.data.get_files()
        
        self.setWindowTitle("test")
        self.status={"playing":False}
        self.image_frame=QLabel()
        self.image_frame.setMinimumSize(424, 240)
        self.image_frame.setAlignment(Qt.AlignCenter)
        self.image_frame.setText("test")
        self.list_widget=QListWidget()
        self.list_widget.insertItems(0, self.file_list)
        self.list_widget.setMinimumWidth(200)
        self.list_widget.itemDoubleClicked.connect(lambda i:self.loadfile(i))
        self.list_widget.setCurrentRow(0)

        dock_widget=QDockWidget("file list", self)
        dock_widget.setObjectName("Data file list")
        dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        dock_widget.setWidget(self.list_widget)

        self.video_timer=QTimer()
        self.video_timer.timeout.connect(self.next_frame)
        self.video_timer.setInterval(30)

        self.videoBar=QToolBar("video playback")

        pfileaction=QAction(QIcon("icons/start.png"), "prevfile", self)
        pfileaction.triggered.connect(self.prev_file)
        self.videoBar.addAction(pfileaction)

        prevaction=QAction(QIcon("icons/larrow.png"), "prev", self)
        prevaction.triggered.connect(self.prev_frame)
        self.videoBar.addAction(prevaction)

        ppaction=QAction(QIcon("icons/playpause.png"), "playpause", self)
        ppaction.triggered.connect(self.playpause)
        self.videoBar.addAction(ppaction)

        nextaction=QAction(QIcon("icons/rarrow.png"), "next", self)
        nextaction.triggered.connect(self.next_frame)
        self.videoBar.addAction(nextaction)

        nfileaction=QAction(QIcon("icons/end.png"), "nextfile", self)
        nfileaction.triggered.connect(self.next_file)
        self.videoBar.addAction(nfileaction)
        
        layout=QVBoxLayout()
        layout.addWidget(self.image_frame)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)

        self.setCentralWidget(self.image_frame)

        self.addToolBar(Qt.BottomToolBarArea, self.videoBar)

        self.render_frame()

    def loadfile(self, i):
        self.data.goto_file(self.list_widget.row(i))
        self.render_frame()

    def playpause(self):
        if self.status["playing"]==False:
            self.video_timer.start()
            self.status["playing"]=True
        else:
            self.video_timer.stop()
            self.status["playing"]=False

    def next_file(self):
        indices=self.data.get_indices()
        if indices[0]!=len(self.file_list)-1:
            self.data.goto_file(indices[0]+1)
            self.render_frame()
            if self.list_widget.currentRow()!=indices[0]:
                self.list_widget.setCurrentRow(indices[0])

    def prev_file(self):
        indices=self.data.get_indices()
        if indices[0]!=0:
            self.data.goto_file(indices[0]-1)
            self.render_frame()
            if self.list_widget.currentRow()!=indices[0]:
                self.list_widget.setCurrentRow(indices[0])

    def next_frame(self):
        if self.data.next():
            self.render_frame()
            indices=self.data.get_indices()
            if self.list_widget.currentRow()!=indices[0]:
                self.list_widget.setCurrentRow(indices[0])

    def prev_frame(self):
        if self.data.prev():
            self.render_frame()
            indices=self.data.get_indices()
            if self.list_widget.currentRow()!=indices[0]:
                self.list_widget.setCurrentRow(indices[0])

    def render_frame(self):
        qimg=QImage(self.data.get_current_frame(), 424, 240, 424*3, QImage.Format_RGB888).rgbSwapped()
        self.image_frame.setPixmap(QPixmap.fromImage(qimg))


print(sys.argv)
app=QApplication(sys.argv)

window=Player(sys.argv[1:])
window.show()
app.exec_()
