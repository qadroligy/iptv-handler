<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");
header('Content-Type: application/json');

// ✅ Handle preflight request for CORS
if (isset($_SERVER['REQUEST_METHOD']) && $_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    echo json_encode(["status" => "ok"]);
    exit();
}

// ✅ Read JSON input safely
$jsonInput = file_get_contents('php://input');
$data = json_decode($jsonInput, true);

if ($jsonInput !== false && ($data === null || !is_array($data))) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Invalid input JSON"]);
    exit();
}

// ✅ Define file paths
$file_path = __DIR__ . '/data/output.cfg';
$log_path = __DIR__ . '/data/python_exec.log'; // ✅ Logging in data/
$debug_path = __DIR__ . '/data/debug.log'; // ✅ Debug logs
$existing_cfg_json = file_exists($file_path) ? file_get_contents($file_path) : null;
$existing_cfg = json_decode($existing_cfg_json, true);

if (!is_array($existing_cfg)) {
    http_response_code(500);
    echo json_encode(["status" => "error", "message" => "Corrupt or missing output.cfg"]);
    exit();
}

// ✅ Debugging: Log incoming request
file_put_contents($debug_path, "Received Data:\n" . json_encode($data, JSON_PRETTY_PRINT) . "\n", FILE_APPEND);

// ✅ Check if Reset action is requested
if (isset($data["reset"]) && $data["reset"] === true) {
    foreach ($existing_cfg as $category => &$groups) {
        if (!is_array($groups)) continue;

        foreach ($groups as &$group) {
            $group["category-id"] = 0;
            $group["custom-group-title"] = $group["source-group-title"];
            $group["include-in-export"] = false; // ✅ Ensure include-in-export is false
        }
    }

    // ✅ Save reset changes to output.cfg
    if (!file_put_contents($file_path, json_encode($existing_cfg, JSON_PRETTY_PRINT))) {
        http_response_code(500);
        echo json_encode(["status" => "error", "message" => "Failed to reset output.cfg"]);
        exit();
    }

    echo json_encode(["status" => "success", "message" => "Reset completed"]);
} else {
    // ✅ Apply updates only if it's not a reset
    foreach ($data as $update) {
        foreach ($existing_cfg as $category => &$groups) {
            if (!is_array($groups)) continue;

            foreach ($groups as &$group) {
                if ($group["source-group-title"] === $update["source-group-title"]) {
                    if (isset($update["include-in-export"])) {
                        $group["include-in-export"] = $update["include-in-export"];
                    }
                    if (isset($update["category-id"])) {
                        $group["category-id"] = $update["category-id"];
                    }
                    if (isset($update["custom-group-title"])) {
                        $group["custom-group-title"] = $update["custom-group-title"];
                    }
                }
            }
        }
    }

    // ✅ Save updated config
    if (!file_put_contents($file_path, json_encode($existing_cfg, JSON_PRETTY_PRINT))) {
        http_response_code(500);
        echo json_encode(["status" => "error", "message" => "Failed to save output.cfg"]);
        exit();
    }

    echo json_encode(["status" => "success", "message" => "Changes saved successfully"]);
}

// ✅ Execute Python sorting script with logging
$command = 'cd /var/www/html/cfg-handler && python3 cfg-handler.py --sort -c ../data/output.cfg 2>&1';
exec($command, $output, $return_var);

// ✅ Save execution logs in `data/` directory
file_put_contents($log_path, implode("\n", $output));

if ($return_var !== 0) {
    http_response_code(500);
    echo json_encode(["status" => "error", "message" => "Sorting failed", "output" => $output]);
} else {
    echo json_encode(["status" => "success", "message" => "Sorting executed successfully"]);
}
?>
