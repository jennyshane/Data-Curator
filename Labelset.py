import json

class LabelSet(object):

    def __init__(self, filenames, frameLabels=[], bboxLabels=[]):
        self.frame_labels=frameLabels
        self.bbox_labels=bboxLabels
        self.nfiles=len(filenames)
        self.filenames=filenames
        self.label_data=[]
        for f in filenames:
            self.label_data.append({})
        

    def addFrameLabel(self, label):
        if type(label)==list:
            self.frame_labels=self.frame_labels+label
        else:
            self.frame_labels.append(label)

    def addBboxLabel(self, label):
        if type(label)==list:
            self.bbox_labels=self.bbox_labels+label
        else:
            self.bbox_labels.append(label)

    def getLabelNames(self):
        return self.frame_labels, self.bbox_labels

    def markFrameLabel(self, fileno, frame, label):
        if label not in self.frame_labels:
            self.frame_labels.append(label)
        if frame not in self.label_data[fileno]:
            self.label_data[fileno][frame]={"flabels":[label], "blabels":[]}
        else:
            if label not in self.label_data[fileno][frame]["flabels"]:
                self.label_data[fileno][frame]["flabels"].append(label)

    def markBboxLabel(self, fileno, frame, label, box):
        if label not in self.bbox_labels:
            self.bbox_labels.append(label)
        if frame not in self.label_data[fileno]:
            self.label_data[fileno][frame]={"flabels":[], "blabels":[(label, box)]}
        else:
            self.label_data[fileno][frame]["blabels"].append((label, box))

    def remove(self, fileno, frame, label, num=0):
        if label in self.frame_labels:
            if frame in self.label_data[fileno] and label in self.label_data[fileno][frame]["flabels"]:
                self.label_data[fileno][frame]["flabels"].remove(label)
                return True
        elif label in self.bbox_labels:
            if frame in self.label_data[fileno]:
                count=0
                for idx, pair in enumerate(self.label_data[fileno][frame]["blabels"]):
                    blabel, box=pair
                    if blabel==label:
                        if count==num:
                            del self.label_data[fileno][frame]["blabels"][idx]
                            return True
                        else:
                            count=count+1
        return False

    def frameQuery(self, fileno, frame, label):
        if label in self.label_data[fileno][frame]["flabels"]:
            return True
        else:
            return False

    def getLabels(self, fileno, frame):
        if frame in self.label_data[fileno]:
            return self.label_data[fileno][frame]["flabels"], self.label_data[fileno][frame]["blabels"]

    def saveLabels(self):
        for fileno, f in enumerate(self.filenames):
            idx=f.find('.')
            if idx!=-1:
                prefix=f[0:idx]
            else:
                prefix=f

            labelfile=prefix+".labels"
            file_labels={}
            for i in self.label_data[fileno]:
                for flabel in self.label_data[fileno][i]["flabels"]:
                    if flabel not in file_labels:
                        file_labels[flabel]=[i]
                    else:
                        file_labels[flabel].append(i)
                for blabel, box in self.label_data[fileno][i]["blabels"]:
                    if blabel not in file_labels:
                        file_labels[blabel]=[(i, box)]
                    else:
                        file_labels[blabel].append((i, box))
            if file_labels!={}:
                f_obj=open(labelfile, "w")
                json.dump(file_labels, f_obj)
                f_obj.close()


if __name__=='__main__':
    testfiles=["vid01", "vid03", "vid04", "vid05", "vid06", "vid07", "vid08", "vid09"]
    frame_labels=["a", "b", "c"]
    bbox_labels=["aa", "bb", "cc"]
    labels=LabelSet(testfiles, frame_labels, bbox_labels)
    for i in range(0, 10):
        labels.markFrameLabel(0, i, "a")
        labels.markFrameLabel(1, i, "a")
        labels.markFrameLabel(2, i, "a")
        labels.markFrameLabel(3, i, "b")
        labels.markFrameLabel(3, i, "c")

    for i in range(0, 5):
        labels.markFrameLabel(3, i*2, "a")
        labels.markFrameLabel(6, i*2, "a")
        labels.markFrameLabel(6, i*2, "b")
        labels.markFrameLabel(6, i*2, "c")

    for i in range(0, 3):
        labels.markBboxLabel(0, i, "aa", (0, 0, 10, 10))
        labels.markBboxLabel(0, i, "bb", (0, 0, 10, 10))

    for i in range(6, 9):
        labels.markBboxLabel(4, i, "cc", (4, 5, 10, 10))
        labels.markBboxLabel(3, i, "bb", (3, 2, 10, 10))

    labels.addFrameLabel("test")
    labels.markFrameLabel(3, 8, "sample")
    print(labels.getLabelNames())
    print(labels.getLabels(3, 8))
    labels.saveLabels()
