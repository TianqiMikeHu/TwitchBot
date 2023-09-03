function setChannel() {
    const params = new Proxy(new URLSearchParams(window.location.search), {
        get: (searchParams, prop) => searchParams.get(prop),
    });
    channel_name = params.channel;
}

function InitializeColorPicler() {
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
    video.style.height = `${window.innerHeight}px`;

    width_INT = (window.innerHeight / 9.0 * 16.0 | 0);
    video.style.width = `${width_INT}px`;

    left_INT = html.clientWidth - width_INT;
    video.style.left = `${left_INT}px`;

    sidebar.style.height = video.style.height;
    sidebar.style.width = video.style.left;
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
}

async function loadInitialJSON(video) {
    let response = await fetch(`https://apoorlywrittenbot.cc/public/json?channel=${channel_name}`);
    if (!response.ok) {
        throw new Error("HTTP status " + response.status);
    }
    let data = await response.json();
    for (const [key, value] of Object.entries(data.coordinates)) {
        let element = create(null);
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
    editButton.style.background = "#d9d9d9";
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
    editButton.style.background = "#6441a5";
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
    resizeBox(img.parentNode.parentNode, img.offsetWidth * mapping[id]["x-scaling"] + 4, img.offsetHeight * mapping[id]["y-scaling"] + 4, mapping[id]["x-scaling"], mapping[id]["y-scaling"]);
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
function addDotsListeners(index) {
    let box = document.getElementById(`box-${index.toString()}`);
    let boxWrapper = document.getElementById(`${index.toString()}`);

    let rightMid = document.getElementById(`right-mid-${index.toString()}`);
    let leftMid = document.getElementById(`left-mid-${index.toString()}`);
    let topMid = document.getElementById(`top-mid-${index.toString()}`);
    let bottomMid = document.getElementById(`bottom-mid-${index.toString()}`);

    let leftTop = document.getElementById(`left-top-${index.toString()}`);
    let rightTop = document.getElementById(`right-top-${index.toString()}`);
    let rightBottom = document.getElementById(`right-bottom-${index.toString()}`);
    let leftBottom = document.getElementById(`left-bottom-${index.toString()}`);
    let rotate = document.getElementById(`rotate-${index.toString()}`);

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