<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

require_once 'config.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true);
    
    $email = sanitizeInput($data['email'] ?? '');
    $password = $data['password'] ?? '';
    $username = sanitizeInput($data['username'] ?? '');
    $full_name = sanitizeInput($data['full_name'] ?? '');
    $date_of_birth = sanitizeInput($data['date_of_birth'] ?? '');
    
    if (empty($email) || empty($password)) {
        echo json_encode(['success' => false, 'message' => 'Email and password are required']);
        exit;
    }
    
    // Validate email
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        echo json_encode(['success' => false, 'message' => 'Invalid email format']);
        exit;
    }
    
    // Validate date of birth if provided
    $date_of_birth_obj = null;
    if (!empty($date_of_birth)) {
        $date_of_birth_obj = date_create($date_of_birth);
        if (!$date_of_birth_obj) {
            echo json_encode(['success' => false, 'message' => 'Invalid date of birth format']);
            exit;
        }
        
        // Check if the user is at least 13 years old
        $today = new DateTime();
        $age = $today->diff($date_of_birth_obj)->y;
        if ($age < 13) {
            echo json_encode(['success' => false, 'message' => 'You must be at least 13 years old to register']);
            exit;
        }
    }
    
    $conn = getDbConnection();
    
    // Check if email already exists
    $stmt = $conn->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows > 0) {
        echo json_encode(['success' => false, 'message' => 'Email already exists']);
        $stmt->close();
        $conn->close();
        exit;
    }
    
    // Check if username already exists (if provided)
    if (!empty($username)) {
        $stmt = $conn->prepare("SELECT user_id FROM user_profiles WHERE username = ?");
        $stmt->bind_param("s", $username);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows > 0) {
            echo json_encode(['success' => false, 'message' => 'Username already taken']);
            $stmt->close();
            $conn->close();
            exit;
        }
    }
    
    // Use a transaction to ensure both user and profile are created
    $conn->begin_transaction();
    
    try {
        // Hash password and create user
        $password_hash = password_hash($password, PASSWORD_DEFAULT);
        
        $stmt = $conn->prepare("INSERT INTO users (email, password_hash) VALUES (?, ?)");
        $stmt->bind_param("ss", $email, $password_hash);
        $stmt->execute();
        
        $user_id = $conn->insert_id;
        
        // Create user profile if username or full_name is provided
        if (!empty($username) || !empty($full_name) || !empty($date_of_birth)) {
            $sql = "INSERT INTO user_profiles (user_id, username, full_name";
            $sql_values = ") VALUES (?, ?, ?";
            $types = "iss";
            $params = [$user_id, $username, $full_name];
            
            if (!empty($date_of_birth)) {
                $sql .= ", date_of_birth";
                $sql_values .= ", ?";
                $types .= "s";
                $params[] = $date_of_birth_obj ? $date_of_birth_obj->format('Y-m-d') : null;
            }
            
            $sql .= $sql_values . ")";
            
            $stmt = $conn->prepare($sql);
            $stmt->bind_param($types, ...$params);
            $stmt->execute();
        }
        
        // Calculate age if date of birth is provided
        $age = null;
        if ($date_of_birth_obj) {
            $today = new DateTime();
            $age = $today->diff($date_of_birth_obj)->y;
        }
        
        $conn->commit();
        
        echo json_encode([
            'success' => true,
            'message' => 'Registration successful',
            'user' => [
                'id' => $user_id,
                'email' => $email,
                'username' => $username,
                'full_name' => $full_name,
                'date_of_birth' => $date_of_birth_obj ? $date_of_birth_obj->format('Y-m-d') : null,
                'age' => $age
            ]
        ]);
    } catch (Exception $e) {
        $conn->rollback();
        echo json_encode(['success' => false, 'message' => 'Registration failed: ' . $e->getMessage()]);
    }
    
    $stmt->close();
    $conn->close();
} else {
    echo json_encode(['success' => false, 'message' => 'Invalid request method']);
}
?> 