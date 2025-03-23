-- Script to add date_of_birth column to user_profiles table if it doesn't exist

-- First check if the column exists
SELECT COUNT(*) INTO @column_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = '4572518_nickflix' 
AND TABLE_NAME = 'user_profiles' 
AND COLUMN_NAME = 'date_of_birth';

-- Add the column if it doesn't exist
SET @query = IF(@column_exists = 0, 
                'ALTER TABLE user_profiles ADD COLUMN date_of_birth DATE NULL AFTER avatar_url', 
                'SELECT "date_of_birth column already exists" AS message');

PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Display confirmation
SELECT IF(@column_exists = 0, 
          'date_of_birth column has been added to user_profiles table', 
          'date_of_birth column already exists in user_profiles table') AS Result; 