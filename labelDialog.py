from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import copy

from Labelset import *

class Color(QWidget):
    def __init__(self, color, *args, **kwargs):
        super(Color, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        self.setMinimumSize(20, 20)
        palette=self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)
    def setcolor(self, color):
        palette=self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)
        self.show()

class LabelSettings(QDialog):
    def __init__(self, labels, label_colors, *args, **kwargs):
        super(LabelSettings, self).__init__(*args, **kwargs)
        self.label_colors=copy.deepcopy(label_colors)
        self.labels=copy.deepcopy(labels)
        
        self.makeLayout()
        self.setWindowTitle("Color picker")

    def makeLayout(self):
        frame_labelnames, bbox_labelnames=self.labels.getLabelNames()
        frame_wid=QWidget()
        self.labels_list=QListWidget()
        for l in frame_labelnames:
            self.labels_list.addItem(l)
        for l in bbox_labelnames:
            self.labels_list.addItem(l)

        fl_addButton=QPushButton("Add Frame Label")
        bl_addButton=QPushButton("Add Box Label")
        removeButton=QPushButton("Remove Label")
        editButton=QPushButton("Edit Label")
        colorButton=QPushButton("Change Label Color")
        self.colorPanel=Color("black")

        QBtn=QDialogButtonBox.Ok|QDialogButtonBox.Cancel
        self.buttonBox=QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout2=QVBoxLayout()
        layout2.addWidget(self.colorPanel)
        layout2.addWidget(fl_addButton)
        layout2.addWidget(bl_addButton)
        layout2.addWidget(removeButton)
        layout2.addWidget(editButton)
        layout2.addWidget(colorButton)

        layout1=QHBoxLayout()
        layout1.addWidget(self.labels_list)
        layout1.addLayout(layout2)

        layout3=QVBoxLayout()
        layout3.addLayout(layout1)
        layout3.addWidget(self.buttonBox)
        self.setLayout(layout3)

        self.labels_list.currentTextChanged.connect(self.listItem_CB)
        fl_addButton.clicked.connect(self.addFL_CB)
        bl_addButton.clicked.connect(self.addBL_CB)
        removeButton.clicked.connect(self.remove_CB)
        editButton.clicked.connect(self.edit_CB)
        colorButton.clicked.connect(self.color_CB)
        
    def addFL_CB(self):
        text, ok=QInputDialog.getText(self, "Add Label", "Add frame label name:")
        if ok:
            frame_labelnames, bbox_labelnames=self.labels.getLabelNames()
            if text in frame_labelnames or text in bbox_labelnames:
                box=QMessageBox(self)
                box.setText("That label name is already in use!")
                box.exec_()
            else:
                self.labels.addFrameLabel(text)
                self.label_colors[text]="blue"
                index=len(frame_labelnames)
                self.labels_list.insertItem(index-1, text)
        
    def addBL_CB(self):
        text, ok=QInputDialog.getText(self, "Add Label", "Add box label name:")
        if ok:
            frame_labelnames, bbox_labelnames=self.labels.getLabelNames()
            if text in frame_labelnames or text in bbox_labelnames:
                box=QMessageBox(self)
                box.setText("That label name is already in use!")
                box.exec_()
            else:
                self.labels.addBboxLabel(text)
                self.label_colors[text]="red"
                index=len(frame_labelnames)+len(bbox_labelnames)
                self.labels_list.insertItem(index, text)

    def remove_CB(self):
        box=QMessageBox(self)
        box.setText("Whoops, that feature isn't implemented")
        box.exec_()

    def edit_CB(self):
        box=QMessageBox(self)
        box.setText("Whoops, that feature isn't implemented")
        box.exec_()


    def color_CB(self):
        dlg=QColorDialog()
        if dlg.exec_():
            colorname=dlg.currentColor().name(QColor.HexRgb)
            label=self.labels_list.currentItem().text()
            self.label_colors[label]=colorname
            self.colorPanel.setcolor(colorname)

    def listItem_CB(self, item):
        label=item
        self.colorPanel.setcolor(self.label_colors[label])
        print("!")
        

if __name__=="__main__":
           
    class MainWindow(QMainWindow):
        def __init__(self, filenames, frame_labels, bbox_labels, *args, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
            self.button=QPushButton("BUTTON")
            self.labels=LabelSet(filenames, frame_labels, bbox_labels)
            self.flabel_list=QComboBox()
            self.flabel_list.addItems(frame_labels)
            self.blabel_list=QComboBox()
            self.blabel_list.addItems(bbox_labels)
            self.label_colors={}
            self.label_colors['']=self.palette().color(QPalette.Background)
            for i in frame_labels:
                self.label_colors[i]="blue"
            for i in bbox_labels:
                self.label_colors[i]="red"

            self.f_colorpanel=Color("blue")
            self.b_colorpanel=Color("red")

            layout=QVBoxLayout()
            layout.addWidget(self.flabel_list)
            layout.addWidget(self.f_colorpanel)
            layout.addWidget(self.blabel_list)
            layout.addWidget(self.b_colorpanel)
            layout.addWidget(self.button)

            widget=QWidget()
            widget.setLayout(layout)

            self.button.clicked.connect(self.buttonCB)
            self.flabel_list.currentIndexChanged[str].connect(self.flist_CB)
            self.blabel_list.currentIndexChanged[str].connect(self.blist_CB)

            self.setCentralWidget(widget)

        def buttonCB(self):
            dlg=LabelSettings(self.labels, self.label_colors)
            if dlg.exec_():
                self.labels=dlg.labels
                self.label_colors=dlg.label_colors
                frame_labels, bbox_labels=self.labels.getLabelNames()
                self.flabel_list.clear()
                self.flabel_list.addItems(frame_labels)
                self.blabel_list.clear()
                self.blabel_list.addItems(bbox_labels)
                self.f_colorpanel.setcolor(self.label_colors[self.flabel_list.currentText()])
                self.b_colorpanel.setcolor(self.label_colors[self.blabel_list.currentText()])

            else:
                print("canceled")

        def flist_CB(self, text):
                self.f_colorpanel.setcolor(self.label_colors[text])

        def blist_CB(self, text):
                self.b_colorpanel.setcolor(self.label_colors[text])

            


    app=QApplication(sys.argv)

    filelist=["file1", "file2", "file3"]
    frame_labels=["junk", "right", "left", "forward"]
    bbox_labels=["pedestrian", "traffic light"]

    window=MainWindow(filelist, frame_labels, bbox_labels)
    window.show()
    app.exec_()


