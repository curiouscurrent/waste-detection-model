import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from scipy.spatial.distance import euclidean
from ultralytics import YOLO
from google.colab import files
from pyswarm import pso  # Import PSO library
import random

# Upload file via Colab's file upload functionality
uploaded = files.upload()

# Check if a file is uploaded and get the file name
if uploaded:
    image_path = next(iter(uploaded))  # Get the first uploaded file's name
    print(f"Uploaded file: {image_path}")

    # Load YOLO model
    model = YOLO('/content/drive/MyDrive/best_p6.pt')

    # Read the uploaded image and process it
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Perform inference to detect trash objects
    results = model.predict(source=image_path)

    # Initialize a list to store trash coordinates
    trash_coords = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls)
            if class_id == 1:
                x_center, y_center, _, _ = box.xywh[0]
                trash_coords.append((x_center, y_center))

    # If no trash is found, return message and exit
    if not trash_coords:
        print("No waste found in the image")
        exit()

    # List of 10 different colors
    color_list = [
        "red", "blue", "green", "orange", "purple", 
        "pink", "cyan", "brown", "magenta", "yellow"
    ]

    # Notify user about valid number of agents
    print("Please enter the number of agents (between 1 and 10):")
    num_agents = int(input("Enter the number of agents: "))

    # Validate the number of agents
    if num_agents < 1 or num_agents > 10:
        print("Invalid number of agents. Please enter a value between 1 and 10.")
        exit()

    # Initialize agent parameters
    collected_trash = set()
    agent_positions = [(random.randint(0, image.shape[1]), random.randint(0, image.shape[0])) for _ in range(num_agents)]
    agent_paths = [[] for _ in range(num_agents)]

    # APF Parameters
    attraction_strength = 1.0
    repulsion_strength = 1.5
    repulsion_distance = 50  # Distance at which agents start to repel each other
    step_size = 5  # Step size for agents' movements

    # Function to display the final frame
    def display_final_frame(image_rgb, trash_coords, agent_paths):
        fig, ax = plt.subplots()
        ax.imshow(image_rgb)
        ax.axis('off')

        # Plot all trash coordinates
        for coord in trash_coords:
            ax.plot(coord[0], coord[1], 'ko')  # 'ko' for black circles

        # Plot paths taken by agents with unique colors
        for agent_idx in range(num_agents):
            path_coords = [trash_coords[node] for node in agent_paths[agent_idx]]
            for i in range(len(path_coords) - 1):
                start_point = path_coords[i]
                end_point = path_coords[i + 1]
                ax.plot(
                    [start_point[0], end_point[0]],
                    [start_point[1], end_point[1]],
                    color=color_list[agent_idx],
                    lw=2
                )

        # Display the final image
        plt.show()

    # Collect trash for agents with APF and dynamic recalculation
    def dynamic_path_recalculation(trash_coords, num_agents):
        while len(collected_trash) < len(trash_coords):
            for agent_idx in range(num_agents):
                agent_position = agent_positions[agent_idx]
                remaining_trash = [i for i in range(len(trash_coords)) if i not in collected_trash]

                if not remaining_trash:
                    break

                # Find the closest trash
                closest_trash = min(remaining_trash, key=lambda x: euclidean(agent_position, trash_coords[x]))
                goal_position = trash_coords[closest_trash]

                # Calculate forces and update position
                direction_to_goal = np.array(goal_position) - np.array(agent_position)
                distance_to_goal = np.linalg.norm(direction_to_goal)

                if distance_to_goal != 0:
                    direction_to_goal /= distance_to_goal  # Normalize to get direction vector
                repulsion_force = np.array([0.0, 0.0])
                for other_agent_idx in range(num_agents):
                    if other_agent_idx != agent_idx:
                        other_agent_position = agent_positions[other_agent_idx]
                        distance_between_agents = euclidean(agent_position, other_agent_position)
                        if distance_between_agents < repulsion_distance:
                            repulsion_direction = np.array(agent_position) - np.array(other_agent_position)
                            repulsion_force += repulsion_direction / (distance_between_agents + 1e-6)

                force = attraction_strength * direction_to_goal + repulsion_strength * repulsion_force
                force_magnitude = np.linalg.norm(force)
                force /= force_magnitude if force_magnitude != 0 else 1

                new_position = np.array(agent_position) + force * step_size
                agent_positions[agent_idx] = tuple(new_position)

                if euclidean(agent_positions[agent_idx], goal_position) < 10:
                    collected_trash.add(closest_trash)
                    agent_paths[agent_idx].append(closest_trash)

            if len(collected_trash) == len(trash_coords):
                display_final_frame(image_rgb, trash_coords, agent_paths)
                break

        return agent_paths

    # Collect trash for agents
    agent_paths = dynamic_path_recalculation(trash_coords, num_agents)

    # Print paths
    for agent_idx, path in enumerate(agent_paths):
        print(f"Path taken by Agent {agent_idx + 1} (Color: {color_list[agent_idx]}):")
        for idx, node in enumerate(path):
            print(f"Step {idx + 1}: Trash object {node + 1} at {trash_coords[node]}")
