<?php
$hiddenFile = __DIR__ . '/data/hidden.json';

if (file_exists($hiddenFile)) {
    file_put_contents($hiddenFile, json_encode([])); // empty array []
    echo json_encode(["success" => true]);
} else {
    echo json_encode(["success" => false, "message" => "hidden.json not found"]);
}
?>
