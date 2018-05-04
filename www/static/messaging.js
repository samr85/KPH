'use strict';
var SOCKET;

function sendMessage(message)
{
    console.log("Tx: " + message)
    SOCKET.send(message)
}

function errorHandler(message) {
    logError(message);
}

function jsHandler(message) {
    eval(message);
}

function logError(message)
{
    message = "Error: " + message
    console.log(message)
    addLogMessage(message);
}

function addLogMessage(message)
{
    /* Get last element currently in the log */
    var holder = $('#messageList')[0]
    var section = sectionTypes.get("message")
    if (holder == undefined || section == undefined) {
        console.log("Failed to find message holder for message:");
        console.log(message);
        return;
    }
    var sort = ""
    var lastElement = holder.lastChild
    if (lastElement) {
        sort = $(lastElement).data("sort")
    }
    sort += "-"
    section.update("extra" + sort, sort, message)
}
var connectionBroken = false

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

function categoriseMessages(section) {
    var message = section.innerHTML
    var colonPos = message.indexOf(":")
    if (colonPos) {
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
    var cont = $("#messageList")[0]
    cont.scrollTop = cont.scrollHeight;
}
initialiseSection("message", standardSection("messageList", categoriseMessages), [])