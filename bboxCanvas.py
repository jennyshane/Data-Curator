from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys

class bboxCanvas(QWidget):
    def __init__(self, w, h, *args, **kwargs):
        super(bboxCanvas, self).__init__(*args, **kwargs)
        self.pixmap=None
        self.boxes=[]
        self.boxcolors=[]
        self.defaultBoxColor="red"
        self.activeBoxColor="blue"
        self.nextbox=None
        self.tpoint=None
        self.setMinimumSize(w, h)
        self.pixmapBox=self.rect()
        print(self.pixmapBox)

    def setPixmap(self, pm):
        self.pixmap=pm
        self.update()

    def resizeEvent(self, e):
        f_w=self.width()
        f_h=self.height()
        p_w=self.pixmap.width()
        p_h=self.pixmap.height()
        f_ratio=f_w/f_h
        p_ratio=p_w/p_h
        if f_ratio==p_ratio:
            self.pixmapBox=self.rect()
        elif f_ratio>p_ratio:
            new_p_w=int(p_w*f_h/p_h)
            new_p_h=f_h
            self.pixmapBox=QRect((f_w-new_p_w)/2, 0, new_p_w, new_p_h)
        else:
            new_p_w=f_w
            new_p_h=int(p_h*f_w/p_w)
            self.pixmapBox=QRect(0, (f_h-new_p_h)/2, new_p_w, new_p_h)
        self.update()

    def paintEvent(self, e):
        painter=QPainter(self)
        if self.pixmap!=None:
            painter.drawPixmap(self.pixmapBox, self.pixmap)
        pen=QPen()
        for i, box in enumerate(self.boxes):
            pen.setWidth(2)
            pen.setColor(QColor(self.boxcolors[i]))
            painter.setPen(pen)
            painter.drawRect(*box)
        if self.tpoint is not None:
            pen.setColor(QColor(self.activeBoxColor))
            if self.nextbox is None:
                pen.setWidth(5)
                painter.setPen(pen)
                painter.drawPoint(*self.tpoint)
            else:
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(*self.nextbox)
        painter.end()

    def mouseMoveEvent(self, e):
        x=e.x()
        y=e.y()
        if self.tpoint is not None:
            px=self.tpoint[0]
            py=self.tpoint[1]
            if x<px:
                x, px=px, x
            if y<py:
                y, py=py, y
            self.nextbox=[px, py, x-px, y-py]
            self.update()

    def mousePressEvent(self, e):
        x=e.x()
        y=e.y()
        if self.tpoint is None:
            self.tpoint=[x, y]
            self.setMouseTracking(True)
        else:
            self.setMouseTracking(False)
            px=self.tpoint[0]
            py=self.tpoint[1]
            if x<px:
                x, px=px, x
            if y<py:
                y, py=py, y
            self.boxes.append([px, py, x-px, y-py])
            self.boxcolors.append(self.defaultBoxColor)
            self.nextbox=None
            self.tpoint=None
        self.update()

    def clear(self):
        self.boxcolors=[]
        self.boxes=[]
        self.nextbox=None
        self.tpoint=None
        self.update()

    def cancelBox(self):
        self.setMouseTracking(False)
        self.nextbox=None
        self.tpoint=None
        self.update()

    def addBox(self, box, color=None):
        self.boxes.append(box)
        if color==None:
            self.boxcolors.append(self.defaultBoxColor)
        else:
            self.boxcolors.append(color)
        self.update()

    def deleteBox(self, idx):
        if idx<len(self.boxes) and idx>-1:
            del self.boxes[idx]
            del self.boxcolors[idx]
            self.update()

    def setColor(self, idx, color=None):
        if idx<len(self.boxcolors) and idx>-1:
            if color is None:
                self.boxcolors[idx]=self.defaultBoxColor
            else:
                self.boxcolors[idx]=color
            self.update()

    def n_boxes(self):
        return len(self.boxes)

if __name__=="__main__":
           
    class MainWindow(QMainWindow):
        def __init__(self, filename, *args, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
            self.image_label=bboxCanvas(499, 480)
            self.image_label.setPixmap(QPixmap(filename))
    
            self.activebox=-1
    
            clearbtn=QPushButton("clear all")
            lcyclebtn=QPushButton("<<")
            rcyclebtn=QPushButton(">>")
            rembtn=QPushButton("clear active")
            sublayout=QHBoxLayout()
            sublayout.addWidget(lcyclebtn)
            sublayout.addWidget(rcyclebtn)
    
            clearbtn.clicked.connect(self.image_label.clear)
            lcyclebtn.clicked.connect(self.boxCycleDown)
            rcyclebtn.clicked.connect(self.boxCycleUp)
            rembtn.clicked.connect(self.remActiveBox)
    
            layout=QVBoxLayout()
            #layout.addWidget(QLabel("bounding box widget"))
            layout.addWidget(self.image_label)
            layout.addWidget(clearbtn)
            layout.addLayout(sublayout)
            layout.addWidget(rembtn)
    
            widget=QWidget()
            widget.setLayout(layout)
    
            self.setCentralWidget(widget)
    
        def remActiveBox(self):
            if self.activebox!=-1:
                self.image_label.deleteBox(self.activebox)
                self.activebox=-1
    
        def boxCycleUp(self):
            if self.activebox!=-1:
                self.image_label.setColor(self.activebox)
            self.activebox=self.activebox+1
            if self.activebox==self.image_label.n_boxes():
                self.activebox=-1
            else:
                self.image_label.setColor(self.activebox, "green")
    
        def boxCycleDown(self):
            if self.activebox!=-1:
                self.image_label.setColor(self.activebox)
            self.activebox=self.activebox-1
            if self.activebox==-2:
                self.activebox=self.image_label.n_boxes()-1
            if self.activebox!=-1:
                self.image_label.setColor(self.activebox, "green")



    app=QApplication(sys.argv)

    window=MainWindow(sys.argv[1])
    window.show()
    app.exec_()


