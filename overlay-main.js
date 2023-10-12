window.onload = async function () {
    resize();
    InitializeEventListeners();
    setChannel();
    InitializeColorPicker();

    let video = document.getElementById('video');
    video.src = `https://player.twitch.tv/?channel=${channel_name}&parent=apoorlywrittenbot.cc&allowfullscreen=false&muted=true&autoplay=true`;

    await loadInitialJSON(video);
    deleteExpiredTimers();
    elementUnfocused();
    // await redraw();
}
window.onresize = function () {
    resize();
}

document.onkeydown = function (evt) {
    if (editing) {
        return;
    }
    evt = evt || window.event;
    var isEscape = false;
    var isDelete = false;
    isEscape = (evt.keyCode === 27);
    isDelete = (evt.keyCode === 46);
    if (isEscape && !commandsView) {
        elementUnfocused();
    }
    else if (isDelete && lastClickedElement != null && !commandsView) {
        let parentIndex = lastClickedElement.parentNode.id;
        let element_json = mapping[parentIndex];
        // Clean up unused images
        for (const ele of element_json.elements) {
            if (ele.category == 'image') {
                imagesInMenu.push(ele.content);
            }
        }
        for (const id of imagesInMenu) {
            delete imagesDictionary[id];
        }
        imagesInMenu = [];
        delete mapping[parentIndex];
        lastClickedElement.parentNode.remove();
        lastClickedElement = null;
        elementUnfocused();
    }
};

function removeAnimation(button, timeout, normal = true) {
    if (normal) {
        setTimeout(() => {
            button.style = `background-color: ${sidebarAlternateColor}; border: 1px solid ${borderAlternateCOlor}`;
            button.style.animation = '';
        }, timeout);
    }
    else {
        setTimeout(() => {
            button.style = `background-color: ${sidebarDefaultColor}; border: 1px solid ${borderColor}`;
            button.style.animation = '';
        }, timeout);
    }
}

async function switchView(e) {
    e.stopPropagation();
    if (editing) {
        return;
    }
    document.addEventListener("click", disable, true);
    document.addEventListener("mousedown", disable, true);
    document.addEventListener("mouseover", disable, true);
    let video = document.getElementById('video');
    let staticBackground = document.getElementById('staticBackground');
    let switchButton = document.getElementById("switchButton");
    let newButton = document.getElementById("newButton");
    let editButton = document.getElementById("editButton");
    let saveButton = document.getElementById("saveButton");
    let clearButton = document.getElementById("clearButton");
    let jsonButton = document.getElementById("jsonButton");
    let fontsButton = document.getElementById("fontsButton");
    if (!commandsView) {
        // Load variables if not done already
        if (channel_name == "inabox44") {
            await loadVariables();
        }
        // Swap background
        video.src = "";
        staticBackground.src = `https://apoorlywrittenbot.cc/media/${channel_name}-background.png`;
        staticBackground.style.display = "block";
        // Sidebar functionality
        commandsView = true;
        elementUnfocused();
        editButton.disabled = false;
        // CLean canvas and show menus
        lastClickedElement = null;
        document.getElementById('canvas').innerHTML = '';
        document.getElementById('commandsView').style.display = 'block';
        document.getElementById('commandsDetails').style.display = 'block';
        // Sidebar style
        let animationIndex = 0;
        for (var button of document.querySelectorAll('.sidebar')) {
            button.style.animation = `fadePurpletoGreen 0.2s ${animationIndex * 0.2}s forwards`;
            removeAnimation(button, 200 * (animationIndex + 1));
            animationIndex++;
        }
        sidebarCurrentColor = sidebarAlternateColor;
        switchButton.innerHTML = 'Switch to Overlay View';
        newButton.innerHTML = 'Commands';
        editButton.innerHTML = 'Counters';
        saveButton.innerHTML = '!kimexplains';
        clearButton.innerHTML = '!fierce';
        jsonButton.innerHTML = '-';
        fontsButton.innerHTML = '-';
        commandsList("COMMANDS");
        setTimeout(() => {
            document.removeEventListener("click", disable, true);
            document.removeEventListener("mousedown", disable, true);
            document.removeEventListener("mouseover", disable, true);
        }, 1400);
    }
    else {
        // Swap background
        video.src = `https://player.twitch.tv/?channel=${channel_name}&parent=apoorlywrittenbot.cc&allowfullscreen=false&muted=true&autoplay=true`;
        staticBackground.style.display = "none";
        document.getElementById('commandsView').style.display = 'none';
        document.getElementById('commandsDetails').style.display = 'none';
        // Restore functionality
        commandsView = false;
        mapping = {};
        index = 0;
        imagesDictionary = {};
        imagesInMenu = [];
        intervalList = [];
        await loadInitialJSON(video);
        editButton.style = `background-color: ${sidebarAlternateColor}; border: 1px solid ${borderAlternateCOlor}`;
        deleteExpiredTimers();
        // Sidebar style
        let animationIndex = 0;
        for (var button of document.querySelectorAll('.sidebar')) {
            button.style.animation = `fadePurpletoGreen 0.2s ${animationIndex * 0.2}s reverse forwards`;
            removeAnimation(button, 200 * (animationIndex + 1), false);
            animationIndex++;
        }
        document.getElementById("switchButton").innerHTML = 'Switch to Commands View';
        document.getElementById("newButton").innerHTML = 'New Element';
        editButton.innerHTML = 'Edit This Element';
        document.getElementById("saveButton").innerHTML = 'Save';
        document.getElementById("clearButton").innerHTML = 'Clear All';
        document.getElementById("jsonButton").innerHTML = 'Show JSON';
        document.getElementById("fontsButton").innerHTML = 'Load Fonts';
        sidebarCurrentColor = sidebarDefaultColor;
        setTimeout(() => {
            elementUnfocused();
            document.removeEventListener("click", disable, true);
            document.removeEventListener("mousedown", disable, true);
            document.removeEventListener("mouseover", disable, true);
        }, 1400);
    }
}

async function create(e) {
    if (e) {
        e.stopPropagation();
    }
    if (commandsView) {
        return await commandsList("COMMANDS");
    }
    if (editing) {
        return;
    }
    let divString = `<div class="box-wrapper" id="${index.toString()}" style="top: ${window.innerHeight / 2}px; left: ${left_INT + width_INT / 2}px;">
            <div class="box" id="box-${index.toString()}">
                <div class="dot rotate" id="rotate-${index.toString()}"></div>
                <div class="dot left-top" id="left-top-${index.toString()}"></div>
                <div class="dot left-bottom" id="left-bottom-${index.toString()}"></div>
                <div class="dot top-mid" id="top-mid-${index.toString()}"></div>
                <div class="dot bottom-mid" id="bottom-mid-${index.toString()}"></div>
                <div class="dot left-mid" id="left-mid-${index.toString()}"></div>
                <div class="dot right-mid" id="right-mid-${index.toString()}"></div>
                <div class="dot right-bottom" id="right-bottom-${index.toString()}"></div>
                <div class="dot right-top" id="right-top-${index.toString()}"></div>
                <div class="rotate-link"></div>
            </div>
        </div>`;
    let element = htmlToElement(divString);
    document.getElementById('canvas').appendChild(element);

    addDotsListeners(index);

    // Autofocus on new element
    if (lastClickedElement != null) {
        displayBorder(false);
    }
    let box = document.getElementById(`box-${index.toString()}`);
    lastClickedElement = box;
    let editButton = document.getElementById("editButton");
    editButton.disabled = false;
    editButton.style.background = "#6441a5";
    let video = document.getElementById('video');
    video.style.pointerEvents = 'none';

    let subelement = document.createElement("div");
    subelement.style = `color: #FFFFFF; font-size: ${window.innerHeight / font_scale}px; display: inline-block;
        pointer-events: none; transform-origin: 0 0; transform: scale(1,1);`;
    subelement.classList.add("box-child");
    subelement.textContent = "PLACEHOLDER";
    box.appendChild(subelement);
    box.style.border = `2px solid ${borderColor}`;
    box.style.width = `${subelement.offsetWidth}px`;
    box.style.height = `${subelement.offsetHeight}px`;

    element_json = {
        top: 50,
        left: 50,
        'x-scaling': 1,
        'y-scaling': 1,
        rotation: 0,
        now: ((Date.now() / 1000) | 0),
        elements: [
            {
                category: 'text',
                content: 'PLACEHOLDER',
                color: '#FFFFFF',
                font: 'Kalam'
            }
        ]
    };
    mapping[element.id] = element_json;
    index += 1;

    return element;
}

async function edit(e) {
    e.stopPropagation();
    if (commandsView) {
        return await commandsList("COUNTER");
    }
    if (editing) {
        return;
    }
    editing = true;
    let menu = document.getElementById("menu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "none";

    let element_json = mapping[lastClickedElement.parentNode.id];

    fonts.unshift("Zrnic");
    fonts.unshift("FoxyMist");
    fonts.unshift("Kalam");

    for (const ele of element_json.elements) {
        let timeString = "-";
        if (ele.expiration) {
            if (ele.active) {
                timeString = "ACTIVE";
            }
            else {
                timeString = `${ele.expiration}`;
            }
        }
        let contentBlock = document.getElementById('contentBlock');
        let selectBlock = document.getElementById('selectBlock');
        let colorBlock = document.getElementById('colorBlock');
        let fontBlock = document.getElementById('fontBlock');
        let timeBlock = document.getElementById('timeBlock');
        let restartBlock = document.getElementById('restartBlock');
        let imgBlock = document.getElementById('imgBlock');

        contentBlock.value = ele.content;
        contentBlock.disabled = false;
        imgBlock.src = '';
        if (ele.category == 'text') {
            selectBlock.selectedIndex = 0;
            selectBlock.options[3].hidden = true;
            textMode();
        }
        else if (ele.category == 'timer') {
            selectBlock.selectedIndex = 1;
            selectBlock.options[3].hidden = true;
            timerMode();
        }
        else { // images
            selectBlock.selectedIndex = 3;
            selectBlock.options[3].hidden = false;
            contentBlock.disabled = true;
            imgBlock.src = imagesDictionary[ele.content];
            imageMode();
        }
        colorBlock.value = ele.color ? ele.color : '#FFFFFF';

        let fontString;
        let selectedFont;
        // Image type does not have a font, use default
        if (ele.category == 'image') {
            selectedFont = "Kalam";
            // Add UUID to list of currently open images
            imagesInMenu.push(ele.content);
        }
        else {
            selectedFont = ele.font ? ele.font : 'Kalam';
        }
        fontBlock.innerHTML = '';
        for (const f of fonts) {
            fontString = `<option ${selectedFont == f ? 'selected' : ''} value="${f}">${f}</option>\n`;
            fontBlock.appendChild(htmlToElement(fontString));
        }

        timeBlock.style.color = ele.active ? 'red' : 'black';
        timeBlock.value = timeString;
        if (ele.category == 'timer' && ele.active == false) {
            timeBlock.disabled = false;
            restartBlock.checked = true;
        }
        else {
            timeBlock.disabled = true;
            restartBlock.checked = false;
        }
        if (ele.category == 'timer' && ele.active) {
            restartBlock.disabled = false;
        }
        else {
            restartBlock.disabled = true;
        }
    }
    fonts.shift();
    fonts.shift();
    fonts.shift();

    mask.style.display = "block";
    menu.style.display = "inline-block";
    menu.style.animation = "menuAnimation 0.5s forwards";
}

async function redraw() {
    // Cancel all timers
    for (const interval of intervalList) {
        clearInterval(interval);
    }
    intervalList = [];
    // Draw new elements
    for (var boxWrapper of document.getElementById("canvas").children) {
        box = boxWrapper.querySelector('.box');
        box.querySelectorAll(".box-child").forEach(e => e.remove());
        parentNode = mapping[boxWrapper.id]["elements"];
        if (parentNode.length == 0) {
            delete mapping[boxWrapper.id];
            boxWrapper.remove();
            continue;
        }
        for (const childNode of parentNode) {
            let subelement = document.createElement("div");
            subelement.classList.add("box-child");
            if (childNode["category"] == "image") {
                subelement.innerHTML = `<img src="${imagesDictionary[childNode["content"]]}" height="${window.innerHeight / 2}px" onload="resizeAfterImgLoad(this);"></img>`;
                subelement.style = `display: inline-block; pointer-events: none; transform-origin: 0 0;`;
            }
            else {
                subelement.style = `color: ${childNode["color"]}; 
                    font-size: ${(window.innerHeight / font_scale)}px; 
                    font-family: ${childNode["font"]}, cursive; display: inline-block;
                    pointer-events: none; transform-origin: 0 0;`;
                subelement.innerHTML = await replaceAsync(childNode["content"], /:([^\s:]+):/g);

                if (childNode["category"] == "timer") {
                    subelement.id = crypto.randomUUID();
                    if (childNode["active"]) {
                        startTimer(subelement.innerHTML, childNode["expiration"], subelement);
                    }
                    else {
                        let seconds = childNode["expiration"];
                        minutes = (seconds / 60) | 0;
                        seconds = (seconds % 60) | 0;
                        minutes = minutes < 10 ? "0" + minutes : minutes;
                        seconds = seconds < 10 ? "0" + seconds : seconds;
                        subelement.innerHTML += `: ${minutes}:${seconds}`;
                    }
                }
            }
            box.appendChild(subelement);
            resizeBox(box, subelement.offsetWidth * mapping[boxWrapper.id]["x-scaling"] + 4, subelement.offsetHeight * mapping[boxWrapper.id]["y-scaling"] + 4, mapping[boxWrapper.id]["x-scaling"], mapping[boxWrapper.id]["y-scaling"]);
            rotateBox(boxWrapper, mapping[boxWrapper.id]["rotation"]);
        }
    }
}

async function closeMenu(e) {
    e.stopPropagation();
    // Remove all UUIDs of open images from imagesDictionary
    for (const id of imagesInMenu) {
        delete imagesDictionary[id];
    }
    imagesInMenu = [];
    // Write to mapping dictionary
    let parentIndex = lastClickedElement.parentNode.id;
    let reference = mapping[parentIndex]["elements"];
    let content, type, color, font, time, restart, img;
    let warning = false;
    let parentNode = [];
    content = document.getElementById('contentBlock').value;
    type = document.getElementById('selectBlock').value;
    color = document.getElementById('colorBlock').value;
    font = document.getElementById('fontBlock').value;
    time = document.getElementById('timeBlock').value;
    restart = document.getElementById('restartBlock').checked;
    img = document.getElementById('imgBlock').src;

    // Validation
    let validateContent = validateInput(document.getElementById('contentBlock'), 'nonEmpty');
    let validateTime = validateInput(document.getElementById('timeBlock'), 'positiveInteger');
    if (!validateContent) {
        content = "PLACEHOLDER";
        document.getElementById('contentBlock').classList.remove("is-invalid");
    }
    if (!validateTime) {
        time = "300";
        document.getElementById('timeBlock').classList.remove("is-invalid");
    }

    if (type != "DELETE") {
        let childNode = {};
        childNode["category"] = type.toLowerCase();
        if (type == "Image") {
            childNode["content"] = crypto.randomUUID();
            // Don't directly link the entire base64 string to avoid JSON menu lag
            imagesDictionary[childNode["content"]] = img;
        }
        else {
            childNode["content"] = content;
            childNode["color"] = color.toUpperCase();
            childNode["font"] = font;
            warning = validateContent ? false : true;
        }
        if (type == "Timer") {
            warning = ((validateContent && validateTime) || !restart) ? false : true;
            childNode["active"] = !restart;
            if (restart) {
                childNode["expiration"] = parseInt(time);
                childNode["UUID"] = crypto.randomUUID();
            }
            else {// Active timer, retain expiration and UUID
                childNode["expiration"] = reference[0]["expiration"];
                childNode["UUID"] = reference[0]["UUID"];
            }
        }
        parentNode.push(childNode);
    }


    let menu = document.getElementById("menu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "auto";
    menu.style.animation = "menuAnimationReversed 0.2s forwards";
    mask.style.display = "none";
    if (warning) {
        alert("Invalid value(s) detected, using default values", "warning");
    }
    else {
        alert("Successfully validated all input values", "success");
    }
    setTimeout(() => {
        menu.style.display = "none";
        editing = false;
    }, 200);

    // Remove element if empty
    if (parentNode.length == 0) {
        delete mapping[parentIndex];
        lastClickedElement.parentNode.remove();
        lastClickedElement = null;
        elementUnfocused();
    }
    else {
        mapping[parentIndex]["elements"] = parentNode;
        await redraw();
    }
}

async function save(e) {
    e.stopPropagation();
    if (commandsView) {
        return await commandsList("KIMEXPLAINS");
    }
    if (editing) {
        return;
    }

    deleteExpiredTimers();
    let json = { "coordinates": mapping, "fonts": fonts, "images": imagesDictionary };
    alert("Please wait...", "info", true);

    fetch(`https://apoorlywrittenbot.cc/restricted/json?channel=${channel_name}`, {
        method: 'POST',
        body: JSON.stringify(json)
    })
        .then(function (response) {
            if (!response.ok) {
                document.querySelectorAll('.alert-info').forEach(e => e.remove());
                alert(`Error: Status ${String(response.status)}`, 'danger');
                throw new Error("HTTP status " + response.status);
            }
            return response.json();
        })
        .then(function (data) {
            imagesDictionary = data.images;
            document.querySelectorAll('.alert-info').forEach(e => e.remove());
            alert("Submitted successfully", "success");
        })

    elementUnfocused();
    lastClickedElement = null;
    await redraw();
}

async function clearAll(e) {
    e.stopPropagation();
    if (commandsView) {
        return await commandsList("FIERCE");
    }
    if (editing) {
        return;
    }
    mapping = {};
    document.getElementById("canvas").textContent = '';
    for (const interval of intervalList) {
        clearInterval(interval);
    }
    intervalList = [];
    elementUnfocused();
}

function showJSON(e) {
    e.stopPropagation();
    if (commandsView) {
        return;
    }
    if (editing) {
        return;
    }
    editing = true;
    let menu = document.getElementById("JSONmenu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "none";
    let video = document.getElementById('video');
    video.style.pointerEvents = 'none';

    fonts.unshift("Zrnic");
    fonts.unshift("FoxyMist");
    fonts.unshift("Kalam");
    let json = { "coordinates": mapping, "fonts": fonts };

    document.getElementById("JSONPRE").textContent = JSON.stringify(json, undefined, 2);
    fonts.shift();
    fonts.shift();
    fonts.shift();

    mask.style.display = "block";
    menu.style.display = "flex";
    menu.style.animation = "menuAnimation 0.5s forwards";
}

function closeJSON(e) {
    e.stopPropagation();
    let menu = document.getElementById("JSONmenu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "auto";
    let video = document.getElementById('video');
    video.style.pointerEvents = 'auto';
    menu.style.animation = "menuAnimationReversed 0.2s forwards";
    mask.style.display = "none";
    setTimeout(() => {
        menu.style.display = "none";
        editing = false;
    }, 200);
}

function loadFonts(e) {
    e.stopPropagation();
    if (commandsView) {
        return;
    }
    if (editing) {
        return;
    }
    editing = true;
    let menu = document.getElementById("fontsMenu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "none";
    let video = document.getElementById('video');
    video.style.pointerEvents = 'none';

    let textbox = document.getElementById("textarea-fonts");
    let fontString = "";
    for (const f of fonts) {
        fontString += `${f}\n`;
    }
    textbox.value = fontString;

    mask.style.display = "block";
    menu.style.display = "flex";
    menu.style.animation = "menuAnimation 0.5s forwards";
}

async function applyFonts(e) {
    e.stopPropagation();
    let menu = document.getElementById("fontsMenu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    let video = document.getElementById('video');
    video.style.pointerEvents = 'auto';

    fonts = document.getElementById("textarea-fonts").value.split("\n");
    fonts = fonts.filter(item => item);
    fonts = fonts.map(s => s.trim());

    WebFontConfig.google.families = fonts;
    await WebFontLoad();

    // Get rid of fonts that no longer exist
    fonts.unshift("Zrnic");
    fonts.unshift("FoxyMist");
    fonts.unshift("Kalam");
    let mapping_copy = {};
    for (let [key, value] of Object.entries(mapping)) {
        for (let i = 0; i < value.elements.length; i++) {
            if (!fonts.includes((value.elements)[i].font)) {
                (value.elements)[i].font = "Kalam";
            }
        }
        mapping_copy[key] = value;
    }
    mapping = mapping_copy;
    fonts.shift();
    fonts.shift();
    fonts.shift();

    canvas.style.pointerEvents = "auto";
    menu.style.animation = "menuAnimationReversed 0.2s forwards";
    mask.style.display = "none";
    setTimeout(() => {
        menu.style.display = "none";
        editing = false;
    }, 200);
}