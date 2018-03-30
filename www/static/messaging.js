var SOCKET;

function sendMessage(message)
{
    console.log("Tx: " + message)
    SOCKET.send(message)
}

function errorHandler(message) {
    logError("Error: " + message);
}

function jsHandler(message) {
    eval(message);
}

function sectionHandlerUNUSED(message) {
    var msgList = message.split(" ")
    if (msgList.length < 2) {
        errorHandler("Invalid section message: " + message)
        return
    }
    var div = $("#" + msgList[0])
    if (div.length != 1) {
        errorHandler("Invalid div to modify: " + msgList[0])
        return
    }
    div = div[0]
    var action = msgList[1]
    if (action == "remove") {
        div.parentNode.removeChild(div)
        return
    }
    else if (action == "append" || action == "replace") {
        if (msgList.length != 3) {
            errorHandler("Invalid section message: " + message)
            return
        }
        $.get(msgList[2])
            .done(function (data) {
                if (action == "append") {
                    div.innerHTML += data
                } else {
                    div.innerHTML = data
                }
            })
            .error(function () {
                errorHandler("Error requesting div refresh for " + divName)
            })
    } else {
        errorHandler("Unknown action: " + action)
    }
}

function logError(message)
{
    console.log(message)
    addLogMessage(message, "errorMessage");
}

function addLogMessage(message, type = null)
{
    var s = document.createElement("div");
    if (type) {
        s.className += " " + type
    }
    s.innerHTML = message;
    cont = $("#messageLog")[0];
    cont.appendChild(s);
    cont.scrollTop = cont.scrollHeight;
}
connectionBroken = false

$(function createWebSocket() {

    if (!("WebSocket" in window)) {
        alert("Your browser does not support web sockets");
        return
    }

    SOCKET = new WebSocket("ws://" + window.location.host + "/ws");

    if (SOCKET) {
        SOCKET.onopen = function (msg) {
            if (connectionBroken)
            {
                connectionBroken = false
                addLogMessage("Connection reestablished")
            }
            // Tell the python handler what sections we're interested in
            if (requestSections)
            {
                requestSections()
            }
        }
        SOCKET.onmessage = function (msg) {
            console.log("Rx: " + msg.data)
            var messageString = msg.data;
            var delim = messageString.indexOf(" ");
            var messageType = messageString.substr(0, delim);
            // Remove and ignore a colon if one has been added
            if (messageType.charAt(messageType.length - 1) == ':') {
                messageType = messageType.substr(0, messageType.length - 1);
            }
            // If we have a handler function for this message type, call it
            if (window[messageType + "Handler"]) {
                var messageContents = messageString.substr(delim + 1);
                window[messageType + "Handler"](messageContents)
            }
            else {
                addLogMessage(messageString)
            }
        }
        SOCKET.onclose = function (msg) {
            if (connectionBroken == false) {
                logError("Connection lost, attempting to reconnect...")
                connectionBroken = true
            }
            setTimeout(createWebSocket, 3000)
        }
    }

});