var channel_name;
var fonts = [];
var WebFontConfig = {
    google: { families: fonts },
    fontinactive: function (familyName, fvd) {
        alert(`Cannot load "${familyName}"`, "warning");
        fonts = fonts.filter(e => e !== familyName)
    },
    active: async function (familyName, fvd) {
        await redraw();
    },
    inactive: async function (familyName, fvd) {
        await redraw();
    },
    timeout: 1500
}

var mapping = {};
var index = 0;
const font_scale = 25;
const borderColor = '#8f00ff';
const borderAlternateCOlor = '#0dbf0d';
const sidebarDefaultColor = '#6441a5';
const sidebarAlternateColor = '#0a8f0b';
var sidebarCurrentColor = sidebarDefaultColor;
const listItemSelectedColor = '#b3e6ff';
const minWidth = 20;
const minHeight = 20;
const listPageSize = 20;
var initX, initY, mousePressX, mousePressY, initW, initH, initRotate;

var left_INT = 0;
var width_INT = 0;

var lastClickedElement;
var lastClickedListItem;
var highlight_name;
var highlight_ele;
var editing = false;
var commandsView = false;

var imagesDictionary = {};
var imagesInMenu = [];
const patterns = {
    nonEmpty: /^(?!\s*$).+/,
    hex: /^[0-9A-F]{6}$/i,
    positiveInteger: /^[1-9]\d*$/,
    integer: /^-?\d+$/,
    noWhiteSpace: /^\S+$/
}
var intervalList = [];
var emotes = {};

var currentCommandsView = "COMMANDS";

var commandsViewVariables = {};

function pagination_config(var_name) {
    return {
        dataSource: commandsViewVariables[var_name],
        pageSize: listPageSize,
        showPageNumbers: false,
        showNavigator: true,
        showGoInput: true,
        showGoButton: true,
        className: "p-2 mx-auto",
        callback: function (data, pagination) {
            commandsListContent.innerHTML = "";
            let ele;
            for (let row of data) {
                ele = htmlToElement(`<div class="h5 listItem border-bottom" id="generated-${row}" onclick="listItemClicked(this);">${row}</div>`);
                commandsListContent.appendChild(ele);
            }
            let nav = document.querySelectorAll('.paginationjs-nav');
            nav[0].innerHTML = `Page ${pagination.pageNumber}/${Math.ceil(pagination.totalNumber / pagination.pageSize)}`;
        }
    }
}