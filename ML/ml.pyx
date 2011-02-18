import numpy as np
import numpy.random as rnd
import random
from math import *
import sys, time, cPickle, os
import ML_pb2
cimport numpy as np
import logging

LOG = logging.getLogger("ML")
logging.basicConfig(stream = sys.stderr, level=logging.INFO)

StateShape=12
NumFeatures=StateShape-6 + 7
class State(object): pass

dt = 1/25.0

def dist(src, dest):
    return sqrt( sum((src-dest)**2) )

def main():
    state0 = np.array([0,0,0,0,
                       rnd.random()*pi,0,
                       0,0,0,0,
                       0,0,0,0,])

    print cPickle.dumps(enum_actions())
    print "END"
    sys.stdout.flush()

    fitted_value_iteration2(state0, 70)

class Model(object):
    def predict(self, state, action):
        raise NotImplementedError

class RandomModel(Model):
    cov = np.diag([5,5,3,3,0.1, 0.05, 0,0,0,0])
    size = cov.shape[0]
    def predict(self, np.ndarray[np.float64_t, ndim=1] state,
                 np.ndarray[long, ndim=1] action):
        #print state[0,0:2] + state[0,2:4]
        cdef np.ndarray[np.float64_t, ndim=1] new_state
        new_state = np.zeros(StateShape)
        new_state[0:2] = state[0:2] + state[2:4]
        new_state[2:4] = state[2:4] + rnd.randn(2) - 0.5
        new_state[4] = state[4] + state[5]
        new_state[5] = state[5]
        new_state[6:10] = state[10:]
        new_state[10:] = action

        return new_state

class StrategyBridge(Model):
    def predict(self, np.ndarray[np.float64_t, ndim=1] state,
                 np.ndarray[long, ndim=1] action):

        cdef np.ndarray[np.float64_t, ndim=1] new_state
        new_state = np.zeros(StateShape)
        new_state = get_state()
        # new_state[0:2] = state[0:2] + state[2:4] #pos
        # new_state[2:4] = state[2:4] #velocity
        # new_state[4] = state[4] + state[5] #orient
        # new_state[5] = state[5] #delta orient
        # new_state[6:10] = state[10:] #past action
        # new_state[10:] = action #action

        return new_state

RM = RandomModel()
Bridge = StrategyBridge()

def get_next_state(model, state, action):
    return model.predict(state, action)

# + noise
# for noise in rnd.multivariate_normal(np.array([0]*model.size),
#                                      model.cov, num_samples) ]

# def estimate_value_function(params):
#     pT = np.transpose(np.mat(params))
#     def value_function(state):
#         result = np.mat(features(state)) * pT
#         return result[0,0]
#     return value_function

def state_pos(state):
    return state[0:2]

def state_reward(np.ndarray[np.float64_t, ndim=1] state):
    """For movement, we want:

    reward = -1/second for non-goal states
    reward = 1 for goal

    Later, we should optimise for going to target via checkpoint,
    simulating scenarios where our next move was likely towards
    another place/state.

    reward = 2 for checkpoint
    reward = 4 for goal if went through checkpoint, -3 otherwise
    """
    # cdef float reward = float( sys.stdin.readline().strip() )
    # return reward

    D = dist(state_pos(state), goal.pos)
    if dist(state_pos(state), goal.pos) < 10:
        # Spend at most about 0.5 extra seconds correcting our orientation
        state_orient = state[4]
        reward = 100 - 0.5 * abs(goal.orientation - state_orient)/pi
    else:
        reward = -D/100.0

    LOG.info("reward: %.4f", reward)
    return reward

def linear_regression(features, values):
    # name = time.strftime('logs/%Y%m%d-%H%M-%S.regression')
    # h = open(name, 'w')
    # cPickle.dump( [features, values], h)
    # h.close()
    # sys.exit(0)

    LOG.info("linear regression- values:" + str(values))
    #LOG.info("linear regression- features:" + str(features[37]))
    result, residues, rank, sing =  np.linalg.lstsq(features, values)
    LOG.info("linear regression- result:%s residues:%s rank:%s, sing:%s",
             str(result), str(residues), str(rank), str(sing))
    return result

Motors = ('drive1', 'drive2', 'turn1', 'turn2')
Settings = range(-1,2) #2401 total; on/off has 81
def list_actions():
    return [(motor, setting) for motor in Motors for setting in Settings]

def _I(x):
    if x == 0: return [[]]
    return [ [d]+rest for d in Settings for rest in _I(x-1) ]
def enum_actions():
    return map(np.array, _I(4))

def take_action(action):
    s=''
    for param in action:
        s+= "|"+str(param)
    LOG.debug("Taking action: %s", s[1:])
    print s[1:]
    sys.stdout.flush()

inf = 1e1000
epsilon = 1
def choose_action(state, policy_params):
    max_eu = -inf
    #print "PREDICT"
    for a in enum_actions():
        #next = get_next_state(Bridge, state, a)
        eu = state_value(get_next_state(Bridge, state, a), policy_params)
        #LOG.info("EU: %f  A:%s", eu, str(a))
        # LOG.debug("MAX:%f  %s",max_eu, str(eu > max_eu))
        if eu > max_eu:
            best_action = a
            max_eu = eu
    # LOG.debug("Action: " + str(best_action))

    if rnd.random() < epsilon:
        return random.sample(enum_actions(), 1)[0]
    return best_action

def get_state():
    WS = ML_pb2.WorldState()
    LOG.debug("Waiting for line")
    msg = ""
    while True:
        line = sys.stdin.readline()
        if line.strip() != "END":
            msg += line
        else:
            break

    WS.ParseFromString( msg[:-1] )
    # lines = map(float, [ for _ in range(6)])
    # x,y, vx,vy, o,vo = lines
    cdef np.ndarray[np.float64_t, ndim=1] new_state
    new_state = np.zeros(StateShape)
    R = WS.robot; B = WS.ball
    LOG.debug("POS: %d,%d", R.pos_x, R.pos_y)
    new_state[0:2] = R.pos_x, R.pos_y
    new_state[2:4] = R.vel_x, R.vel_y
    new_state[4] = R.angle
    new_state[5] = R.ang_v
    new_state[6] = R.left_angle
    new_state[7] = R.right_angle

    new_state[8:10] = B.pos_x, B.pos_y
    new_state[10:12] = B.vel_x, B.vel_y

    # new_state[0:2] = x,y
    # new_state[2:4] = vx,vy
    # new_state[4] = o
    # new_state[5] = vo
    return new_state

def execute_policy(policy_params, max_time):
    "Call the simulator"
    print 'RESET'
    states = []
    rewards = []
    cdef int t
    for t from 0 <= t < max_time:
        state = get_state()
        action = choose_action(state, policy_params)
        take_action(action)
        states.append( state )
        rewards.append( state_reward(state ) )
        LOG.debug("Policy at t=%d", t)

    #LOG.info("exec_policy" + str(states) + str(rewards))
    return states, rewards

MAX_EU=-1e1000
goal = State()
goal.pos = [0,0]
goal.pos[0] = rnd.randint(60,560)
goal.pos[1] = rnd.randint(80,360)
goal.orientation = 2*pi*rnd.random() - pi

def fitted_value_iteration2(state0, max_time):
    print max_time
    sys.stdout.flush()
    policy_params = np.zeros(NumFeatures)
    N=0
    try:
        while True:
            trial, rewards = execute_policy(policy_params, max_time)
            LOG.info("Policy: "+ str(policy_params) )
            LOG.info("Iteration: %d", N); N+=1
            policy_params = fitted_value_iteration(trial, rewards, policy_params)
    finally:
        name = time.strftime('logs/%Y%m%d-%H%M-%S.policy')
        h = open(name, 'w')
        cPickle.dump(policy_params, h)
        LOG.info("Final policy saved to: %s", name)
        LOG.info("Maximum EU: %.6f", MAX_EU)
        LOG.info("Policy:" + str(policy_params))

def features(np.ndarray[np.float64_t, ndim=1] state):
    x,y = state[0], state[1]
    vx,vy = state[2], state[3]
    o = state[4]
    vo = state[5]
    dx, dy = goal.pos[0]-x, goal.pos[1]-y
    do = atan2(dy, dx)
    Dist2 = dx**2 + dy**2
    cdef np.ndarray[np.float64_t, ndim=1] F
    F = np.array([x,y,vx,vy,o,vo,
                  #w1,w2,d1,d2,o**2,
                  do, do**2, sin(do), cos(do), tan(do), exp(do),
                  Dist2]) #+ state[10:].tolist())
    return F

def state_value(np.ndarray[np.float64_t, ndim=1] state,
                np.ndarray[np.float64_t, ndim=1] policyT):

    cdef np.ndarray[np.float64_t, ndim=1] F = features(state)
    return np.dot(F, policyT)

def fitted_value_iteration(states, rewards, policy_params):
    policyT = np.transpose(policy_params)
    model = Bridge
    inf = 1e1000
    discount = 0.99
    values = []
    actions = enum_actions()
    for i, state in enumerate(states):
        LOG.debug("Fitted value iteration: %d", i)
        values.append(-inf)
        for action in actions:
            next_state = get_next_state(model, state, action)

            q_action = discount * state_value(next_state, policyT)

            if q_action > values[i]:
                values[i] = rewards[i] + q_action

        if values[i] + rewards[i] > MAX_EU:
            LOG.info("REW:"+str(rewards[i]))
            MAX_EU = values[i]

    print "END"
    policy_params = linear_regression( map(features, states), values )
    return policy_params


if __name__ == '__main__':
    #import cProfile
    #cProfile.run('main()')
    main()
