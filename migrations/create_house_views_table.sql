-- Create house_views table to track individual views
CREATE TABLE IF NOT EXISTS house_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    house_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (house_id) REFERENCES houses(h_id) ON DELETE CASCADE
);

-- Add index for better performance
CREATE INDEX idx_house_views_house_id ON house_views(house_id);
CREATE INDEX idx_house_views_created_at ON house_views(created_at);
