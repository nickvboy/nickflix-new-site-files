<?php
header('Content-Type: ' . (isset($_GET['json']) ? 'application/json' : 'text/html; charset=utf-8'));
require_once 'config.php';

if (isset($_GET['json'])) {
    // JSON response mode for API testing
    $response = [
        'success' => false,
        'message' => 'Database connection test failed',
        'tables' => [],
        'error' => null
    ];
    
    try {
        $conn = getDbConnection();
        $response['success'] = true;
        $response['message'] = 'Database connection successful';
        
        // Test if tables exist and get their structure
        $tables = ['users', 'user_profiles'];
        foreach ($tables as $table) {
            $result = $conn->query("SHOW TABLES LIKE '$table'");
            if ($result->num_rows > 0) {
                $tableInfo = ['name' => $table, 'exists' => true, 'fields' => []];
                
                // Get table structure
                $structure = $conn->query("DESCRIBE $table");
                if ($structure) {
                    while ($row = $structure->fetch_assoc()) {
                        $tableInfo['fields'][] = [
                            'name' => $row['Field'],
                            'type' => $row['Type'],
                            'null' => $row['Null'],
                            'key' => $row['Key'],
                            'default' => $row['Default']
                        ];
                    }
                }
                
                $response['tables'][] = $tableInfo;
            } else {
                $response['tables'][] = ['name' => $table, 'exists' => false];
            }
        }
        
        $conn->close();
    } catch (Exception $e) {
        $response['error'] = $e->getMessage();
    }
    
    echo json_encode($response, JSON_PRETTY_PRINT);
    exit;
}

// HTML response mode
echo "<h2>Database Connection Test</h2>";

try {
    $conn = getDbConnection();
    echo "<p style='color: green;'>✓ Database connection successful!</p>";

    // Test if tables exist and show their structure
    $tables = ['users', 'user_profiles'];
    foreach ($tables as $table) {
        $result = $conn->query("SHOW TABLES LIKE '$table'");
        if ($result->num_rows > 0) {
            echo "<p style='color: green;'>✓ Table '$table' exists.</p>";
            
            // Show table structure
            $structure = $conn->query("DESCRIBE $table");
            if ($structure) {
                echo "<h3>Structure of '$table':</h3>";
                echo "<table border='1' cellpadding='5' style='border-collapse: collapse;'>";
                echo "<tr><th>Field</th><th>Type</th><th>Null</th><th>Key</th><th>Default</th></tr>";
                while ($row = $structure->fetch_assoc()) {
                    echo "<tr>";
                    echo "<td>{$row['Field']}</td>";
                    echo "<td>{$row['Type']}</td>";
                    echo "<td>{$row['Null']}</td>";
                    echo "<td>{$row['Key']}</td>";
                    echo "<td>{$row['Default']}</td>";
                    echo "</tr>";
                }
                echo "</table><br>";
            }
        } else {
            echo "<p style='color: red;'>✗ Table '$table' does not exist.</p>";
        }
    }

    $conn->close();
} catch (Exception $e) {
    echo "<p style='color: red;'>Error: " . $e->getMessage() . "</p>";
    echo "<h3>Debug Information:</h3>";
    echo "<pre>";
    echo "Host: " . DB_HOST . "\n";
    echo "Database: " . DB_NAME . "\n";
    echo "User: " . DB_USER . "\n";
    echo "</pre>";
}
?> 