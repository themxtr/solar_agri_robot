#!/usr/bin/env python3
"""
field_navigator.py
------------------
Automatically sends the robot sweeping through the field rows 
using the Nav2 NavigateToPose action server.
Includes a command listener for manual skip/reset.
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import time

class FieldNavigator(Node):
    def __init__(self):
        super().__init__('field_navigator')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Command subscriber for manual skip/reset/start
        self.command_sub = self.create_subscription(String, '/mission/command', self.command_callback, 10)

        # Define the zigzag path through all 4 crop gaps
        self.waypoints = [
            (-1.5, -2.25, 0.0), # Enter Gap 1
            (7.5, -2.25, 0.0),  # End of Gap 1
            (7.5, -0.75, 3.14), # Shift to End of Gap 2
            (-1.5, -0.75, 3.14),# Start of Gap 2
            (-1.5, 0.75, 0.0),  # Shift across to Start of Gap 3
            (7.5, 0.75, 0.0),   # End of Gap 3
            (7.5, 2.25, 3.14),  # Shift to End of Gap 4
            (-1.5, 2.25, 3.14), # Start of Gap 4
            (-2.0, 0.0, 0.0)    # Return to station
        ]
        self.current_wp_idx = 0
        self.transition_timer = None
        self.goal_handle = None

        # Wait a bit before starting to ensure Nav2 costmaps are loaded
        self.get_logger().info("Field Navigator waiting 30s. Send 'start' to /mission/command to start now.")
        self.start_timer = self.create_timer(30.0, self.start_mission)

    def command_callback(self, msg):
        cmd = msg.data.lower().strip()
        self.get_logger().info(f"📩 Received Mission Command: {cmd}")
        
        if cmd == 'start':
            if self.start_timer:
                self.start_timer.cancel()
            self.start_mission()
        elif cmd == 'skip':
            self.get_logger().info("⏭️ Skipping current waypoint...")
            self.cancel_current_goal()
            self.current_wp_idx += 1
            self.create_transition_timer(1.0)
        elif cmd == 'reset':
            self.get_logger().info("🔄 Resetting mission to Waypoint 1...")
            self.cancel_current_goal()
            self.current_wp_idx = 0
            self.create_transition_timer(2.0)

    def cancel_current_goal(self):
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
            self.goal_handle = None

    def start_mission(self):
        if hasattr(self, 'start_timer') and self.start_timer:
            self.start_timer.cancel()
        self.get_logger().info("Mission Starting: Connecting to Action Server...")
        self._action_client.wait_for_server()
        self.send_next_waypoint()

    def send_next_waypoint(self):
        if self.current_wp_idx >= len(self.waypoints):
            self.get_logger().info("🌽 Field traversal complete! Robot at station.")
            return

        x, y, yaw = self.waypoints[self.current_wp_idx]
        self.get_logger().info(f"Navigating to Waypoint {self.current_wp_idx+1}/{len(self.waypoints)} -> [X: {x}, Y: {y}]")

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        
        from math import sin, cos
        goal_msg.pose.pose.orientation.z = sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = cos(yaw / 2.0)

        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.get_logger().error('Waypoint rejected! Retrying in 5s...')
            self.create_transition_timer(5.0)
            return

        self._get_result_future = self.goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        self.goal_handle = None
        
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f"✅ Waypoint {self.current_wp_idx+1} Reached.")
            self.current_wp_idx += 1
            self.create_transition_timer(2.0)
        elif status == GoalStatus.STATUS_ABORTED:
            self.get_logger().warn(f"⚠️ Waypoint {self.current_wp_idx+1} ABORTED. Retrying same WP in 5s...")
            self.create_transition_timer(5.0)
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().info(f"🚫 Waypoint {self.current_wp_idx+1} CANCELED.")
        else:
            self.get_logger().warn(f"❓ Status {status}. Moving to next WP in 5s.")
            self.current_wp_idx += 1
            self.create_transition_timer(5.0)

    def create_transition_timer(self, seconds):
        if self.transition_timer is not None:
            self.transition_timer.cancel()
        self.transition_timer = self.create_timer(seconds, self.timer_callback)

    def timer_callback(self):
        self.transition_timer.cancel()
        self.transition_timer = None
        self.send_next_waypoint()

def main(args=None):
    rclpy.init(args=args)
    navigator = FieldNavigator()
    try:
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
