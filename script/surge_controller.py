#!/usr/bin/env python
import rospy
from script.pid import PID
from std_msgs.msg import Int16
from std_msgs.msg import Float64
from std_msgs.msg import Empty
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import Twist
import tf
import math

from PI_Controller import*

class SurgeController:

    def __init__(self):

        self.sensor_sub = rospy.Subscriber("distance_sonar", Float64MultiArray, self.sensor_callback)
        self.reset_sub = rospy.Subscriber("controllers/reset", Empty, self.reset_callback)
        self.desired_val_sub = rospy.Subscriber("controller/surge/desired", Float64, self.desired_val_callback)
        self.pub = rospy.Publisher('controller/surge/effort', Float64, queue_size=10)
        
        self.init = False

        self.startup_surge = 0.0

        self.step = 0.02
        self.prev_time = 0

        self.controller = PID()

        self.get_params()
        self.set_controller()

    def set_controller(self):
        self.controller.set_gains(self.kp, self.ki, self.kd)
        self.controller.set_step(self.step)
        
    def desired_val_callback(self, msg):
        self.desired_val = msg.data

    def get_params(self):
        self.kp = rospy.get_param('controller/surge/kp', 0.0)
        self.ki = rospy.get_param('controller/surge/ki', 0.0)
        self.kd = rospy.get_param('controller/surge/kd', 0.0)

    def reset_callback(self, data):
        self.controller.reset_controller()
        self.init = True

    def sensor_callback(self,data):
        pinger_distance = data.data[0]
        pinger_confidence = data.data[1]
        
        # update dt
        curr_time = rospy.Time.now().to_sec()
        dt = curr_time - self.prev_time
        self.prev_time = curr_time

        surge = pinger_distance
        surge_error = self.desired_val - surge

        # Control:
        self.controller.set_step(dt)
        control_effort = self.controller.control(surge_error)  #removed r
        self.pub.publish(Float64(control_effort))

def main(args):
  rospy.init_node('surge_controller_node')
  controller = SurgeController()
  try:
    rospy.spin()
  except KeyboardInterrupt:
    print("Shutting down")
