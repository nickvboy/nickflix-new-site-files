<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

require_once 'config.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // In a real session-based system, you would destroy the session here
    // For our localStorage-based auth, we just return success
    // The frontend will handle clearing the user data
    
    echo json_encode([
        'success' => true,
        'message' => 'Logged out successfully'
    ]);
} else {
    echo json_encode([
        'success' => false,
        'message' => 'Invalid request method'
    ]);
}
?> 