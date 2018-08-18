
var idleTime = 0;
setInterval(function () { idleTime++; }, 1000);
function resetIdle(e) { idleTime = 0; }
$(document).mousedown(resetIdle)
$(document).keydown(resetIdle)
if ("ontouchstart" in document) {
    $(document).touchstart(resetIdle)
}
function beeper(_unused) {
    if (!document.hasFocus() || idleTime > 10)
    {
        // only beep once every 3 seconds, and if the user is idle or this window doesn't have focus so user doesn't get bombarded with them!
        if (Date.now() - lastbeep > 3000)
        {
            beep.play();
            lastbeep = Date.now();
        }
    } else {
        console.log("idle time too small: " + idleTime);
    }
}
var beep = new Audio("static/beep.mp3");
var lastbeep = Date.now()

function messageBox(contents, title, classes, id, alert=true) {
    if (id)
    {
        if ($('#' + id).length)
            return
    }

    if (alert) beeper()

    var divHTML = "<div "
    if (id) divHTML += "id='" + id + "' "
    if (title) divHTML += "title='" + title + "' "
    if (classes) divHTML += "class='" + classes + "' "
    divHTML += ">" + contents + "</div>"
    $(divHTML).dialog({
        buttons: {
            "close": function () {
                $(this).dialog("close");
            }
        },
        close: function() {$(this).remove()},
        modal: true
    });
}

function closeMessageById(id) {
    var div = $('#' + id);
    if (div.length)
    {
        div.dialog('close');
    }
}