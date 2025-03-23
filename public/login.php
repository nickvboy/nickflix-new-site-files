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
    
    if (empty($email) || empty($password)) {
        echo json_encode(['success' => false, 'message' => 'Email and password are required']);
        exit;
    }
    
    $conn = getDbConnection();
    
    // Get user with the provided email
    $stmt = $conn->prepare("SELECT id, email, password_hash FROM users WHERE email = ?");
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 1) {
        $user = $result->fetch_assoc();
        if (password_verify($password, $user['password_hash'])) {
            // Get additional user info from user_profiles
            $profile_stmt = $conn->prepare("SELECT username, full_name, avatar_url, date_of_birth FROM user_profiles WHERE user_id = ?");
            $profile_stmt->bind_param("i", $user['id']);
            $profile_stmt->execute();
            $profile_result = $profile_stmt->get_result();
            $profile = $profile_result->fetch_assoc();

            // Calculate age if date of birth is provided
            $age = null;
            $date_of_birth = null;
            if (!empty($profile['date_of_birth'])) {
                $date_of_birth = $profile['date_of_birth'];
                $dob = new DateTime($date_of_birth);
                $today = new DateTime();
                $age = $today->diff($dob)->y;
            }

            echo json_encode([
                'success' => true,
                'message' => 'Login successful',
                'user' => [
                    'id' => $user['id'],
                    'email' => $user['email'],
                    'username' => $profile['username'] ?? null,
                    'full_name' => $profile['full_name'] ?? null,
                    'avatar_url' => $profile['avatar_url'] ?? null,
                    'date_of_birth' => $date_of_birth,
                    'age' => $age
                ]
            ]);
            $profile_stmt->close();
        } else {
            echo json_encode(['success' => false, 'message' => 'Invalid email or password']);
        }
    } else {
        echo json_encode(['success' => false, 'message' => 'Invalid email or password']);
    }
    
    $stmt->close();
    $conn->close();
} else {
    echo json_encode(['success' => false, 'message' => 'Invalid request method']);
}
?> 