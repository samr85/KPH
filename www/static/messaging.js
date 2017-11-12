var socket;

function sendMessage(message)
{
    socket.send(message)
}

function logError(message)
{
    addLogMessage(message, "errorMessage")
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

    var host = "ws://" + window.location.host + "/ws";
    socket = new WebSocket(host);

    if (socket) {
        socket.onopen = function (msg) {
            if (connectionBroken)
            {
                connectionBroken = false
                addLogMessage("Connection reestablished")
            }
        }
        socket.onmessage = function (msg) {
            message = msg.data
            if (message.startsWith("js: ")) {
                js = message.substring(4);
                eval(js);
            } else if (message.toLowerCase().startsWith("error: ")) {
                logError(message)
            }
            else {
                addLogMessage(message)
            }
        }
        socket.onclose = function (msg) {
            if (connectionBroken == false) {
                logError("Connection lost, attempting to reconnect...")
                connectionBroken = true
            }
            setTimeout(createWebSocket, 3000)
        }
    }

});