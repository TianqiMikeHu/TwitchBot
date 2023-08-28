window.onload = async function () {
    resize();
    InitializeEventListeners();
    setChannel();

    let video = document.getElementById('video');
    video.src = `https://player.twitch.tv/?channel=${channel_name}&parent=apoorlywrittenbot.cc&allowfullscreen=false&muted=true&autoplay=true&controls=false`;

    await loadInitialJSON(video);
    deleteExpiredTimers();
    elementUnfocused();
    await redraw();
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
        let index = lastClickedElement.id;
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
        lastClickedElement.remove();
        lastClickedElement = null;
        elementUnfocused();
    }
};

var dragging = function () {
    return {
        move: function (divid, xpos, ypos) {
            divid.style.left = xpos + 'px';
            divid.style.top = ypos + 'px';
        },
        startMoving: function (divid, container, evt) {
            evt = evt || window.event;
            let rect = divid.getBoundingClientRect();
            let video = document.getElementById(container);
            var posX = evt.clientX,
                posY = evt.clientY,
                divTop = divid.style.top,
                divLeft = divid.style.left,
                eWi = parseInt(rect.width),
                eHe = parseInt(rect.height),
                cL = parseInt(video.style.left),
                cWi = parseInt(video.style.width),
                cHe = parseInt(video.style.height);
            document.getElementById(container).style.cursor = 'move';
            divTop = divTop.replace('px', '');
            divLeft = divLeft.replace('px', '');
            var diffX = posX - divLeft,
                diffY = posY - divTop;

            document.onmousemove = function (evt) {
                evt = evt || window.event;
                var posX = evt.clientX,
                    posY = evt.clientY,
                    aX = posX - diffX,
                    aY = posY - diffY;
                if (aX < cL) aX = cL;
                if (aY < 0) aY = 0;
                if (aX + eWi > (cL + cWi)) aX = cL + cWi - eWi;
                if (aY + eHe > cHe) aY = cHe - eHe;
                dragging.move(divid, aX, aY);
            }
        },
        stopMoving: function (divid, container) {
            let video = document.getElementById(container);
            video.style.cursor = 'default';
            mapping[divid.id]["top"] = Math.round(parseFloat(divid.style.top) * 100.0 / window.innerHeight * 1000) / 1000;
            mapping[divid.id]["left"] = Math.round((parseFloat(divid.style.left) - parseFloat(video.style.left)) * 100.0 / parseFloat(video.style.width) * 1000) / 1000;
            document.onmousemove = function () { }
        },
    }
}();

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
    let divString = `<div id="${index.toString()}" 
            style="position: absolute; top: ${window.innerHeight / 2}px; left: ${left_INT + width_INT / 2}px; white-space: nowrap; line-height: 1.0;
            -webkit-user-select: none;
            -moz-user-select: none;
            -o-user-select: none;
            -ms-user-select: none;
            -khtml-user-select: none;
            user-select: none;" 
            onmousedown="elementFocused(this, event);" 
            onmouseup="dragging.stopMoving(this, 'video');"></div>`;
    let element = htmlToElement(divString);
    element.style.border = '2px solid #ff6600';

    index += 1;
    document.getElementById('canvas').appendChild(element);

    // Autofocus on new element
    if (lastClickedElement != null) {
        lastClickedElement.style.border = '2px solid transparent';
    }
    lastClickedElement = element;
    let editButton = document.getElementById("editButton");
    editButton.disabled = false;
    editButton.style.background = "#6441a5";
    let video = document.getElementById('video');
    video.style.pointerEvents = 'none';

    let subelement = document.createElement("div");
    subelement.style = `color: #FFFFFF; font-size: ${window.innerHeight / font_scale}px;`;
    subelement.textContent = "PLACEHOLDER";
    document.getElementById(element.id).appendChild(subelement);

    element_json = {
        top: 50,
        left: 50,
        now: ((Date.now() / 1000) | 0),
        elements: [
            {
                category: 'text',
                content: 'PLACEHOLDER',
                color: 'FFFFFF',
                size: '100',
                font: 'Kalam'
            }
        ]
    };
    mapping[element.id] = element_json;

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
    let tableBody = document.getElementById("tableBody");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "none";
    tableBody.textContent = '';
    validationDictionary = {};

    let element_json = mapping[lastClickedElement.id];

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

        let fontString = "";
        let selectedFont = "";
        // Image type does not have a font, use default
        if (ele.category == 'image') {
            selectedFont = "Kalam";
            // Add UUID to list of currently open images
            imagesInMenu.push(ele.content);
        }
        else {
            selectedFont = ele.font;
        }
        for (const f of fonts) {
            fontString += `<option ${selectedFont == f ? 'selected' : ''} value="${f}">${f}</option>\n`;
        }

        let divString = `<div class="tableRow mb-2" style="height: 12%">
                <div class="wordsColumn d-flex justify-content-center" style="height: 12%;">
                    <input type="text" style="resize: none;"" class="form-control needs-validation rounded-0" id="words${index}" placeholder="PLACEHOLDER" 
                    value="${ele.category == 'image' ? '*Size is % of Window Height*' : ele.content}"
                    onkeyup="validateInput(this, 'nonEmpty');" onpaste="pasteImage(this);" ${ele.category == 'image' ? 'disabled' : ''}></input>
                </div>
                <div class="typeColumn d-flex justify-content-center" style="height: 12%;">
                    <select class="form-select rounded-0" id="select${index}" onchange="selectTrigger(this);">
                        <option ${ele.category == 'text' ? 'selected' : ''} value="Text">Text</option>
                        <option ${ele.category == 'timer' ? 'selected' : ''} value="Timer">Timer</option>
                        <option value="DELETE">DELETE</option>
                        <option ${ele.category == 'image' ? 'selected' : ''} value="Image" ${ele.category == 'image' ? '' : 'hidden'}>Image</option>
                      </select>
                </div>
                <div class="colorColumn d-flex justify-content-center" style="height: 12%;">
                    <div class="input-group">
                        <span class="input-group-text rounded-0" id="color${index}Prepend">#</span>
                        <input type="text" class="form-control needs-validation rounded-0" id="color${index}"
                            aria-describedby="color${index}Prepend" placeholder="FFFFFF" value="${ele.category == 'image' ? 'FFFFFF' : ele.color}"
                            onkeyup="validateInput(this, 'hex');">
                    </div>
                </div>
                <div class="sizeColumn d-flex justify-content-center" style="height: 12%;">
                    <div class="input-group">
                        <input type="text" class="form-control needs-validation rounded-0" id="size${index}"
                            aria-describedby="size${index}Postpend" placeholder="100" value="${ele.size}"
                            onkeyup="validateInput(this, 'positiveFloat');">
                        <span class="input-group-text rounded-0" id="size${index}Postpend">%</span>
                    </div>
                </div>
                <div class="fontColumn d-flex justify-content-center" style="height: 12%;">
                    <select class="form-select rounded-0" id="selectFont${index}"">
                        ${fontString}
                      </select>
                </div>
                <div class="timeColumn d-flex justify-content-center" style="height: 12%;">
                    <div class="input-group">
                        <input type="text" class="form-control needs-validation rounded-0" id="time${index}"
                            aria-describedby="time${index}Postpend" style="color:${ele.active ? 'red' : 'black'}"
                            placeholder="300" value=${timeString} ${ele.category == 'timer' && ele.active == false ? '' : 'disabled'}
                            onkeyup="validateInput(this, 'positiveInteger');">
                        <span class="input-group-text rounded-0" id="time${index}Postpend">s</span>
                    </div>
                </div>
                <div class="restartColumn d-flex align-items-center justify-content-center" style="height: 12%; background-color: white;">
                    <input type="checkbox" class="form-check-input form-control needs-validation rounded-0" id="restart${index}" 
                        style="width: 100%; height: 100%; margin: 0px;" onchange="checkboxTrigger(this);"
                        ${ele.category == 'timer' && ele.active ? '' : 'disabled'} ${ele.category == 'timer' && ele.active == false ? 'checked' : ''}>
                </div>
            </div>`;


        let tableRow = htmlToElement(divString);
        tableBody.appendChild(tableRow);
        let imgPlaceholder = htmlToElement(`<img id="img${index}" class="menuImage" src="${ele.category == 'image' ? imagesDictionary[ele.content] : ''}"></img>`);
        tableBody.appendChild(imgPlaceholder);
        validationDictionary[`words${index}`] = true;
        validationDictionary[`color${index}`] = true;
        validationDictionary[`size${index}`] = true;
        validationDictionary[`time${index}`] = true;
        index += 1;
    }
    fonts.shift();
    fonts.shift();

    mask.style.display = "block";
    menu.style.display = "flex";
    menu.style.animation = "menuAnimation 0.5s";
}

function subelement(e) {
    e.stopPropagation();
    let tableBody = document.getElementById("tableBody");
    let index = (tableBody.childElementCount) / 2;
    fonts.unshift("FoxyMist");
    fonts.unshift("Kalam");
    let fontString = "";
    for (const f of fonts) {
        fontString += `<option ${"Kalam" == f ? 'selected' : ''} value="${f}">${f}</option>\n`;
    }

    let divString = `<div class="tableRow mb-2" style="height: 12%">
                <div class="wordsColumn d-flex justify-content-center" style="height: 12%;">
                    <input type="text" style="resize: none;"" class="form-control needs-validation rounded-0 is-invalid" id="words${index}" placeholder="PLACEHOLDER"
                    onkeyup="validateInput(this, 'nonEmpty');" onpaste="pasteImage(this);"></input>
                </div>
                <div class="typeColumn d-flex justify-content-center" style="height: 12%;">
                    <select class="form-select rounded-0" id="select${index}" onchange="selectTrigger(this);">
                        <option selected value="Text">Text</option>
                        <option value="Timer">Timer</option>
                        <option value="DELETE">DELETE</option>
                        <option value="Image" hidden>Image</option>
                      </select>
                </div>
                <div class="colorColumn d-flex justify-content-center" style="height: 12%;">
                    <div class="input-group">
                        <span class="input-group-text rounded-0" id="color${index}Prepend">#</span>
                        <input type="text" class="form-control needs-validation rounded-0" id="color${index}"
                            aria-describedby="color${index}Prepend" placeholder="FFFFFF" value="FFFFFF"
                            onkeyup="validateInput(this, 'hex');">
                    </div>
                </div>
                <div class="sizeColumn d-flex justify-content-center" style="height: 12%;">
                    <div class="input-group">
                        <input type="text" class="form-control needs-validation rounded-0" id="size${index}"
                            aria-describedby="size${index}Postpend" placeholder="100" value="100"
                            onkeyup="validateInput(this, 'positiveFloat');">
                        <span class="input-group-text rounded-0" id="size${index}Postpend">%</span>
                    </div>
                </div>
                <div class="fontColumn d-flex justify-content-center" style="height: 12%;">
                    <select class="form-select rounded-0" id="selectFont${index}"">
                        ${fontString}
                      </select>
                </div>
                <div class="timeColumn d-flex justify-content-center" style="height: 12%;">
                    <div class="input-group">
                        <input type="text" class="form-control needs-validation rounded-0" id="time${index}"
                            aria-describedby="time${index}Postpend" style="color:black"
                            placeholder="300" value="-" disabled
                            onkeyup="validateInput(this, 'positiveInteger');">
                        <span class="input-group-text rounded-0" id="time${index}Postpend">s</span>
                    </div>
                </div>
                <div class="restartColumn d-flex align-items-center justify-content-center" style="height: 12%; background-color: white;">
                    <input type="checkbox" class="form-check-input form-control needs-validation rounded-0" id="restart${index}" 
                        style="width: 100%; height: 100%; margin: 0px;" onchange="checkboxTrigger(this);"
                        disabled>
                </div>
            </div>`;

    fonts.shift();
    fonts.shift();
    let tableRow = htmlToElement(divString);
    tableBody.appendChild(tableRow);
    let imgPlaceholder = htmlToElement(`<img id="img${index}" class="menuImage"></img>`);
    tableBody.appendChild(imgPlaceholder);
    validationDictionary[`words${index}`] = false;
    validationDictionary[`color${index}`] = true;
    validationDictionary[`size${index}`] = true;
    validationDictionary[`time${index}`] = true;
}

async function redraw() {
    // Cancel all timers
    for (const interval of intervalList) {
        clearInterval(interval);
    }
    intervalList = [];
    // Draw new elements
    for (var element of document.getElementById("canvas").children) {
        element.innerHTML = '';
        parentNode = mapping[element.id]["elements"];
        if (parentNode.length == 0) {
            delete mapping[element.id];
            element.remove();
            continue;
        }
        for (const childNode of parentNode) {
            let subelement = document.createElement("div");
            if (childNode["category"] == "image") {
                subelement.innerHTML = `<img src="${imagesDictionary[childNode["content"]]}" height="${window.innerHeight / 100 * childNode["size"]}px" style="pointer-events:none;"></img>`;
            }
            else {
                subelement.style = `color: #${childNode["color"]}; font-size: ${(window.innerHeight / font_scale) / 100 * childNode["size"]}px; font-family: ${childNode["font"]}, cursive;`;
                subelement.innerHTML = await replaceAsync(childNode["content"], /:([^\s:]+):/g, childNode["size"]);

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
            element.appendChild(subelement);
        }
    }
}

async function closemenu(e) {
    e.stopPropagation();
    for (const [key, value] of Object.entries(validationDictionary)) {
        if (!value) {
            alert("Please fix the invalid value(s)", "warning");
            return;
        }
    }
    // Remove all UUIDs of open images from imagesDictionary
    for (const id of imagesInMenu) {
        delete imagesDictionary[id];
    }
    imagesInMenu = [];
    // Write to mapping dictionary
    let index = lastClickedElement.id;
    let reference = mapping[index]["elements"];
    let words, type, color, size, time, restart, img;
    let parentNode = [];
    for (let i = 0; i < (tableBody.childElementCount) / 2; i++) {  // row iteration
        words = document.getElementById(`words${i}`).value;
        type = document.getElementById(`select${i}`).value;
        color = document.getElementById(`color${i}`).value;
        size = document.getElementById(`size${i}`).value;
        font = document.getElementById(`selectFont${i}`).value;
        time = document.getElementById(`time${i}`).value;
        restart = document.getElementById(`restart${i}`).checked;
        img = document.getElementById(`img${i}`).src;
        if (type == "DELETE") {
            continue;
        }
        let childNode = {};
        childNode["category"] = type.toLowerCase();
        if (type == "Image") {
            childNode["content"] = crypto.randomUUID();
            // Don't directly link the entire base64 string to avoid JSON menu lag
            imagesDictionary[childNode["content"]] = img;
        }
        else {
            childNode["content"] = words;
            childNode["color"] = color.toUpperCase();
            childNode["font"] = font;
        }
        childNode["size"] = size;
        if (type == "Timer") {
            childNode["active"] = !restart;
            if (restart) {
                childNode["expiration"] = parseInt(time);
                childNode["UUID"] = crypto.randomUUID();
            }
            else {// Active timer, retain expiration and UUID
                childNode["expiration"] = reference[i]["expiration"];
                childNode["UUID"] = reference[i]["UUID"];
            }
        }
        parentNode.push(childNode);
    }

    let menu = document.getElementById("menu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "auto";
    menu.style.animation = "menuAnimationReversed 0.2s";
    mask.style.display = "none";
    alert("Successfully validated all input values", "success");
    setTimeout(() => {
        menu.style.display = "none";
        editing = false;
    }, 200);

    // Remove element if empty
    if (parentNode.length == 0) {
        delete mapping[index];
        lastClickedElement.remove();
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

    fetch(`https://apoorlywrittenbot.cc/restricted/${channel_name}/json`, {
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
    menu.style.animation = "menuAnimation 0.5s";
}

function closeJSON(e) {
    e.stopPropagation();
    let menu = document.getElementById("JSONmenu");
    let mask = document.getElementById("mask");
    let canvas = document.getElementById("canvas");
    canvas.style.pointerEvents = "auto";
    menu.style.animation = "menuAnimationReversed 0.2s";
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
    menu.style.animation = "menuAnimation 0.5s";
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
    menu.style.animation = "menuAnimationReversed 0.2s";
    mask.style.display = "none";
    setTimeout(() => {
        menu.style.display = "none";
        editing = false;
    }, 200);
    await redraw();
}