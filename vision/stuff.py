import pygame, sys, random
from opencv import cv, highgui
from features import Features
from preprocess import Preprocessor
from segmentation import Segmenter

# goalDim = (60, 18)
# robotDim = (20,18)
# pitchDim = (244, 122)

g_capture = None
g_slider_pos = 0

def on_trackbar(pos):
    highgui.cvSetCaptureProperty(capture, highgui.CV_CAP_PROP_POS_FRAMES, pos)

winMap = {}

def updateWin(name, frame):
    if not winMap.has_key(name):
        winMap[name] = \
        {'window' : highgui.cvNamedWindow(name, highgui.CV_WINDOW_AUTOSIZE)}
        print winMap[name]

    highgui.cvShowImage(name, frame)

def updateTrackbar(name, window_name):
    if not winMap.has_key(name):
        raise NameError, "No such window:", window_name
    elif not WinMap[name].has_key('trackbar'):
        WinMap[name] = \
        {'trackbar' : highgui.cvCreateTrackbar(
                name, window_name, g_slider_pos, frames, on_trackbar)}


Xbgr=[35,10,20]
def setB(x): Xbgr[0]=x
def setG(x): Xbgr[1]=x
def setR(x): Xbgr[2]=x

def setFA(x): Features.A=x
def setFB(x): Features.B=x

def bar():
    # create windows
    # highgui.cvNamedWindow('Raw', highgui.CV_WINDOW_AUTOSIZE)
    # highgui.cvNamedWindow('Adaptive threshold', highgui.CV_WINDOW_AUTOSIZE)
    # highgui.cvNamedWindow('Threshold', highgui.CV_WINDOW_AUTOSIZE)

    # create capture device
    #g_capture = cvCreateCameraCapture(-1)
    g_capture = highgui.cvCreateFileCapture(sys.argv[-1])
    highgui.cvSetCaptureProperty(g_capture,
                                 highgui.CV_CAP_PROP_FRAME_WIDTH, 768)
    highgui.cvSetCaptureProperty(g_capture,
                                 highgui.CV_CAP_PROP_FRAME_HEIGHT, 512)

    frames = highgui.cvGetCaptureProperty(g_capture,
                                          highgui.CV_CAP_PROP_FRAME_COUNT)
    # print FPS
    print 'FPS:', \
        highgui.cvGetCaptureProperty(g_capture, highgui.CV_CAP_PROP_FPS)

    if not g_capture:
        print "Error opening g_capture device"
        sys.exit(1)

    size = cv.cvSize(768, 576)
    num_chans = 3
    chsv = [ cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 1)
             for _ in range(num_chans) ]
    cbgr = [ cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 1)
             for _ in range(num_chans) ]

    gray = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 1)
    Iavg = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 3)
    IGD = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 3)
    bg = highgui.cvLoadImage('background.png')
    # Roughly keeps the lightness constant across the pitch.
    # i.e. the robot won't suddenly become much lighter, etc.
    #cv.cvConvertScale(bg2,bg2,0.6,0)
    ground_mask = highgui.cvLoadImage('ground_mask.png')
    #bgSidesMask = highgui.cvLoadImage('bg_sides_mask.png')
    pitch_mask = highgui.cvLoadImage('pitch_mask.png')

    # bg2 = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 3)
    # cv.cvZero(bg2)
    #cv.cvAnd(bg, ground_mask, bg)
    #cv.cvAnd(bg, pitch_mask, bg2)
    #cv.cvSub(bg, bg2, bg2)

    # updateWin("X", bg)
    # highgui.cvCreateTrackbar("R", 'X', Xbgr[2], 255, setR)
    # highgui.cvCreateTrackbar("G", 'X', Xbgr[1], 255, setG)
    # highgui.cvCreateTrackbar("B", 'X', Xbgr[0], 255, setB)

    # updateWin("Contour", bg)
    # highgui.cvCreateTrackbar("A", 'Contour', Features.A, 30, setFA)
    # highgui.cvCreateTrackbar("B", 'Contour', Features.B, 30, setFB)

    Imask = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 3)
    pIat = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 1)
    Iopen = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 1)
    Iclose = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 1)

    pause=False
    frame=None
    n=0
    while True:
        # capture the current frame
        if not pause:
            #Use something like this for, say, averaging a pic
            #frame = highgui.cvLoadImage('train/%08d.png' % n)

            frame = highgui.cvQueryFrame(g_capture)
            if frame is None: break
            cv.cvAnd(frame, pitch_mask, frame)

        #size = cv.cvGetSize(frame)

        ########################################
        cv.cvCvtColor(frame, gray, cv.CV_BGR2GRAY)

        ########################################
        # Ignore potentially distracting things outside the pitch
        # updateWin('BG', bg)
        # updateWin('BG2', bg2)

        ########################################
        #TODO: how to make this work with python?
        #cv.cvSetImageROI(frame, cv.cvRect(0,50,768,450))

        ########################################
        #center = cv.cvPoint(random.randrange(1,768), random.randrange(1,512))
        #cv.cvCircle(frame, center, 15, cv.CV_BGR(300,1,1))

        ########################################
        updateWin('Raw', frame)
        # if frames > 0:
        #     updateTrackbar("Position", "Raw")

        ########################################
        #updateWin('Corrected', Preprocessor.undistort(frame))

        ########################################
        #print [(x.height, x.width) for x in map(cv.cvGetSize, [frame,bg,bg2,Iavg])]
        cv.cvSub(frame, bg, Iavg)
        updateWin('BG del 0', Iavg)
        # cv.cvAbsDiff(Iavg, bg2, Iavg)
        # updateWin('BG del 2', Iavg)
        gray = Features.threshold(Iavg, ('bgr',Xbgr,(255,255,255,)), op=cv.cvOr)
        updateWin('BG del', gray)
        cv.cvCvtColor(gray, IGD, cv.CV_GRAY2BGR)
        cv.cvAnd(IGD, frame, IGD)
        updateWin('X', IGD)
        #print Xbgr

        kernel = cv.cvCreateStructuringElementEx(5, 5,
                                                 0, 0, #X,Y offsets
                                                 cv.CV_SHAPE_RECT)

        # Finds the approximate position of each object with little noise
        # The approximation should later be refined by some method
        cv.cvMorphologyEx(IGD, IGD, None, kernel, cv.CV_MOP_OPEN)
        cv.cvMorphologyEx(IGD, IGD, None, kernel, cv.CV_MOP_CLOSE)

        # It = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 1)
        # cv.cvCvtColor(IGD, It, cv.CV_BGR2GRAY)
        # cv.cvThreshold(It, It, 1, 255, cv.CV_THRESH_BINARY)
        # cv.cvCvtColor(It, IGD, cv.CV_GRAY2BGR)
        # cv.cvAnd(IGD, frame, IGD)

        # cv.cvCvtColor(IGD, gray, cv.CV_BGR2GRAY)
        updateWin('X', gray)
        # Features.find_connected_components(gray)

        # updateWin('Yellow', Features.threshold(Iavg, Features.Tyellow))
        # updateWin('Yellow orig', Features.threshold(frame, Features.Tyellow))
        # updateWin('Ball orig', Features.threshold(frame, Features.Tball))
        # updateWin('Ball BG-', Features.threshold(Iavg, Features.Tball))
        #updateWin('Yellow orig', Features.threshold(frame, Features.Tyellow))

        # o=Segmenter.segment(Features.threshold(frame, Features.Tblue), 'Blue')
        # print o

        ########################################

        # hsv = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 3)
        # cv.cvCvtColor(frame, hsv, cv.CV_BGR2HSV)
        # cv.cvSplit(hsv, chsv[0], chsv[1], chsv[2], None)
        # updateWin('Hue', chsv[0])
        # updateWin('Saturation', chsv[1])
        # updateWin('Value', chsv[2])

        ########################################
        # bgr = cv.cvCloneImage(frame)
        # cv.cvSplit(bgr, cbgr[0], cbgr[1], cbgr[2], None)
        # updateWin('Blue', cbgr[0])
        # updateWin('Green', cbgr[1])
        # updateWin('Red', cbgr[2])

        ########################################
        # N=n-665
        # cv.cvAddWeighted(frame, 1.0/(N+1), Iavg, N/(N+1.0), 0, Iavg)
        # print 1.0/(N+1), N/(N+1.0)
        # updateWin('Average', Iavg)
        # n=n+1

        ########################################
        #It = cv.cvCreateImage(size, cv.IPL_DEPTH_8U, 1)
        #cv.cvThreshold(c[2], It, 200, 100, cv.CV_THRESH_BINARY_INV)
        # updateWin('backplate', Features.threshold(frame, Features.Tbackplate))
        # updateWin('ball', Features.threshold(frame, Features.Tball))
        # updateWin('blue', Features.threshold(frame, Features.Tblue))

        ########################################
        # cv.cvSmooth(IGD, Imask, cv.CV_GAUSSIAN, 11)
        # cv.cvSub(IGD, Imask, Imask)
        # updateWin('Gaussian diff', Imask)

        ########################################
        Tsides = ( 'bgr', (100,  100,  100), (255, 255, 255) )
        # sides = Features.threshold(Iavg, Tsides)
        # updateWin('Sides', sides)
        # cv.cvSmooth(Iavg, IGD, cv.CV_GAUSSIAN, 11)
        # cv.cvSub(Iavg, IGD, IGD)
        #cv.cvAdd(IGD,Imask,IGD)
        #cv.cvCvtColor(IGD, gray, cv.CV_BGR2GRAY)
        # cv.cvAdaptiveThreshold(gray, gray, 255, cv.CV_ADAPTIVE_THRESH_MEAN_C,
        #                        cv.CV_THRESH_BINARY_INV, 9, 9)
        # updateWin('Gaussian diff 2', IGD)

        ########################################
        # cv.cvAdaptiveThreshold(gray, Iat, 255, cv.CV_ADAPTIVE_THRESH_MEAN_C,
        #                        cv.CV_THRESH_BINARY_INV, 5, 5)
        #updateWin("Adaptive thresholding", Iat)

        #Combine GaussDiff with adaptive thresholding and original
        # cv.cvCvtColor(Iat, IGD, cv.CV_GRAY2BGR)
        # cv.cvAddWeighted(frame, 1/8.0, Imask, 2.0, 0, Imask)
        # #cv.cvAddWeighted(Imask, 2/3.0, IGD, 1.0, 0, Imask)
        # updateWin("Combo", Imask)

        ########################################

        # cv.cvCanny(gray, Iat, 0, 9, 3)
        # updateWin("Canny", Iat)

        # kernel = cv.cvCreateStructuringElementEx(3,3,1,1,cv.CV_SHAPE_RECT)
        #cv.cvMorphologyEx(gray, Iopen, None, kernel, cv.CV_MOP_OPEN)

        # highgui.cvShowImage('Raw', frame)
        # cv.cvReleaseImage(gray) # needed?

        # handle events
        k = highgui.cvWaitKey(5)

        # processing depending on the character
        if k == 'p':
            pause=not pause

        if k == 0x1b:
            print 'ESC pressed. Exiting ...'
            break

    #Iavg = cv.cvCreateImage(size, cv.IPL_DEPTH_32S, 3)
    #highgui.cvShowImage('Raw', Iavg)
    highgui.cvSaveImage("avg.png", Iavg)
    highgui.cvDestroyAllWindows()

if __name__ == "__main__":
    bar()
