-- Create enum type for file extensions
CREATE TYPE file_extension AS ENUM ('.jpg', '.png', '.gif');

-- Create images table
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    size INTEGER NOT NULL CHECK (size > 0),
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_type file_extension NOT NULL
);

-- Comment on table and columns for documentation
COMMENT ON TABLE images IS 'Stores metadata for uploaded image files';
COMMENT ON COLUMN images.id IS 'Unique identifier for each image';
COMMENT ON COLUMN images.filename IS 'Name of the file in the storage system';
COMMENT ON COLUMN images.original_name IS 'Original name of the file when it was uploaded';
COMMENT ON COLUMN images.size IS 'Size of the file in bytes';
COMMENT ON COLUMN images.upload_time IS 'When the file was uploaded';
COMMENT ON COLUMN images.file_type IS 'File extension (.jpg, .png, or .gif)';
