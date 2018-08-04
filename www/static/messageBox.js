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

function logError(message)
{
    message = "Error: " + message;
    console.log(message);
    addLogMessage(message);
}

function addLogMessage(message)
{
    /* Get last element currently in the log */
    var holder = $('#messageList')[0];
    var section = sectionTypes.get("message");
    if (holder === undefined || section === undefined) {
        console.log("Failed to find message holder for message:");
        console.log(message);
        return;
    }
    var sort = "";
    var lastElement = holder.lastChild;
    if (lastElement) {
        sort = $(lastElement).data("sort");
    }
    sort += "-";
    section.update("extra" + sort, sort, message);
}

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
}
initialiseSection("message", standardSection("messageList", categoriseMessages), []);

function messageBoxToggle(dir) {
    if (dir) {
        $('#messageBoxToggleHide').show();
        $('#messageBoxToggleShow').hide();
        $('#messageList').css("height", "auto");
    } else {
        $('#messageBoxToggleHide').hide();
        $('#messageBoxToggleShow').show();
        $('#messageList').css("height", "2.4em");
        var cont = $("#messageList")[0];
        cont.scrollTop = cont.scrollHeight;
    }
}