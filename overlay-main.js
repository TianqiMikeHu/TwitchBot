window.onload = async function () {
    resize();
    InitializeEventListeners();
    setChannel();
    InitializeColorPicler();

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
    if (isEscape) {
        elementUnfocused();
    }
    else if (isDelete && lastClickedElement != null) {
        let index = lastClickedElement.parentNode.id;
        let element_json = mapping[index];
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
        delete mapping[index];
        lastClickedElement.parentNode.remove();
        lastClickedElement = null;
        elementUnfocused();
    }
};

function help(e) {
    e.stopPropagation();
    if (editing) {
        return;
    }
    window.open('https://www.youtube.com/watch?v=6N9nNLtI9A0', '_blank').focus();
}

function create(e) {
    if (e) {
        e.stopPropagation();
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

function edit(e) {
    e.stopPropagation();
    if (editing) {
        return;
    }
    editing = true;
    let menu = document.getElementById("menu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "none";

    let element_json = mapping[lastClickedElement.parentNode.id];

    let index = 0;
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

        index += 1;
    }
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
    let index = lastClickedElement.parentNode.id;
    let reference = mapping[index]["elements"];
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
        delete mapping[index];
        lastClickedElement.parentNode.remove();
        lastClickedElement = null;
        elementUnfocused();
    }
    else {
        mapping[index]["elements"] = parentNode;
        await redraw();
    }
}

async function save(e) {
    e.stopPropagation();
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

function clearAll(e) {
    e.stopPropagation();
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
    if (editing) {
        return;
    }
    editing = true;
    let menu = document.getElementById("JSONmenu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "none";

    fonts.unshift("FoxyMist");
    fonts.unshift("Kalam");
    let json = { "coordinates": mapping, "fonts": fonts };

    document.getElementById("JSONPRE").textContent = JSON.stringify(json, undefined, 2);
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
    menu.style.animation = "menuAnimationReversed 0.2s forwards";
    mask.style.display = "none";
    setTimeout(() => {
        menu.style.display = "none";
        editing = false;
    }, 200);
}

function loadFonts(e) {
    e.stopPropagation();
    if (editing) {
        return;
    }
    editing = true;
    let menu = document.getElementById("fontsMenu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "none";

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

    fonts = document.getElementById("textarea-fonts").value.split("\n");
    fonts = fonts.filter(item => item);
    fonts = fonts.map(s => s.trim());

    WebFontConfig.google.families = fonts;
    WebFontLoad();

    // Get rid of fonts that no longer exist
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

    canvas.style.pointerEvents = "auto";
    menu.style.animation = "menuAnimationReversed 0.2s forwards";
    mask.style.display = "none";
    setTimeout(() => {
        menu.style.display = "none";
        editing = false;
    }, 200);
}