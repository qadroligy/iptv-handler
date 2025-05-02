// 2023-10-02 Klockan 09:29

let configData = {};
let hiddenGroups = [];
let viewMode = "default"; // Modes: "default", "all", "hidden"

const CATEGORY_ID_MAP = {
    0: "unsorted",
    1: "live-channels",
    2: "movies",
    3: "series",
    4: "4k-movies",
    5: "box-sets",
    6: "live-sports",
    7: "kids-movies",
    8: "kids-series",
    9: "music-events",
    10: "24/7",
    99: "favorites"
};

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    if (!messageDiv) {
        console.error("⚠️ Message element not found!");
        return;
    }

    messageDiv.textContent = text;
    messageDiv.style.color = type === 'success' ? 'green' : 'red';
    messageDiv.style.opacity = 1;

    setTimeout(() => messageDiv.style.opacity = 0, 3000);
}


async function loadConfig() {
    try {
        const [outputResponse, hiddenResponse] = await Promise.all([
            fetch('/data/output.json?nocache=' + new Date().getTime()),
            fetch('/data/hidden.json?nocache=' + new Date().getTime()) // ✅ Load hidden.json
        ]);

        if (!outputResponse.ok || !hiddenResponse.ok) throw new Error("Failed to load JSON files");

        configData = await outputResponse.json();
        hiddenGroups = await hiddenResponse.json(); // ✅ Store hidden items

        console.log("✅ Loaded configData:", configData);
        console.log("✅ Loaded hiddenGroups:", hiddenGroups); // ✅ Debugging

        renderTable(getFilteredGroups());
    } catch (error) {
        console.error("❌ Error loading JSON files:", error);
        showMessage("❌ Failed to load output.json or hidden.json.", "error");
    }
}

function renderTable(groups) {
    const tableBody = document.querySelector("#configTable tbody");
    tableBody.innerHTML = "";

    groups.forEach(group => {
        const isHidden = hiddenGroups.some(hg => hg["source-group-title"] === group["source-group-title"]);
        if (viewMode === "default" && isHidden) return;
        if (viewMode === "hidden" && !isHidden) return;

        const row = document.createElement("tr");
        if (isHidden) row.classList.add("faded");

        row.innerHTML = `
            <td><input type="checkbox" class="hidden-checkbox" data-source-title="${group["source-group-title"]}"></td>
            <td></td> 
            <td>${group["source-group-title"]}</td>
            <td><input type="text" class="custom-title" data-source-title="${group["source-group-title"]}" value="${group["custom-group-title"]}"></td>
            <td><input type="checkbox" class="include-export" data-source-title="${group["source-group-title"]}" ${group["include-in-export"] ? "checked" : ""}></td>
            <td>
                <select class="category-select" data-source-title="${group["source-group-title"]}">
                    ${Object.entries(CATEGORY_ID_MAP).map(([id, name]) => `
                        <option value="${id}" ${group["category-id"] == id ? "selected" : ""}>${name}</option>
                    `).join("")}
                </select>
            </td>
            <td>${group["channel-count"] || 0}</td>
        `;

        tableBody.appendChild(row);
    });

    // ✅ Update category-id instantly
    document.querySelectorAll(".category-select").forEach(select => {
        select.addEventListener("change", event => {
            const sourceGroupTitle = event.target.getAttribute("data-source-title");
            const newCategoryId = event.target.value;
            updateCategoryId(sourceGroupTitle, newCategoryId);
        });
    });

    // ✅ Update include-in-export instantly
    document.querySelectorAll(".include-export").forEach(checkbox => {
        checkbox.addEventListener("change", event => {
            const sourceGroupTitle = event.target.getAttribute("data-source-title");
            const newIncludeExport = event.target.checked;
            updateIncludeExport(sourceGroupTitle, newIncludeExport);
        });
    });

    // ✅ Update custom-group-title instantly
    document.querySelectorAll(".custom-title").forEach(input => {
        input.addEventListener("input", event => {
            const sourceGroupTitle = event.target.getAttribute("data-source-title");
            const newCustomTitle = event.target.value;
            updateCustomTitle(sourceGroupTitle, newCustomTitle);
        });
    });
}

async function updateCategoryId(sourceGroupTitle, newCategoryId) {
    configData.unsorted.forEach(group => {
        if (group["source-group-title"] === sourceGroupTitle) {
            group["category-id"] = parseInt(newCategoryId, 10);
        }
    });

    console.log(`✅ Updated category-id for '${sourceGroupTitle}' to ${newCategoryId}`);

    await saveChanges([{ "source-group-title": sourceGroupTitle, "category-id": parseInt(newCategoryId, 10) }]);
}

async function updateIncludeExport(sourceGroupTitle, newIncludeExport) {
    configData.unsorted.forEach(group => {
        if (group["source-group-title"] === sourceGroupTitle) {
            group["include-in-export"] = newIncludeExport;
        }
    });

    console.log(`✅ Updated 'include-in-export' for '${sourceGroupTitle}' to ${newIncludeExport}`);

    await saveChanges([{ "source-group-title": sourceGroupTitle, "include-in-export": newIncludeExport }]);
}

async function updateCustomTitle(sourceGroupTitle, newCustomTitle) {
    configData.unsorted.forEach(group => {
        if (group["source-group-title"] === sourceGroupTitle) {
            group["custom-group-title"] = newCustomTitle;
        }
    });

    console.log(`✅ Updated 'custom-group-title' for '${sourceGroupTitle}' to "${newCustomTitle}"`);

    await saveChanges([{ "source-group-title": sourceGroupTitle, "custom-group-title": newCustomTitle }]);
}

async function saveChanges(updatedData) {
    await fetch('/save.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedData)
    });
}




// ✅ Toggle view modes for table display
function toggleViewMode() {
    viewMode = viewMode === "default" ? "all" : viewMode === "all" ? "hidden" : "default";
    console.log(`View mode changed to: ${viewMode}`);
    renderTable(getFilteredGroups());
}




// ✅ Toggle view modes for table display
function toggleViewMode() {
    viewMode = viewMode === "default" ? "all" : viewMode === "all" ? "hidden" : "default";
    console.log(`View mode changed to: ${viewMode}`);
    renderTable(getFilteredGroups());
}

function getAllGroups() {
    let all = [];
    for (const section in configData) {
        if (Array.isArray(configData[section])) {
            all = all.concat(configData[section]);
        }
    }
    return all;
}



// ✅ Ensure filtering is consistent with current view mode
function getFilteredGroups() {
    if (viewMode === "all") return getAllGroups();   // ✅ Show everything
    if (viewMode === "hidden") return hiddenGroups;  // ✅ Show only hidden items
    return getAllGroups().filter(group => 
        !hiddenGroups.some(hidden => hidden["source-group-title"] === group["source-group-title"])
    );
    
}

// ✅ Select/deselect all checkboxes correctly
function toggleSelectAll() {
    const checkboxes = document.querySelectorAll(".hidden-checkbox");
    const allSelected = Array.from(checkboxes).every(checkbox => checkbox.checked);

    checkboxes.forEach(checkbox => checkbox.checked = !allSelected);
    
    // ✅ Console log the selection state
    console.log(`Select All checkbox changed: ${!allSelected ? 'Selected All' : 'Deselected All'}`);

}

function toggleExportAll() {
    const checkboxes = document.querySelectorAll(".include-export");
    const allSelected = Array.from(checkboxes).every(checkbox => checkbox.checked);

    checkboxes.forEach(checkbox => {
        checkbox.checked = !allSelected;

        // Update the corresponding data in configData for all categories
        const sourceGroupTitle = checkbox.getAttribute("data-source-title");
        Object.keys(configData).forEach(category => {
            if (Array.isArray(configData[category])) {
                configData[category].forEach(group => {
                    if (group["source-group-title"] === sourceGroupTitle) {
                        group["include-in-export"] = checkbox.checked;
                    }
                });
            }
        });
    });

    console.log(`Select All Export: ${!allSelected ? 'Selected All' : 'Deselected All'}`);

    // Save changes on the fly
    const updatedData = Object.keys(configData).flatMap(category => {
        if (Array.isArray(configData[category])) {
            return configData[category].map(group => ({
                "source-group-title": group["source-group-title"],
                "include-in-export": group["include-in-export"]
            }));
        }
        return [];
    });

    saveChanges(updatedData);
}



function getUpdatedGroups() {
    const updated = [];
    let newHiddenGroups = [...hiddenGroups]; // ✅ Preserve existing hidden items

    document.querySelectorAll(".hidden-checkbox").forEach(checkbox => {
        const sourceGroupTitle = checkbox.getAttribute("data-source-title");
        const isGreyedOut = checkbox.closest("tr").classList.contains("faded"); // ✅ Check if row is greyed out

        if (checkbox.checked && viewMode === "default") {
            // ✅ Add checked items to hidden.json in Default view
            if (!newHiddenGroups.some(item => item["source-group-title"] === sourceGroupTitle)) {
                newHiddenGroups.push({ "source-group-title": sourceGroupTitle });
            }
        } else if (checkbox.checked && viewMode === "all" && !isGreyedOut) {
            // ✅ Move non-grey checked items to hidden.json in ALL view
            if (!newHiddenGroups.some(item => item["source-group-title"] === sourceGroupTitle)) {
                newHiddenGroups.push({ "source-group-title": sourceGroupTitle });
            }
        } else if (checkbox.checked && viewMode === "all" && isGreyedOut) {
            // ✅ Remove grey checked items from hidden.json in ALL view
            newHiddenGroups = newHiddenGroups.filter(item => item["source-group-title"] !== sourceGroupTitle);
        } else if (checkbox.checked && viewMode === "hidden") {
            // ✅ Remove checked items from hidden.json in Hidden view
            newHiddenGroups = newHiddenGroups.filter(item => item["source-group-title"] !== sourceGroupTitle);
        }
    });

    hiddenGroups = newHiddenGroups; // ✅ Ensure hidden.json updates correctly

    console.log("✅ Final hidden groups:", JSON.stringify(hiddenGroups, null, 2));

    return updated; // Keeps other config changes intact
}


async function saveConfig() {
    const updatedGroups = getUpdatedGroups();

    let existingHiddenGroups = [];
    try {
        const hiddenResponse = await fetch('/data/hidden.json?nocache=' + new Date().getTime());
        if (hiddenResponse.ok) {
            existingHiddenGroups = await hiddenResponse.json();
        }
    } catch (error) {
        console.error("❌ Error loading hidden.json:", error);
    }

    if (viewMode === "default") {
        hiddenGroups = [...existingHiddenGroups, ...hiddenGroups.filter(newItem =>
            !existingHiddenGroups.some(existingItem => existingItem["source-group-title"] === newItem["source-group-title"])
        )];
    } else if (viewMode === "hidden") {
        hiddenGroups = existingHiddenGroups.filter(item =>
            !document.querySelector(`.hidden-checkbox[data-source-title="${item["source-group-title"]}"]`).checked
        );
    }

    console.log("✅ Final hidden groups after update:", JSON.stringify(hiddenGroups, null, 2));

    document.getElementById('spinner').style.display = 'inline';

    await fetch('/save.php', { // ✅ This now triggers sorting automatically
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedGroups)
    });

    await fetch('/save_hidden.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(hiddenGroups)
    });

    document.getElementById('spinner').style.display = 'none';

    // ✅ Reload page after sorting
    setTimeout(() => {
        location.reload();
    }, 500);
}

async function resetConfig() {
    console.log("🔄 Starting reset...");

    // ✅ Clear all hidden groups
    hiddenGroups.forEach(group => {
        //console.log(`🔹 Resetting hidden group: ${group["source-group-title"]}`);
        group["category-id"] = 0;
        group["custom-group-title"] = group["source-group-title"];
        group["include-in-export"] = false; // ✅ Ensure include-in-export is false
    });

    hiddenGroups = [];
    console.log("✅ Hidden groups cleared:", hiddenGroups);

    function resetGroups(groups, categoryName) {
        if (!Array.isArray(groups)) {
            console.warn(`⚠️ Skipping ${categoryName} - Not an array`);
            return;
        }

        if (groups.length === 0) {
          //  console.log(`🔄 ${categoryName} is empty, adding default entry`);
            groups.push({
                "source-group-title": categoryName,
                "custom-group-title": categoryName,
                "include-in-export": false, // ✅ Ensure include-in-export is false
                "channel-count": 0,
                "category-id": 0
            });
        }

        groups.forEach(group => {
          //  console.log(`🔹 Resetting group: ${group["source-group-title"]}`);
            group["category-id"] = 0;
            group["custom-group-title"] = group["source-group-title"];
            group["include-in-export"] = false; // ✅ Ensure include-in-export is false
        });
    }

    Object.keys(configData).forEach(category => {
        resetGroups(configData[category], category);
    });

    //console.log("✅ Reset completed! Saving changes...", JSON.stringify(configData, null, 2));
    console.log("✅ Reset completed! Saving changes...");

    await fetch('/save_hidden.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(hiddenGroups)
    });

    await fetch('/save.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reset: true, configData }) // ✅ Explicitly mark as reset
    });

    showMessage("✅ Reset complete!", "success");

    setTimeout(() => {
        loadConfig();
        document.getElementById('resetModal').classList.remove('show');
    }, 500);
}


window.onload = () => {
    loadConfig(); // ✅ Load the configuration at startup

    document.getElementById('applyButton').addEventListener('click', () => {
        saveConfig();
    });

    // ✅ Reset button logic (add it here)
    document.getElementById('resetButton').addEventListener('click', () => {
        document.getElementById('resetModal').classList.add('show');
    });

    document.getElementById('confirmReset').addEventListener('click', () => {
        resetConfig(); // ✅ Call reset function on confirmation
        document.getElementById('resetModal').classList.remove('show');
    });

    document.getElementById('cancelReset').addEventListener('click', () => {
        document.getElementById('resetModal').classList.remove('show');
    });

    document.getElementById('selectAllCheckbox').addEventListener('click', toggleSelectAll);
    
    document.getElementById("exportCheckbox").addEventListener("click", toggleExportAll);

        
    
    

    // ✅ Add event listener to the eye icon header
    const eyeHeader = document.getElementById('eyeHeader');
    eyeHeader.style.cursor = "pointer";
    eyeHeader.setAttribute("title", "Click to toggle view: Default → All → Hidden");
    eyeHeader.addEventListener('click', toggleViewMode);
};



