var fonts = [];
var WebFontConfig = {
    google: {
        families: fonts
    },
    fontactive: function (familyName, fvd) {
        // alert(`Successfully loaded "${familyName}"`, "success");
    },
    fontinactive: function (familyName, fvd) {
        alert(`Cannot load "${familyName}"`, "warning");
        fonts = fonts.filter(e => e !== familyName)
    },
    timeout: 1500
}

var mapping = {};
var index = 0;
const font_scale = 25;

var left_INT = 0;
var width_INT = 0;

var lastClickedElement;
var editing = false;

var validationDictionary = {};
var imagesDictionary = {};
var imagesInMenu = [];
const patterns = {
    nonEmpty: /^(?!\s*$).+/,
    hex: /^[0-9A-F]{6}$/i,
    positiveInteger: /^[1-9]\d*$/,
    positiveFloat: /^(?=.+)(?:[1-9]\d*|0)?(?:\.\d+)?$/
}

var intervalList = [];
var emotes = {};

function WebFontLoad() {
    document.querySelectorAll('[href*="fonts.googleapis.com/css?"]').forEach(e => e.remove());
    if (WebFontConfig.google.families.length) {
        WebFont.load(WebFontConfig);
    }
}

function resize() {
    let video = document.getElementById('video');
    let html = document.getElementById('html');
    let sidebar = document.getElementById('sidebar');
    video.style.height = `${window.innerHeight}px`;

    width_INT = (window.innerHeight / 9.0 * 16.0 | 0);
    video.style.width = `${width_INT}px`;

    left_INT = html.clientWidth - width_INT;
    video.style.left = `${left_INT}px`;

    sidebar.style.height = video.style.height;
    sidebar.style.width = video.style.left;
}

function pasteImage(words) {
    // use event.originalEvent.clipboard for newer chrome versions
    var items = (event.clipboardData || event.originalEvent.clipboardData).items;
    // find pasted image among pasted items
    var blob = null;
    for (var i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") === 0) {
            blob = items[i].getAsFile();
        }
    }
    // load image if there is a pasted image
    if (blob !== null) {
        var reader = new FileReader();
        reader.onload = function (event) {
            let id = (words.id).substring(5);
            document.getElementById(`img${id}`).src = event.target.result;
            words.disabled = true;
            words.value = "*Size is % of Window Height*";
            words.classList.remove("is-invalid");
            validationDictionary[words.id] = true;
            let select = document.getElementById(`select${id}`);
            select.options[3].removeAttribute("hidden");
            select.options[3].setAttribute('selected', 'true');
            select.value = "Image";
        };
        reader.readAsDataURL(blob);
    }
}

window.onload = async function () {
    document.body.style.overflow = 'hidden';
    resize();

    let helpButton = document.getElementById("helpButton");
    helpButton.addEventListener("click", help);

    let newButton = document.getElementById("newButton");
    newButton.addEventListener("click", create);

    let editButton = document.getElementById("editButton");
    editButton.addEventListener("click", edit);

    let saveButton = document.getElementById("saveButton");
    saveButton.addEventListener("click", save);

    let clearButton = document.getElementById("clearButton");
    clearButton.addEventListener("click", clearAll);

    let jsonButton = document.getElementById("jsonButton");
    jsonButton.addEventListener("click", showJSON);

    let fontsButton = document.getElementById("fontsButton");
    fontsButton.addEventListener("click", loadFonts);

    let video = document.getElementById('video');

    let response = await fetch("https://apoorlywrittenbot.cc/public/json/mike_hu_0_0");
    if (!response.ok) {
        throw new Error("HTTP status " + response.status);
    }
    let data = await response.json();
    let count = 0;
    for (const [key, value] of Object.entries(data.coordinates)) {
        let element = create(null);
        element.style.top = `${value.top / 100.0 * window.innerHeight}px`;
        element.style.left = `${value.left / 100.0 * parseFloat(video.style.width) + parseFloat(video.style.left)}px`;
    }
    fonts = data.fonts;
    WebFontConfig.google.families = fonts;
    WebFontLoad();
    // Reset index
    for (const [key, value] of Object.entries(data.coordinates)) {
        mapping[count.toString()] = value;
        count++;
    }
    imagesDictionary = data.images;
    deleteExpiredTimers();
    elementUnfocused();
    video.src = "https://player.twitch.tv/?channel=mike_hu_0_0&parent=apoorlywrittenbot.cc&allowfullscreen=false&muted=true&autoplay=true&controls=false";
    await redraw();
}
window.onresize = function () {
    resize();
}


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

function elementUnfocused() {
    if (lastClickedElement != null) {
        lastClickedElement.style.border = '2px solid transparent';
    }
    let editButton = document.getElementById("editButton");
    editButton.disabled = true;
    if (!editing) {
        let video = document.getElementById('video');
        video.style.pointerEvents = 'auto';
    }
    editButton.style.background = "#d9d9d9";
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

function elementFocused(element, event) {
    //Unfocus last element
    if (lastClickedElement != null) {
        lastClickedElement.style.border = '2px solid transparent';
    }

    element.style.border = '2px solid #ff6600';
    lastClickedElement = element;

    let editButton = document.getElementById("editButton");
    editButton.disabled = false;
    editButton.style.background = "#6441a5";
    let video = document.getElementById('video');
    video.style.pointerEvents = 'none';

    dragging.startMoving(element, 'video', event);
}

function htmlToElement(html) {
    var template = document.createElement('template');
    html = html.trim();
    template.innerHTML = html;
    return template.content.firstChild;
}

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

function selectTrigger(select) {
    let type = select.value;
    let id = (select.id).substring(6);
    let time = document.getElementById(`time${id}`);
    let restart = document.getElementById(`restart${id}`);
    let img = document.getElementById(`img${id}`);
    let words = document.getElementById(`words${id}`);
    words.disabled = false;
    document.getElementById(`select${id}`).options[3].setAttribute('hidden', 'true');
    img.src = "";
    if (type == "Timer") {
        time.disabled = false;
        time.value = "";
        time.style.color = "black";
        restart.disabled = true;
        restart.checked = true;
        validationDictionary[`time${id}`] = false;
        time.classList.add("is-invalid");
    }
    else {
        time.disabled = true;
        time.value = "-";
        time.style.color = "black";
        restart.disabled = true;
        restart.checked = false;
        validationDictionary[`time${id}`] = true;
        time.classList.remove("is-invalid");
    }
}

function checkboxTrigger(checkbox) {
    let id = (checkbox.id).substring(7);
    let time = document.getElementById(`time${id}`);
    if (checkbox.checked) {
        time.value = "";
        time.style.color = "black";
        time.disabled = false;
        validationDictionary[`time${id}`] = false;
        time.classList.add("is-invalid");
    }
    else {
        time.value = "ACTIVE";
        time.style.color = "red";
        time.disabled = true;
        validationDictionary[`time${id}`] = true;
        time.classList.remove("is-invalid");
    }
}

const alert = (message, type, permanent = false) => {
    const wrapper = document.createElement('div')
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible" role="alert" style="z-index:99;">`,
        `   <div>${message}</div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>'
    ].join('');

    let alertPlaceholder = document.getElementById('liveAlertPlaceholder');
    alertPlaceholder.append(wrapper);
    if (permanent == false) {
        setTimeout(() => {
            wrapper.remove();
        }, 3000);
    }
}

function validateInput(input, pattern) {
    if (patterns[pattern].test(input.value)) {
        input.classList.remove("is-invalid");
        validationDictionary[input.id] = true;
    } else {
        input.classList.add("is-invalid");
        validationDictionary[input.id] = false;
    }
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
        let imgPlaceholder = htmlToElement(`<img id="img${index}" style="display:block;margin-left:auto;margin-right:auto;width:100%;" src="${ele.category == 'image' ? imagesDictionary[ele.content] : ''}"></img>`);
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
    let imgPlaceholder = htmlToElement(`<img id="img${index}" style="display:block;margin-left:auto;margin-right:auto;width:100%;"></img>`);
    tableBody.appendChild(imgPlaceholder);
    validationDictionary[`words${index}`] = false;
    validationDictionary[`color${index}`] = true;
    validationDictionary[`size${index}`] = true;
    validationDictionary[`time${index}`] = true;
}

async function getImg(emoteName, size) {
    if (emotes[emoteName]) {
        return new Promise((res, rej) => {
            res(`<img src="https://static-cdn.jtvnw.net/emoticons/v2/${emotes[emoteName]}/dark/3.0" 
                                style="pointer-events: none; height: ${(window.innerHeight / font_scale) / 50 * size}px;">`);
        });
    }
    else {
        let response = await fetch(`https://apoorlywrittenbot.cc/public/emote?name=${emoteName}`);
        if (!response.ok) {
            return new Promise((res, rej) => {
                res(emoteName);
            });
        }
        let data = await response.json();
        emotes[emoteName] = data.id;
        return new Promise((res, rej) => {
            res(`<img src="https://static-cdn.jtvnw.net/emoticons/v2/${emotes[emoteName]}/dark/3.0" 
                                style="pointer-events: none; height: ${(window.innerHeight / font_scale) / 50 * size}px;">`);
        });
    }
}

async function replaceAsync(str, regex, size) {
    const promises = [];
    str.replace(regex, (match, key) => {
        const promise = getImg(key, size);
        promises.push(promise);
    });
    const data = await Promise.all(promises);
    return str.replace(regex, () => data.shift());
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

function deleteExpiredTimers() {
    // Activate timers and throw out expired ones
    for (var [index, element] of Object.entries(mapping)) {
        let j = (element.elements).length;
        let now = ((Date.now() / 1000) | 0);
        element.now = now;
        for (let i = 0; i < j; i++) {
            if ((element.elements)[i]["expiration"] != null) {
                if ((element.elements)[i]["active"]) {
                    if ((element.elements)[i]["expiration"] - 30 <= now) {
                        (element.elements).splice(i, 1);
                        i--;
                        j--;
                    }
                }
                else {
                    (element.elements)[i]["active"] = true;
                    (element.elements)[i]["expiration"] += (30 + now);
                }
            }
        }
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

    fetch("https://apoorlywrittenbot.cc/restricted/mike_hu_0_0/json", {
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

function startTimer(timerText, expiration, element) {
    var diff, TTL, minutes, seconds, timerIntervalID;
    function timer() {
        TTL = expiration - ((Date.now() / 1000) | 0);
        diff = TTL - 30;

        minutes = (diff / 60) | 0;
        seconds = (diff % 60) | 0;

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        if (diff <= 0) {
            element.innerHTML = `${timerText}: DONE`;
            clearInterval(timerIntervalID);
        }
        else {
            element.innerHTML = `${timerText}: ${minutes}:${seconds}`;
        }
    };
    timer();
    timerIntervalID = setInterval(timer, 1000);
    intervalList.push(timerIntervalID);
}