function setChannel() {
    const params = new Proxy(new URLSearchParams(window.location.search), {
        get: (searchParams, prop) => searchParams.get(prop),
    });
    channel_name = params.channel;
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