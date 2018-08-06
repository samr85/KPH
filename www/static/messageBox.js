'use strict';

function alertHandler(message) {
    message = window.atob(message);
    var colonPos = message.indexOf(":");
    var msgType = "Message";
    if (colonPos > 0) {
        msgType = message.substr(0, colonPos);
        if (message.charAt(colonPos + 1) === " "){
            colonPos += 1;
        }
        message = message.substr(colonPos + 1);
    }
    $("<div title='" + msgType + "'>" + message + "</div>").dialog({
        buttons: {
            "OK": function () {
                $(this).dialog("close");
            }
        },
        modal: true
        });
}

function logError(message, id)
{
    message = "Error: " + message;
    console.log(message);
    messageBox(message, "Error", "errorMessageBox", id)
}

var messageBoxToggleShown = false
function categoriseMessages(section) {
    var message = section.innerHTML;
    var colonPos = message.indexOf(":");
    if (colonPos > 0) {
        switch (message.substr(0, colonPos).toLowerCase()) {
            case "error":
                section.className += " errorMessage";
                break;
            case "message sent":
                section.className += " messageSent";
                break;

            case "team message":
            case "admin message":
                section.className += " messageReceived";
                break;

            case "announcement":
                section.className += " announcement";
                break;
        }
    }
    var cont = $("#messageList")[0];
    cont.scrollTop = cont.scrollHeight;
    if (!messageBoxToggleShown && $('#messageList')[0].childElementCount > 2)
    {
        messageBoxToggleShown = true;
        $('#messageBoxToggleShow').show();
    }
}
initialiseSection("message", standardSection("messageList", categoriseMessages), []);

function messageBoxToggle(dir) {
    if (dir) {
        $('#messageBoxToggleHide').show();
        $('#messageBoxToggleShow').hide();
        $('#messageList').css("max-height", "none");
    } else {
        $('#messageBoxToggleHide').hide();
        $('#messageBoxToggleShow').show();
        $('#messageList').css("max-height", "2.4em");
        var cont = $("#messageList")[0];
        cont.scrollTop = cont.scrollHeight;
    }
}