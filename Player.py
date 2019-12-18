import sys
import time
from Dataset import *
from Labelset import *
from labelDialog import *

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from bboxCanvas import *


class Player(QMainWindow):
    def __init__(self, data, labels, *args, **kwargs):
        super(Player, self).__init__(*args, **kwargs)

        self.data=Dataset(data)
        self.file_list=[]
        for f in self.data.get_files():
            self.file_list.append(f.split("/")[-1])

        self.labelset=LabelSet(self.file_list, labels[0], labels[1])
        
        self.setWindowTitle("test")
        self.status={"playing":False}
        self.image_frame=bboxCanvas(848, 480)
        self.list_widget=QListWidget()
        self.list_widget.insertItems(0, self.file_list)
        self.list_widget.setMinimumWidth(200)
        self.list_widget.itemDoubleClicked.connect(lambda i:self.loadfile(i))
        self.list_widget.setCurrentRow(0)

        dock_widget=QDockWidget("file list", self)
        dock_widget.setObjectName("Data file list")
        dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        dock_widget.setWidget(self.list_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)

        self.video_timer=QTimer()
        self.video_timer.timeout.connect(self.next_frame)
        self.video_timer.setInterval(30)

        self.createLabelBar()
        self.createVideoBar()

        mainWidget=QWidget()
        layout=QVBoxLayout()
        layout.addWidget(self.labelBar)
        layout.addWidget(self.image_frame)
        layout.addWidget(self.videoBar)
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

        self.label_range={"start":[0, 0], "end":[0, 0]}

        self.render_frame()

    def createLabelBar(self):
        frame_labels, bbox_labels=self.labelset.getLabelNames()
        self.labelBar=QToolBar("labeling")
        self.labelBar.addWidget(QLabel("Frame Labels: "))

        self.frame_label_selection=QComboBox()
        self.frame_label_selection.addItems(frame_labels)
        self.labelBar.addWidget(self.frame_label_selection)

        self.lBracketAction=QAction(QIcon("icons/lbracket.png"), "begin label range", self)
        lBracketAction.setCheckable(True)
        lBracketAction.triggered.connect(self.l_bracket)
        self.labelBar.addAction(lBracketAction)

        self.rBracketAction=QAction(QIcon("icons/rbracket.png"), "end label range", self)
        rBracketAction.setCheckable(True)
        rBracketAction.triggered.connect(self.r_bracket)
        self.labelBar.addAction(rBracketAction)

        markFrameAction=QAction(QIcon("icons/flag.png"), "Mark Frame", self)
        markFrameAction.triggered.connect(self.mark_frame)
        self.labelBar.addAction(markFrameAction)

        self.labelBar.addSeparator()
        self.labelBar.addWidget(QLabel("Box Labels: "))

        self.box_label_selection=QComboBox()
        self.box_label_selection.addItems(bbox_labels)
        self.labelBar.addWidget(self.box_label_selection)


    def createVideoBar(self):
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
        
  
    def loadfile(self, i):
        self.data.goto_file(self.list_widget.row(i))
        self.render_frame()

    def playpause(self):
        if self.status["playing"]==False:
            self.image_frame.setEnable(False)
            self.video_timer.start()
            self.status["playing"]=True
        else:
            self.image_frame.setEnable(True)
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
        self.image_frame.clear()
        qimg=QImage(self.data.get_current_frame(), 424, 240, 424*3, QImage.Format_RGB888).rgbSwapped()
        self.image_frame.setPixmap(QPixmap.fromImage(qimg).scaled(848, 480))

    def l_bracket(self):
        self.label_range["start"]=self.data.get_indices()

    def r_bracket(self):
        self.label_range["end"]=self.data.get_indices()

    def mark_frame(self):
        current_label=self.frame_label_selection.currentText()
        if self.lBracketAction.isChecked() and self.rBracketAction.isChecked():
            filenames=self.data.get_files()
            if self.label_range["start"][0]==self.label_range["end"][0]:
                nframes=self.label_range["end"][1]-self.label_range["start"][1]+1
                message='Assigning label "'+current_label+'" to '+str(nframes)+" frames in file "+fileneames[self.label_range["start"][0]]+'\nOK?'
                reply=QMessageBox.question(self, "Confirm", message, QMessageBox.Ok|QMessageBox.Cancel)
                if reply==QMessageBox.Ok:
                    for i in range(self.label_range["start"][1], self.label_range["end"][1]+1):
                        self.labelSet.markFrameLabel(self.label_range["start"][0], i, current_label)

            elif self.label_range["start"][0]<self.label_range["end"][0]:
                message='Assigning label "'+current_label+'" to range from frame# '+str(self.label_range["start"][1])+
                "in file "+fileneames[self.label_range["start"][0]]+" to frame# "+str(self.label_range["end"][1])+
                "in file "+fileneames[self.label_range["end"][0]]+".\nOK?"
                reply=QMessageBox.question(self, "Confirm", message, QMessageBox.Ok|QMessageBox.Cancel)
                if reply==QMessageBox.Ok:
                    for i in range(self.label_range["start"][0]+1, self.label_range["end"][0]):
                        for j in range(0, self.data.n_frames(i)):
                            self.labelSet.markFrameLabel(i, j, current_label)
                    for j in range(self.label_range["start"][1], self.data.n_frames(self.label_range["start"][0])):
                        self.labelSet.markFrameLabel(self.label_range["start"][0], j, current_label)
                    for j in range(0, self.label_range["end"][1]+1):
                        self.labelSet.markFrameLabel(self.label_range["end"][0], j, current_label)

            else:
                box=QMessageBox(self)
                box.setText("Range not in order")
                box.exec_()

        elif self.lBracketAction.isChecked():
            box=QMessageBox(self)
            box.setText("Label range start is set, but end is not set!")
            box.exec_()
        elif self.rBracketAction.isChecked():
            box=QMessageBox(self)
            box.setText("Label range end is set, but start is not set!")
            box.exec_()
        else:
            indices=self.data.get_indices()
            self.labelSet.markFrameLabel(indices[0], indices[1], current_label)

    def mark_box(self, x, y, w, h):
        pass

print(sys.argv)
app=QApplication(sys.argv)

window=Player(sys.argv[1:], [["test", "sample"], ["testb", "sampleb"]])
window.show()
app.exec_()
