#!/usr/bin/env python3.10
'''
This uses a CAN link layer to check response to an AME frame

Usage:
python3.10 check_fr20_ame.py

The -h option will display a full list of options.
'''

import sys

from openlcb.nodeid import NodeID
from openlcb.canbus.canframe import CanFrame
from openlcb.canbus.controlframe import ControlFrame
from queue import Empty

import olcbchecker.framelayer

def getFrame(timeout=0.3) :
    return olcbchecker.framelayer.readQueue.get(True, timeout)

def purgeFrames(timeout=0.3):
    while True :
        try :
            received = getFrame(timeout) # timeout if no entries
        except Empty:
             break

def check():
    # set up the infrastructure

    trace = olcbchecker.framelayer.trace # just to be shorter
    ownnodeid = olcbchecker.framelayer.configure.ownnodeid
    targetnodeid = olcbchecker.framelayer.configure.targetnodeid

    timeout = 0.3
    
    purgeFrames()

    ###############################
    # checking sequence starts here
    ###############################

    # send the global AME frame to start the exchange
    frame = CanFrame(ControlFrame.AME.value, 0x001)  # bogus alias
    olcbchecker.framelayer.sendCanFrame(frame)
        
    try :
        # loop for an AMD from DBC or at least not from us
        while True :
            # check for AMD frame
            waitFor = "waiting for initial AMD frame after global AME"
            frame = getFrame(1.0)
            if (frame.header & 0xFF_FFF_000) != 0x10_701_000 :
                print ("Failure - frame was not AMD frame in first part")
                return 3
        
            # check it carries a node ID
            if len(frame.data) < 6 :
                print ("Failure - first part AMD frame did not carry node ID")
                return 3
        
            if targetnodeid is None :
                # we'll take the first one not from us
                if NodeID(frame.data) != NodeID(ownnodeid) :
                    break
            else :  # here we have a node ID to match
                if NodeID(frame.data) == NodeID(targetnodeid) :
                    break
            
            # loop to try again


        purgeFrames()
        
        # get that node ID, create and send an AMD using it
        frame = CanFrame(ControlFrame.AME.value, 0x001, frame.data)  # bogus alias
        olcbchecker.framelayer.sendCanFrame(frame)

        # check for AMD frame
        waitFor = "waiting for AMD frame after AME with address "+str(NodeID(frame.data))
        frame = getFrame(1.0)
        if (frame.header & 0xFF_FFF_000) != 0x10_701_000 :
            print ("Failure - frame was not AMD frame in second part")
            return 3
        
        # check it carries a node ID
        if len(frame.data) < 6 :
            print ("Failure - second AMD frame did not carry node ID")
            return 3
        
        
    except Empty:
        print ("Failure - no frame received while "+waitFor)
        return 3

    if trace >= 10 : print("Passed")
    return 0
 
if __name__ == "__main__":
    sys.exit(check())
    
