# 🌱☀️ Solar Agricultural Robot — ROS 2 Workspace

A ROS 2 **Humble** workspace for an autonomous solar-powered agricultural robot. The system leverages **Gazebo** for realistic physics simulation, **SLAM Toolbox** for dynamic real-time mapping, and Navigation2 (**Nav2**) explicitly configured with **Dijkstra's Algorithm** for calculating routes safely through crop fields.

---

## 🛠️ How to Clone & Build

You must have ROS 2 Humble installed on your system.

### 1. Install Dependencies
Because we use the official Navigation and SLAM systems, make sure their system libraries are installed:
```bash
sudo apt update
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-slam-toolbox ros-humble-gazebo-ros-pkgs -y
```

### 2. Clone Workspace
```bash
cd ~
git clone https://github.com/themxtr/solar_agri_robot.git
cd solar_agri_robot
```

### 3. Build & Source
Build the ROS 2 packages using `colcon`:
```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

---

## 🚀 How to Run the Simulation

The entire physics engine, robot spawner, SLAM map builder, and Nav2 infrastructure is wrapped into **one single launch file**.

```bash
ros2 launch solar_agri_bringup simulation.launch.py
```

### What happens when you run this?
1. **Gazebo** opens showing a 3D farm field (`field.world`) populated with 5 rows of tall green crops, and the robot spawns at the centre.
2. **RViz2** opens containing the visualization tools.
3. The robot's LiDAR spins, generating `/scan` messages.
4. **SLAM Toolbox** picks up the LiDAR scans and begins drawing a 2D map in RViz (seen as white passable space and black obstacles).
5. **Nav2** initializes its Costmaps on top of the SLAM map so we can route the robot.

---

## 🗺️ How to Use RViz & Start Navigation

Because RViz is an engineering visualisation tool, **you will not see full 3D green crops in RViz**. Instead, you will see a top-down tactical layout. To actually see the 3D green crops, you must look at the **Gazebo 3D Simulation Window** that opens alongside RViz.

### 🌟 TROUBLESHOOTING: Gazebo Crash / No Crops Visible
If you run the launch file but **only RViz opens** (or you see an error like `[gzclient] process has died`), your Linux system is likely blocking Gazebo's display driver because of Wayland. 

**Run this fix in your terminal before launching to force it to work:**
```bash
export QT_QPA_PLATFORM=xcb
ros2 launch solar_agri_bringup simulation.launch.py
```
*This will successfully force the Gazebo window to appear so you can see the 3D crops!*

### 1. Understanding the RViz Map
- **Black Outlines**: These are the physical crop cylinders that your LiDAR laser is actively hitting in Gazebo.
- **Inflated Halos**: Surrounding the black dots, you will see colored "buffers" (Costmaps). Nav2 uses this buffer to ensure the robot doesn't steer too close to a crop and dent its chassis.

### 2. Step-by-Step Nav2 Goal (Dijkstra Path Plan)
Once the SLAM map starts rendering black crop outlines:
1. Look at the very top toolbar in the RViz window.
2. Click the **`Nav2 Goal`** button (often has a green arrow icon).
3. Move your mouse into the main map view. Click and hold down inside a clear path between crop rows, dragging your mouse slightly to dictate which direction the robot should face when it arrives.
4. Release the mouse. 
   - A red line **(Dijkstra trajectory)** will immediately be calculated around the crop obstacles.
   - The robot will begin physically driving down the row!

> 💡 **Tip:** Try putting a `Nav2 Goal` down a completely different row. Watch as Dijkstra's algorithm safely navigates the headlands to enter the next row without hitting the crops.

---

## 📁 Workspace Structure

| Package / Folder | Description |
|---|---|
| **`solar_agri_bringup`** | Contains `simulation.launch.py` which strings Gazebo, SLAM, and Nav2 together. |
| **`solar_agri_control`** | Python nodes for checking solar battery telemetry (`solar_monitor.py`). |
| **`solar_agri_description`** | Stores the robot's physical blueprint (`solar_agri_robot.urdf.xacro`) containing the skid-steer and LiDAR Gazebo plugins, along with the `sim_display.rviz` config map. |
| **`solar_agri_navigation`** | Stores `nav2_params.yaml`, explicitly setting `use_astar: false` on the `GridBased` planner to enforce pure Dijkstra logic, as well as costmap limits. |
| **`solar_agri_simulation`** | Includes custom generated field layouts. Contains `field.world` with the crop placement matrices. |

---

## 🛠️ Useful ROS 2 Commands

View the live battery/solar telemetry output in the terminal while the robot drives:
```bash
ros2 topic echo /solar/status
```

View the raw LiDAR distances:
```bash
ros2 topic echo /scan
```

Manually drive the robot with your keyboard (requires `ros-humble-teleop-twist-keyboard` installed):
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
