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
var initX, initY, mousePressX, mousePressY, initW, initH, initRotate;

var left_INT = 0;
var width_INT = 0;

var lastClickedElement;
var lastClickedListItem;
var editing = false;
var commandsView = false;

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