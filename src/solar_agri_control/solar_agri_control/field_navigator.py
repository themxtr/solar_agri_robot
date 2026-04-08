#!/usr/bin/env python3
"""
field_navigator.py
------------------
Automatically sends the robot sweeping through the field rows 
using the Nav2 NavigateToPose action server.
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
import time

class FieldNavigator(Node):
    def __init__(self):
        super().__init__('field_navigator')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Define the zigzag path through all 4 crop gaps
        # Gaps are at Y = -2.25, -0.75, 0.75, 2.25
        self.waypoints = [
            (-1.5, -2.25, 0.0), # Enter Gap 1 (between Row 0 & 1), face positive X
            (7.5, -2.25, 0.0),  # End of Gap 1
            (7.5, -0.75, 3.14), # Shift to End of Gap 2, face negative X
            (-1.5, -0.75, 3.14),# Start of Gap 2
            (-1.5, 0.75, 0.0),  # Shift across to Start of Gap 3, face positive X
            (7.5, 0.75, 0.0),   # End of Gap 3
            (7.5, 2.25, 3.14),  # Shift to End of Gap 4, face negative X
            (-1.5, 2.25, 3.14), # Start of Gap 4
            (-2.0, 0.0, 0.0)    # Return to station, face positive X
        ]
        self.current_wp_idx = 0

        # Wait a bit before starting to ensure Nav2 costmaps are loaded
        self.get_logger().info("Field Navigator waiting 20s for SLAM mapping and Nav2...")
        self.timer = self.create_timer(20.0, self.start_mission)

    def start_mission(self):
        self.timer.cancel()
        self.get_logger().info("Mission Started: Connecting to Action Server...")
        self._action_client.wait_for_server()
        self.send_next_waypoint()

    def send_next_waypoint(self):
        if self.current_wp_idx >= len(self.waypoints):
            self.get_logger().info("🌽 Field traversal complete! Robot is safely at station.")
            return

        x, y, yaw = self.waypoints[self.current_wp_idx]
        self.get_logger().info(f"Navigating to Waypoint {self.current_wp_idx+1}/{len(self.waypoints)} -> [X: {x}, Y: {y}]")

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        
        # Simple yaw to quaternion (yaw is around Z axis)
        from math import sin, cos
        goal_msg.pose.pose.orientation.z = sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = cos(yaw / 2.0)

        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Waypoint rejected by Nav2 server! Aborting mission.')
            return

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        # Status code 4 is SUCCEEDED in actionlib
        if status == 4:
            self.get_logger().info(f"✅ Reached Waypoint {self.current_wp_idx+1}.")
            self.current_wp_idx += 1
            # Slight pause before sending the next goal
            time.sleep(2.0)
            self.send_next_waypoint()
        else:
            self.get_logger().warn(f"Failed to reach waypoint. Status Code: {status}")


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
