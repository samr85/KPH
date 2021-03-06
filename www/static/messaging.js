'use strict';
var SOCKET;

function sendMessage(message)
{
    console.log("Tx: " + message);
    SOCKET.send(message);
}

function errorHandler(message) {
    logError(message);
}

function jsHandler(message) {
    eval(message);
}

var connectionBroken = false;

$(function createWebSocket() {

    if (!("WebSocket" in window)) {
        alert("Your browser does not support web sockets");
        return;
    }

    SOCKET = new WebSocket("ws://" + window.location.host + "/ws");

    if (SOCKET) {
        SOCKET.onopen = function (msg) {
            if (connectionBroken) {
                connectionBroken = false;
                closeMessageById("connectionBroken");
            }
            // Tell the python handler what sections we're interested in
            if (requestSections) {
                requestSections();
            }
        };
        SOCKET.onmessage = function (msg) {
            console.log("Rx: " + msg.data);
            var messageString = msg.data;
            var delim = messageString.indexOf(" ");
            var messageType = messageString.substr(0, delim);
            // Remove and ignore a colon if one has been added
            if (messageType.charAt(messageType.length - 1) === ':') {
                messageType = messageType.substr(0, messageType.length - 1);
            }
            // If we have a handler function for this message type, call it
            if (window[messageType + "Handler"]) {
                var messageContents = messageString.substr(delim + 1);
                window[messageType + "Handler"](messageContents);
            }
            else {
                errorHandler("Recieved unknown command: <br />" + messageString);
            }
        };
        SOCKET.onclose = function (msg) {
            if (connectionBroken === false) {
                logError("Connection lost, attempting to reconnect...", "connectionBroken");
                connectionBroken = true;
            }
            setTimeout(createWebSocket, 3000);
        };
    }

});
