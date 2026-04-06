"""
robot_controller.py
--------------------
Differential-drive controller for the Solar Agricultural Robot.

Subscribed Topics
  /cmd_vel  (geometry_msgs/Twist)  – velocity commands

Published Topics
  /wheel_speeds  (std_msgs/Float32MultiArray)  – [FL, FR, RL, RR] rad/s
  /robot_status  (std_msgs/String)             – human-readable status string
  /odom          (nav_msgs/Odometry)           – dead-reckoning odometry
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray, String
from tf2_ros import TransformBroadcaster


class RobotController(Node):
    """4-wheel differential-drive controller with dead-reckoning odometry."""

    # Robot physical parameters
    WHEEL_RADIUS  = 0.10   # m
    WHEEL_BASE    = 0.56   # m  (track width centre-to-centre)
    MAX_SPEED     = 1.5    # m/s  (linear)
    MAX_OMEGA     = 2.0    # rad/s (angular)
    CTRL_PERIOD   = 0.05   # s  → 20 Hz

    def __init__(self):
        super().__init__('robot_controller')

        # --- declare & read parameters ---
        self.declare_parameter('wheel_radius', self.WHEEL_RADIUS)
        self.declare_parameter('wheel_base',   self.WHEEL_BASE)
        self.declare_parameter('max_speed',    self.MAX_SPEED)

        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_base   = self.get_parameter('wheel_base').value
        self.max_speed    = self.get_parameter('max_speed').value

        # --- internal state ---
        self.cmd_vel   = Twist()
        self.x = self.y = self.yaw = 0.0
        self.last_time = self.get_clock().now()

        # --- QoS ---
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )

        # --- subscribers ---
        self.create_subscription(Twist, '/cmd_vel', self._cmd_vel_cb, 10)

        # --- publishers ---
        self.wheel_pub  = self.create_publisher(Float32MultiArray, '/wheel_speeds', 10)
        self.status_pub = self.create_publisher(String, '/robot_status', 10)
        self.odom_pub   = self.create_publisher(Odometry, '/odom', sensor_qos)
        self.tf_broadcaster = TransformBroadcaster(self)

        # --- control timer ---
        self.create_timer(self.CTRL_PERIOD, self._control_loop)

        self.get_logger().info('🤖 RobotController started — wheel_radius=%.3f m, wheel_base=%.3f m' %
                               (self.wheel_radius, self.wheel_base))

    # ------------------------------------------------------------------ #
    def _cmd_vel_cb(self, msg: Twist):
        # Clamp incoming velocity
        v = max(-self.max_speed, min(self.max_speed, msg.linear.x))
        w = max(-self.MAX_OMEGA, min(self.MAX_OMEGA, msg.angular.z))
        self.cmd_vel.linear.x  = v
        self.cmd_vel.angular.z = w

    # ------------------------------------------------------------------ #
    def _control_loop(self):
        now   = self.get_clock().now()
        dt    = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now

        v = self.cmd_vel.linear.x
        w = self.cmd_vel.angular.z

        # Wheel angular speeds (rad/s)
        v_left  = (v - w * self.wheel_base / 2.0) / self.wheel_radius
        v_right = (v + w * self.wheel_base / 2.0) / self.wheel_radius

        # Publish wheel speeds [FL, FR, RL, RR]
        wm = Float32MultiArray()
        wm.data = [v_left, v_right, v_left, v_right]
        self.wheel_pub.publish(wm)

        # Dead-reckoning odometry
        delta_x   = v * math.cos(self.yaw) * dt
        delta_y   = v * math.sin(self.yaw) * dt
        delta_yaw = w * dt
        self.x   += delta_x
        self.y   += delta_y
        self.yaw += delta_yaw

        # Publish TF
        tf_msg = TransformStamped()
        tf_msg.header.stamp    = now.to_msg()
        tf_msg.header.frame_id = 'odom'
        tf_msg.child_frame_id  = 'base_footprint'
        tf_msg.transform.translation.x = self.x
        tf_msg.transform.translation.y = self.y
        tf_msg.transform.translation.z = 0.0
        qz = math.sin(self.yaw / 2.0)
        qw = math.cos(self.yaw / 2.0)
        tf_msg.transform.rotation.z = qz
        tf_msg.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(tf_msg)

        # Publish Odometry
        odom = Odometry()
        odom.header.stamp            = now.to_msg()
        odom.header.frame_id         = 'odom'
        odom.child_frame_id          = 'base_footprint'
        odom.pose.pose.position.x    = self.x
        odom.pose.pose.position.y    = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x    = v
        odom.twist.twist.angular.z   = w
        self.odom_pub.publish(odom)

        # Publish human-readable status
        mode = 'MOVING' if abs(v) > 0.01 or abs(w) > 0.01 else 'IDLE'
        status = (f'[{mode}] v={v:.2f} m/s  ω={w:.2f} rad/s  '
                  f'pos=({self.x:.2f}, {self.y:.2f})  yaw={math.degrees(self.yaw):.1f}°')
        self.status_pub.publish(String(data=status))


def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down RobotController...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
