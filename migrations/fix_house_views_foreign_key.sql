-- Drop the existing foreign key constraint if it exists
ALTER TABLE house_views DROP FOREIGN KEY IF EXISTS house_views_ibfk_1;

-- Drop the existing index
DROP INDEX IF EXISTS idx_house_views_house_id ON house_views;

-- Recreate the foreign key constraint with the correct table name
ALTER TABLE house_views 
ADD CONSTRAINT fk_house_views_house
FOREIGN KEY (house_id) REFERENCES house(h_id) 
ON DELETE CASCADE;

-- Recreate the index
CREATE INDEX idx_house_views_house_id ON house_views(house_id);
