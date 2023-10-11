function setChannel() {
    const params = new Proxy(new URLSearchParams(window.location.search), {
        get: (searchParams, prop) => searchParams.get(prop),
    });
    channel_name = params.channel;
}

function convertRemToPixels(rem) {
    return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

function InitializeColorPicker() {
    Coloris({
        themeMode: 'dark',
        clearButton: true
    });
}

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
    let staticBackground = document.getElementById('staticBackground');

    video.style.height = `${window.innerHeight}px`;
    staticBackground.style.height = `${window.innerHeight}px`;

    width_INT = (window.innerHeight / 9.0 * 16.0 | 0);
    video.style.width = `${width_INT}px`;
    staticBackground.style.width = `${width_INT}px`;

    left_INT = html.clientWidth - width_INT;
    video.style.left = `${left_INT}px`;
    staticBackground.style.left = `${left_INT}px`;

    sidebar.style.height = video.style.height;
    sidebar.style.width = video.style.left;

    // Scrollable menus
    document.getElementById('menu').style.height = `${window.innerHeight * .75}px`;
    document.getElementById('menuScrollable').style.height = `${window.innerHeight * .75 - convertRemToPixels(4)}px`;

    document.getElementById('JSONmenu').style.height = `${window.innerHeight * .9}px`;
    document.getElementById('JSONmenuScrollable').style.height = `${window.innerHeight * .9 - convertRemToPixels(4)}px`;

    document.getElementById('commandsView').style.left = video.style.left;
    document.getElementById('commandsView').style.height = `${window.innerHeight - 60}px`;
    document.getElementById('commandsView').style.width = `${(width_INT - 120) * 0.25}px`;

    document.getElementById('commandsList').style.height = `${window.innerHeight - 60 - convertRemToPixels(4)}px`;
    document.getElementById('commandsList').style.width = `${(width_INT - 120) * 0.25}px`;

    document.getElementById('commandsDetails').style.height = `${window.innerHeight - 60}px`;
    document.getElementById('commandsDetailsScrollable').style.height = `${window.innerHeight - 60 - convertRemToPixels(4)}px`;
    document.getElementById('commandsDetails').style.width = `${(width_INT - 120) * 0.75}px`;
}

function setSidebarColor(button) {
    button.style.background = sidebarCurrentColor;
}

function textMode() {
    let timeBlockParent = document.getElementById('timeBlockParent');
    let restartBlockParent = document.getElementById('restartBlockParent');
    let colorBlockParent = document.getElementById('colorBlockParent');
    let fontBlockParent = document.getElementById('fontBlockParent');

    colorBlockParent.classList.add('d-block');
    colorBlockParent.classList.remove('d-none');
    fontBlockParent.classList.add('d-block');
    fontBlockParent.classList.remove('d-none');
    timeBlockParent.classList.remove('d-block');
    timeBlockParent.classList.add('d-none');
    restartBlockParent.classList.remove('d-flex');
    restartBlockParent.classList.add('d-none');
}

function timerMode() {
    let timeBlockParent = document.getElementById('timeBlockParent');
    let restartBlockParent = document.getElementById('restartBlockParent');
    let colorBlockParent = document.getElementById('colorBlockParent');
    let fontBlockParent = document.getElementById('fontBlockParent');

    colorBlockParent.classList.add('d-block');
    colorBlockParent.classList.remove('d-none');
    fontBlockParent.classList.add('d-block');
    fontBlockParent.classList.remove('d-none');
    timeBlockParent.classList.add('d-block');
    timeBlockParent.classList.remove('d-none');
    restartBlockParent.classList.add('d-flex');
    restartBlockParent.classList.remove('d-none');
}

function imageMode() {
    let timeBlockParent = document.getElementById('timeBlockParent');
    let restartBlockParent = document.getElementById('restartBlockParent');
    let colorBlockParent = document.getElementById('colorBlockParent');
    let fontBlockParent = document.getElementById('fontBlockParent');

    timeBlockParent.classList.remove('d-block');
    timeBlockParent.classList.add('d-none');
    restartBlockParent.classList.remove('d-flex');
    restartBlockParent.classList.add('d-none');
    colorBlockParent.classList.remove('d-block');
    colorBlockParent.classList.add('d-none');
    fontBlockParent.classList.remove('d-block');
    fontBlockParent.classList.add('d-none');
}

function pasteImage(content) {
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
            let imgBlock = document.getElementById(`imgBlock`);
            imgBlock.src = event.target.result;
            content.disabled = true;
            content.value = "*Change Type to remove image*";
            content.classList.remove("is-invalid");
            let select = document.getElementById('selectBlock');
            select.options[3].removeAttribute("hidden");
            select.options[3].setAttribute('selected', 'true');
            select.value = "Image";
            imageMode();
        };
        reader.readAsDataURL(blob);
    }
}

function resizeMenuImg(img) {
    if (img.height > img.width) {
        img.style.width = `${img.width / img.height * 100}%`;
    }
    else {
        img.style.width = '100%';
    }
}

function InitializeEventListeners() {
    let switchButton = document.getElementById("switchButton");
    switchButton.addEventListener("click", switchView);

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
}

async function loadInitialJSON(video) {
    let response = await fetch(`https://apoorlywrittenbot.cc/public/json?channel=${channel_name}`);
    if (!response.ok) {
        throw new Error("HTTP status " + response.status);
    }
    let data = await response.json();
    for (const [key, value] of Object.entries(data.coordinates)) {
        let element = await create(null);
        element.style.top = `${value.top / 100.0 * window.innerHeight}px`;
        element.style.left = `${value.left / 100.0 * parseFloat(video.style.width) + parseFloat(video.style.left)}px`;
    }
    fonts = data.fonts;
    WebFontConfig.google.families = fonts;
    WebFontLoad();
    // Reset index
    let count = 0;
    for (const [key, value] of Object.entries(data.coordinates)) {
        mapping[count.toString()] = value;
        count++;
    }
    imagesDictionary = data.images;
}

// Modifies lastClickedElement
function displayBorder(visible) {
    lastClickedElement.style.border = `2px solid ${visible ? borderColor : 'transparent'}`;
    for (var child of lastClickedElement.querySelectorAll('.dot')) {
        child.style.display = `${visible ? 'flex' : 'none'}`;
    }
    lastClickedElement.querySelector('.rotate-link').style.display = `${visible ? 'flex' : 'none'}`;
}

function elementUnfocused() {
    if (lastClickedElement != null) {
        displayBorder(false);
    }
    let editButton = document.getElementById("editButton");
    editButton.disabled = true;
    if (!editing) {
        let video = document.getElementById('video');
        video.style.pointerEvents = 'auto';
    }
    // editButton.style.background = "#d9d9d9";
}

function elementFocused(event, element) {
    //Unfocus last element
    if (lastClickedElement != null) {
        displayBorder(false);
    }

    lastClickedElement = element;
    displayBorder(true);

    let editButton = document.getElementById("editButton");
    editButton.disabled = false;
    editButton.style.background = sidebarDefaultColor;
    let video = document.getElementById('video');
    video.style.pointerEvents = 'none';
}

function htmlToElement(html) {
    var template = document.createElement('template');
    html = html.trim();
    template.innerHTML = html;
    return template.content.firstChild;
}

function selectTrigger(select) {
    let type = select.value;
    let time = document.getElementById('timeBlock');
    let restart = document.getElementById('restartBlock');
    let img = document.getElementById('imgBlock');
    let content = document.getElementById('contentBlock');
    content.disabled = false;
    img.src = "";
    select.options[3].setAttribute('hidden', 'true');
    if (type == "DELETE") {
        return;
    }
    else if (type == "Timer") {
        timerMode();
        time.value = "";
        time.style.color = "black";
        restart.disabled = true;
        time.disabled = false;
        restart.checked = true;
        time.classList.add("is-invalid");
    }
    else {
        textMode();
        time.style.color = "black";
        restart.disabled = true;
        restart.checked = false;
        time.classList.remove("is-invalid");
    }
}

function checkboxTrigger(checkbox) {
    let time = document.getElementById('timeBlock');
    if (checkbox.checked) {
        time.value = "";
        time.style.color = "black";
        time.disabled = false;
        time.classList.add("is-invalid");
    }
    else {
        time.value = "ACTIVE";
        time.style.color = "red";
        time.disabled = true;
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
        return true;
    } else {
        input.classList.add("is-invalid");
        return false;
    }
}

async function getImg(emoteName) {
    if (emotes[emoteName]) {
        return new Promise((res, rej) => {
            res(`<img src="https://static-cdn.jtvnw.net/emoticons/v2/${emotes[emoteName]}/dark/3.0" 
                                style="pointer-events: none; height: ${(window.innerHeight / font_scale) * 2}px;">`);
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
                                style="pointer-events: none; height: ${(window.innerHeight / font_scale) * 2}px;" onload="resizeAfterImgLoad(this);">`);
        });
    }
}

async function replaceAsync(str, regex) {
    const promises = [];
    str.replace(regex, (match, key) => {
        const promise = getImg(key);
        promises.push(promise);
    });
    const data = await Promise.all(promises);
    return str.replace(regex, () => data.shift());
}

function resizeAfterImgLoad(img) {
    let id = img.parentNode.parentNode.parentNode.id; // img->box-child->box->boxWrapper
    resizeBox(img.parentNode.parentNode, img.parentNode.offsetWidth * mapping[id]["x-scaling"] + 4, img.parentNode.offsetHeight * mapping[id]["y-scaling"] + 4, mapping[id]["x-scaling"], mapping[id]["y-scaling"]);
}

function deleteExpiredTimers() {
    // Activate timers and throw out expired ones
    for (var [objIndex, element] of Object.entries(mapping)) {
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

//////////////////////////
function addDotsListeners(boxIndex) {
    let box = document.getElementById(`box-${boxIndex.toString()}`);
    let boxWrapper = document.getElementById(`${boxIndex.toString()}`);

    let rightMid = document.getElementById(`right-mid-${boxIndex.toString()}`);
    let leftMid = document.getElementById(`left-mid-${boxIndex.toString()}`);
    let topMid = document.getElementById(`top-mid-${boxIndex.toString()}`);
    let bottomMid = document.getElementById(`bottom-mid-${boxIndex.toString()}`);

    let leftTop = document.getElementById(`left-top-${boxIndex.toString()}`);
    let rightTop = document.getElementById(`right-top-${boxIndex.toString()}`);
    let rightBottom = document.getElementById(`right-bottom-${boxIndex.toString()}`);
    let leftBottom = document.getElementById(`left-bottom-${boxIndex.toString()}`);
    let rotate = document.getElementById(`rotate-${boxIndex.toString()}`);

    boxWrapper.addEventListener('mousedown', e => dragHandler(e, boxWrapper), false);
    box.addEventListener('mousedown', e => elementFocused(e, box), false);
    rightMid.addEventListener('mousedown', e => resizeHandler(e, boxWrapper, box, false, false, true, false));
    leftMid.addEventListener('mousedown', e => resizeHandler(e, boxWrapper, box, true, false, true, false));
    topMid.addEventListener('mousedown', e => resizeHandler(e, boxWrapper, box, false, true, false, true));
    bottomMid.addEventListener('mousedown', e => resizeHandler(e, boxWrapper, box, false, false, false, true));
    leftTop.addEventListener('mousedown', e => resizeHandler(e, boxWrapper, box, true, true, true, true));
    rightTop.addEventListener('mousedown', e => resizeHandler(e, boxWrapper, box, false, true, true, true));
    rightBottom.addEventListener('mousedown', e => resizeHandler(e, boxWrapper, box, false, false, true, true));
    leftBottom.addEventListener('mousedown', e => resizeHandler(e, boxWrapper, box, true, false, true, true));
    rotate.addEventListener('mousedown', e => rotateHandler(e, boxWrapper, box), false);
}

function repositionBox(boxWrapper, x, y) {
    boxWrapper.style.left = x + 'px';
    boxWrapper.style.top = y + 'px';
}

function resizeBox(box, w, h, xScale, yScale) {
    box.style.width = w + 'px';
    box.style.height = h + 'px';

    for (var child of box.querySelectorAll('.box-child')) {
        child.style.transform = `scale(${xScale}, ${yScale})`;
    }
}


function getCurrentRotation(el) {
    var st = window.getComputedStyle(el, null);
    var tm = st.getPropertyValue("-webkit-transform") ||
        st.getPropertyValue("-moz-transform") ||
        st.getPropertyValue("-ms-transform") ||
        st.getPropertyValue("-o-transform") ||
        st.getPropertyValue("transform")
    "none";
    if (tm != "none") {
        var values = tm.split('(')[1].split(')')[0].split(',');
        var angle = Math.round(Math.atan2(values[1], values[0]) * (180 / Math.PI));
        return (angle < 0 ? angle + 360 : angle);
    }
    return 0;
}

function rotateBox(boxWrapper, deg) {
    boxWrapper.style.transform = `rotate(${deg}deg)`;
}

function dragHandler(event, boxWrapper) {
    if (event.target.className.indexOf("dot") > -1) {
        return;
    }

    boxWrapper.querySelector('.box').style.cursor = 'grabbing';

    initX = boxWrapper.offsetLeft;
    initY = boxWrapper.offsetTop;
    mousePressX = event.clientX;
    mousePressY = event.clientY;


    function eventMoveHandler(event) {
        repositionBox(boxWrapper, initX + (event.clientX - mousePressX),
            initY + (event.clientY - mousePressY));
    }

    boxWrapper.addEventListener('mousemove', eventMoveHandler, false);
    window.addEventListener('mouseup', function eventEndHandler() {
        boxWrapper.querySelector('.box').style.cursor = 'grab';
        let video = document.getElementById('video');
        mapping[boxWrapper.id]["top"] = Math.round(parseFloat(boxWrapper.style.top) * 100.0 / window.innerHeight * 1000) / 1000;
        mapping[boxWrapper.id]["left"] = Math.round((parseFloat(boxWrapper.style.left) - parseFloat(video.style.left)) * 100.0 / parseFloat(video.style.width) * 1000) / 1000;

        boxWrapper.removeEventListener('mousemove', eventMoveHandler, false);
        window.removeEventListener('mouseup', eventEndHandler);
    }, false);
}

// handle resize
function resizeHandler(event, boxWrapper, box, left = false, top = false, xResize = false, yResize = false) {
    initX = boxWrapper.offsetLeft;
    initY = boxWrapper.offsetTop;
    mousePressX = event.clientX;
    mousePressY = event.clientY;

    const boxChildWidth = box.querySelector('.box-child').offsetWidth;
    const boxChildHeight = box.querySelector('.box-child').offsetHeight;

    initW = box.offsetWidth;
    initH = box.offsetHeight;

    initRotate = getCurrentRotation(boxWrapper);
    var initRadians = initRotate * Math.PI / 180;
    var cosFraction = Math.cos(initRadians);
    var sinFraction = Math.sin(initRadians);

    var initialXScale = mapping[boxWrapper.id]["x-scaling"], initialYScale = mapping[boxWrapper.id]["y-scaling"];

    function eventMoveHandler(event) {
        var wDiff = (event.clientX - mousePressX);
        var hDiff = (event.clientY - mousePressY);
        var rotatedWDiff = cosFraction * wDiff + sinFraction * hDiff;
        var rotatedHDiff = cosFraction * hDiff - sinFraction * wDiff;

        var newW = initW, newH = initH, newX = initX, newY = initY;

        // calculate new width and height
        if (xResize) {
            if (left) {
                newW = initW - rotatedWDiff;
            } else {
                newW = initW + rotatedWDiff;
            }
            if (newW < minWidth) {
                newW = minWidth;
            }
        }

        if (yResize) {
            if (top) {
                newH = initH - rotatedHDiff;
            } else {
                newH = initH + rotatedHDiff;
            }
            if (newH < minHeight) {
                newH = minHeight;
            }
        }

        var scale, xScale, yScale;
        // constrain aspect ratio, if a corner is being dragged
        if (xResize && yResize) {
            scale = Math.max(newW / initW, newH / initH);
            newW = scale * initW;
            newH = scale * initH;
        }

        // recalculate position
        if (xResize) {
            if (left) {
                rotatedWDiff = initW - newW;
            } else {
                rotatedWDiff = newW - initW;
            }
            newX += 0.5 * rotatedWDiff * cosFraction;
            newY += 0.5 * rotatedWDiff * sinFraction;
        }


        if (yResize) {
            if (top) {
                rotatedHDiff = initH - newH;
            } else {
                rotatedHDiff = newH - initH;
            }
            newX -= 0.5 * rotatedHDiff * sinFraction;
            newY += 0.5 * rotatedHDiff * cosFraction;
        }

        xScale = (newW - 4) / boxChildWidth;
        yScale = (newH - 4) / boxChildHeight;

        resizeBox(box, boxChildWidth * xScale + 4, boxChildHeight * yScale + 4, xScale, yScale);
        repositionBox(boxWrapper, newX, newY);
    }


    window.addEventListener('mousemove', eventMoveHandler, false);
    window.addEventListener('mouseup', function eventEndHandler() {
        let video = document.getElementById('video');
        mapping[boxWrapper.id]["top"] = Math.round(parseFloat(boxWrapper.style.top) * 100.0 / window.innerHeight * 1000) / 1000;
        mapping[boxWrapper.id]["left"] = Math.round((parseFloat(boxWrapper.style.left) - parseFloat(video.style.left)) * 100.0 / parseFloat(video.style.width) * 1000) / 1000;

        var child = box.querySelector('.box-child');
        var matrix = new WebKitCSSMatrix(child.style.transform);
        mapping[boxWrapper.id]["x-scaling"] = matrix.m11;
        mapping[boxWrapper.id]["y-scaling"] = matrix.m22;

        window.removeEventListener('mousemove', eventMoveHandler, false);
        window.removeEventListener('mouseup', eventEndHandler);
    }, false);
}

function rotateHandler(event, boxWrapper, box) {
    var arrowRects = box.getBoundingClientRect();
    var arrowX = arrowRects.left + arrowRects.width / 2;
    var arrowY = arrowRects.top + arrowRects.height / 2;

    function eventMoveHandler(event) {
        var angle = Math.atan2(event.clientY - arrowY, event.clientX - arrowX) + Math.PI / 2;
        rotateBox(boxWrapper, angle * 180 / Math.PI);
        mapping[boxWrapper.id]["rotation"] = angle * 180 / Math.PI;
    }

    window.addEventListener('mousemove', eventMoveHandler, false);

    window.addEventListener('mouseup', function eventEndHandler() {
        window.removeEventListener('mousemove', eventMoveHandler, false);
        window.removeEventListener('mouseup', eventEndHandler);
    }, false);
}

async function commandsList(var_name) {
    currentCommandsView = var_name;
    let commandsListContent;
    switch (currentCommandsView) {
        case "COMMANDS":
            document.getElementById('cmdListTitle').innerHTML = "Commands List";
            listItemUnclicked();
            document.getElementById('cmdResponse').placeholder = "Command Response";
            for (var ele of document.querySelectorAll(".collapsable")) {
                ele.classList.remove("d-none");
                ele.classList.add("d-block");
            }
            commandsListContent = document.getElementById('commandsListContent');
            commandsListContent.innerHTML = "";
            for (let row of commandsViewVariables['COMMANDS']) {
                commandsListContent.appendChild(htmlToElement(`<div class="h5 listItem border-bottom" onclick="listItemClicked(this);">${row}</div>`));
            }
            break;
        case "COUNTER":
            document.getElementById('cmdListTitle').innerHTML = "Counters List";
            listItemUnclicked();
            document.getElementById('cmdResponse').placeholder = "0";
            for (var ele of document.querySelectorAll(".collapsable")) {
                ele.classList.add("d-none");
            }
            response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/variables?var=counters`);
            if (!response.ok) {
                throw new Error("HTTP status " + response.status);
            }
            data = await response.json();
            content = JSON.parse(data['value']);
            commandsListContent = document.getElementById('commandsListContent');
            commandsListContent.innerHTML = "";
            for (let row of commandsViewVariables['COUNTER']) {
                commandsListContent.appendChild(htmlToElement(`<div class="h5 listItem border-bottom" onclick="listItemClicked(this);">${row}</div>`));
            }
            break;
        case "KIMEXPLAINS":
            document.getElementById('cmdListTitle').innerHTML = "!Kimexplains List";
            listItemUnclicked();
            document.getElementById('cmdResponse').placeholder = "Kim Explains #44: clip URL";
            for (var ele of document.querySelectorAll(".collapsable")) {
                ele.classList.add("d-none");
            }
            response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/variables?var=kimexplains`);
            if (!response.ok) {
                throw new Error("HTTP status " + response.status);
            }
            data = await response.json();
            content = JSON.parse(data['value']);
            commandsListContent = document.getElementById('commandsListContent');
            commandsListContent.innerHTML = "";
            for (let i = 0; i < commandsViewVariables['KIMEXPLAINS']; i++) {
                commandsListContent.appendChild(htmlToElement(`<div class="h5 listItem border-bottom" onclick="listItemClicked(this);">!kimexplains ${i + 1}</div>`));
            }
            break;
        case "FIERCE":
            document.getElementById('cmdListTitle').innerHTML = "!Fierce List";
            listItemUnclicked();
            document.getElementById('cmdResponse').placeholder = "Fierce hates something inaboxMRDR";
            for (var ele of document.querySelectorAll(".collapsable")) {
                ele.classList.add("d-none");
            }
            response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/variables?var=fierce`);
            if (!response.ok) {
                throw new Error("HTTP status " + response.status);
            }
            data = await response.json();
            content = JSON.parse(data['value']);
            commandsListContent = document.getElementById('commandsListContent');
            commandsListContent.innerHTML = "";
            for (let i = 0; i < commandsViewVariables['FIERCE']; i++) {
                commandsListContent.appendChild(htmlToElement(`<div class="h5 listItem border-bottom" onclick="listItemClicked(this);">!fierce ${i + 1}</div>`));
            }
            break;
        default:
            break;
    }
    let cmdResponse = document.getElementById('cmdResponse');
    let cmdGlobal = document.getElementById('cmdGlobal');
    let cmdUser = document.getElementById('cmdUser');
    let cmdSchedule = document.getElementById('cmdSchedule');
    cmdResponse.classList.remove('is-invalid');
    cmdGlobal.classList.remove('is-invalid');
    cmdUser.classList.remove('is-invalid');
    cmdSchedule.classList.remove('is-invalid');
}

async function listItemClicked(item) {
    if (lastClickedListItem == item) {
        return;
    }
    if (lastClickedListItem != null) {
        lastClickedListItem.style.background = 'white';
    }
    item.style.background = listItemSelectedColor;
    lastClickedListItem = item;

    document.getElementById('cmdName').innerHTML = item.innerHTML;
    let cmdResponse = document.getElementById('cmdResponse');
    let cmdPermission = document.getElementById('cmdPermission');
    let cmdType = document.getElementById('cmdType');
    let cmdGlobal = document.getElementById('cmdGlobal');
    let cmdUser = document.getElementById('cmdUser');
    let cmdSchedule = document.getElementById('cmdSchedule');
    let saveIcon = document.getElementById('saveIcon');
    let trashIcon = document.getElementById('trashIcon');

    cmdResponse.disabled = false;
    cmdPermission.disabled = false;
    cmdType.disabled = false;
    cmdGlobal.disabled = false;
    cmdUser.disabled = false;
    cmdSchedule.disabled = false;
    saveIcon.disabled = false;
    trashIcon.disabled = false;

    cmdResponse.classList.remove('is-invalid');
    cmdGlobal.classList.remove('is-invalid');
    cmdUser.classList.remove('is-invalid');
    cmdSchedule.classList.remove('is-invalid');

    let response, data;
    switch (currentCommandsView) {
        case "COMMANDS":
            response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/commands?var=${encodeURIComponent(item.innerHTML)}`);
            if (!response.ok) {
                throw new Error("HTTP status " + response.status);
            }
            data = await response.json();

            cmdResponse.value = data.command_response;
            cmdPermission.value = data.command_permission;
            cmdType.value = data.command_type;
            cmdGlobal.value = data.command_cooldown_global;
            cmdUser.value = data.command_cooldown_user;
            cmdSchedule.value = data.command_cooldown_schedule;
            break;
        case "COUNTER":
            response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/counters?var=${encodeURIComponent(item.innerHTML)}`);
            if (!response.ok) {
                throw new Error("HTTP status " + response.status);
            }
            data = await response.json();
            cmdResponse.value = data.var_val;
            break;
        case "KIMEXPLAINS":
            trashIcon.disabled = true;
            response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/kimexplains?var=${encodeURIComponent(item.innerHTML.split(' ')[1])}`);
            if (!response.ok) {
                throw new Error("HTTP status " + response.status);
            }
            data = await response.json();
            cmdResponse.value = data.quotes_val;
            break;
        case "FIERCE":
            trashIcon.disabled = true;
            response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/fierce?var=${encodeURIComponent(item.innerHTML.split(' ')[1])}`);
            if (!response.ok) {
                throw new Error("HTTP status " + response.status);
            }
            data = await response.json();
            cmdResponse.value = data.quotes_val;
            break;
        default:
            break;
    }
}

function listItemUnclicked() {
    if (lastClickedListItem != null) {
        lastClickedListItem.style.background = 'white';
    }
    lastClickedListItem = null;

    document.getElementById('cmdName').innerHTML = "-No Item Selected-";
    let cmdResponse = document.getElementById('cmdResponse');
    let cmdPermission = document.getElementById('cmdPermission');
    let cmdType = document.getElementById('cmdType');
    let cmdGlobal = document.getElementById('cmdGlobal');
    let cmdUser = document.getElementById('cmdUser');
    let cmdSchedule = document.getElementById('cmdSchedule');
    let saveIcon = document.getElementById('saveIcon');
    let trashIcon = document.getElementById('trashIcon');

    cmdResponse.disabled = true;
    cmdPermission.disabled = true;
    cmdType.disabled = true;
    cmdGlobal.disabled = true;
    cmdUser.disabled = true;
    cmdSchedule.disabled = true;
    saveIcon.disabled = true;
    trashIcon.disabled = true;

    cmdResponse.value = '';
    cmdPermission.value = 'E';
    cmdType.value = 'SIMPLE';
    cmdGlobal.value = '';
    cmdUser.value = '';
    cmdSchedule.value = '';
}

function newListItem() {
    if (editing) {
        return;
    }
    editing = true;
    let menu = document.getElementById("newListItem");
    let mask = document.getElementById("mask");

    document.getElementById('commandsView').style.pointerEvents = "none";
    document.getElementById('commandsDetails').style.pointerEvents = "none";

    let newCmdName = document.getElementById('newCmdName');
    let newCmdResponse = document.getElementById('newCmdResponse');

    switch (currentCommandsView) {
        case "COMMANDS":
            newCmdName.style.display = 'block';
            newCmdResponse.style.display = 'block';
            newCmdName.placeholder = "!commandName";
            newCmdResponse.placeholder = "Command Response";
            newCmdName.value = "";
            newCmdResponse.value = "";
            newCmdName.classList.add("is-invalid");
            newCmdResponse.classList.add("is-invalid");
            document.getElementById('newCmdTitle').innerHTML = "New Command";
            break;
        case "COUNTER":
            newCmdName.style.display = 'block';
            newCmdResponse.style.display = 'none';
            newCmdName.placeholder = "counterName";
            newCmdName.value = "";
            newCmdName.classList.add("is-invalid");
            document.getElementById('newCmdTitle').innerHTML = "New Counter";
            break;
        case "KIMEXPLAINS":
            newCmdName.style.display = 'none';
            newCmdResponse.style.display = 'block';
            newCmdResponse.placeholder = "Kim Explains #44: clip URL";
            newCmdResponse.value = "";
            newCmdResponse.classList.add("is-invalid");
            document.getElementById('newCmdTitle').innerHTML = "New KimExplains Quote";
            break;
        case "FIERCE":
            newCmdName.style.display = 'none';
            newCmdResponse.style.display = 'block';
            newCmdResponse.placeholder = "Fierce hates something inaboxMRDR";
            newCmdResponse.value = "";
            newCmdResponse.classList.add("is-invalid");
            document.getElementById('newCmdTitle').innerHTML = "New Fierce Quote";
            break;
        default:
            break;
    }

    mask.style.display = "block";
    menu.style.display = "flex";
    menu.style.animation = "menuAnimation 0.5s forwards";
}

function disable(e) {
    e.stopPropagation();
    e.preventDefault();
}

async function addListItem() {
    document.addEventListener("click", disable, true);
    let newCmdName = document.getElementById('newCmdName');
    let newCmdResponse = document.getElementById('newCmdResponse');
    let config, response, data;

    switch (currentCommandsView) {
        case "COMMANDS":
            if (newCmdName.classList.contains("is-invalid")) {
                alert("Command name invalid. Operation cancelled.", "warning");
                break;
            }
            if (newCmdResponse.classList.contains("is-invalid")) {
                alert("Command Response invalid. Operation cancelled.", "warning");
                break;
            }
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_cmd", "cmd": [`!cmd add ${newCmdName.value} ${newCmdResponse.value.replaceAll('\n', ' ')}`] })
            }
            break;
        case "COUNTER":
            if (newCmdName.classList.contains("is-invalid")) {
                alert("Counter name invalid. Operation cancelled.", "warning");
                break;
            }
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_cmd", "cmd": [`!editcounter ${newCmdName.value} 0`] })
            }
            break;
        case "KIMEXPLAINS":
            if (newCmdResponse.classList.contains("is-invalid")) {
                alert("Quote content invalid. Operation cancelled.", "warning");
                break;
            }
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_quotes", "cmd": [`!kimexplains add ${newCmdResponse.value.replaceAll('\n', ' ')}`] })
            }
            break;
        case "FIERCE":
            if (newCmdResponse.classList.contains("is-invalid")) {
                alert("Quote content invalid. Operation cancelled.", "warning");
                break;
            }
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_quotes", "cmd": [`!fierce add ${newCmdResponse.value.replaceAll('\n', ' ')}`] })
            }
            break;
        default:
            break;
    }

    if (config) {
        alert("Please wait...", "info", true);
        response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot-web?channel=inabox44`, config);
        document.querySelectorAll('.alert-info').forEach(e => e.remove());
        if (!response.ok) {
            alert("Error: Request timed out. Check if bot is down.", "danger");
        }
        else {
            data = await response.json();
            for (let feedback of data) {
                if (feedback.includes("[ERROR]")) {
                    alert(feedback, "danger");
                }
                else {
                    let commandsListContent = document.getElementById('commandsListContent');
                    let highlight, ele;
                    switch (currentCommandsView) {
                        case "COMMANDS":
                            commandsViewVariables['COMMANDS'].push(newCmdName.value);
                            commandsViewVariables['COMMANDS'] = commandsViewVariables['COMMANDS'].sort();
                            commandsListContent.innerHTML = "";
                            for (let row of commandsViewVariables['COMMANDS']) {
                                ele = htmlToElement(`<div class="h5 listItem border-bottom" onclick="listItemClicked(this);">${row}</div>`);
                                if (row == newCmdName.value) {
                                    highlight = ele;
                                }
                                commandsListContent.appendChild(ele);
                            }
                            break;
                        case "COUNTER":
                            commandsViewVariables['COUNTER'].push(newCmdName.value);
                            commandsViewVariables['COUNTER'] = commandsViewVariables['COUNTER'].sort();
                            commandsListContent.innerHTML = "";
                            for (let row of commandsViewVariables['COUNTER']) {
                                ele = htmlToElement(`<div class="h5 listItem border-bottom" onclick="listItemClicked(this);">${row}</div>`);
                                if (row == newCmdName.value) {
                                    highlight = ele;
                                }
                                commandsListContent.appendChild(ele);
                            }
                            break;
                        case "KIMEXPLAINS":
                            commandsViewVariables['KIMEXPLAINS'] += 1;
                            highlight = htmlToElement(`<div class="h5 listItem border-bottom" onclick="listItemClicked(this);">!kimexplains ${commandsViewVariables['KIMEXPLAINS']}</div>`);
                            commandsListContent.appendChild(highlight);
                            break;
                        case "FIERCE":
                            commandsViewVariables['FIERCE'] += 1;
                            highlight = htmlToElement(`<div class="h5 listItem border-bottom" onclick="listItemClicked(this);">!fierce ${commandsViewVariables['FIERCE']}</div>`);
                            commandsListContent.appendChild(highlight);
                            break;
                        default:
                            return;
                    }
                    highlight.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
                    await listItemClicked(highlight);
                    alert(feedback, "success");
                }
            }
        }
    }

    let menu = document.getElementById("newListItem");
    let mask = document.getElementById("mask");

    document.getElementById('commandsView').style.pointerEvents = "auto";
    document.getElementById('commandsDetails').style.pointerEvents = "auto";

    menu.style.animation = "menuAnimationReversed 0.2s forwards";
    mask.style.display = "none";
    setTimeout(() => {
        menu.style.display = "none";
        editing = false;
    }, 200);
    document.removeEventListener('click', disable, true);
}

async function saveListItem(event) {
    document.addEventListener("click", disable, true);
    let config, response, data;
    let cmdName = document.getElementById('cmdName');
    let cmdResponse = document.getElementById('cmdResponse');
    let cmdPermission = document.getElementById('cmdPermission');
    let cmdType = document.getElementById('cmdType');
    let cmdGlobal = document.getElementById('cmdGlobal');
    let cmdUser = document.getElementById('cmdUser');
    let cmdSchedule = document.getElementById('cmdSchedule');

    switch (currentCommandsView) {
        case "COMMANDS":
            if (cmdResponse.classList.contains("is-invalid")) {
                alert("Command Response invalid. Operation cancelled.", "warning");
                break;
            }
            if (cmdGlobal.classList.contains("is-invalid")) {
                alert("Command Global Cooldown invalid. Operation cancelled.", "warning");
                break;
            }
            if (cmdUser.classList.contains("is-invalid")) {
                alert("Command User Cooldown invalid. Operation cancelled.", "warning");
                break;
            }
            if (cmdSchedule.classList.contains("is-invalid")) {
                alert("Command Schedule Cooldown invalid. Operation cancelled.", "warning");
                break;
            }
            config = {
                method: 'POST',
                body: JSON.stringify({
                    "action": "web_api_cmd", "cmd": [
                        `!cmd edit ${cmdName.innerHTML} ${cmdResponse.value.replaceAll('\n', ' ')}`,
                        `!cmd options ${cmdName.innerHTML} permission=${cmdPermission.value},type=${cmdType.value},global=${cmdGlobal.value},user=${cmdUser.value},schedule=${cmdSchedule.value}`
                    ]
                })
            }
            break;
        case "COUNTER":
            if (cmdResponse.classList.contains("is-invalid") || !parseInt(cmdResponse.value.trim())) {
                alert("Counter value invalid. Operation cancelled.", "warning");
                break;
            }
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_cmd", "cmd": [`!editcounter ${cmdName.innerHTML} ${parseInt(cmdResponse.value.trim())}`] })
            }
            break;
        case "KIMEXPLAINS":
            if (cmdResponse.classList.contains("is-invalid")) {
                alert("Quote content invalid. Operation cancelled.", "warning");
                break;
            }
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_quotes", "cmd": [`!kimexplains edit ${cmdName.innerHTML.split(' ')[1]} ${cmdResponse.value.replaceAll('\n', ' ')}`] })
            }
            break;
        case "FIERCE":
            if (cmdResponse.classList.contains("is-invalid")) {
                alert("Quote content invalid. Operation cancelled.", "warning");
                break;
            }
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_quotes", "cmd": [`!fierce edit ${cmdName.innerHTML.split(' ')[1]} ${cmdResponse.value.replaceAll('\n', ' ')}`] })
            }
            break;
        default:
            return;
    }

    if (config) {
        alert("Please wait...", "info", true);
        response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot-web?channel=inabox44`, config);
        document.querySelectorAll('.alert-info').forEach(e => e.remove());
        if (!response.ok) {
            alert("Error: Request timed out. Check if bot is down.", "danger");
        }
        else {
            data = await response.json();
            for (let feedback of data) {
                if (feedback.includes("[ERROR]")) {
                    alert(feedback, "danger");
                }
                else {
                    alert(feedback, "success");
                }
            }
        }
    }
    document.removeEventListener('click', disable, true);
}

async function deleteListItem(event) {
    document.addEventListener("click", disable, true);
    let config, response, data;
    let cmdName = document.getElementById('cmdName');

    switch (currentCommandsView) {
        case "COMMANDS":
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_cmd", "cmd": [`!cmd del ${cmdName.innerHTML}`] })
            }
            break;
        case "COUNTER":
            config = {
                method: 'POST',
                body: JSON.stringify({ "action": "web_api_cmd", "cmd": [`!deletecounter ${cmdName.innerHTML}`] })
            }
            break;
        default:
            return;
    }

    if (config) {
        alert("Please wait...", "info", true);
        response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot-web?channel=inabox44`, config);
        document.querySelectorAll('.alert-info').forEach(e => e.remove());
        if (!response.ok) {
            alert("Error: Request timed out. Check if bot is down.", "danger");
        }
        else {
            data = await response.json();
            for (let feedback of data) {
                if (feedback.includes("[ERROR]")) {
                    alert(feedback, "danger");
                }
                else {
                    alert(feedback, "success");
                    let removeIndex;
                    switch (currentCommandsView) {
                        case "COMMANDS":
                            removeIndex = commandsViewVariables['COMMANDS'].indexOf(cmdName.innerHTML);
                            if (removeIndex !== -1) {
                                commandsViewVariables['COMMANDS'].splice(removeIndex, 1);
                            }
                            await commandsList('COMMANDS');
                            break;
                        case "COUNTER":
                            removeIndex = commandsViewVariables['COUNTER'].indexOf(cmdName.innerHTML);
                            if (removeIndex !== -1) {
                                commandsViewVariables['COUNTER'].splice(removeIndex, 1);
                            }
                            await commandsList('COUNTER');
                            break;
                        default:
                            return;
                    }
                }
            }
        }
    }
    document.removeEventListener('click', disable, true);
}

async function loadVariables() {
    let response, data;
    if (!commandsViewVariables['COMMANDS']) {
        response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/variables?var=commands`);
        if (!response.ok) {
            throw new Error("HTTP status " + response.status);
        }
        data = await response.json();
        commandsViewVariables['COMMANDS'] = JSON.parse(data['value']).sort();
    }
    if (!commandsViewVariables['COUNTER']) {
        response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/variables?var=counters`);
        if (!response.ok) {
            throw new Error("HTTP status " + response.status);
        }
        data = await response.json();
        commandsViewVariables['COUNTER'] = JSON.parse(data['value']);
    }
    if (!commandsViewVariables['KIMEXPLAINS']) {
        response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/variables?var=kimexplains`);
        if (!response.ok) {
            throw new Error("HTTP status " + response.status);
        }
        data = await response.json();
        commandsViewVariables['KIMEXPLAINS'] = JSON.parse(data['value']);
    }
    if (!commandsViewVariables['FIERCE']) {
        response = await fetch(`https://apoorlywrittenbot.cc/restricted/inabot/variables?var=fierce`);
        if (!response.ok) {
            throw new Error("HTTP status " + response.status);
        }
        data = await response.json();
        commandsViewVariables['FIERCE'] = JSON.parse(data['value']);
    }
}