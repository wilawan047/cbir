-- Add view_count column to houses table
ALTER TABLE houses ADD COLUMN view_count INT DEFAULT 0;

-- Update existing rows to have 0 views
UPDATE houses SET view_count = 0 WHERE view_count IS NULL;
