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

### 🤖 Headless Autonomous Mode (RViz Only)
To run the full simulation with autonomous navigation but **without** the Gazebo 3D window (showing only RViz), use this new integrated command:
```bash
ros2 launch solar_agri_bringup autonomous.launch.py
```

### What happens when you run this?
1. **Gazebo** opens showing a 3D farm field (`field.world`) populated with 5 rows of tall green crops, and the robot spawns at the centre.
2. **RViz2** opens containing the visualization tools.
3. The robot's LiDAR spins, generating `/scan` messages.
4. **SLAM Toolbox** picks up the LiDAR scans and begins drawing a 2D map in RViz.
5. **Nav2** initializes its Costmaps on top of the SLAM map.
6. **Autonomous Field Navigator**: After a 20-second initialization window, the robot will automatically begin its mission to sweep through all 4 crop gaps.

---

## 🛠️ New Launch Options

### 1. Standalone RViz2
If you want to restart RViz without restarting the entire simulation, or if you ran the simulation headlessly:
```bash
ros2 launch solar_agri_bringup rviz.launch.py
```

### 2. Running Simulation without RViz
If you prefer to launch the simulation backend only (e.g., to use the standalone RViz launch later):
```bash
ros2 launch solar_agri_bringup simulation.launch.py use_rviz:=false
```

---

## 🤖 Autonomous Field Mission: "All Crops" Path

The robot is programmed to systematically inspect the field by traversing every gap between the rows.

1. **Launch the Mission**:
   ```bash
   ros2 launch solar_agri_bringup autonomous.launch.py
   ```
2. **Initialization (30s)**: The robot waits 30 seconds to allow the SLAM map to solidify and the Nav2 costmaps to initialize.
3. **Manual Mission Control**: You can control the sequence via terminal:
   - **Start Now**: `ros2 topic pub -1 /mission/command std_msgs/msg/String "data: start"`
   - **Skip current waypoint**: `ros2 topic pub -1 /mission/command std_msgs/msg/String "data: skip"`
   - **Reset Mission**: `ros2 topic pub -1 /mission/command std_msgs/msg/String "data: reset"`

### Navigation Tips:
- **Linear Driving**: The controller is tuned for straight driving (`curvature_feedback_gain: 2.0`) without "random" spinning by disabling unnecessary rotations in the rows.
- **Auto-Recovery**: If a waypoint is aborted (stuck), the robot will automatically retry after 5 seconds.

---


## 🗺️ How to Use RViz & Start Navigation

Because RViz is an engineering visualisation tool, **you will not see full 3D green crops in RViz by default**. Instead, you will see a top-down tactical layout of black dots. To see the 3D green crops in RViz, follow the "Adding Crop Markers" step below.

### 🌟 TROUBLESHOOTING: Gazebo Crash / No Crops Visible
If you run the launch file but **only RViz opens** (or you see an error like `[gzclient] process has died`), your Linux system is likely blocking Gazebo's display driver because of Wayland. 

**Run this fix in your terminal before launching to force it to work:**
```bash
export QT_QPA_PLATFORM=xcb
ros2 launch solar_agri_bringup simulation.launch.py
```
*This will successfully force the Gazebo window to appear so you can see the 3D crops!*

### 🛠️ 1. Adding 3D Crop Markers (Visualisation)
To visualize the farm field as 3D cylinders in RViz:
1. Look at the **`Displays`** panel on the left side of the RViz window.
2. Click the **`Add`** button at the bottom of that panel.
3. Search for or scroll to **`MarkerArray`** and click OK.
4. A new `MarkerArray` item will appear in your display list. Expand it.
5. Change the **`Topic`** field from empty to **`/crop_markers`**.
6. *Presto!* The 3D green crops will now appear on your map, matching the Gazebo field.

### 📍 2. Manual Navigation (Nav2 Goal)
Once the SLAM map starts rendering black crop outlines:
1. Look at the very top toolbar in the RViz window.
2. Click the **`Nav2 Goal`** button (often has a green arrow icon).
3. Move your mouse into the main map view. Click and hold down inside a clear path between crop rows, dragging your mouse slightly to dictate which direction the robot should face when it arrives.
4. Release the mouse. 
   - A red line **(Dijkstra trajectory)** will immediately be calculated.
   - The robot will begin physically driving down the row!

## 📍 Mastery Guide: Manual Navigation in RViz

If you want to manually direct the robot instead of using the autonomous script, follow these exact steps to ensure stable operation:

### Step 1: Initialize (2D Pose Estimate)
- Click the **`2D Pose Estimate`** button in the top RViz toolbar.
- Click on the map at the robot's current position and **drag in the direction it faces**.
- *This is mandatory! Nav2 needs an initial location to activate its planning bridge.*

### Step 2: Set Destination (Nav2 Goal)
- Click the **`Nav2 Goal`** button in the top toolbar.
- Click anywhere in the field and drag for orientation.
- **Dijkstra Calculation**: A red line will appear immediately, and the robot will start driving.

### Step 3: Troubleshooting "Action Server Not Available"
- **Why?**: This usually means the robot is outside the map or the system is resetting.
- **Fix**: We have enabled **Rolling Window** for the costmaps. This means the robot is *always* at the center of a 20x20m area, so you should never see "Out of Bounds" errors again.
- If RViz becomes unresponsive, simply restart the launch file and repeat Step 1.

---

## 🎯 Single Point Navigation (Custom Goals)

If you want to send the robot to a **specific location** that is NOT part of the autonomous sweep:

### Option A: Using RViz (Visual)
1. Select the **`Nav2 Goal`** tool from the top toolbar.
2. **Click** the exact spot on the map where you want the robot to go.
3. **Hold and Drag** to set the direction the robot should face upon arrival.
4. Release the mouse. The robot will plan a path through the crops to that exact point.

### Option B: Using Terminal (Coordinate Precision)
If you know the exact `(x, y)` coordinates (e.g., `x=5.0, y=0.75`), run this command:
```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 5.0, y: 0.75, z: 0.0}, orientation: {w: 1.0}}}}"
```

> [!TIP]
> **Field coordinates map**:
> - Row 1 Center: `y = -3.0`
> - **Safe Path 1**: `y = -2.25`
> - Row 2 Center: `y = -1.5`
> - **Safe Path 2**: `y = -0.75`
> - Row 3 Center: `y = 0.0`
> - **Safe Path 3**: `y = 0.75`
> - Row 4 Center: `y = 1.5`
> - **Safe Path 4**: `y = 2.25`
> - Row 5 Center: `y = 3.0`
>
> **Troubleshooting ABORTED goals**: If you send a goal like `y=1.0`, it might be too close to a crop (Row 4 is at `y=1.5`). We have reduced the inflation radius to `0.15m` to help, but aim for the **Safe Path** coordinates above for best results!

---

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
