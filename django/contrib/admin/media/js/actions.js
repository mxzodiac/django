function hideAll(elems) {
  for (var e = 0; e < elems.length; e++) {
    elems[e].style.display = 'none';
  }
}

function showAll(elems) {
  for (var e = 0; e < elems.length; e++) {
    elems[e].style.display = 'block';
  }
}

function hasClass(ele,cls) {
    return ele.className.match(new RegExp('(\\s|^)'+cls+'(\\s|$)'));
}

function addClass(ele,cls) {
    if (!this.hasClass(ele,cls)) ele.className += " "+cls;
}

function removeClass(ele,cls) {
    if (hasClass(ele,cls)) {
        var reg = new RegExp('(\\s|^)'+cls+'(\\s|$)');
        ele.className=ele.className.replace(reg,' ');
    }
}

// Why only store the checkbox selector below and not the result? Because
// if another piece of JavaScript fiddles with rows on the page
// (think AJAX delete), modifying the stored checkboxes later may fail.
var actionForm = document.getElementById('action-form');
var actionCheckboxes = document.getElementsBySelector('#action-form tr input.action-select');
var selectButtons = document.getElementsBySelector('button[name=select_all]');
var deselectButtons = document.getElementsBySelector('button[name=deselect_all]');

var checker = function(checked) {
    if (checked) {
        hideAll(selectButtons);
        showAll(deselectButtons);
    }
    else {
        hideAll(deselectButtons);
        showAll(selectButtons);
    }
    var countCheckBoxes = actionCheckboxes.length;
    if(!countCheckBoxes) {
        objCheckBoxes.checked = checked;
    } else {
        // set the check value for all check boxes
        for(var i = 0; i < countCheckBoxes; i++) {
            objCheckBoxes[i].checked = checked;
        }
    }
}

//call the functions
showAll(selectButtons);
addEvent(selectButtons, 'click', checker(true));
addEvent(deselectButtons, 'click', checker(false));

// Highlight selected rows on change, and trigger the change event in
// case any are selected by default.
addEvent(actionCheckbox, 'change', function () {
    var row = this.parentNode.parentNode;
    if (this.checked) {
        addClass(row, 'selected'); }
    else {
        removeClass(row, 'selected');
    }
})
