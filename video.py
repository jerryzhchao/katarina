#!/usr/bin/python
"""
  Utility for extraction of video stream from navdata log
  usage:
       ./video.py <input navdata log> <output video file> [<output frames directory>]
"""
import sys
import struct
import os
from navdata import cutPacket,videoAckRequired

class VideoFrames:
    def __init__( self, onlyIFrames=False, verbose=True ):
        self.onlyIFrames = onlyIFrames
        self.verbose = verbose
        self.currentFrameNumber = None
        self.parts = None
        self.frames = []

    def append( self, packet ):
        "append video packet with piece of frame"
        assert videoAckRequired( packet )
        frameNumber, frameFlags, fragmentNumber, fragmentsPerFrame = struct.unpack("<HBBB", packet[7:12])
        data = packet[12:]
        if frameNumber != self.currentFrameNumber:
            if self.currentFrameNumber is not None and self.parts is not None:
                s = ""
                for i,d in enumerate(self.parts):
                    if d is None:
                        if self.verbose:
                            print (self.currentFrameNumber, i, len(self.parts))
                        continue
                    s += d
                self.frames.append( s )
            if self.verbose:
                print "processing", frameNumber
            self.currentFrameNumber = frameNumber
            if self.onlyIFrames and frameFlags != 1:
                self.parts = None
            else:
                self.parts = [None]*fragmentsPerFrame
        if not self.onlyIFrames or frameFlags == 1:
            if self.parts[ fragmentNumber ] is not None:
                if self.verbose:
                    print "duplicity", (frameNumber, fragmentNumber)
            self.parts[ fragmentNumber ] = data

    def getFrame( self ):
        if len(self.frames) == 0:
            return None
        frame = self.frames[0]
        self.frames = self.frames[1:]
        return frame



def navdata2video( inputFile, outputFile, outDir = ".", dumpIndividualFrames=False, startIndex=0 ):
    data = open(inputFile, "rb").read()
    out = open(outputFile, "wb")
    vf = VideoFrames()
    frameIndex = startIndex
    while len(data) > 0:
        packet, data = cutPacket( data )
        if videoAckRequired( packet ):
            vf.append( packet )
        frame = vf.getFrame()
        if frame:
            if dumpIndividualFrames:
                fout = open(outDir+os.sep+"frame%04d.bin" % frameIndex, "wb")
                fout.write(frame)
                fout.close()                    
                frameIndex += 1
            out.write(frame)
    out.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print __doc__
        sys.exit(2)
    if len(sys.argv) == 3:
        navdata2video( sys.argv[1], sys.argv[2] )
    else:
        outDir = sys.argv[3]
        startIndex = len(os.listdir( outDir ))
        navdata2video( sys.argv[1], sys.argv[2], outDir=outDir, dumpIndividualFrames=True, startIndex=startIndex )

# vim: expandtab sw=4 ts=4 

