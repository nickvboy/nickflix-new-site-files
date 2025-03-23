<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once 'config.php';

// Function to check if a column exists in a table
function columnExists($conn, $table, $column) {
    $query = "SELECT COUNT(*) AS column_exists
              FROM information_schema.COLUMNS 
              WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = ?
              AND COLUMN_NAME = ?";
    
    $stmt = $conn->prepare($query);
    $stmt->bind_param("ss", $table, $column);
    $stmt->execute();
    $result = $stmt->get_result();
    $row = $result->fetch_assoc();
    $stmt->close();
    
    return $row['column_exists'] > 0;
}

try {
    $conn = getDbConnection();
    
    // Check if date_of_birth column exists
    $date_of_birth_exists = columnExists($conn, 'user_profiles', 'date_of_birth');
    
    if (!$date_of_birth_exists) {
        // Add date_of_birth column
        $alter_query = "ALTER TABLE user_profiles ADD COLUMN date_of_birth DATE NULL AFTER avatar_url";
        if ($conn->query($alter_query)) {
            echo json_encode([
                'success' => true,
                'message' => 'date_of_birth column has been added to user_profiles table'
            ]);
        } else {
            echo json_encode([
                'success' => false,
                'message' => 'Failed to add date_of_birth column: ' . $conn->error
            ]);
        }
    } else {
        echo json_encode([
            'success' => true,
            'message' => 'date_of_birth column already exists in user_profiles table'
        ]);
    }
    
    $conn->close();
} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'message' => 'Database update failed: ' . $e->getMessage()
    ]);
}
?> 