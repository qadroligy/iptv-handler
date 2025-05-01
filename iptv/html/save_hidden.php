
<?php
$data = file_get_contents("php://input");

if ($data === false) {
    echo json_encode(["success" => false, "error" => "Failed to read input data"]);
    exit;
}

$result = file_put_contents(__DIR__ . "/data/hidden.json", $data);
// Uppdaterad kategori ska sparas
//$result = file_put_contents(__DIR__ . "/data/output.json", $data);



if ($result === false) {
    echo json_encode(["success" => false, "error" => "Failed to save data"]);
    exit;
}

echo json_encode(["success" => true]);
?>

