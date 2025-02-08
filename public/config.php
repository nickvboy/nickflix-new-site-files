<?php
// Database configuration - using direct values since .env might not be accessible on shared hosting
define('DB_HOST', 'fdb1029.awardspace.net');
define('DB_USER', '4572518_nickflix');
define('DB_PASS', 'Alexvboy1234');
define('DB_NAME', '4572518_nickflix');

// Create connection
function getDbConnection() {
    $conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
    
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }
    
    return $conn;
}

// Function to sanitize input
function sanitizeInput($data) {
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data);
    return $data;
}
?> 