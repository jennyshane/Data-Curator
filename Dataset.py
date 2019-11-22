import os 
import gc
import sys
import glob
import struct
import time
import concurrent.futures
import numpy as np
import scipy.misc

magic_word=[1, 9, 8, 3]

image_size=424*240*3

class DataReadError(Exception):
    def __init__(self, message, culprit=''):
        self.message=message #the error message
        self.culprit=culprit #the file or directory causing the error

class Dataset(object):

    def __init__(self, file_directory):
        self.executor=concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.data_files=[]  #list of {filename, num_frames}
        self.directories=[] #list of source directories
        if type(file_directory)==list:
            for s_dir in sorted(file_directory):
                self.parse_directory(s_dir)
        else:
            self.parse_directory(file_directory)

        self.total_frames=0
        if self.data_files==[]:
            raise DataReadError("no data files found")
        else:
            for f in self.data_files:
                self.total_frames=self.total_frames+f["length"]
        self.current_file_idx=0 
        self.current_frame_idx=0
        self.n_files=len(self.data_files)
        print(self.n_files)
        self.load_file(0)
        self.load_file(1)

    def load_internal(self, index):
        with open(self.data_files[index]["filename"], 'rb') as f_handle:
            frame_index=0
            while True:
                chunk=f_handle.read(12)
                if chunk:
                    *word, STR, THR=struct.unpack('4Bii', chunk)
                    if word!=magic_word:
                        raise DataReadError("unexpected header word in file ", im_file)
                        break
                    else:
                        self.data_files[index]["data"][frame_index]={"STR":STR, "THR":THR, "image":None}
                        self.data_files[index]["data"][frame_index]["image"]=f_handle.read(image_size)
                        frame_index=frame_index+1
                else:
                    f_handle.close()
                    break
            return True 

 
    def load_file(self, index):
        if self.data_files[index]["isLoaded"] is not None and self.data_files[index]["isLoaded"].result():
            return
        else:
            self.data_files[index]["isLoaded"]=self.executor.submit(self.load_internal, index)

    def unload_file(self, index):
        if self.data_files[index]["isLoaded"]==None:
            return
        else:
            if self.data_files[index]["isLoaded"].result()!=True:
                self.data_files[index]["isLoaded"].cancel()
                if self.data_files[index]["isLoaded"].cancelled():
                    self.data_files[index]["isLoaded"].result()

            self.data_files[index]["data"]=[None]*self.data_files[index]["length"]
            gc.collect()
            self.data_files[index]["isLoaded"]=None

    def get_current_frame(self):
        if self.data_files[self.current_file_idx]["isLoaded"].result():
            return self.data_files[self.current_file_idx]["data"][self.current_frame_idx]["image"]

    def get_current_stats(self):
        if self.data_files[self.current_file_idx]["isLoaded"].result():
            return (self.data_files[self.current_file_idx]["data"][self.current_frame_idx]["STR"], 
                    self.data_files[self.current_file_idx]["data"][self.current_frame_idx]["THR"])

    def get_indices(self):
        return (self.current_file_idx, self.current_frame_idx)

    def get_files(self):
        file_list=[]
        for f in self.data_files:
            file_list.append(f["filename"])
        return file_list
           
    def get_current_filename(self):
        return self.data_files[self.current_file_idx]["filename"]

    def isFirst(self):
        if self.current_file_idx==0 and self.current_frame_idx==0:
            return True
        else:
            return False

    def isLast(self):
        if self.current_file_idx==self.n_files-1 and self.current_frame_idx==self.data_files[self.n_files-1]["length"]-1:
            return True
        else:
            return False

    def start(self):
        self.current_file_idx=0 
        self.current_frame_idx=0
        self.load_file(0)
        self.load_file(1)
        for i in range(2, self.n_files):
            self.unload_file(i)

    def end(self):
        self.current_file_idx=self.n_files-1
        self.current_frame_idx=self.data_files[self.current_file_idx]["length"]-1
        self.load_file(self.n_files-1)
        self.load_file(self.n_files-2)
        for i in range(0, self.n_files-2):
            self.unload_file(i)

    def goto_frame(self, idx):
        if idx<0 or idx>self.data_files[self.current_file_idx]["length"]-1:
            raise DataReadError("frame index out of range", str(idx))
        self.current_frame_idx=idx

    def next(self):
        if self.isLast():
            return False 
        else:
            self.current_frame_idx=self.current_frame_idx+1
            if self.current_frame_idx==self.data_files[self.current_file_idx]["length"]:
                self.current_file_idx=self.current_file_idx+1
                self.current_frame_idx=0
                if self.current_file_idx!=self.n_files-1:
                    self.load_file(self.current_file_idx+1)
                if self.current_file_idx-3>=0:
                    self.unload_file(self.current_file_idx-3)
            return True

    def prev(self):
        if self.isFirst():
            return False
        else:
            self.current_frame_idx=self.current_frame_idx-1
            if self.current_frame_idx==-1:
                self.current_file_idx=self.current_file_idx-1
                self.current_frame_idx=self.data_files[self.current_file_idx]["length"]-1
                if self.current_file_idx!=0:
                    self.load_file(self.current_file_idx-1)
                if self.current_file_idx+3<self.n_files:
                    self.unload_file(self.current_file_idx+3)
            return True

    def goto_file(self, idx):
        if idx<0 or idx>self.n_files-1:
            raise DataReadError("file index out of range", str(idx))
        if idx==0:
            self.start()
        elif idx==self.n_files-1:
            self.end()
        else:
            for i in range(0, idx-1):
                self.unload_file(i)
            for i in range(idx+2, self.n_files-1):
                self.unload_file(i)
            for i in range(idx-1, idx+2):
                self.load_file(i)
        self.current_file_idx=idx
        self.current_frame_idx=0


    def parse_directory(self, directory):
        if not os.path.isdir(directory):
            raise DataReadError("Unable to find directory", directory)
        if directory in self.directories:
            return
        self.directories.append(directory)
        image_files=glob.glob(os.path.join(directory, "data*"))
        files=[]
        for im_file in sorted(image_files):
            f_handle=open(im_file, 'rb')
            num_images=0
            while True:
                chunk=f_handle.read(12)
                if chunk:
                    *word, STR, THR=struct.unpack('4Bii', chunk)
                    if word!=magic_word:
                        raise DataReadError("unexpected header word in file ", im_file)
                        break
                    else:
                        f_handle.seek(image_size, 1)
                        num_images=num_images+1
                else:
                    f_handle.close()
                    break
            if num_images>0:
                self.data_files.append({"filename": im_file, "length": num_images, "isLoaded":None, "data":[None]*num_images})

if __name__=="__main__":
    if len(sys.argv)<2:
        print("needs at least one directory as argument")
    else:
        try:
            data=Dataset(sys.argv[1:])
            print(data.get_files())
        except DataReadError as err:
            print("DataReadError: {0} -- {1}".format(err.message, err.culprit))
        print(data.isFirst())
        while data.next():
            time.sleep(.0001)
        print(data.get_indices())
        while data.prev():
            time.sleep(.0001)
        print(data.get_indices())
