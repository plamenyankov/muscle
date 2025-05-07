-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS muscle_fitness
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

USE muscle_fitness;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Muscle groups table
CREATE TABLE IF NOT EXISTS muscle_groups (
    muscle_group_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- Exercises table
CREATE TABLE IF NOT EXISTS exercises (
    exercise_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    muscle_group_id INT,
    equipment_type ENUM('machine', 'free_weight', 'bodyweight', 'other') NOT NULL,
    is_compound BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (muscle_group_id) REFERENCES muscle_groups(muscle_group_id) ON DELETE SET NULL
);

-- Workout templates table
CREATE TABLE IF NOT EXISTS workout_templates (
    template_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Workout template exercises
CREATE TABLE IF NOT EXISTS template_exercises (
    template_exercise_id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL,
    exercise_id INT NOT NULL,
    target_sets INT NOT NULL,
    target_reps INT NOT NULL,
    target_weight DECIMAL(6,2),
    exercise_order INT NOT NULL,
    rest_seconds INT,
    FOREIGN KEY (template_id) REFERENCES workout_templates(template_id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id) ON DELETE CASCADE
);

-- Workout sessions table
CREATE TABLE IF NOT EXISTS workout_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    template_id INT,
    session_date DATETIME NOT NULL,
    duration_minutes INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES workout_templates(template_id) ON DELETE SET NULL
);

-- Exercise sets (workout log entries)
CREATE TABLE IF NOT EXISTS exercise_sets (
    set_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    exercise_id INT NOT NULL,
    set_number INT NOT NULL,
    reps INT NOT NULL,
    weight DECIMAL(6,2),
    completed BOOLEAN DEFAULT TRUE,
    perceived_difficulty INT CHECK (perceived_difficulty BETWEEN 1 AND 10),
    notes TEXT,
    FOREIGN KEY (session_id) REFERENCES workout_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id) ON DELETE CASCADE
);

-- Insert basic muscle groups
INSERT INTO muscle_groups (name, description) VALUES
('Chest', 'Pectoralis major and minor muscles'),
('Back', 'Latissimus dorsi, rhomboids, and trapezius muscles'),
('Legs', 'Quadriceps, hamstrings, glutes, and calves'),
('Shoulders', 'Deltoid muscles (anterior, lateral, and posterior)'),
('Arms', 'Biceps and triceps'),
('Core', 'Abdominal muscles, obliques, and lower back'),
('Full Body', 'Exercises that engage multiple major muscle groups');

-- Insert sample exercises
INSERT INTO exercises (name, description, muscle_group_id, equipment_type, is_compound) VALUES
-- Chest
('Bench Press', 'Lie on a bench and press a barbell upward', 1, 'free_weight', TRUE),
('Incline Dumbbell Press', 'Press dumbbells upward while on an incline bench', 1, 'free_weight', TRUE),
('Chest Fly Machine', 'Machine that targets chest muscles through a fly motion', 1, 'machine', FALSE),
('Push-ups', 'Body weight exercise pushing away from the ground', 1, 'bodyweight', TRUE),

-- Back
('Pull-ups', 'Vertical pulling exercise using body weight', 2, 'bodyweight', TRUE),
('Lat Pulldown', 'Machine that simulates pull-ups', 2, 'machine', FALSE),
('Seated Row', 'Horizontal pulling exercise using a cable machine', 2, 'machine', FALSE),
('Deadlift', 'Picking up a barbell from the ground', 2, 'free_weight', TRUE),

-- Legs
('Squats', 'Bend knees to lower body with barbell on shoulders', 3, 'free_weight', TRUE),
('Leg Press', 'Press weight away using legs on a machine', 3, 'machine', TRUE),
('Leg Extension', 'Extend legs against resistance on a machine', 3, 'machine', FALSE),
('Leg Curl', 'Curl legs against resistance on a machine', 3, 'machine', FALSE),

-- Shoulders
('Overhead Press', 'Press barbell or dumbbells overhead', 4, 'free_weight', TRUE),
('Lateral Raise', 'Raise dumbbells to sides to target lateral deltoids', 4, 'free_weight', FALSE),
('Shoulder Press Machine', 'Machine version of the overhead press', 4, 'machine', TRUE),
('Face Pull', 'Pull rope attachment towards face to target rear deltoids', 4, 'machine', FALSE),

-- Arms
('Barbell Curl', 'Curl a barbell to target biceps', 5, 'free_weight', FALSE),
('Tricep Pushdown', 'Push cable attachment down to target triceps', 5, 'machine', FALSE),
('Hammer Curl', 'Curl dumbbells with neutral grip', 5, 'free_weight', FALSE),
('Skull Crusher', 'Lower weight to forehead while lying down', 5, 'free_weight', FALSE),

-- Core
('Crunches', 'Basic abdominal exercise', 6, 'bodyweight', FALSE),
('Plank', 'Hold position similar to push-up to engage core', 6, 'bodyweight', FALSE),
('Cable Crunch', 'Kneeling crunch using cable machine', 6, 'machine', FALSE),
('Russian Twist', 'Twisting motion while seated to engage obliques', 6, 'bodyweight', FALSE),

-- Full Body
('Burpees', 'Combination of squat, push-up, and jump', 7, 'bodyweight', TRUE),
('Clean and Press', 'Olympic lift combining clean and overhead press', 7, 'free_weight', TRUE),
('Kettlebell Swing', 'Swing kettlebell using hip hinge motion', 7, 'free_weight', TRUE);

-- Create indexes for better performance
CREATE INDEX idx_exercises_muscle_group ON exercises(muscle_group_id);
CREATE INDEX idx_template_exercises_template ON template_exercises(template_id);
CREATE INDEX idx_workout_sessions_user ON workout_sessions(user_id);
CREATE INDEX idx_workout_sessions_date ON workout_sessions(session_date);
CREATE INDEX idx_exercise_sets_session ON exercise_sets(session_id);
CREATE INDEX idx_exercise_sets_exercise ON exercise_sets(exercise_id);
