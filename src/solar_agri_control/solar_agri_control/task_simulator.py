"""
task_simulator.py
------------------
A kinematic task simulator for the Solar Agricultural Robot.
- Generates a virtual field of crops (green) and weeds (red) via RViz MarkerArray.
- Drives the robot in a lawnmower pattern across the field via /cmd_vel.
"""

import math
import random
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Point
from nav_msgs.msg import Odometry
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA


class TaskSimulator(Node):
    def __init__(self):
        super().__init__('task_simulator')

        # Control params
        self.row_length = 5.0  # meters
        self.num_rows = 5
        self.row_spacing = 1.0  # meters
        self.linear_speed = 0.5
        self.angular_speed = 0.5

        # State machine
        self.state = 'FORWARD'
        self.current_row = 0
        self.start_x = 0.0
        self.start_y = 0.0
        self.start_yaw = 0.0
        self.target_yaw = 0.0

        # Current Odometry
        self.has_odom = False
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        # ROS interfaces
        from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_markers = self.create_publisher(MarkerArray, '/field_markers', 1)
        self.sub_odom = self.create_subscription(Odometry, '/odom', self.odom_cb, sensor_qos)

        # Timers
        self.create_timer(0.1, self.control_loop)
        self.create_timer(2.0, self.publish_markers)

        # Generate field map
        self.marker_array = self.generate_field_markers()

        self.get_logger().info('Task Simulator started for ' + str(self.num_rows) + ' rows.')

    def odom_cb(self, msg: Odometry):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        # yaw from quaternion
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)

        if not self.has_odom:
            self.has_odom = True
            self.start_x = self.x
            self.start_y = self.y
            self.start_yaw = self.yaw

    def generate_field_markers(self) -> MarkerArray:
        ma = MarkerArray()
        id_counter = 0

        for row in range(self.num_rows):
            y_pos = row * self.row_spacing
            
            # Plant every 0.5 meters
            for i in range(int(self.row_length / 0.5) + 1):
                x_pos = i * 0.5
                
                # Mostly crops (green), occasional weed (red)
                is_weed = random.random() < 0.15

                m = Marker()
                m.header.frame_id = 'odom'
                m.ns = 'field'
                m.id = id_counter
                id_counter += 1
                m.type = Marker.CYLINDER if not is_weed else Marker.SPHERE
                m.action = Marker.ADD
                
                m.pose.position.x = x_pos
                m.pose.position.y = y_pos
                m.pose.position.z = 0.1
                m.pose.orientation.w = 1.0
                
                m.scale.x = 0.15
                m.scale.y = 0.15
                m.scale.z = 0.2 if not is_weed else 0.15
                
                c = ColorRGBA()
                c.a = 1.0
                if not is_weed:
                    c.r, c.g, c.b = 0.1, 0.8, 0.2  # Green crop
                else:
                    c.r, c.g, c.b = 0.9, 0.1, 0.1  # Red weed
                m.color = c
                
                ma.markers.append(m)

        return ma

    def publish_markers(self):
        # Update timestamp and publish
        for m in self.marker_array.markers:
            m.header.stamp = self.get_clock().now().to_msg()
        self.pub_markers.publish(self.marker_array)

    def control_loop(self):
        if not self.has_odom:
            return

        cmd = Twist()
        
        if self.state == 'FORWARD':
            # Drive straight until row length
            dist = math.hypot(self.x - self.start_x, self.y - self.start_y)
            if dist < self.row_length:
                cmd.linear.x = self.linear_speed
            else:
                self.state = 'TURN_1'
                self.start_x = self.x
                self.start_y = self.y
                self.start_yaw = self.yaw
                
                # Alternate turn direction
                turn_dir = 1.0 if self.current_row % 2 == 0 else -1.0
                self.target_yaw = self.start_yaw + turn_dir * (math.pi / 2.0)
                cmd.linear.x = 0.0

        elif self.state == 'TURN_1':
            # Turn 90 degrees
            diff = self.normalize_angle(self.target_yaw - self.yaw)
            if abs(diff) > 0.05:
                cmd.angular.z = math.copysign(self.angular_speed, diff)
            else:
                self.state = 'SHIFT'
                self.start_x = self.x
                self.start_y = self.y
                self.start_yaw = self.yaw
                cmd.angular.z = 0.0

        elif self.state == 'SHIFT':
            # Drive to the next row (row_spacing)
            dist = math.hypot(self.x - self.start_x, self.y - self.start_y)
            if dist < self.row_spacing:
                cmd.linear.x = self.linear_speed
            else:
                self.state = 'TURN_2'
                self.start_x = self.x
                self.start_y = self.y
                self.start_yaw = self.yaw
                
                turn_dir = 1.0 if self.current_row % 2 == 0 else -1.0
                self.target_yaw = self.start_yaw + turn_dir * (math.pi / 2.0)
                cmd.linear.x = 0.0

        elif self.state == 'TURN_2':
            # Turn another 90 degrees to face back down the field
            diff = self.normalize_angle(self.target_yaw - self.yaw)
            if abs(diff) > 0.05:
                cmd.angular.z = math.copysign(self.angular_speed, diff)
            else:
                if self.current_row < self.num_rows - 1:
                    self.current_row += 1
                    self.state = 'FORWARD'
                    self.start_x = self.x
                    self.start_y = self.y
                    self.start_yaw = self.yaw
                else:
                    self.state = 'DONE'
                cmd.angular.z = 0.0

        elif self.state == 'DONE':
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

        self.pub_cmd_vel.publish(cmd)

    def normalize_angle(self, angle: float) -> float:
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle


def main(args=None):
    rclpy.init(args=args)
    node = TaskSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
