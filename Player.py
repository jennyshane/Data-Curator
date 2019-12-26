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
        self.label_colors={}
        self.label_colors['']=self.palette().color(QPalette.Background)
        for i in labels[0]:
            self.label_colors[i]="blue"
        for i in labels[1]:
            self.label_colors[i]="red"
        
        self.setWindowTitle("test")
        self.status={"playing":False}
        self.image_frame=bboxCanvas(848, 480)
        self.list_widget=QListWidget()
        self.list_widget.insertItems(0, self.file_list)
        self.list_widget.setMinimumWidth(200)
        self.list_widget.itemDoubleClicked.connect(lambda i:self.loadfile(i))
        self.list_widget.setCurrentRow(0)
        self.image_frame.new_box_signal.connect(self.mark_box)

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

        label_layout=QHBoxLayout()
        self.label_list_widget=QListWidget()
        self.label_list_widget.setFlow(QListView.LeftToRight)
        self.label_list_widget.setMaximumHeight(30)
        self.activeBox=-1
        lCycleBtn=QPushButton("<<")
        lCycleBtn.clicked.connect(self.boxCycleDown)
        rCycleBtn=QPushButton(">>")
        rCycleBtn.clicked.connect(self.boxCycleUp)
        remBtn=QPushButton("remove")
        remBtn.clicked.connect(self.remActiveBox)
        label_layout.addWidget(self.label_list_widget)
        label_layout.addWidget(lCycleBtn)
        label_layout.addWidget(rCycleBtn)
        label_layout.addWidget(remBtn)

        mainWidget=QWidget()
        layout=QVBoxLayout()
        layout.addWidget(self.labelBar)
        #layout.addWidget(self.label_list_widget)
        layout.addLayout(label_layout)
        layout.addWidget(self.image_frame)
        layout.addWidget(self.videoBar)
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

        self.label_range={"start":[0, 0], "end":[0, 0]}

        self.render_frame()
        self.fillLabels()

    def createLabelBar(self):
        frame_labels, bbox_labels=self.labelset.getLabelNames()
        self.labelBar=QToolBar("labeling")
        self.labelBar.addWidget(QLabel("Frame Labels: "))

        self.frame_label_selection=QComboBox()
        self.frame_label_selection.addItems(frame_labels)
        self.labelBar.addWidget(self.frame_label_selection)

        self.lBracketAction=QAction(QIcon("icons/lbracket.png"), "begin label range", self)
        self.lBracketAction.setCheckable(True)
        self.lBracketAction.triggered.connect(self.l_bracket)
        self.labelBar.addAction(self.lBracketAction)

        self.rBracketAction=QAction(QIcon("icons/rbracket.png"), "end label range", self)
        self.rBracketAction.setCheckable(True)
        self.rBracketAction.triggered.connect(self.r_bracket)
        self.labelBar.addAction(self.rBracketAction)

        markFrameAction=QAction(QIcon("icons/flag.png"), "Mark Frame", self)
        markFrameAction.triggered.connect(self.mark_frame)
        self.labelBar.addAction(markFrameAction)

        self.labelBar.addSeparator()
        self.labelBar.addWidget(QLabel("Box Labels: "))

        self.box_label_selection=QComboBox()
        self.box_label_selection.addItems(bbox_labels)
        self.labelBar.addWidget(self.box_label_selection)
        self.box_label_selection.currentIndexChanged[str].connect(self.boxLabelSelectCB)

        manageBtn=QPushButton("Manage Labels")
        manageBtn.clicked.connect(self.manageLabels)
        self.labelBar.addWidget(manageBtn)


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
        spacer=QWidget()
        spacer.setMinimumWidth(20)
        self.frameNumberLabel=QLabel()
        self.fileNumberLabel=QLabel()
        self.videoBar.addWidget(self.fileNumberLabel)
        self.videoBar.addWidget(spacer)
        self.videoBar.addWidget(self.frameNumberLabel)

        
  
    def loadfile(self, i):
        self.data.goto_file(self.list_widget.row(i))
        self.activeBox=-1
        self.render_frame()
        self.fillLabels()

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
            self.activeBox=-1
            self.render_frame()
            self.fillLabels()
            if self.list_widget.currentRow()!=indices[0]:
                self.list_widget.setCurrentRow(indices[0])

    def prev_file(self):
        indices=self.data.get_indices()
        if indices[0]!=0:
            self.data.goto_file(indices[0]-1)
            self.activeBox=-1
            self.render_frame()
            self.fillLabels()
            if self.list_widget.currentRow()!=indices[0]:
                self.list_widget.setCurrentRow(indices[0])

    def next_frame(self):
        if self.data.next():
            self.activeBox=-1
            self.render_frame()
            self.fillLabels()
            indices=self.data.get_indices()
            if self.list_widget.currentRow()!=indices[0]:
                self.list_widget.setCurrentRow(indices[0])

    def prev_frame(self):
        if self.data.prev():
            self.activeBox=-1
            self.render_frame()
            self.fillLabels()
            indices=self.data.get_indices()
            if self.list_widget.currentRow()!=indices[0]:
                self.list_widget.setCurrentRow(indices[0])

    def render_frame(self):
        indices=self.data.get_indices()
        self.image_frame.clear()
        qimg=QImage(self.data.get_current_frame(), 424, 240, 424*3, QImage.Format_RGB888).rgbSwapped()
        self.image_frame.setPixmap(QPixmap.fromImage(qimg).scaled(848, 480))
        self.fileNumberLabel.setText("File # "+str(indices[0])+"/"+str(len(self.file_list)))
        self.frameNumberLabel.setText("Frame # "+str(indices[1])+"/"+str(self.data.n_frames(indices[0])))

    def l_bracket(self):
        if self.lBracketAction.isChecked():
            self.label_range["start"]=self.data.get_indices()

    def r_bracket(self):
        if self.rBracketAction.isChecked():
            self.label_range["end"]=self.data.get_indices()

    def mark_frame(self):
        current_label=self.frame_label_selection.currentText()
        indices=self.data.get_indices()
        mark_current=False
        if self.lBracketAction.isChecked() and self.rBracketAction.isChecked():
            filenames=self.data.get_files()
            if self.label_range["start"][0]==self.label_range["end"][0]:
                nframes=self.label_range["end"][1]-self.label_range["start"][1]+1
                message='Assigning label "'+current_label+'" to '+str(nframes)+" frames in file "+filenames[self.label_range["start"][0]]+'\nOK?'
                reply=QMessageBox.question(self, "Confirm", message, QMessageBox.Ok|QMessageBox.Cancel)
                if reply==QMessageBox.Ok:
                    for i in range(self.label_range["start"][1], self.label_range["end"][1]+1):
                        self.labelset.markFrameLabel(self.label_range["start"][0], i, current_label)
                        if [self.label_range["start"][0], i]==indices:
                            mark_current=True

            elif self.label_range["start"][0]<self.label_range["end"][0]:
                message='Assigning label "'+current_label+'" to range from frame# '+str(self.label_range["start"][1])+\
                " in file "+filenames[self.label_range["start"][0]]+" to frame# "+str(self.label_range["end"][1])+\
                " in file "+filenames[self.label_range["end"][0]]+".\nOK?"
                reply=QMessageBox.question(self, "Confirm", message, QMessageBox.Ok|QMessageBox.Cancel)
                if reply==QMessageBox.Ok:
                    for i in range(self.label_range["start"][0]+1, self.label_range["end"][0]):
                        for j in range(0, self.data.n_frames(i)):
                            self.labelset.markFrameLabel(i, j, current_label)
                            if [i, j]==indices:
                                mark_current=True

                    for j in range(self.label_range["start"][1], self.data.n_frames(self.label_range["start"][0])):
                        self.labelset.markFrameLabel(self.label_range["start"][0], j, current_label)
                        if [self.label_range["start"][0], j]==indices:
                            mark_current=True
                    for j in range(0, self.label_range["end"][1]+1):
                        self.labelset.markFrameLabel(self.label_range["end"][0], j, current_label)
                        if [self.label_range["end"][0], j]==indices:
                            mark_current=True

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
            self.labelset.markFrameLabel(indices[0], indices[1], current_label)
            mark_current=True
        if mark_current==True:
            item=QListWidgetItem(current_label)
            item.setBackground(QColor(self.label_colors[current_label]))
            self.label_list_widget.addItem(item)

    def fillLabels(self):
        self.label_list_widget.clear()
        indices=self.data.get_indices()
        flabels, blabels=self.labelset.getLabels(indices[0], indices[1])
        self.label_list_widget.clear()
        if flabels!=[]:
            for i in flabels:
                item=QListWidgetItem(i)
                item.setBackground(QColor(self.label_colors[i]))
                self.label_list_widget.addItem(item)
        if blabels!=[]:
            for label, box in blabels:
                self.image_frame.addBox(box, self.label_colors[label])
            if self.activeBox!=-1:
                self.image_frame.setColor(self.activeBox, "white")


    def mark_box(self, x, y, w, h):
        indices=self.data.get_indices()
        current_label=self.box_label_selection.currentText()
        self.labelset.markBboxLabel(indices[0], indices[1], current_label, [x, y, w, h])
        self.fillLabels()

    def manageLabels(self):
        dlg=LabelSettings(self.labelset, self.label_colors)
        if dlg.exec_():
            self.labelset=dlg.labels
            self.label_colors=dlg.label_colors
            frame_labels, box_labels=self.labelset.getLabelNames()
            self.frame_label_selection.clear()
            self.frame_label_selection.addItems(frame_labels)
            self.box_label_selection.clear()
            self.box_label_selection.addItems(box_labels)
            self.fillLabels()

    def boxLabelSelectCB(self, label):
        self.image_frame.setColorDefaults(QColor(self.label_colors[label]), "default")
        self.image_frame.setColorDefaults(QColor(self.label_colors[label]), "new")

    def boxCycleUp(self):
        indices=self.data.get_indices()
        flabels, blabels=self.labelset.getLabels(indices[0], indices[1])
        if self.activeBox!=-1:
            activelabel=blabels[self.activeBox][0]
            self.image_frame.setColor(self.activeBox, self.label_colors[activelabel])
        self.activeBox=self.activeBox+1
        if self.activeBox==len(blabels):
            self.activeBox=-1
        else:
            print(self.activeBox)
            self.image_frame.setColor(self.activeBox, "white")
            print("!")

    def boxCycleDown(self):
        indices=self.data.get_indices()
        flabels, blabels=self.labelset.getLabels(indices[0], indices[1])
        if self.activeBox!=-1:
            activelabel=blabels[self.activeBox][0]
            self.image_frame.setColor(self.activeBox, self.label_colors[activelabel])
        self.activeBox=self.activeBox-1
        if self.activeBox==-2:
            self.activeBox=len(blabels)-1
        if self.activeBox!=-1:
            self.image_frame.setColor(self.activeBox, "white")

    def remActiveBox(self):
        indices=self.data.get_indices()
        flabels, blabels=self.labelset.getLabels(indices[0], indices[1])
        if self.activeBox!=-1:
            reply=QMessageBox.question(self, "Confirm", "Remove highlighted box with label "+blabels[self.activeBox][0]+"?", 
                    QMessageBox.Ok|QMessageBox.Cancel)
            if reply==QMessageBox.Ok:
                self.labelset.removeByIdx(indices[0], indices[1], self.activeBox)
                self.fillLabels()
        else:
            frame_label=self.label_list_widget.currentItem().text()
            reply=QMessageBox.question(self, "Confirm", "Remove label "+frame_label+"?", QMessageBox.Ok|QMessageBox.Cancel)
            if reply==QMessageBox.Ok:
                self.labelset.remove(indices[0], indices[1], frame_label)
                self.fillLabels()

print(sys.argv)
app=QApplication(sys.argv)

window=Player(sys.argv[1:], [["test", "sample"], ["testb", "sampleb"]])
window.show()
app.exec_()
