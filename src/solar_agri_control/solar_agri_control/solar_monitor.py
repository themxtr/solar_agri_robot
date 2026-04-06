"""
solar_monitor.py
-----------------
Monitors the solar panel state of the Solar Agricultural Robot.

Published Topics
  /solar/voltage        (std_msgs/Float32)  – simulated panel voltage (V)
  /solar/current        (std_msgs/Float32)  – simulated panel current (A)
  /solar/power          (std_msgs/Float32)  – computed power (W)
  /solar/battery_pct    (std_msgs/Float32)  – battery state of charge (%)
  /solar/status         (std_msgs/String)   – human-readable solar status

Parameters
  publish_rate   (float, default 1.0)   – Hz
  panel_voc      (float, default 21.0)  – open-circuit voltage (V)
  panel_isc      (float, default 5.5)   – short-circuit current (A)
  battery_cap_wh (float, default 100.0) – battery capacity (Wh)
"""

import math
import random
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String


class SolarMonitor(Node):
    """Publishes simulated solar panel and battery telemetry."""

    def __init__(self):
        super().__init__('solar_monitor')

        # --- parameters ---
        self.declare_parameter('publish_rate',   1.0)
        self.declare_parameter('panel_voc',      21.0)
        self.declare_parameter('panel_isc',      5.5)
        self.declare_parameter('battery_cap_wh', 100.0)

        self.rate        = self.get_parameter('publish_rate').value
        self.voc         = self.get_parameter('panel_voc').value
        self.isc         = self.get_parameter('panel_isc').value
        self.battery_cap = self.get_parameter('battery_cap_wh').value

        # simulated battery state (starts at 80 %)
        self._battery_wh   = self.battery_cap * 0.80
        self._sim_time     = 0.0   # seconds elapsed

        # --- publishers ---
        self.pub_voltage  = self.create_publisher(Float32, '/solar/voltage',     10)
        self.pub_current  = self.create_publisher(Float32, '/solar/current',     10)
        self.pub_power    = self.create_publisher(Float32, '/solar/power',       10)
        self.pub_bat_pct  = self.create_publisher(Float32, '/solar/battery_pct', 10)
        self.pub_status   = self.create_publisher(String,  '/solar/status',      10)

        # --- timer ---
        self.create_timer(1.0 / self.rate, self._publish)

        self.get_logger().info(
            '☀️  SolarMonitor started — Voc=%.1f V, Isc=%.1f A, cap=%.0f Wh' %
            (self.voc, self.isc, self.battery_cap)
        )

    # ------------------------------------------------------------------ #
    def _solar_irradiance(self) -> float:
        """Return a simulated solar irradiance factor 0-1 following a daily arc."""
        # Simulate a 12-hour solar day; peak at t=6h (21600 s)
        hour_angle = (self._sim_time % 86400.0) / 86400.0 * 2 * math.pi
        raw = math.sin(hour_angle)
        irradiance = max(0.0, raw)
        # Add sensor noise ±3 %
        noise = 1.0 + random.uniform(-0.03, 0.03)
        return irradiance * noise

    # ------------------------------------------------------------------ #
    def _publish(self):
        self._sim_time += 1.0 / self.rate

        irr = self._solar_irradiance()

        # Simplified PV model
        voltage = self.voc * (1.0 - 0.04 * (1.0 - irr))  # slightly lower at low irr
        current = self.isc * irr
        power   = voltage * current

        # Update battery (net: solar charges, assume 10 W constant load)
        LOAD_W = 10.0
        delta_wh = (power - LOAD_W) * (1.0 / self.rate) / 3600.0
        self._battery_wh = max(0.0, min(self.battery_cap, self._battery_wh + delta_wh))
        battery_pct = (self._battery_wh / self.battery_cap) * 100.0

        # Charging / discharging label
        if battery_pct >= 99.9:
            charge_label = 'FULL'
        elif power > LOAD_W:
            charge_label = 'CHARGING'
        elif power > 0:
            charge_label = 'DISCHARGING'
        else:
            charge_label = 'NIGHT'

        # Publish
        self.pub_voltage.publish(Float32(data=float(voltage)))
        self.pub_current.publish(Float32(data=float(current)))
        self.pub_power.publish(Float32(data=float(power)))
        self.pub_bat_pct.publish(Float32(data=float(battery_pct)))

        status_str = (
            f'[{charge_label}] '
            f'V={voltage:.2f} V  I={current:.2f} A  P={power:.1f} W  '
            f'Battery={battery_pct:.1f}%  Irr={irr*100:.0f}%'
        )
        self.pub_status.publish(String(data=status_str))

        self.get_logger().debug(status_str)


def main(args=None):
    rclpy.init(args=args)
    node = SolarMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down SolarMonitor...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
