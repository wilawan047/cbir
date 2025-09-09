-- Create database if not exists
CREATE DATABASE IF NOT EXISTS projectdb;
USE projectdb;

-- Create admins table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create project table
CREATE TABLE IF NOT EXISTS project (
    p_id INT AUTO_INCREMENT PRIMARY KEY,
    p_name VARCHAR(100) NOT NULL,
    p_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create house_type table
CREATE TABLE IF NOT EXISTS house_type (
    t_id INT AUTO_INCREMENT PRIMARY KEY,
    t_name VARCHAR(100) NOT NULL,
    t_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create house table
CREATE TABLE IF NOT EXISTS house (
    h_id INT AUTO_INCREMENT PRIMARY KEY,
    h_title VARCHAR(100) NOT NULL,
    h_description TEXT,
    h_image VARCHAR(255),
    price DECIMAL(10,2),
    t_id INT,
    p_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (t_id) REFERENCES house_type(t_id) ON DELETE SET NULL,
    FOREIGN KEY (p_id) REFERENCES project(p_id) ON DELETE SET NULL
);

-- Create house_features table (newly added)
CREATE TABLE IF NOT EXISTS house_features (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 