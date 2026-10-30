from collections import deque
from typing import Dict, List, Optional, Set

# Biomechanical movement graph
# joint_stress: list of joints under heavy axial or shear load
EXERCISE_GRAPH = {
    # Quad-dominant / Squat Pattern
    "barbell_back_squat": {
        "name": "Barbell Back Squat",
        "muscle": "quads",
        "joint_stress": ["knee", "lower_back"],
        "substitutes": ["goblet_squat", "leg_press"]
    },
    "goblet_squat": {
        "name": "Goblet Squat",
        "muscle": "quads",
        "joint_stress": ["knee"],
        "substitutes": ["leg_press", "bodyweight_box_squat"]
    },
    "leg_press": {
        "name": "Leg Press",
        "muscle": "quads",
        "joint_stress": ["knee"],
        "substitutes": ["bodyweight_box_squat", "leg_extension"]
    },
    "bodyweight_box_squat": {
        "name": "Bodyweight Box Squat",
        "muscle": "quads",
        "joint_stress": [],
        "substitutes": ["leg_extension"]
    },
    "leg_extension": {
        "name": "Seated Leg Extension (Controlled)",
        "muscle": "quads",
        "joint_stress": [],
        "substitutes": []
    },

    # Posterior Chain / Hinge Pattern
    "conventional_deadlift": {
        "name": "Barbell Deadlift",
        "muscle": "hamstrings_back",
        "joint_stress": ["lower_back", "knee"],
        "substitutes": ["romanian_deadlift", "trap_bar_deadlift"]
    },
    "romanian_deadlift": {
        "name": "Dumbbell Romanian Deadlift",
        "muscle": "hamstrings_back",
        "joint_stress": ["lower_back"],
        "substitutes": ["seated_leg_curl", "glute_bridge"]
    },
    "seated_leg_curl": {
        "name": "Seated Machine Leg Curl",
        "muscle": "hamstrings_back",
        "joint_stress": [],
        "substitutes": ["glute_bridge"]
    },
    "glute_bridge": {
        "name": "Bodyweight Glute Bridge",
        "muscle": "hamstrings_back",
        "joint_stress": [],
        "substitutes": []
    },

    # Horizontal Press Pattern
    "barbell_bench_press": {
        "name": "Barbell Bench Press",
        "muscle": "chest",
        "joint_stress": ["shoulder", "wrist"],
        "substitutes": ["dumbbell_floor_press", "pushups"]
    },
    "dumbbell_floor_press": {
        "name": "Dumbbell Floor Press",
        "muscle": "chest",
        "joint_stress": ["wrist"],
        "substitutes": ["pushups", "cable_chest_fly"]
    },
    "pushups": {
        "name": "Incline / Knee Push-ups",
        "muscle": "chest",
        "joint_stress": ["wrist"],
        "substitutes": ["cable_chest_fly"]
    },
    "cable_chest_fly": {
        "name": "Cable / Band Chest Fly",
        "muscle": "chest",
        "joint_stress": [],
        "substitutes": []
    },

    # Vertical Press Pattern
    "standing_overhead_press": {
        "name": "Standing Overhead Press",
        "muscle": "shoulders",
        "joint_stress": ["shoulder", "lower_back"],
        "substitutes": ["seated_dumbbell_press", "lateral_raises"]
    },
    "seated_dumbbell_press": {
        "name": "Seated Dumbbell Shoulder Press",
        "muscle": "shoulders",
        "joint_stress": ["shoulder"],
        "substitutes": ["lateral_raises"]
    },
    "lateral_raises": {
        "name": "Dumbbell / Cable Lateral Raises",
        "muscle": "shoulders",
        "joint_stress": [],
        "substitutes": []
    }
}


def find_safe_progression(exercise_key: str, user_conditions: List[str]) -> Dict:
    """
    Executes Breadth-First Search (BFS) graph traversal to identify the closest
    biomechanically safe alternative exercise that completely prunes contraindicated joints.
    """
    if exercise_key not in EXERCISE_GRAPH:
        return {"status": "error", "message": f"Exercise '{exercise_key}' not present in movement ontology."}

    # Normalize conditions (e.g. "knee pain" -> matches "knee")
    cleaned_conditions = [c.strip().lower() for c in user_conditions]

    queue = deque([exercise_key])
    visited: Set[str] = set([exercise_key])
    traversed_path = []

    while queue:
        current_node = queue.popleft()
        node_data = EXERCISE_GRAPH[current_node]
        traversed_path.append(node_data["name"])

        # Check if current exercise stresses any flagged joint
        is_safe = True
        violated_joints = []
        for stress_joint in node_data["joint_stress"]:
            for cond in cleaned_conditions:
                if stress_joint in cond:
                    is_safe = False
                    violated_joints.append(stress_joint)

        # If it is safe, return this node
        if is_safe:
            return {
                "original_exercise": EXERCISE_GRAPH[exercise_key]["name"],
                "prescribed_exercise": node_data["name"],
                "target_muscle": node_data["muscle"],
                "status": "adapted" if current_node != exercise_key else "optimal",
                "adaptation_path": traversed_path,
                "avoided_joint_stress": list(set(violated_joints)) if not is_safe else [],
                "algorithm": "BFS Graph Traversal & Joint Contraindication Pruning"
            }

        # Otherwise, traverse neighboring substitute nodes in the graph
        for neighbor in node_data["substitutes"]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return {
        "status": "unresolved",
        "original_exercise": EXERCISE_GRAPH[exercise_key]["name"],
        "prescribed_exercise": "Isometric Rest / Physical Therapy Consultation",
        "adaptation_path": traversed_path,
        "algorithm": "BFS Graph Traversal & Joint Contraindication Pruning"
    }