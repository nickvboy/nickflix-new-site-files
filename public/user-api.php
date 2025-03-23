<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

require_once 'config.php';

function getAuthenticatedUserId() {
    // This is a simplistic approach - in a real app, use proper JWT tokens or sessions
    if (isset($_GET['user_id']) && is_numeric($_GET['user_id'])) {
        return intval($_GET['user_id']);
    }
    return null;
}

// GET operations - retrieve user profile
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $userId = getAuthenticatedUserId();
    
    if (!$userId) {
        echo json_encode(['success' => false, 'message' => 'Authentication required']);
        exit;
    }
    
    $conn = getDbConnection();
    
    // Get user with profile data
    $stmt = $conn->prepare("
        SELECT u.id, u.email, p.username, p.full_name, p.avatar_url 
        FROM users u 
        LEFT JOIN user_profiles p ON u.id = p.user_id 
        WHERE u.id = ?
    ");
    
    $stmt->bind_param("i", $userId);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 1) {
        $userData = $result->fetch_assoc();
        echo json_encode([
            'success' => true,
            'user' => [
                'id' => $userData['id'],
                'email' => $userData['email'],
                'username' => $userData['username'],
                'full_name' => $userData['full_name'],
                'avatar_url' => $userData['avatar_url'],
                'membership' => 'Free' // For now hardcoded, would come from a membership table
            ]
        ]);
    } else {
        echo json_encode(['success' => false, 'message' => 'User not found']);
    }
    
    $stmt->close();
    $conn->close();
}

// PUT operations - update user profile
else if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    $userId = getAuthenticatedUserId();
    
    if (!$userId) {
        echo json_encode(['success' => false, 'message' => 'Authentication required']);
        exit;
    }
    
    $data = json_decode(file_get_contents('php://input'), true);
    
    $username = sanitizeInput($data['username'] ?? null);
    $fullName = sanitizeInput($data['full_name'] ?? null);
    $avatarUrl = sanitizeInput($data['avatar_url'] ?? null);
    
    if (!$username && !$fullName && !$avatarUrl) {
        echo json_encode(['success' => false, 'message' => 'No data to update']);
        exit;
    }
    
    $conn = getDbConnection();
    
    // Check if username already exists (if provided)
    if ($username) {
        $stmt = $conn->prepare("SELECT user_id FROM user_profiles WHERE username = ? AND user_id != ?");
        $stmt->bind_param("si", $username, $userId);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows > 0) {
            echo json_encode(['success' => false, 'message' => 'Username already taken']);
            $stmt->close();
            $conn->close();
            exit;
        }
    }
    
    // Begin transaction
    $conn->begin_transaction();
    
    try {
        // Check if profile exists
        $stmt = $conn->prepare("SELECT user_id FROM user_profiles WHERE user_id = ?");
        $stmt->bind_param("i", $userId);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows > 0) {
            // Update existing profile
            $updateFields = [];
            $updateParams = [];
            $updateTypes = "";
            
            if ($username !== null) {
                $updateFields[] = "username = ?";
                $updateParams[] = $username;
                $updateTypes .= "s";
            }
            
            if ($fullName !== null) {
                $updateFields[] = "full_name = ?";
                $updateParams[] = $fullName;
                $updateTypes .= "s";
            }
            
            if ($avatarUrl !== null) {
                $updateFields[] = "avatar_url = ?";
                $updateParams[] = $avatarUrl;
                $updateTypes .= "s";
            }
            
            if (!empty($updateFields)) {
                $updateQuery = "UPDATE user_profiles SET " . implode(", ", $updateFields) . " WHERE user_id = ?";
                $updateParams[] = $userId;
                $updateTypes .= "i";
                
                $stmt = $conn->prepare($updateQuery);
                $stmt->bind_param($updateTypes, ...$updateParams);
                $stmt->execute();
            }
        } else {
            // Create new profile
            $stmt = $conn->prepare("INSERT INTO user_profiles (user_id, username, full_name, avatar_url) VALUES (?, ?, ?, ?)");
            $stmt->bind_param("isss", $userId, $username, $fullName, $avatarUrl);
            $stmt->execute();
        }
        
        $conn->commit();
        
        // Get updated user data
        $stmt = $conn->prepare("
            SELECT u.id, u.email, p.username, p.full_name, p.avatar_url 
            FROM users u 
            LEFT JOIN user_profiles p ON u.id = p.user_id 
            WHERE u.id = ?
        ");
        
        $stmt->bind_param("i", $userId);
        $stmt->execute();
        $result = $stmt->get_result();
        $userData = $result->fetch_assoc();
        
        echo json_encode([
            'success' => true,
            'message' => 'Profile updated successfully',
            'user' => [
                'id' => $userData['id'],
                'email' => $userData['email'],
                'username' => $userData['username'],
                'full_name' => $userData['full_name'],
                'avatar_url' => $userData['avatar_url'],
                'membership' => 'Free' // For now hardcoded
            ]
        ]);
    } catch (Exception $e) {
        $conn->rollback();
        echo json_encode(['success' => false, 'message' => 'Profile update failed: ' . $e->getMessage()]);
    }
    
    $stmt->close();
    $conn->close();
}

// Unsupported methods
else {
    echo json_encode(['success' => false, 'message' => 'Unsupported request method']);
}
?> 