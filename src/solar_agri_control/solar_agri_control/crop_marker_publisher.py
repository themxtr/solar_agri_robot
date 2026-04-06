"""
crop_marker_publisher.py
-------------------------
Publishes 3D MarkerArrays to RViz2 to visualize the Gazebo crops.
Matches the 5x10 grid generated in field.world.
"""
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA

class CropMarkerPublisher(Node):
    def __init__(self):
        super().__init__('crop_marker_publisher')
        self.pub_markers = self.create_publisher(MarkerArray, '/crop_markers', 10)
        self.create_timer(1.0, self.publish_markers)
        self.marker_array = self._generate_markers()
        self.get_logger().info('Publishing 3D crop markers to RViz2 on /crop_markers')

    def _generate_markers(self) -> MarkerArray:
        ma = MarkerArray()
        id_counter = 0

        # Matches the field.world generation: 5 rows, 10 cols
        for r in range(5):
            for c in range(10):
                x_pos = c * 0.7
                y_pos = (r - 2) * 1.5

                m = Marker()
                m.header.frame_id = 'map'
                m.ns = 'crops'
                m.id = id_counter
                id_counter += 1
                m.type = Marker.CYLINDER
                m.action = Marker.ADD
                
                # Crops are 0.5m tall in Gazebo, origin shifted by 0.25 in Z
                m.pose.position.x = x_pos
                m.pose.position.y = y_pos
                m.pose.position.z = 0.25
                m.pose.orientation.w = 1.0
                
                m.scale.x = 0.1
                m.scale.y = 0.1
                m.scale.z = 0.5
                
                c_rgba = ColorRGBA()
                c_rgba.a = 0.9
                c_rgba.r, c_rgba.g, c_rgba.b = 0.1, 0.8, 0.2  # Green crop
                m.color = c_rgba
                
                ma.markers.append(m)
        return ma

    def publish_markers(self):
        now = self.get_clock().now().to_msg()
        for m in self.marker_array.markers:
            m.header.stamp = now
        self.pub_markers.publish(self.marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = CropMarkerPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
