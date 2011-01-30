from utils import *
import time
from math import *
from robot_estimator import *
from ball_estimator import *

class Robot: pass
class Ball:
    pos=None

class World(object):

    # Lengths are in millimetres
    PitchWidth   = 1215
    PitchLength  = 2240
    ballDiameter = 45
    goalLength   = 585

    max_states   = 5000
    states = []

    vHorizon = 6   # How many past states to use when calculating
                   # velocity
    vWeight  = 0.5 # How much weight to give to the latest 'raw'
                   # velocity vs. the recent past average

    # The entities we are interested in
    entityNames = ('ball', 'blue', 'yellow')

    def __init__(self, ourColour = None):
        self.name = "Real World"
        self.time = time.time()
        self.openLog()

        self.ourColour = ourColour
        assert ourColour in ('blue', 'yellow'), \
            "Legal robot colour is required"

        self.ents = {}
        self.est_ball   = BallEstimator()
        self.est_yellow = RobotEstimator()
        self.est_blue   = RobotEstimator()

    def openLog(self):
        self.log = open('anomalities.txt', 'a')

    def update(self, time, ents):
        self.time = time
        self.ents = ents

        self.pointer = None

        self.est_ball.update( ents['balls'] )
        self.est_yellow.update( [ents['yellow']] )
        self.est_blue.update( [ents['blue']] )

        self.convertMeasurements()
        self.assignSides()
        self.updateStates()

    def __getPos(self, ent):
        x,y = entCenter(ent)
        return np.array((x,y))

    def __getRobot(self, est):
        robot = Robot()
        robot.pos = estimator.getPos()
        robot.velocity = estimator.getVelocity()
        robot.orientation = estimator.getOrientation()
        return robot

    def getSelf(self):
        return self.__getRobot( self.us )
    def getOpponent(self):
        return self.__getRobot( self.them )

    def getBall(self):

        ball = Ball()
        ball.pos =      self.est_ball.getPos()
        ball.velocity = self.est_ball.getVelocity()
        return ball

    def updateStates(self):
        self.ents['time'] = self.time
        self.states.append(self.ents)
        if len(self.states) > self.max_states:
            del self.states[0]

    def assignSides(self):
        if self.ourColour == 'blue':
            self.us   = self.est_blue
            self.them = self.est_yellow
        else:
            self.us   = self.est_yellow
            self.them = self.est_blue

    def convertMeasurements(self):
        "Convert image measures to real-world measures"
        for ent in self.ents:
            pass

class ReversedWorld(World):
    "See us as the other robot - useful if we have two AIs"
    def getSelf(self):
        return super(ReversedWorld, self).getOpponent()
    def getOpponent(self):
        return super(ReversedWorld, self).getSelf()
