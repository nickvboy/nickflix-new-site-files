<?php
header('Content-Type: ' . (isset($_GET['json']) ? 'application/json' : 'text/html; charset=utf-8'));
require_once 'config.php';

// Get SQL queries from database.sql file
$sqlContent = file_get_contents(__DIR__ . '/database.sql');
$sqlQueries = explode(';', $sqlContent);

if (isset($_GET['json'])) {
    // JSON response mode
    $response = [
        'success' => true,
        'message' => 'Database setup complete',
        'tables_created' => [],
        'errors' => []
    ];
    
    try {
        $conn = getDbConnection();
        
        foreach ($sqlQueries as $query) {
            $query = trim($query);
            if (empty($query)) continue;
            
            // Extract table name from the query
            if (preg_match('/CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+`?(\w+)`?/i', $query, $matches)) {
                $tableName = $matches[1];
                
                try {
                    if ($conn->query($query)) {
                        $response['tables_created'][] = $tableName;
                    } else {
                        $response['errors'][] = [
                            'table' => $tableName,
                            'error' => $conn->error
                        ];
                        $response['success'] = false;
                    }
                } catch (Exception $e) {
                    $response['errors'][] = [
                        'table' => $tableName,
                        'error' => $e->getMessage()
                    ];
                    $response['success'] = false;
                }
            }
        }
        
        $conn->close();
        
        if (!empty($response['errors'])) {
            $response['message'] = 'Database setup completed with errors';
        }
    } catch (Exception $e) {
        $response['success'] = false;
        $response['message'] = 'Database connection failed: ' . $e->getMessage();
    }
    
    echo json_encode($response, JSON_PRETTY_PRINT);
    exit;
}

// HTML response mode
echo "<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Database Setup</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .success { color: green; }
        .error { color: red; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Database Setup</h1>";

try {
    $conn = getDbConnection();
    echo "<p class='success'>Database connection successful!</p>";
    
    $tablesCreated = [];
    $errors = [];
    
    foreach ($sqlQueries as $query) {
        $query = trim($query);
        if (empty($query)) continue;
        
        // Extract table name from the query
        if (preg_match('/CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+`?(\w+)`?/i', $query, $matches)) {
            $tableName = $matches[1];
            
            try {
                if ($conn->query($query)) {
                    $tablesCreated[] = $tableName;
                    echo "<p class='success'>✓ Table '$tableName' created or already exists.</p>";
                } else {
                    $errors[] = "Error creating table '$tableName': " . $conn->error;
                    echo "<p class='error'>✗ Error creating table '$tableName': " . $conn->error . "</p>";
                }
            } catch (Exception $e) {
                $errors[] = "Error creating table '$tableName': " . $e->getMessage();
                echo "<p class='error'>✗ Error creating table '$tableName': " . $e->getMessage() . "</p>";
            }
        }
    }
    
    if (empty($errors)) {
        echo "<h2 class='success'>Database setup complete!</h2>";
    } else {
        echo "<h2 class='error'>Database setup completed with errors.</h2>";
    }
    
    echo "<h3>SQL Script Used:</h3>";
    echo "<pre>" . htmlspecialchars($sqlContent) . "</pre>";
    
    $conn->close();
} catch (Exception $e) {
    echo "<p class='error'>Database connection failed: " . $e->getMessage() . "</p>";
    echo "<h3>Debug Information:</h3>";
    echo "<pre>";
    echo "Host: " . DB_HOST . "\n";
    echo "Database: " . DB_NAME . "\n";
    echo "User: " . DB_USER . "\n";
    echo "</pre>";
}

echo "
    <p><a href='test-db.php'>View Database Tables</a></p>
</body>
</html>";
?> 