-- Add index on filename for faster lookups
CREATE INDEX idx_images_filename ON images(filename);

-- Add index on upload_time for sorting by newest/oldest
CREATE INDEX idx_images_upload_time ON images(upload_time);
